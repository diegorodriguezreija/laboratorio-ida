"""
Modificadores de E2â€“E4 (bloques A y B). Cambian la conducta: van tras un flag apagado por defecto y se
miden aparte (preregistro `v14/preregistro_E2_E4.md`). No tocan ningÃºn fichero del nÃºcleo ni de los
mundos: se instalan desde aquÃ­, en las instancias de cada partida, al empezar su primer latido.

- `calibracion_cuerpo_crafter` (bloque A):
  - P1, `factor_lastre_carga`: multiplica los 0,5 por latido que el soma resta en vigilia si cree
    llevar carga (`estado_somatico.py:120`).
  - P1', `factor_desgaste_basal`: multiplica el desgaste basal de 0,8 por latido en vigilia.
  - P2, `alcance_peligro`: las piezas de peligro (depredadores, flechas, lava) mÃ¡s lejos que ese alcance
    (Manhattan) llegan con la nocicepciÃ³n a 0 y el arousal limitado a 0,5. La lista de depredadores
    que usan los componentes de Crafter no cambia (van por tipo).
  Con los valores originales (1,0; 1,0; sin lÃ­mite) no cambia nada.
- `curiosidad_intrinseca` (bloque B): `CompCuriosidadIntrinseca`, componente de S2 en REACCIONAR.
"""

from __future__ import annotations

import contextlib
import time
from typing import Any, Dict, Iterator, List

import numpy as np

from nivel_1_core.arbitros import identificar_sistema_origen
from nivel_1_core.contratos import Pieza
from nivel_1_core.vocabulario import V_Comando, V_Estado
from nivel_2_sistemas.sistema_base import ComponenteCognitivoBase

CLASES_PELIGRO = ("Amenaza_Predador", "Peligro_Lava")
DESGASTE_BASAL, LASTRE_CARGA = 0.8, 0.5  # estado_somatico.py:120


# ---------------------------------------------------------------------------------------------
# Bloque A: calibraciÃ³n del cuerpo simulado de Crafter
# ---------------------------------------------------------------------------------------------

def instalar_calibracion(core: Any, cal: Dict[str, float]) -> None:
    soma, sensor = core.soma, core.sensor
    fb, fc, alcance = cal["factor_desgaste_basal"], cal["factor_lastre_carga"], cal["alcance_peligro"]
    if fb != 1.0 or fc != 1.0:
        original = soma.aplicar_metabolismo_latido

        def metabolismo(ciclo_actual: int, max_latidos: int = 500) -> None:
            ali0 = soma.alimentacion
            despierto = soma.estado_afectivo != V_Estado.DORMIDO
            carga = soma.objeto_cargado is not None
            original(ciclo_actual, max_latidos)
            if despierto:  # sustituye solo el desgaste de la alimentaciÃ³n en vigilia
                nuevo = DESGASTE_BASAL * fb + (LASTRE_CARGA * fc if carga else 0.0)
                soma.alimentacion = float(max(0.0, min(100.0, ali0 - nuevo)))

        soma.aplicar_metabolismo_latido = metabolismo
    if alcance < 99.0:
        percibir = sensor.percibir_mundo

        def percibir_calibrado():
            nodo, piezas, ady = percibir()
            for p in piezas:
                if p.tipo_componente in CLASES_PELIGRO and float(p.product.get("distancia_manhattan", 0)) > alcance:
                    t = np.array(p.tensor_sensorial, dtype=np.float64)
                    t[5] = 0.0
                    p.tensor_sensorial = t
                    p.arousal = min(p.arousal, 0.5)
            return nodo, piezas, ady

        sensor.percibir_mundo = percibir_calibrado


def instalar_correccion_carga(core: Any, pesados: List[str]) -> None:
    """E5, bloque E: al empezar cada latido, el soma solo lleva carga si el inventario del juego tiene alguno
    de los objetos de `pesados`; si no, `objeto_cargado = None` (Crafter devuelve un `objeto_cargado` con el
    estado del jugador tras cualquier COGER, adaptador_crafter.py:678-686)."""
    soma = core.soma
    original = soma.aplicar_metabolismo_latido

    def metabolismo(ciclo_actual: int, max_latidos: int = 500) -> None:
        jugador = getattr(getattr(core.sensor, "env", None), "_player", None)
        inv = dict(getattr(jugador, "inventory", {}) or {}) if jugador is not None else {}
        if any(inv.get(k, 0) > 0 for k in pesados):
            if soma.objeto_cargado is None:
                soma.objeto_cargado = {"id": "carga_pesada", "es_nutritivo": False}
        else:
            soma.objeto_cargado = None
        original(ciclo_actual, max_latidos)

    soma.aplicar_metabolismo_latido = metabolismo


# ---------------------------------------------------------------------------------------------
# Bloque B: curiosidad intrÃ­nseca
# ---------------------------------------------------------------------------------------------

def puntuacion_a0(p: Pieza, estres: float) -> float:
    """La puntuaciÃ³n del Ã¡rbitro A0 (arbitros.py:93-100), sin desesperaciÃ³n (la compuerta la excluye)."""
    peso = float(p.product.get("peso_sinaptico", 1.0))
    mod = max(0.80, min(1.25, 0.85 + 0.15 * peso))
    return ((p.arousal * estres) + (p.trust * (1.0 - estres))) * mod


