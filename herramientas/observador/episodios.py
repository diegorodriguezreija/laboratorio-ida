"""
SegmentaciÃ³n de episodios en lÃ­nea, con las reglas del plan (secciÃ³n 4.4) y los umbrales y seÃ±ales
de cada mundo (`ajustes.episodio`, `ajustes.senales_episodio`).

Apertura: arousal â‰¥ umbral, sorpresa (si el mundo lo permite), |Î”vit| â‰¥ umbral o |Î”ali| â‰¥ umbral.
Cierre: calma (arousal < umbral, sin sorpresa y |Î”vit| < umbral), longitud mÃ¡xima, colapso o sueÃ±o.
Balance vital: Î”vit + 0,5 Ã— Î”ali entre el latido anterior a la apertura y el cierre.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from herramientas.observador.senales import huella_apertura


def signo(x: float, tolerancia: float) -> int:
    return 0 if abs(x) <= tolerancia else (1 if x > 0 else -1)


class Segmentador:
    def __init__(self, umbrales: Dict[str, Any], tolerancia_neutro: float, partida: str = ""):
        self.u = umbrales
        self.tol = tolerancia_neutro
        self.partida = partida
        self.previo: Optional[Dict[str, Any]] = None
        self.abierto: Optional[Dict[str, Any]] = None
        self.cuenta = 0

    def paso(self, s: Dict[str, Any]) -> Dict[str, Any]:
        """Devuelve {"abre": episodio | None, "cierra": episodio | None} para este latido."""
        u, prev = self.u, self.previo
        dvit = abs(s["vit"] - prev["vit"]) if prev else 0.0
        dali = abs(s["ali"] - prev["ali"]) if prev else 0.0
        sorpresa = s["sorpresa"] and u["sorpresa_abre"]
        out: Dict[str, Any] = {"abre": None, "cierra": None}
        if self.abierto is None:
            motivos = [m for m, c in (("arousal", s["arousal_ep"] >= u["abre_arousal"]), ("sorpresa", sorpresa),
                                      ("vitalidad", dvit >= u["abre_dvit"]), ("alimentacion", dali >= u["abre_dali"])) if c]
            if motivos:
                base = prev or s
                self.cuenta += 1
                self.abierto = {"id": f"{self.partida}#{self.cuenta}", "partida": self.partida, "desde": s["n"],
                                "motivos": motivos, "vit0": base["vit"], "ali0": base["ali"], "longitud": 0,
                                "huella": huella_apertura(s, motivos), "max_arousal": 0.0}
                out["abre"] = self.abierto
        if self.abierto is not None:
            ep = self.abierto
            ep["longitud"] += 1
            ep["max_arousal"] = max(ep["max_arousal"], s["arousal_ep"])
            calma = s["arousal_ep"] < u["cierra_arousal"] and not sorpresa and dvit < u["cierra_dvit"]
            if calma or s["colapso"] or ep["longitud"] >= u["longitud_max"]:
                out["cierra"] = self._cerrar(s, "calma" if calma else ("colapso_o_sueno" if s["colapso"] else "longitud"))
        self.previo = s
        return out

    def _cerrar(self, s: Dict[str, Any], motivo: str) -> Dict[str, Any]:
        ep = self.abierto
        dv, da = s["vit"] - ep["vit0"], s["ali"] - ep["ali0"]
        ep.update({"hasta": s["n"], "cierre": motivo, "d_vit": dv, "d_ali": da, "balance": dv + 0.5 * da})
        ep["signo"] = signo(ep["balance"], self.tol)
        self.abierto = None
        return ep

    def forzar_cierre(self) -> Optional[Dict[str, Any]]:
        """Al morir o al acabar el episodio de juego: cierra el episodio abierto, si lo hay."""
        if self.abierto is None or self.previo is None:
            return None
        return self._cerrar(self.previo, "fin")

    def balance_desde(self, vit0: float, ali0: float) -> float:
        p = self.previo
        return (p["vit"] - vit0) + 0.5 * (p["ali"] - ali0) if p else 0.0

