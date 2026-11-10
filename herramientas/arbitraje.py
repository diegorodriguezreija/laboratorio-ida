"""
Lectura del arbitraje (preregistro E5, bloque D): clase de cada candidato y su puntuación A0.
Solo lee las piezas; no escribe en ellas. Lo usan el observador (D) y la curiosidad con la regla nueva (F).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from nivel_1_core.arbitros import identificar_sistema_origen

MARCAS_SUPERVIVENCIA = ("es_supervivencia_pag", "flash_supervivencia", "soltar_lastre_emergencia")
CLAVES_PROPOSITO = ("meta_teleologica", "meta_estrategica", "meta_tecnologica", "objetivo", "motivo", "curiosidad")
ENTRADAS_NO_CAUSALES = ("Propiocepcion", "Alarma_Supervivencia", "Simulacion_Ruta", "Comp_")


def clase(p: Any) -> str:
    """«supervivencia», «relleno» o «proposito» (reglas del preregistro E5, sección 2)."""
    prod = p.product
    cmd = str(prod.get("comando", ""))
    if any(prod.get(m) for m in MARCAS_SUPERVIVENCIA) or cmd in ("ACC_ATACAR", "ACC_DEGLUTIR") \
            or prod.get("motivo") == "evasion_amenaza":
        return "supervivencia"
    dormir = bool(prod.get("dormir")) or str(prod.get("target", "")) == "DORMIR"
    if cmd in ("ACC_ESPERAR", "ACC_ACECHAR", "ACC_MOVER") and not dormir \
            and not any(k in prod for k in CLAVES_PROPOSITO) \
            and all(str(i).startswith(ENTRADAS_NO_CAUSALES) for i in p.inputs):
        return "relleno"
    return "proposito"


def puntuacion(p: Any, soma: Any) -> float:
    """Puntuación del árbitro A0 (arbitros.py:83-100), con la desesperación."""
    estres = float(max(0.0, min(1.0, soma.cortisol)))
    ar = float(p.arousal)
    veto = bool(p.product.get("trampa_parasitaria_evitada") or p.product.get("veto_moral"))
    if soma.alimentacion <= soma.UMBRAL_INANICION_CRITICA and not p.product.get("sacrificio_consciente") and not veto:
        ar = max(ar, float(p.product.get("arousal_s1_crudo", ar)))
    mod = max(0.80, min(1.25, 0.85 + 0.15 * float(p.product.get("peso_sinaptico", 1.0))))
    return (ar * estres + float(p.trust) * (1.0 - estres)) * mod


def candidatos(onda: Any, soma: Any) -> List[Dict[str, Any]]:
    return sorted(({"id": str(pid), "sistema": identificar_sistema_origen(p), "comando": str(p.product.get("comando", "")),
                    "objetivo": str(p.product.get("target", "")), "clase": clase(p), "puntuacion": puntuacion(p, soma)}
                   for pid, p in onda.reactiva.acc.get("Impulso", {}).items()), key=lambda c: -c["puntuacion"])


def registro(onda: Any, soma: Any) -> Dict[str, Any]:
    """Fila del arbitraje de un latido ya terminado."""
    cands = candidatos(onda, soma)
    ejec = onda.reactiva.ef.get("Ejecucion", {}).get("Ejecucion")
    gid = str(ejec.inputs[0]) if ejec is not None and ejec.inputs and ejec.inputs[0] != "TribunalMotor" else None
    ganador: Optional[Dict[str, Any]] = next((c for c in cands if c["id"] == gid), None)
    cf = onda.metricas.get("contrafactual") or {}
    return {
        "n_candidatos": len(cands),
        "ganador": ganador,
        "mejor": cands[0] if cands else None,
        "margen": (cands[0]["puntuacion"] - cands[1]["puntuacion"]) if len(cands) >= 2 else None,
        "acecho": bool(ejec is not None and str(ejec.product.get("comando")) == "ACC_ACECHAR"),
        "arbitros": {k: str(v.get("comando")) for k, v in cf.items()},
        "discrepan_de_A0": list(onda.metricas.get("desacuerdos_contrafactuales", []) or []),
        "candidatos": [{k: c[k] for k in ("id", "sistema", "comando", "objetivo", "clase")} | {"puntuacion": round(c["puntuacion"], 4)}
                       for c in cands[:8]],
    }