class CompCuriosidadIntrinseca(ComponenteCognitivoBase):
    """Empuja hacia el nodo adyacente menos visitado cuando no hay peligro ni hambre y sobra amplitud.
    Nunca por encima de S1: su puntuaciÃ³n A0 queda bajo la menor de los impulsos de S1 menos un margen."""

    def __init__(self, ajustes: Dict[str, float]):
        super().__init__("Comp_CuriosidadIntrinseca", "S2")
        self.a = ajustes
        self.ms: List[float] = []
        self.propuestas = 0

    async def procesar_reactiva(self, onda, ctx) -> bool:
        t0 = time.perf_counter()
        try:
            return self._proponer(onda, ctx)
        finally:
            self.ms.append((time.perf_counter() - t0) * 1000.0)

    def _proponer(self, onda, ctx) -> bool:
        soma, activa, a = ctx["soma"], ctx["activa"], self.a
        sup = onda.reactiva.ev.get("Supervivencia", {}).get("Alarma_Supervivencia")
        peligro = float(sup.product.get("nivel_peligro", 0.0)) if sup else 0.0
        if peligro >= a["peligro_max"] or soma.alimentacion <= a["alimentacion_min"]:
            return False
        if onda.amplitud_restante() < a["amplitud_restante_min"] * onda.amplitud_max:
            return False
        propio = next(iter(onda.reactiva.ev.get("Propiocepcion", {}).values()), None)
        ady = list(propio.product.get("nodos_adyacentes", [])) if propio else []
        if not ady:
            return False
        grafo = activa.grafo_topologico
        visitas = {n: sum(ar.get(n, {}).get("veces_transitado", 0.0) for ar in grafo.values()) for n in ady}
        destino = min(ady, key=lambda n: (visitas[n], ady.index(n)))
        novedad = 1.0 / (1.0 + visitas[destino])
        mod = max(0.80, min(1.25, 0.85 + 0.15 * float(self.peso_sinaptico)))
        objetivo = a["peso"] * novedad  # su puntuaciÃ³n A0 serÃ­a objetivo Ã— mod
        if a.get("regla", "bajo_s1") == "relleno":  # E5, bloque F
            from herramientas.arbitraje import candidatos
            cands = candidatos(onda, soma)
            superv_s1 = any(c["sistema"] == "S1" and c["clase"] == "supervivencia" for c in cands)
            if not superv_s1 and (not cands or cands[0]["clase"] == "relleno"):
                objetivo = ((cands[0]["puntuacion"] if cands else 0.0) + a["peso"] * novedad) / mod
            else:
                topes = [(c["puntuacion"] - a["margen_s1"]) / mod for c in cands if c["sistema"] == "S1"]
                topes += [(cands[0]["puntuacion"] - a["margen_s1"]) / mod] if cands else []
                objetivo = min([objetivo] + topes)
        else:
            estres = float(max(0.0, min(1.0, soma.cortisol)))
            s1 = [puntuacion_a0(p, estres) for p in onda.reactiva.acc.get("Impulso", {}).values()
                  if identificar_sistema_origen(p) == "S1"]
            if s1:
                objetivo = min(objetivo, (min(s1) - a["margen_s1"]) / mod)
        if objetivo <= 0.0:
            return False
        p = Pieza(id=f"impulso_curiosidad_{destino}", tipo_componente="Impulso", arousal=objetivo, trust=objetivo,
                  product={"comando": V_Comando.MOVER, "target": destino, "origen_sistema": "S2",
                           "curiosidad": True, "novedad": round(novedad, 4)},
                  inputs=["Propiocepcion", self.id_componente])
        self.emitir_impulso(onda, p, coste_amplitud=1)
        self.propuestas += 1
        return True


# ---------------------------------------------------------------------------------------------
# InstalaciÃ³n desde fuera, al empezar cada partida
# ---------------------------------------------------------------------------------------------

@contextlib.contextmanager
def modificando(flags: Dict[str, Any], ajustes: Dict[str, Any]) -> Iterator[Dict[str, List[Any]]]:
    """Instala los modificadores encendidos en cada GestorOndaCore al empezar su primer latido.
    Con los dos flags apagados no envuelve nada."""
    estado: Dict[str, List[Any]] = {"curiosidad": []}
    cal = flags.get("calibracion_cuerpo_crafter", False)
    cur = flags.get("curiosidad_intrinseca", False)
    carga = flags.get("corregir_carga_falsa_crafter", False)
    if not (cal or cur or carga):
        yield estado
        return
    from nivel_1_core.gestor_onda import GestorOndaCore
    original = GestorOndaCore.__dict__["ejecutar_latido"]
    instalados = set()

    async def latido(self, *aa, **kk):
        if id(self) not in instalados:
            instalados.add(id(self))
            if cal:
                instalar_calibracion(self, ajustes["calibracion"])
            if carga:
                instalar_correccion_carga(self, ajustes["carga_pesados"])
            if cur:
                comp = CompCuriosidadIntrinseca(ajustes["curiosidad"])
                next(s for s in self.sistemas if s.nombre == "S2").inyectar_componente("REACCIONAR", comp)
                estado["curiosidad"].append(comp)
        return await original(self, *aa, **kk)

    GestorOndaCore.ejecutar_latido = latido
    try:
        yield estado
    finally:
        GestorOndaCore.ejecutar_latido = original

