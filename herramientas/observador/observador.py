"""
Observador de la v14 (pasos 2 y 3). Se engancha desde fuera, como el registro de la v13:

    obs = ObservadorV14("crafter", flags, ajustes, salida="â€¦/episodio.jsonl.gz")
    with observando(obs):
        ...  # ejecutar el episodio como siempre
    resumen = obs.cerrar()

Envuelve `GestorOndaCore.ejecutar_latido` (para leer la Onda al terminar cada latido) y
`SistemaCognitivoTriunico._ejecutar_tres_barridos` (para saber cuÃ¡nta amplitud gasta cada
Componente), y los restaura al salir. Todo el trabajo se hace despuÃ©s del latido: no ocupa el plazo
de la Onda. Su coste se mide aparte y se compara con el tope (`ajustes.tope_coste`).

QuÃ© hace en cada latido (camino rÃ¡pido):
1. Lee las seÃ±ales del mundo (`senales.py`) y los tres indicadores.
2. Elige las K Piezas de mayor arousal de la Onda, sin las del cuerpo ni las motoras
   (`ajustes.clases_excluidas`), y les asigna su Sistema de origen.
3. Presupuesto de memoria virtual, en orden S1, S2, S3: S1 siempre guarda; S2 y S3 solo si al
   terminar les queda `restante_minimo_s2_s3` del presupuesto, y como mucho `fraccion_sobrante`
   de lo que les queda. Cada guardado y cada recuperaciÃ³n cuestan unidades virtuales; la amplitud
   real de la Onda no se toca.
4. RecuperaciÃ³n (paso 2, solo se registra): cada Sistema con presupuesto busca, para cada Pieza que
   ha guardado, el registro consolidado mÃ¡s relevante de su clase. Al abrirse un episodio, S3 busca
   el episodio pasado mÃ¡s parecido por su huella de apertura y se anota su signo; al cerrarse, se
   compara con el signo real.
5. Proactiva (paso 3, solo se registra): ver `proactiva.py`.

Mantenimiento (camino lento): en los latidos de sueÃ±o, cada `mantenimiento_cada` latidos y al cerrar.
"""

from __future__ import annotations

import contextlib
import gzip
import json
import math
import os
import time
from typing import Any, Dict, Iterator, List, Optional, Tuple

import numpy as np

from herramientas.observador.almacen import Almacen, Registro
from herramientas.observador.episodios import Segmentador
from herramientas.observador.proactiva import Proactiva
from herramientas.observador.creencias import Creencias
from herramientas.observador.senales import SISTEMAS, leer

ORDEN = {"S1": 0, "S2": 1, "S3": 2}


def _rasgos(p: Any) -> np.ndarray:
    t = p.tensor_sensorial
    base = np.asarray(t, dtype=float).copy() if t is not None else np.zeros(6)
    return np.concatenate([base, [float(p.arousal), float(p.trust)]])


def _modalidad_demostrada(p: Any) -> bool:
    return str(p.product.get("modalidad", "")).startswith("DEMOSTRADO")


