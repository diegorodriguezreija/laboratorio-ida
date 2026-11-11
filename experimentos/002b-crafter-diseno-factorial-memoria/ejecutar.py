"""
Script de ejecución formal para el Experimento 002b:
Diseño Factorial 2x2 — Desacoplamiento de Arquitectura Bioinspirada vs. Memoria Espacial en Crafter 2D.
Evalúa 60 semillas vírgenes pareadas (3040 a 3099) en 4 brazos pareados (240 episodios en total).
"""

import asyncio
import csv
import importlib
import json
import math
import os
import sys
import time
from typing import Any, Dict, List, Tuple

import numpy as np

# Configuración de rutas
RUTA_EXPERIMENTO = os.path.dirname(os.path.abspath(__file__))
RUTA_LAB = os.path.abspath(os.path.join(RUTA_EXPERIMENTO, "..", ".."))
if RUTA_LAB not in sys.path:
    sys.path.insert(0, RUTA_LAB)
if os.path.join(RUTA_LAB, "base") not in sys.path:
    sys.path.insert(0, os.path.join(RUTA_LAB, "base"))

import crafter
from nivel_1_core.contratos import Arquetipo
from nivel_3_componentes.mundos.mundo_crafter.adaptador_crafter import AdaptadorCrafter
from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import (
    ACHIEVEMENTS_22,
    calcular_crafter_score_poblacional,
    evaluar_individuo_en_semilla,
)
from nivel_3_componentes.rutas_salida import asegurar_directorio_de, directorio_salidas

# Importar líneas base
modulo_voraz_base = importlib.import_module("lineas-base.crafter_voraz")
AgenteCrafterVoraz = modulo_voraz_base.AgenteCrafterVoraz

modulo_voraz_mem = importlib.import_module("lineas-base.crafter_voraz_memoria")
AgenteCrafterVorazMemoria = modulo_voraz_mem.AgenteCrafterVorazMemoria

RUTA_SALIDA_DIR = directorio_salidas("002b-crafter-diseno-factorial-memoria")
RUTA_CSV = os.path.join(RUTA_SALIDA_DIR, "episodios_pareados.csv")
RUTA_JSON_RESUMEN = os.path.join(RUTA_SALIDA_DIR, "resumen_estadistico.json")


def evaluar_agente_voraz(seed: int, con_memoria: bool, max_pasos: int = 500) -> Dict[str, Any]:
    """Evalúa la línea base voraz (Brazo 1: Reactivo sin memoria, o Brazo 3: Con memoria)."""
    adaptador = AdaptadorCrafter(radio_vision=6, max_pasos=max_pasos, seed=seed)
    adaptador.conectar()
    env = adaptador.env

    if con_memoria:
        agente = AgenteCrafterVorazMemoria(radio_vision=6, memoria_activa=True)
        nombre_brazo = "Voraz_Memoria"
        factor_arq = "Tradicional"
        factor_mem = "Con_Memoria"
    else:
        agente = AgenteCrafterVoraz(radio_vision=6)
        nombre_brazo = "Voraz_Reactivo"
        factor_arq = "Tradicional"
        factor_mem = "Sin_Memoria"

    pasos = 0
    muerte_detectada = False
    logros_desbloqueados = set()

    for paso in range(1, max_pasos + 1):
        player = env._player
        px, py = int(player.pos[0]), int(player.pos[1])
        world = env._world

        xmin = max(0, px - 6)
        xmax = min(64, px + 7)
        ymin = max(0, py - 6)
        ymax = min(64, py + 7)

        vista_local = {}
        for x in range(xmin, xmax):
            for y in range(ymin, ymax):
                vista_local[(x, y)] = world[(x, y)]

        salud = int(player.health)
        comida = int(player.inventory.get("food", 9))
        bebida = int(player.inventory.get("drink", 9))
        energia = int(player.inventory.get("energy", 9))
        daylight = float(world.daylight)
        sleeping = bool(player.sleeping)
        facing = tuple(player.facing)
        inventario = dict(player.inventory)

        if salud <= 0:
            muerte_detectada = True
            break

        accion_str = agente.decidir(
            player_pos=(px, py),
            facing=facing,
            salud=salud,
            comida=comida,
            bebida=bebida,
            energia=energia,
            daylight=daylight,
            sleeping=sleeping,
            inventario=inventario,
            vista_local=vista_local,
        )

        accion_idx = AdaptadorCrafter.ACCIONES_MAP.get(accion_str, 0)
        _, _, done, info = env.step(accion_idx)
        pasos += 1

        for ach, val in info.get("achievements", {}).items():
            if val > 0:
                logros_desbloqueados.add(ach)

        if done or env._player.health <= 0:
            muerte_detectada = True
            break

    if hasattr(env, "close"):
        try:
            env.close()
        except Exception:
            pass

    retornos = getattr(agente, "retornos_fuera_de_vista", 0)
    score_ind = float(np.mean([1.0 if a in logros_desbloqueados else 0.0 for a in ACHIEVEMENTS_22]) * 100)

    return {
        "semilla": seed,
        "brazo": nombre_brazo,
        "arquitectura": factor_arq,
        "memoria": factor_mem,
        "logros": len(logros_desbloqueados),
        "crafter_score_individual": round(score_ind, 2),
        "duracion_pasos": pasos,
        "retornos_fuera_de_vista": retornos,
        "desglose_logros": ";".join(sorted(list(logros_desbloqueados))),
        "muerte": muerte_detectada,
    }


