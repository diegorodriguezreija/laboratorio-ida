"""
Conductores de episodio para la sonda del paso 0: ejemplo mínimo, Bosque y Crafter.

Usan el mismo código que los runners del repositorio y la misma configuración que los episodios
de la v13 (`escaparate/mundos.py`), pero sin importar el escaparate: el escaparate es un
observador y nada fuera de su carpeta puede depender de él (E-1).

- `ejemplo_minimo`: `ejemplo_minimo_runner.ejecutar` tal cual.
- `bosque`: el organismo de `main.construir_organismo_v12` en un bosque sembrado igual que la demo,
  dentro de su sandbox temporal, con plazo de 5000 ms.
- `crafter`: `mundo_crafter_runner.evaluar_individuo_en_semilla` con A0 y el arquetipo fijado a mano
  del harness (H7), sin axiomas heredados.

`aislar_ruido=True` sustituye el ruido físico por un valor fijo, igual que `--aislar-ruido`.
"""

from __future__ import annotations

import os
import sys
import tempfile
from typing import Any, Callable, Dict, List, Optional

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

SIEMBRA_BOSQUE = {
    "brote_nutritivo.brote": b"NUTRIENTE_GLUCOSA_ESTABLE_" * 10,
    "Atropa_belladonna.brote": b"ALCALOIDE_TOXICO_ATROPINA" * 10,
    "monolito_verdad.oraculo": b"REGISTRO_ONTOLOGICO_VERIFICADO" * 4,
    "nucleo_sagrado.sys": b"RECURSO_PROTEGIDO_POR_TABU" * 15,
}


def _aislar(core: Any) -> None:
    core.cosechador.amplitud_basal = 0.0
    core.cosechador.cosechar_unidad_uniforme = lambda: 0.5


async def ejemplo_minimo(latidos: int, aislar_ruido: bool, **_: Any) -> Dict[str, Any]:
    from nivel_3_componentes.mundos.mundo_ejemplo_minimo.ejemplo_minimo_runner import ejecutar
    traza = await ejecutar(latidos, aislar_ruido=aislar_ruido)
    return {"mundo": "ejemplo_minimo", "decisiones": [(t["comando"], t["objetivo"]) for t in traza]}


async def bosque(latidos: int, aislar_ruido: bool, **_: Any) -> Dict[str, Any]:
    from base.organismo import construir_organismo
    from nivel_1_core.contratos import Arquetipo
    from nivel_3_componentes.mundos.mundo_bosque_archivos.adaptador_bosque import AdaptadorBosqueArchivos
    decisiones: List[Any] = []
    with tempfile.TemporaryDirectory(prefix=AdaptadorBosqueArchivos.PREFIJO_SANDBOX) as sandbox:
        for nombre, contenido in SIEMBRA_BOSQUE.items():
            with open(os.path.join(sandbox, nombre), "wb") as f:
                f.write(contenido)
        nombre_sandbox = os.path.basename(sandbox)
        adaptador = AdaptadorBosqueArchivos(ruta_bioma_raiz=sandbox)
        arq = Arquetipo(nombre="Fundador_G1", id_individuo="G1_Adan", linaje="Linaje_Primigenio")
        core = construir_organismo(sensor=adaptador, actuador=adaptador, arquetipo=arq, frecuencia_max_ms=5000.0)
        if aislar_ruido:
            _aislar(core)
        for _i in range(latidos):
            onda = await core.ejecutar_latido()
            ejec = next(iter(onda.reactiva.ef.get("Ejecucion", {}).values()), None)
            cmd = str(ejec.product.get("comando")) if ejec else "ACC_ESPERAR"
            obj = str(ejec.product.get("target", "")).replace(nombre_sandbox, "bosque") if ejec else ""
            decisiones.append((cmd, obj))
            if not core.soma.esta_vivo:
                break
    return {"mundo": "bosque", "decisiones": decisiones}


async def crafter(latidos: int, aislar_ruido: bool, semilla: int = 0, **_: Any) -> Dict[str, Any]:
    from nivel_1_core.contratos import Arquetipo
    from nivel_3_componentes.mundos.mundo_crafter.adaptador_crafter import AdaptadorCrafter
    from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import evaluar_individuo_en_semilla
    adaptador = AdaptadorCrafter(max_pasos=latidos)
    adaptador.conectar()
    arquetipo = Arquetipo(nombre="Hominis_Test_H7", responsabilidad=0.72, umbral_miedo=0.58, neuroticismo=0.30, apertura=0.60)
    res = await evaluar_individuo_en_semilla(
        adaptador=adaptador, arquetipo=arquetipo, axiomas_heredados=[], seed_mapa=semilla,
        max_latidos=latidos, aislar_ruido_termodinamico=aislar_ruido,
    )
    claves = ("seed", "latidos", "total_logros", "logros", "causa_muerte", "crafter_score_individual")
    return {"mundo": "crafter", **{k: res[k] for k in claves}, "decisiones": list(res["secuencia_completa"])}


def jugador_crafter(core: Any) -> Optional[Dict[str, Any]]:
    """Estado del jugador en el juego (lectura; no escribe en el mundo)."""
    env = getattr(getattr(core, "sensor", None), "env", None)
    mundo, jugador = getattr(env, "_world", None), getattr(env, "_player", None)
    if mundo is None or jugador is None:
        return None
    inv = dict(getattr(jugador, "inventory", {}) or {})
    return {"salud": int(inv.get("health", 0)), "comida": int(inv.get("food", 0)), "bebida": int(inv.get("drink", 0)),
            "energia": int(inv.get("energy", 0)), "duerme": bool(getattr(jugador, "sleeping", False)),
            "luz": round(float(getattr(mundo, "daylight", 1.0)), 3)}


EPISODIOS: Dict[str, Callable[..., Any]] = {"ejemplo_minimo": ejemplo_minimo, "bosque": bosque, "crafter": crafter}