class ObservadorV14:
    def __init__(self, mundo: str, flags: Dict[str, Any], ajustes: Dict[str, Any], salida: Optional[str] = None,
                 partida: str = ""):
        self.mundo, self.flags, self.a = mundo, flags, ajustes
        self.activo = flags["memoria_experiencia"] != "apagada" or flags["observar_activa"] or flags["observar_proactiva"]
        self.perfil = flags["memoria_experiencia"]
        self.partida = partida
        self.almacen = Almacen(olvido=ajustes["olvido"])
        self.seg = Segmentador(ajustes["episodio"], ajustes["proactiva"]["tolerancia_neutro"], partida)
        self.pro = Proactiva(ajustes["proactiva"])
        self._f = gzip.open(salida, "wt", encoding="utf-8") if salida else None
        self._cola: List[Dict[str, Any]] = []
        self.creencias = Creencias(salida) if (ajustes["creencias"] and salida) else None
        self._comps: List[Dict[str, Any]] = []
        self._exp_s3_antes: set = set()
        self._ultimo_core: Any = None
        self._ultimo_senal: Optional[Dict[str, Any]] = None
        self.ms_latido: List[float] = []
        self.ms_mantenimiento: List[float] = []
        self.plazos: set = set()
        self.cerrados: List[Dict[str, Any]] = []
        self.predicciones_ep: Dict[str, Dict[str, Any]] = {}
        self.aciertos_ep: List[Dict[str, Any]] = []
        self.recuperaciones = 0
        self.recuperaciones_validas: List[Dict[str, Any]] = []
        self.pendientes_rec: List[Dict[str, Any]] = []
        self.guardadas = {"S1": 0, "S2": 0, "S3": 0, "Core": 0}
        self.descartadas_presupuesto = 0
        self.clases_guardadas: Dict[str, int] = {}
        self.uso_virtual: Dict[str, List[float]] = {s: [] for s in SISTEMAS}
        self.indicadores: List[Dict[str, Any]] = []
        self.s3 = {"proyectadas": 0, "consumidas": 0, "sorpresas": 0, "abiertas_final": 0}

    # ------------------------------------------------------------------------------------------
    def antes(self, core: Any) -> None:
        self._comps = []
        self._exp_s3_antes = set(getattr(core.proactiva, "expectativas", {}).keys())

    def despues(self, core: Any, onda: Any) -> None:
        if not self.activo:
            return
        t0 = time.perf_counter()
        self._ultimo_core = core
        s = leer(core, onda, self.a["senales_episodio"], self.a["peligro_crafter"])
        self._ultimo_senal = s
        self.plazos.add(s["plazo_ms"])
        fila: Dict[str, Any] = {
            "tipo": "latido", "n": s["n"], "indicadores": s["indicadores"],
            # Campos para los anÃ¡lisis fuera del latido (A1, C1 a C3)
            "comando": s["comando"], "objetivo": s["objetivo"], "sistema": s["sistema_ganador"],
            "cuerpo": {"ali": round(s["ali_soma"], 3), "vit": round(s["vit_soma"], 3), "afecto": s["afecto"],
                       "cortisol": round(s["cortisol"], 4), "urgencia": round(s["urgencia_s1"], 4),
                       "peligro_s1": round(s["peligro_externo"], 4), "carga": s["carga"], "vivo": s["vivo_soma"]},
            "ejecutado": s["ejecutado"], "ubicacion": s["ubicacion"], "formales": s["formales"],
            "amp": [s["amp_usada"], s["amp_max"]], "sorpresa": s["sorpresa"],
        }
        if "mundo" in s:
            fila.update({"mundo": s["mundo"], "pos": s["pos"], "peligro_juego": s["peligro_juego"]})
        if self.a["registrar_arbitraje"]:  # E5, bloque D
            from herramientas.arbitraje import registro
            fila["arbitraje"] = registro(onda, core.soma)
        if self.flags["indicadores_generales"]:
            self.indicadores.append(s["indicadores"])

        # LÃ­nea base: el bucle de expectativas de S3 que ya existe (solo se cuenta)
        despues_exp = set(getattr(core.proactiva, "expectativas", {}).keys())
        consumidas = self._exp_s3_antes - despues_exp
        self.s3["consumidas"] += len(consumidas)
        self.s3["proyectadas"] += 1 if onda.reactiva.acc.get("Impulso") else 0
        self.s3["sorpresas"] += 1 if s["sorpresa"] else 0
        self.s3["abiertas_final"] = len(despues_exp)

        # Episodio (seÃ±ales del mundo)
        ev_seg = self.seg.paso(s)
        cerrados_ahora: List[str] = []
        if ev_seg["cierra"] is not None:
            cerrados_ahora.append(self._cierre_episodio(ev_seg["cierra"]))
        ep_abierto = self.seg.abierto["id"] if self.seg.abierto else None

        # 2. SelecciÃ³n de las K Piezas de mayor arousal (sin cuerpo ni motoras)
        excl = set(self.a["clases_excluidas"])
        comp_sis = {c["componente"]: c["sistema"] for c in self._comps}
        cand: List[Tuple[float, str, str, Any, str, str]] = []
        for canal, piezas in onda.reactiva.ef.items():
            if canal in excl:
                continue
            for p in piezas.values():
                if p.tipo_componente in excl:
                    continue
                cand.append((float(p.arousal), str(p.tipo_componente), str(p.id), p, canal, self._origen(p, comp_sis)))
        # Mayor arousal primero; en empate (en Crafter casi todo vale 1,0) gana el Sistema anterior
        # (S1 tiene ventaja) y, despuÃ©s, la clase y el id. Una pieza por entidad: K entidades distintas,
        # no la misma entidad vista desde varias clases (Objeto, Concepto, Sujeto comparten id).
        cand.sort(key=lambda x: (-x[0], ORDEN.get(x[5], 3), x[1], x[2]))
        elegidas, vistos = [], set()
        for c in cand:
            if c[2] in vistos:
                continue
            vistos.add(c[2])
            elegidas.append(c)
            if len(elegidas) >= self.a["k_piezas"]:
                break

        # 3 y 4. Por turnos, en orden fijo S1, S2, S3: cada Sistema guarda sus Piezas elegidas y, si
        # observar_activa, recupera; su disponible se calcula despuÃ©s de lo que gastaron los anteriores.
        mp = self.a["memoria_presupuesto"]
        c_g, c_r = mp["coste_guardar"], mp["coste_recuperar"]
        restante_real = self._restante_por_sistema(s)
        disp: Dict[str, Dict[str, float]] = {}
        gastado_antes = 0.0
        sel_log, recs = [], []
        origen = [(sis_, aro, clase, pid, p, canal) for aro, clase, pid, p, canal, sis_ in elegidas]
        for sis in ("Core",) + SISTEMAS:
            mias = [x for x in origen if x[0] == sis]
            if sis == "Core":
                for _, aro, clase, pid, p, canal in mias:  # lo que no tiene Sistema lo guarda el Core
                    self._guardar(s, sis, aro, clase, pid, p, comp_sis, ep_abierto)
                    sel_log.append({"clase": clase, "id": pid, "arousal": round(aro, 4), "sistema": sis, "canal": canal, "guardada": True})
                continue
            restante = max(0.0, restante_real[sis] - gastado_antes)
            disponible = float(math.floor(mp["fraccion_sobrante"] * restante))
            permitido = sis == "S1" or (self.perfil == "completa" and restante / (s["amp_max"] or 1) >= mp["restante_minimo_s2_s3"])
            usado = 0.0
            guardados_sis = []
            for _, aro, clase, pid, p, canal in mias:
                guardar = sis == "S1" or (permitido and disponible - usado >= c_g)  # S1 siempre guarda
                if guardar:
                    usado += c_g
                    guardados_sis.append(self._guardar(s, sis, aro, clase, pid, p, comp_sis, ep_abierto))
                else:
                    self.descartadas_presupuesto += 1
                sel_log.append({"clase": clase, "id": pid, "arousal": round(aro, 4), "sistema": sis, "canal": canal, "guardada": guardar})
            if self.flags["observar_activa"] and permitido:
                for reg in guardados_sis:
                    if disponible - usado < c_r:
                        break
                    usado += c_r
                    r = self.almacen.recuperar(reg.clase, reg.rasgos, s["n"])
                    self.recuperaciones += 1
                    if r is not None:
                        r.update({"consulta": f"{reg.clase}:{reg.id}", "por": sis, "n": s["n"]})
                        self.almacen.anotar_recuerdo((reg.clase, reg.id), r)
                        recs.append(r)
                        if ep_abierto is not None and r["episodio"]:
                            self.pendientes_rec.append({"episodio_actual": ep_abierto, "episodio_recuperado": r["episodio"]})
                # Al abrirse un episodio, S3 busca el episodio pasado mÃ¡s parecido (huella de apertura)
                if sis == "S3" and ev_seg["abre"] is not None and disponible - usado >= c_r:
                    usado += c_r
                    r = self.almacen.recuperar_episodio(ev_seg["abre"]["huella"], s["n"])
                    if r is not None:
                        self.predicciones_ep[ev_seg["abre"]["id"]] = r
                        recs.append({"episodio_parecido": r, "para": ev_seg["abre"]["id"], "n": s["n"]})
            disp[sis] = {"restante": restante, "disponible": disponible, "usado": usado}
            gastado_antes += usado
        fila["seleccion"] = sel_log
        fila["recuperaciones"] = recs
        fila["presupuesto"] = {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in disp.items()}
        for sis in SISTEMAS:
            base = disp[sis]["restante"]
            self.uso_virtual[sis].append(disp[sis]["usado"] / base if base > 0 else 0.0)

        # 5. Proactiva (paso 3), solo registrada
        if self.flags["observar_proactiva"]:
            propio = next(iter(onda.reactiva.ev.get("Propiocepcion", {}).values()), None)
            adyacentes = list(propio.product.get("nodos_adyacentes", [])) if propio else []
            ev_clases = {}
            for canal in ("Objeto", "Escena"):
                for pid, p in onda.reactiva.ev.get(canal, {}).items():
                    clase = str(p.product.get("tipo_entidad") or p.tipo_componente)
                    ev_clases.setdefault(str(pid), clase)
                    nodo = p.product.get("target_nodo")  # Crafter: la casilla a la que apunta la acciÃ³n
                    if nodo:
                        ev_clases.setdefault(str(nodo), clase)
            clase_obj = Proactiva.clase_objetivo(s["objetivo"], ev_clases, str(onda.ubicacion_actual), adyacentes)
            sobra_s3 = disp["S3"]["restante"] - disp["S3"]["usado"]
            puede = self.perfil == "completa" and s["amp_max"] > 0 and sobra_s3 / s["amp_max"] >= self.a["proactiva"]["restante_minimo"]
            validadas = self.pro.validar(s["n"], s["vit"], s["ali"], cerrados_ahora)
            exp = self.pro.anotar(s["n"], s["comando"], clase_obj, s["objetivo"], ep_abierto, s["vit"], s["ali"], puede)
            fila["proactiva"] = {"expectativa": exp, "validadas": [v for v in validadas if "expectativa" in v],
                                 "pendientes": len(self.pro.pendientes), "abiertas": self.pro.abiertas(),
                                 "clase_objetivo": clase_obj, "puede": puede, "episodio": ep_abierto}

        # Mantenimiento: sueÃ±o, periÃ³dico
        cada = self.a["mantenimiento_cada"]
        ms = (time.perf_counter() - t0) * 1000.0
        self.ms_latido.append(ms)
        fila["ms_observador"] = round(ms, 4)
        self._escribir(fila)
        if s["dormido"] or (cada and s["n"] % cada == 0):
            t1 = time.perf_counter()
            m = self.almacen.mantenimiento(s["n"])  # el registro se escribe al morir (cerrar), no aquÃ­
            if self.creencias is not None:  # E5, bloque G2
                self.creencias.leer(core, s["n"])
            m["ms"] = (time.perf_counter() - t1) * 1000.0
            self.ms_mantenimiento.append(m["ms"])
            self._escribir({"tipo": "mantenimiento", "n": s["n"], **m})

    # ------------------------------------------------------------------------------------------
    def _restante_por_sistema(self, s: Dict[str, Any]) -> Dict[str, float]:
        """Amplitud real que quedaba en la Onda al terminar cada Sistema su procesamiento reactivo."""
        amp_max = float(s["amp_max"] or 0)
        consumido, out = 0.0, {}
        for c in self._comps:
            consumido += c["amplitud"]
            out[c["sistema"]] = amp_max - consumido
        anterior = amp_max
        for sis in SISTEMAS:  # un Sistema que no corriÃ³ (sueÃ±o, guillotina) hereda lo que quedaba
            out.setdefault(sis, anterior)
            anterior = out[sis]
        return out

    def _guardar(self, s, sis, aro, clase, pid, p, comp_sis, ep_abierto) -> Registro:
        reg = Registro(clase=clase, id=pid, latido=s["n"], arousal=aro, confianza=float(p.trust), rasgos=_rasgos(p),
                       sistema=sis, componente=next((i for i in reversed(p.inputs) if i in comp_sis), ""),
                       episodio=ep_abierto, protegido=_modalidad_demostrada(p) or bool(p.heredado))
        self.almacen.guardar(reg)
        self.guardadas[sis] += 1
        self.clases_guardadas[clase] = self.clases_guardadas.get(clase, 0) + 1
        return reg

    @staticmethod
    def _origen(p: Any, comp_sis: Dict[str, str]) -> str:
        sp = [x for x in p.sistemas_participantes if x in ORDEN]
        if sp:
            return min(sp, key=ORDEN.get)
        for i in reversed(p.inputs):
            if i in comp_sis:
                return comp_sis[i]
        return "Core"

    def _cierre_episodio(self, ep: Dict[str, Any]) -> str:
        self.almacen.guardar_episodio(ep)
        self.cerrados.append({k: ep[k] for k in ("id", "desde", "hasta", "longitud", "motivos", "cierre", "balance", "signo")})
        pred = self.predicciones_ep.pop(ep["id"], None)
        if pred is not None:
            previos = [c["signo"] for c in self.cerrados[:-1]]
            base = sum(1 for x in previos if x == ep["signo"]) / len(previos) if previos else None
            self.aciertos_ep.append({"episodio": ep["id"], "real": ep["signo"], "predicho": pred["signo"],
                                     "acierto": pred["signo"] == ep["signo"], "coseno": pred["coseno"],
                                     "base_misma_vida": base})
        firmas = {c["id"]: c["signo"] for c in self.cerrados}
        quedan = []
        for p in self.pendientes_rec:
            if p["episodio_actual"] == ep["id"]:
                sr = firmas.get(p["episodio_recuperado"])
                if sr is not None:
                    self.recuperaciones_validas.append({"acierto": sr == ep["signo"]})
            else:
                quedan.append(p)
        self.pendientes_rec = quedan
        self._escribir({"tipo": "episodio", **self.cerrados[-1]})
        return ep["id"]

    def _escribir(self, evento: Dict[str, Any]) -> None:
        """Camino rÃ¡pido: solo encola. Se serializa una vez, al morir (`cerrar` â†’ `_volcar`)."""
        if self._f is not None:
            self._cola.append(evento)

    def _volcar(self) -> None:
        if self._f is not None and self._cola:
            self._f.write("".join(json.dumps(e, ensure_ascii=False, default=float) + "\n" for e in self._cola))
        self._cola = []

    # ------------------------------------------------------------------------------------------
    def cerrar(self) -> Dict[str, Any]:
        if not self.activo:
            return {"activo": False}
        ep = self.seg.forzar_cierre()
        if ep is not None:
            self._cierre_episodio(ep)
        s = self._ultimo_senal
        if s is not None:
            self.pro.validar(s["n"], s["vit"], s["ali"], [], todas=True)
        m = self.almacen.mantenimiento(s["n"] if s else 0)
        self.ms_mantenimiento.append(m["ms"])
        if self.creencias is not None and self._ultimo_core is not None:
            self.creencias.leer(self._ultimo_core, s["n"] if s else 0)
            self.creencias.escribir(self.partida, s["n"] if s else 0)
        res = self.resumen(m)
        self._escribir({"tipo": "fin", **res})
        self._volcar()
        if self._f is not None:
            self._f.close()
            self._f = None
        return res

    def resumen(self, m: Dict[str, Any]) -> Dict[str, Any]:
        v = self.pro.validadas
        ac = [x["acierto"] for x in v]
        return {
            "activo": True, "partida": self.partida, "latidos": len(self.ms_latido), "plazo_ms": sorted(self.plazos),
            "ms_observador": self.ms_latido, "ms_mantenimiento": self.ms_mantenimiento,
            "episodios": self.cerrados, "almacen": m, "guardadas": self.guardadas,
            "descartadas_presupuesto": self.descartadas_presupuesto, "clases_guardadas": self.clases_guardadas,
            "uso_virtual_medio": {k: (float(np.mean(x)) if x else 0.0) for k, x in self.uso_virtual.items()},
            "recuperaciones": self.recuperaciones,
            "recuperaciones_validadas": len(self.recuperaciones_validas),
            "recuperaciones_acierto": (sum(x["acierto"] for x in self.recuperaciones_validas) / len(self.recuperaciones_validas)) if self.recuperaciones_validas else None,
            "episodios_predichos": self.aciertos_ep,
            "proactiva": {"creadas": self.pro.creadas, "validadas": len(v), "aciertos": sum(ac),
                          "sin_hipotesis": self.pro.sin_hipotesis, "omitidas_por_tope": self.pro.omitidas_por_tope,
                          "max_abiertas": self.pro.max_abiertas_visto, "max_pendientes": self.pro.max_pendientes_visto,
                          "pendientes_al_final": len(self.pro.pendientes),
                          "validaciones": [{"frecuencia": x["expectativa"]["frecuencia"], "confianza": x["expectativa"]["confianza"],
                                            "acierto": x["acierto"], "acierto_base": x.get("acierto_base"),
                                            "clave": x["clave"], "resultado": x["resultado"],
                                            "edad": x["edad"], "motivo": x["motivo"]} for x in v],
                          "demostraciones": self.pro.eventos_demostracion,
                          "hipotesis": {f"{k[0]}|{k[1]}": {"resultados": h.resultados, "confianza": round(h.confianza, 4),
                                                           "confirmaciones": h.confirmaciones, "falsaciones": h.falsaciones,
                                                           "demostrada": h.demostrada} for k, h in self.pro.hipotesis.items()}},
            "s3_existente": self.s3,
            "indicadores": self.indicadores,
        }


