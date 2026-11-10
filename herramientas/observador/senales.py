"""
Señales que el observador lee de cada latido, por mundo (solo lectura).

- `soma` (por defecto): el arousal del Episodio es la urgencia de S1 (arousal de
  `Alarma_Supervivencia`, `s1_reactivo.py:150-156`); vitalidad y alimentación son las del soma.
- `mundo_crafter`: el soma de Crafter está saturado (ARQUITECTURA §13), así que para observar se usan
  el peligro externo de S1 (`nivel_peligro`) y la salud y la comida+bebida del juego. No se toca el soma.

También calcula los tres indicadores generales (solo observación):
- peligro o urgencia: máx(peligro externo, urgencia metabólica);
- tensión o concentración: amplitud usada / amplitud máxima del latido;
- calma o sueño: 1 si duerme; si no, (1 − peligro) × (1 − cortisol).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

COMANDOS = ("ACC_MOVER", "ACC_COGER", "ACC_ESPERAR", "ACC_DEGLUTIR", "ACC_ATACAR", "ACC_ACECHAR", "ACC_SOLTAR", "ACC_ASIMILAR")
SISTEMAS = ("S1", "S2", "S3")


def jugador_crafter(core: Any) -> Optional[Dict[str, Any]]:
    env = getattr(getattr(core, "sensor", None), "env", None)
    mundo, jugador = getattr(env, "_world", None), getattr(env, "_player", None)
    if mundo is None or jugador is None:
        return None
    inv = dict(getattr(jugador, "inventory", {}) or {})
    return {"salud": int(inv.get("health", 0)), "comida": int(inv.get("food", 0)), "bebida": int(inv.get("drink", 0)),
            "energia": int(inv.get("energy", 0)), "duerme": bool(getattr(jugador, "sleeping", False)),
            "luz": round(float(getattr(mundo, "daylight", 1.0)), 3),
            "logros": len(getattr(core.sensor, "logros_desbloqueados", ()) or ())}


def _num(v: Any, defecto: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return defecto


CLASES_PELIGRO_JUEGO = ("Amenaza_Predador", "Peligro_Lava")  # piezas de escena del adaptador de Crafter
PREFIJOS_FORMALES = ("Sujeto", "Predicado", "Proposicion", "Sentencia", "Logica")


def leer(core: Any, onda: Any, tipo_senales: str, peligro_crafter: str = "s1") -> Dict[str, Any]:
    soma = core.soma
    ev = onda.reactiva.ev
    sup = ev.get("Supervivencia", {}).get("Alarma_Supervivencia")
    ejec = onda.reactiva.ef.get("Ejecucion", {}).get("Ejecucion")
    afecto = str(soma.estado_afectivo)
    formales: Dict[str, int] = {}
    for canal, piezas in onda.reactiva.ef.items():
        for p in piezas.values():
            t = str(p.tipo_componente)
            if t.startswith(PREFIJOS_FORMALES):
                formales[t] = formales.get(t, 0) + 1
    s: Dict[str, Any] = {
        "n": int(onda.ciclo),
        "plazo_ms": float(onda.frecuencia_max_ms),
        "amp_max": int(onda.amplitud_max),
        "amp_usada": int(onda.amplitud_consumida),
        "comando": str(ejec.product.get("comando")) if ejec else "ACC_ESPERAR",
        "objetivo": str(ejec.product.get("target", "")) if ejec else "",
        "sistema_ganador": str(onda.metricas.get("sistema_ganador", "")),
        "componente_ganador": str(onda.metricas.get("componente_ganador", "")),
        "afecto": afecto,
        "cortisol": float(soma.cortisol),
        "sorpresa": "Sorpresa" in ev,
        "urgencia_s1": _num(sup.arousal) if sup else 0.0,
        "peligro_externo": _num(sup.product.get("nivel_peligro")) if sup else 0.0,
        "vivo_soma": bool(soma.esta_vivo),
        "vit_soma": float(soma.vitalidad),
        "ali_soma": float(soma.alimentacion),
        "carga": soma.objeto_cargado is not None,
        # Hubo acción en el mundo: el Tribunal ejecutó (no acechó ni esperó sin impulsos)
        "ejecutado": bool(ejec and ejec.product.get("modo_ablacion") and str(ejec.product.get("comando")) != "ACC_ACECHAR"),
        "ubicacion": str(onda.ubicacion_actual),
        "formales": formales,
    }
    if tipo_senales == "mundo_crafter":
        m = jugador_crafter(core) or {"salud": 0, "comida": 0, "bebida": 0, "energia": 0, "duerme": False, "luz": 1.0}
        s["mundo"] = m
        jugador = getattr(getattr(getattr(core, "sensor", None), "env", None), "_player", None)
        s["pos"] = [int(jugador.pos[0]), int(jugador.pos[1])] if jugador is not None else None
        s["peligro_juego"] = 1.0 if any(p.tipo_componente in CLASES_PELIGRO_JUEGO for p in ev.get("Escena", {}).values()) else 0.0
        s["arousal_ep"] = s["peligro_juego"] if peligro_crafter == "juego" else s["peligro_externo"]
        s["vit"] = float(m["salud"])
        s["ali"] = float(m["comida"] + m["bebida"])
        s["dormido"] = afecto == "DORMIDO" or m["duerme"]
        s["colapso"] = m["salud"] <= 0 or m["duerme"]
        s["urgencia_metabolica"] = 1.0 - min(m["comida"], m["bebida"]) / 9.0
        s["extra"] = [m["salud"] / 9.0, m["comida"] / 9.0, m["bebida"] / 9.0, m["energia"] / 9.0, float(m["luz"])]
    else:
        s["arousal_ep"] = s["urgencia_s1"]
        s["vit"] = s["vit_soma"]
        s["ali"] = s["ali_soma"]
        s["dormido"] = afecto == "DORMIDO"
        s["colapso"] = (not s["vivo_soma"]) or s["comando"] == "ACC_COLAPSO" or s["dormido"]
        ali = s["ali_soma"]
        s["urgencia_metabolica"] = 0.95 if ali <= soma.UMBRAL_INANICION_CRITICA else max(0.0, (100.0 - ali) / 100.0)
        s["extra"] = [0.0] * 5
    externo = s["peligro_juego"] if (tipo_senales == "mundo_crafter" and peligro_crafter == "juego") else s["peligro_externo"]
    s["peligro_obs"] = externo
    peligro = max(externo, s["urgencia_metabolica"])
    tension = s["amp_usada"] / s["amp_max"] if s["amp_max"] else 0.0
    calma = 1.0 if s["dormido"] else (1.0 - peligro) * (1.0 - s["cortisol"])
    s["indicadores"] = {"peligro": round(peligro, 4), "tension": round(tension, 4), "calma": round(calma, 4),
                        "franja_peligro": "alta" if peligro >= 0.75 else ("media" if peligro >= 0.35 else "baja")}
    return s


def huella_apertura(s: Dict[str, Any], motivos: List[str]) -> List[float]:
    """Lo que se sabe al abrir un episodio: motivo, estado, peligro, orden y sistema ganador."""
    v = [1.0 if m in motivos else 0.0 for m in ("arousal", "sorpresa", "vitalidad", "alimentacion")]
    v += [s["ali_soma"] / 100.0, s["vit_soma"] / 100.0, s.get("peligro_obs", s["peligro_externo"])]
    v += list(s["extra"])
    v += [1.0 if s["comando"] == c else 0.0 for c in COMANDOS]
    v += [1.0 if s["sistema_ganador"] == x else 0.0 for x in SISTEMAS]
    return v