async def main():
    print("=" * 80)
    print("EXPERIMENTO 002b: DISEÑO FACTORIAL 2x2")
    print("IdA v12.0 vs. Línea Base Voraz (Con y Sin Memoria Alocéntrica)")
    print("Semillas vírgenes pareadas: 3040 a 3099 (N = 60 por brazo, Total 240 episodios)")
    print("=" * 80)

    # Cargar linaje ancestral de IdA
    ruta_linaje = os.path.join(RUTA_LAB, "tests_arquitectura", "fixtures", "linaje_evolutivo_crafter.json")
    if not os.path.exists(ruta_linaje):
        ruta_linaje = os.path.join(RUTA_LAB, "archivo-v14", "analisis_historico", "linajes_ejemplo", "linaje_evolutivo_crafter.json")
    with open(ruta_linaje, "r", encoding="utf-8") as f:
        datos_linaje = json.load(f)

    axiomas_g12 = datos_linaje.get("axiomas_heredados", [])
    historial = datos_linaje.get("historial_generaciones", [])
    reg_g12 = historial[11] if len(historial) >= 12 else historial[-1]
    rasgos_g12 = reg_g12["arquetipo_rasgos"]

    arquetipo_ida = Arquetipo(
        nombre="Hominis_G12_Selected",
        id_individuo="Hominis_G12",
        linaje="Linaje_Hominis_Crafter",
        generacion=12,
        apertura=float(rasgos_g12["apertura"]),
        responsabilidad=float(rasgos_g12["responsabilidad"]),
        neuroticismo=float(rasgos_g12["neuroticismo"]),
        umbral_miedo=float(rasgos_g12["umbral_miedo"]),
    )

    adaptador_ida = AdaptadorCrafter(radio_vision=6)

    semillas = list(range(3040, 3100))
    n_total = len(semillas)

    asegurar_directorio_de(RUTA_CSV)
    
    campos = [
        "semilla",
        "brazo",
        "arquitectura",
        "memoria",
        "logros",
        "crafter_score_individual",
        "duracion_pasos",
        "retornos_fuera_de_vista",
        "desglose_logros",
        "muerte",
    ]

    registros_completos = []

    print(f"\nIniciando ejecución de los 4 brazos pareados sobre {n_total} semillas...")
    t0_global = time.time()

    for idx, s in enumerate(semillas, start=1):
        t0_seed = time.time()
        print(f"\n--- [Semilla {s}] ({idx}/{n_total}) ---")

        # Brazo 1: Voraz Reactivo (Sin Memoria)
        r1 = evaluar_agente_voraz(s, con_memoria=False)
        registros_completos.append(r1)

        # Brazo 2: IdA Sin Memoria (Ablación limpia de memoria alocéntrica)
        ev2 = await evaluar_individuo_en_semilla(
            adaptador=adaptador_ida,
            arquetipo=arquetipo_ida,
            axiomas_heredados=axiomas_g12,
            seed_mapa=s,
            max_latidos=500,
            memoria_alocentrica=False,
        )
        r2 = {
            "semilla": s,
            "brazo": "IdA_SinMemoria",
            "arquitectura": "Bioinspirado",
            "memoria": "Sin_Memoria",
            "logros": ev2["total_logros"],
            "crafter_score_individual": ev2.get("crafter_score_individual", 0.0),
            "duracion_pasos": ev2["latidos"],
            "retornos_fuera_de_vista": 0,
            "desglose_logros": ";".join(ev2["logros"]),
            "muerte": bool(ev2["salud_final"] <= 0),
        }
        registros_completos.append(r2)

        # Brazo 3: Voraz con Memoria Espacial
        r3 = evaluar_agente_voraz(s, con_memoria=True)
        registros_completos.append(r3)

        # Brazo 4: IdA Canónica Completa (Con Memoria)
        ev4 = await evaluar_individuo_en_semilla(
            adaptador=adaptador_ida,
            arquetipo=arquetipo_ida,
            axiomas_heredados=axiomas_g12,
            seed_mapa=s,
            max_latidos=500,
            memoria_alocentrica=True,
        )
        r4 = {
            "semilla": s,
            "brazo": "IdA_Canonica",
            "arquitectura": "Bioinspirado",
            "memoria": "Con_Memoria",
            "logros": ev4["total_logros"],
            "crafter_score_individual": ev4.get("crafter_score_individual", 0.0),
            "duracion_pasos": ev4["latidos"],
            "retornos_fuera_de_vista": 0,
            "desglose_logros": ";".join(ev4["logros"]),
            "muerte": bool(ev4["salud_final"] <= 0),
        }
        registros_completos.append(r4)

        t_seed = time.time() - t0_seed
        print(f"  B1 (Voraz Reactivo)  : {r1['logros']} logros | {r1['duracion_pasos']} pasos")
        print(f"  B2 (IdA Sin Memoria)  : {r2['logros']} logros | {r2['duracion_pasos']} pasos")
        print(f"  B3 (Voraz Memoria)   : {r3['logros']} logros | {r3['duracion_pasos']} pasos (Retornos: {r3['retornos_fuera_de_vista']})")
        print(f"  B4 (IdA Canónica)    : {r4['logros']} logros | {r4['duracion_pasos']} pasos")
        print(f"  [Semilla {s} completada en {t_seed:.1f} s]")

        # Guardado incremental para tolerancia a fallos
        with open(RUTA_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            writer.writerows(registros_completos)

    t_global = time.time() - t0_global
    print(f"\n{'-'*80}")
    print(f"Ejecución de los 240 episodios completada con éxito en {t_global/60:.2f} minutos.")
    print(f"Datos almacenados en: {RUTA_CSV}")
    print(f"{'-'*80}")

    # Ejecutar análisis estadístico pre-registrado
    from analizar import analizar_datos
    resumen = analizar_datos(RUTA_CSV)
    with open(RUTA_JSON_RESUMEN, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    print(f"Resumen estadístico guardado en: {RUTA_JSON_RESUMEN}")


if __name__ == "__main__":
    asyncio.run(main())
