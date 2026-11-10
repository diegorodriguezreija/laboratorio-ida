"""
Experiencia proactiva, solo observada (plan, secciones 4.5 y 6, paso 3).

Cada latido, la acciÃ³n elegida (orden + clase del objetivo) queda pendiente de su resultado: el signo
del balance vital (seÃ±ales del mundo) entre ese latido y el cierre de su episodio, o
`horizonte_latidos` despuÃ©s si no hay episodio o si el episodio se alarga. Con ese resultado se
actualiza la hipÃ³tesis de la acciÃ³n.

Cuando a S3 le sobra mÃ¡s presupuesto (`restante_minimo`) y la acciÃ³n ya tiene hipÃ³tesis, el
observador anota ademÃ¡s una **expectativa** legible: Â«si COGER (tree), la situaciÃ³n mejorarÃ¡Â».
Se valida a la vez que la acciÃ³n: **demostraciÃ³n**. La confianza sube con cada confirmaciÃ³n y baja
mÃ¡s con cada falsaciÃ³n; Â«demostradaÂ» exige `min_confirmaciones` y ninguna falsaciÃ³n en las Ãºltimas
`ventana_falsacion` validaciones.

Para no acumular expectativas sin validar (al contrario que las de S3 hoy, ARQUITECTURA Â§13), cada
pendiente caduca en `horizonte_latidos` como mucho, hay un tope de `max_abiertas` y al morir se
cierran todas. Nada de esto se escribe en `DimensionProactiva`.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

from herramientas.observador.episodios import signo

VERBO = {"ACC_MOVER": "MOVERSE a", "ACC_COGER": "COGER", "ACC_ESPERAR": "ESPERAR en", "ACC_DEGLUTIR": "COMER",
         "ACC_ATACAR": "ATACAR", "ACC_ACECHAR": "ACECHAR", "ACC_SOLTAR": "SOLTAR", "ACC_ASIMILAR": "CONSULTAR"}
RESULTADO = {1: "mejorarÃ¡", 0: "seguirÃ¡ igual", -1: "empeorarÃ¡"}


@dataclass
class Hipotesis:
    resultados: Dict[int, int] = field(default_factory=lambda: {1: 0, 0: 0, -1: 0})
    confianza: float = 0.5
    confirmaciones: int = 0
    falsaciones: int = 0
    recientes: Deque[bool] = field(default_factory=lambda: deque(maxlen=64))
    demostrada: bool = False

    def prediccion(self) -> Tuple[int, float]:
        total = sum(self.resultados.values())
        s = max((1, 0, -1), key=lambda k: (self.resultados[k], k == 0))
        return s, (self.resultados[s] / total if total else 0.0)


class Proactiva:
    def __init__(self, ajustes: Dict[str, Any]):
        self.a = ajustes
        self.hipotesis: Dict[Tuple[str, str], Hipotesis] = {}
        self.pendientes: Deque[Dict[str, Any]] = deque()
        self.validadas: List[Dict[str, Any]] = []
        self.creadas = 0
        self.omitidas_por_tope = 0
        self.sin_hipotesis = 0
        self.max_abiertas_visto = 0
        self.max_pendientes_visto = 0
        self.eventos_demostracion: List[Dict[str, Any]] = []
        self.global_: Dict[int, int] = {1: 0, 0: 0, -1: 0}

    @staticmethod
    def clase_objetivo(objetivo: str, ev_clases: Dict[str, str], ubicacion: str, adyacentes: List[str]) -> str:
        if objetivo in ev_clases:
            return ev_clases[objetivo]
        if objetivo == ubicacion or objetivo in adyacentes or objetivo.startswith("nodo_"):
            return "Lugar"
        if objetivo == "DORMIR":
            return "Sueno"
        return "Otro"

    def abiertas(self) -> int:
        return sum(1 for p in self.pendientes if p.get("expectativa"))

    def anotar(self, n: int, comando: str, clase: str, id_obj: str, episodio: Optional[str],
               vit: float, ali: float, puede_esperar: bool) -> Optional[Dict[str, Any]]:
        """Deja la acciÃ³n pendiente de resultado y, si hay sobrante e hipÃ³tesis, anota la expectativa."""
        clave = (comando, clase)
        pend = {"n": n, "clave": clave, "episodio": episodio, "vit0": vit, "ali0": ali, "expectativa": None}
        exp = None
        if puede_esperar:
            h = self.hipotesis.get(clave)
            if h is None or sum(h.resultados.values()) == 0:
                self.sin_hipotesis += 1
            elif self.abiertas() >= self.a["max_abiertas"]:
                self.omitidas_por_tope += 1
            else:
                pred, base = h.prediccion()
                exp = {"n": n, "sujeto": f"{clase}:{id_obj}", "predicado": comando, "proposicion": RESULTADO[pred],
                       "prediccion": pred, "confianza": round(h.confianza, 4), "frecuencia": round(base, 4),
                       "frase": f"Si {VERBO.get(comando, comando)} ({clase}), la situaciÃ³n {RESULTADO[pred]}."}
                pend["expectativa"] = exp
                self.creadas += 1
        self.pendientes.append(pend)
        self.max_abiertas_visto = max(self.max_abiertas_visto, self.abiertas())
        self.max_pendientes_visto = max(self.max_pendientes_visto, len(self.pendientes))
        return exp

    def validar(self, n: int, vit: float, ali: float, cerrados: List[str], todas: bool = False) -> List[Dict[str, Any]]:
        """Valida las pendientes cuyo episodio se cerrÃ³, las que cumplen el horizonte y, si `todas`, el resto."""
        hechas, quedan = [], deque()
        for p in self.pendientes:
            por_episodio = p["episodio"] is not None and p["episodio"] in cerrados
            por_horizonte = n - p["n"] >= self.a["horizonte_latidos"]
            if por_episodio or por_horizonte or todas:
                hechas.append(self._resolver(p, n, vit, ali, "episodio" if por_episodio else ("horizonte" if por_horizonte else "fin")))
            else:
                quedan.append(p)
        self.pendientes = quedan
        return hechas

    def _resolver(self, p: Dict[str, Any], n: int, vit: float, ali: float, motivo: str) -> Dict[str, Any]:
        resultado = signo((vit - p["vit0"]) + 0.5 * (ali - p["ali0"]), self.a["tolerancia_neutro"])
        h = self.hipotesis.setdefault(p["clave"], Hipotesis())
        out = {"n": n, "desde": p["n"], "clave": list(p["clave"]), "resultado": resultado, "motivo": motivo}
        exp = p["expectativa"]
        # LÃ­nea base: predecir siempre el resultado mÃ¡s frecuente hasta ahora en esta vida, sin mirar la acciÃ³n
        base = max((1, 0, -1), key=lambda k: (self.global_[k], k == 0)) if sum(self.global_.values()) else None
        if exp is not None:
            acierto = exp["prediccion"] == resultado
            out["acierto_base"] = base == resultado if base is not None else None
            if acierto:
                h.confirmaciones += 1
                h.confianza += self.a["paso_sube"] * (1.0 - h.confianza)
            else:
                h.falsaciones += 1
                h.confianza -= self.a["paso_baja"] * h.confianza
            h.recientes.append(acierto)
            ventana = list(h.recientes)[-self.a["ventana_falsacion"]:]
            antes = h.demostrada
            h.demostrada = (h.confirmaciones >= self.a["min_confirmaciones"] and all(ventana)
                            and h.confianza >= self.a["confianza_demostrada"])
            if h.demostrada != antes:
                self.eventos_demostracion.append({"n": n, "clave": list(p["clave"]), "demostrada": h.demostrada,
                                                  "frase": exp["frase"], "confianza": round(h.confianza, 4)})
            out.update({"expectativa": exp, "acierto": acierto, "confianza_despues": round(h.confianza, 4),
                        "edad": p["n"]})
            self.validadas.append(out)
        h.resultados[resultado] += 1
        self.global_[resultado] += 1
        return out