@contextlib.contextmanager
def observando(obs: ObservadorV14) -> Iterator[ObservadorV14]:
    """Engancha el observador a GestorOndaCore y a los barridos; los restaura al salir."""
    from nivel_1_core.gestor_onda import GestorOndaCore
    from nivel_2_sistemas.sistema_base import SistemaCognitivoTriunico

    latido = GestorOndaCore.__dict__["ejecutar_latido"]
    barridos_attr = SistemaCognitivoTriunico.__dict__["_ejecutar_tres_barridos"]
    barridos = barridos_attr.__func__

    async def barridos_observados(comp, onda, ctx):
        a0 = onda.amplitud_consumida
        try:
            await barridos(comp, onda, ctx)
        finally:
            obs._comps.append({"sistema": comp.sistema, "componente": comp.id_componente,
                               "amplitud": onda.amplitud_consumida - a0})

    async def latido_observado(self, *a, **k):
        obs.antes(self)
        onda = await latido(self, *a, **k)
        obs.despues(self, onda)
        return onda

    GestorOndaCore.ejecutar_latido = latido_observado
    SistemaCognitivoTriunico._ejecutar_tres_barridos = staticmethod(barridos_observados)
    try:
        yield obs
    finally:
        GestorOndaCore.ejecutar_latido = latido
        SistemaCognitivoTriunico._ejecutar_tres_barridos = barridos_attr

