"""
Script de ejecución formal para el Experimento 002:
IdA v12.0 vs. Agente Voraz Tradicional vs. Agente Aleatorio en Crafter 2D.
Evalúa 40 semillas pareadas (3000 a 3039) garantizando paridad de observación y acción.
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
from herramientas.estadistica import (
    bootstrap_ci_diferencia_pareada,
    calcular_cliffs_delta,
    evaluar_comparativa_pareada,
)
from nivel_1_core.contratos import Arquetipo
from nivel_3_componentes.mundos.mundo_crafter.adaptador_crafter import AdaptadorCrafter
from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import (
    ACHIEVEMENTS_22,
    calcular_crafter_score_poblacional,
    evaluar_individuo_en_semilla,
)
from nivel_3_componentes.rutas_salida import asegurar_directorio_de, directorio_salidas

# Importar el agente voraz de líneas-base dinámicamente
modulo_voraz = importlib.import_module("lineas-base.crafter_voraz")
AgenteCrafterVoraz = modulo_voraz.AgenteCrafterVoraz

RUTA_SALIDA_DIR = directorio_salidas("002-crafter-ida-vs-voraz")
RUTA_CSV = os.path.join(RUTA_SALIDA_DIR, "episodios_pareados.csv")
RUTA_JSON_RESUMEN = os.path.join(RUTA_SALIDA_DIR, "resumen_estadistico.json")


def evaluar_agente_voraz_en_semilla(seed: int, max_pasos: int = 500) -> Dict[str, Any]:
    """Evalúa el agente voraz tradicional con vista local restringida (radio 6)."""
    env = crafter.Env(
        area=(64, 64),
        view=(9, 9),
        size=(64, 64),
        reward=True,
        length=max_pasos,
        seed=seed,
    )
    env.reset()
    agente = AgenteCrafterVoraz(radio_vision=6)

    pasos = 0
    muerte_detectada = False
    logros_desbloqueados = set()

    for paso in range(1, max_pasos + 1):
        player = env._player
        px, py = int(player.pos[0]), int(player.pos[1])
        world = env._world

        # Construir la vista local idéntica a la que percibe IdA (radio 6)
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
    return {
        "semilla": seed,
        "brazo": "Voraz",
        "pasos": pasos,
        "muerte": muerte_detectada,
        "logros": sorted(list(logros_desbloqueados)),
        "num_logros": len(logros_desbloqueados),
    }


def evaluar_agente_aleatorio_en_semilla(seed: int, max_pasos: int = 500) -> Dict[str, Any]:
    """Evalúa un agente aleatorio uniforme para anclar la cota inferior."""
    env = crafter.Env(
        area=(64, 64),
        view=(9, 9),
        size=(64, 64),
        reward=True,
        length=max_pasos,
        seed=seed,
    )
    env.reset()
    rng = np.random.default_rng(seed=seed)

    pasos = 0
    muerte_detectada = False
    logros_desbloqueados = set()

    for paso in range(1, max_pasos + 1):
        if env._player.health <= 0:
            muerte_detectada = True
            break

        accion_idx = int(rng.integers(0, 17))
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
    return {
        "semilla": seed,
        "brazo": "Aleatorio",
        "pasos": pasos,
        "muerte": muerte_detectada,
        "logros": sorted(list(logros_desbloqueados)),
        "num_logros": len(logros_desbloqueados),
    }


async def main():
    print("=" * 80)
    print("EXPERIMENTO 002: CONTRASTE DE RENDIMIENTO EN CRAFTER 2D")
    print("IdA v12.0 (Arquetipo G12) vs. Agente Voraz Tradicional vs. Agente Aleatorio")
    print("Semillas pareadas: 3000 a 3039 (N = 40)")
    print("=" * 80)

    # 1. Cargar arquetipo y axiomas ancestrales de IdA
    # Ubicación oficial en fixtures de arquitectura y archivo histórico
    ruta_linaje = os.path.join(RUTA_LAB, "tests_arquitectura", "fixtures", "linaje_evolutivo_crafter.json")
    if not os.path.exists(ruta_linaje):
        ruta_linaje = os.path.join(RUTA_LAB, "archivo-v14", "analisis_historico", "linajes_ejemplo", "linaje_evolutivo_crafter.json")
    if not os.path.exists(ruta_linaje):
        raise FileNotFoundError(f"No se encontró el linaje ancestral en {ruta_linaje}")

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

    semillas = list(range(3000, 3040))
    resultados_ida = []
    resultados_voraz = []
    resultados_aleatorio = []

    print(f"\n[1/3] Evaluando IdA v12.0 en 40 semillas...")
    t0_ida = time.time()
    for idx, s in enumerate(semillas):
        res = await evaluar_individuo_en_semilla(
            adaptador=adaptador_ida,
            arquetipo=arquetipo_ida,
            axiomas_heredados=axiomas_g12,
            seed_mapa=s,
            max_latidos=500,
        )
        res_limpio = {
            "semilla": s,
            "brazo": "IdA",
            "pasos": res["latidos"],
            "muerte": bool(res["salud_final"] <= 0),
            "logros": res["logros"],
            "num_logros": res["total_logros"],
        }
        resultados_ida.append(res_limpio)
        print(f"  - IdA Semilla {s} ({idx+1}/40): {res_limpio['num_logros']} logros | {res_limpio['pasos']} pasos")
    t_ida = time.time() - t0_ida
    print(f"  Completado IdA en {t_ida:.1f} s")

    print(f"\n[2/3] Evaluando Agente Voraz en 40 semillas...")
    t0_voraz = time.time()
    for idx, s in enumerate(semillas):
        res_v = evaluar_agente_voraz_en_semilla(seed=s, max_pasos=500)
        resultados_voraz.append(res_v)
        print(f"  - Voraz Semilla {s} ({idx+1}/40): {res_v['num_logros']} logros | {res_v['pasos']} pasos")
    t_voraz = time.time() - t0_voraz
    print(f"  Completado Voraz en {t_voraz:.1f} s")

    print(f"\n[3/3] Evaluando Agente Aleatorio en 40 semillas...")
    t0_aleat = time.time()
    for idx, s in enumerate(semillas):
        res_a = evaluar_agente_aleatorio_en_semilla(seed=s, max_pasos=500)
        resultados_aleatorio.append(res_a)
    t_aleat = time.time() - t0_aleat
    print(f"  Completado Aleatorio en {t_aleat:.1f} s")

    # Guardar CSV crudo
    asegurar_directorio_de(RUTA_CSV)
    with open(RUTA_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["semilla", "brazo", "pasos", "muerte", "num_logros", "logros_lista"])
        for r in resultados_ida + resultados_voraz + resultados_aleatorio:
            writer.writerow([
                r["semilla"],
                r["brazo"],
                r["pasos"],
                1 if r["muerte"] else 0,
                r["num_logros"],
                ";".join(r["logros"]),
            ])
    print(f"\n[+] Datos crudos guardados en: {RUTA_CSV}")

    # Calcular Crafter Score por brazo
    score_ida_dict = calcular_crafter_score_poblacional([{"logros": r["logros"]} for r in resultados_ida])
    score_voraz_dict = calcular_crafter_score_poblacional([{"logros": r["logros"]} for r in resultados_voraz])
    score_aleat_dict = calcular_crafter_score_poblacional([{"logros": r["logros"]} for r in resultados_aleatorio])

    score_ida = score_ida_dict["crafter_score"]
    logros_ida = score_ida_dict["success_rates"]
    score_voraz = score_voraz_dict["crafter_score"]
    logros_voraz = score_voraz_dict["success_rates"]
    score_aleat = score_aleat_dict["crafter_score"]
    logros_aleat = score_aleat_dict["success_rates"]

    # Estadísticas de supervivencia y logros
    pasos_ida = [r["pasos"] for r in resultados_ida]
    pasos_voraz = [r["pasos"] for r in resultados_voraz]
    pasos_aleat = [r["pasos"] for r in resultados_aleatorio]

    num_logros_ida = [r["num_logros"] for r in resultados_ida]
    num_logros_voraz = [r["num_logros"] for r in resultados_voraz]
    num_logros_aleat = [r["num_logros"] for r in resultados_aleatorio]

    # Contrastes pareados IdA vs Voraz
    comp_pasos = evaluar_comparativa_pareada(pasos_ida, pasos_voraz, "IdA", "Voraz")
    comp_logros = evaluar_comparativa_pareada(num_logros_ida, num_logros_voraz, "IdA", "Voraz")

    resumen = {
        "n_semillas": len(semillas),
        "crafter_scores": {
            "ida": score_ida,
            "voraz": score_voraz,
            "aleatorio": score_aleat,
        },
        "pasos_supervivencia": comp_pasos,
        "logros_desbloqueados": comp_logros,
        "tasas_por_logro": {
            "ida": logros_ida,
            "voraz": logros_voraz,
            "aleatorio": logros_aleat,
        },
    }

    with open(RUTA_JSON_RESUMEN, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("RESUMEN DE RESULTADOS")
    print("=" * 80)
    print(f"Crafter Score: IdA = {score_ida:.2f} % | Voraz = {score_voraz:.2f} % | Aleatorio = {score_aleat:.2f} %")
    print(f"Pasos Supervivencia: IdA = {comp_pasos['media_tratamiento']:.1f} vs Voraz = {comp_pasos['media_control']:.1f} | Diff = {comp_pasos['delta_media']:+.1f} [95% CI: {comp_pasos['ci_95'][0]:+.1f}, {comp_pasos['ci_95'][1]:+.1f}] | Wilcoxon p = {comp_pasos['wilcoxon_p']:.4f}")
    print(f"Logros Desbloqueados: IdA = {comp_logros['media_tratamiento']:.2f} vs Voraz = {comp_logros['media_control']:.2f} | Diff = {comp_logros['delta_media']:+.2f} [95% CI: {comp_logros['ci_95'][0]:+.2f}, {comp_logros['ci_95'][1]:+.2f}] | Wilcoxon p = {comp_logros['wilcoxon_p']:.4f}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
