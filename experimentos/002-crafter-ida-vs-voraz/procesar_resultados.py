"""
Procesa el CSV ya generado de 120 episodios (40 semillas x 3 brazos) y genera el resumen estadístico formal.
"""

import csv
import json
import os
import sys
import numpy as np

RUTA_EXPERIMENTO = os.path.dirname(os.path.abspath(__file__))
RUTA_LAB = os.path.abspath(os.path.join(RUTA_EXPERIMENTO, "..", ".."))
if RUTA_LAB not in sys.path:
    sys.path.insert(0, RUTA_LAB)
if os.path.join(RUTA_LAB, "base") not in sys.path:
    sys.path.insert(0, os.path.join(RUTA_LAB, "base"))

from herramientas.estadistica import (
    bootstrap_ci_diferencia_pareada,
    calcular_cliffs_delta,
    evaluar_comparativa_pareada,
)
from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import (
    ACHIEVEMENTS_22,
    calcular_crafter_score_poblacional,
)
from nivel_3_componentes.rutas_salida import directorio_salidas

RUTA_SALIDA_DIR = directorio_salidas("002-crafter-ida-vs-voraz")
RUTA_CSV = os.path.join(RUTA_SALIDA_DIR, "episodios_pareados.csv")
RUTA_JSON_RESUMEN = os.path.join(RUTA_SALIDA_DIR, "resumen_estadistico.json")


def procesar():
    resultados_ida = []
    resultados_voraz = []
    resultados_aleatorio = []

    with open(RUTA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for fila in reader:
            item = {
                "semilla": int(fila["semilla"]),
                "brazo": fila["brazo"],
                "pasos": int(fila["pasos"]),
                "muerte": bool(int(fila["muerte"])),
                "num_logros": int(fila["num_logros"]),
                "logros": fila["logros_lista"].split(";") if fila["logros_lista"] else [],
            }
            if item["brazo"] == "IdA":
                resultados_ida.append(item)
            elif item["brazo"] == "Voraz":
                resultados_voraz.append(item)
            elif item["brazo"] == "Aleatorio":
                resultados_aleatorio.append(item)

    resultados_ida.sort(key=lambda x: x["semilla"])
    resultados_voraz.sort(key=lambda x: x["semilla"])
    resultados_aleatorio.sort(key=lambda x: x["semilla"])

    score_ida_dict = calcular_crafter_score_poblacional([{"logros": r["logros"]} for r in resultados_ida])
    score_voraz_dict = calcular_crafter_score_poblacional([{"logros": r["logros"]} for r in resultados_voraz])
    score_aleat_dict = calcular_crafter_score_poblacional([{"logros": r["logros"]} for r in resultados_aleatorio])

    score_ida = score_ida_dict["crafter_score"]
    logros_ida = score_ida_dict["success_rates"]
    score_voraz = score_voraz_dict["crafter_score"]
    logros_voraz = score_voraz_dict["success_rates"]
    score_aleat = score_aleat_dict["crafter_score"]
    logros_aleat = score_aleat_dict["success_rates"]

    pasos_ida = [r["pasos"] for r in resultados_ida]
    pasos_voraz = [r["pasos"] for r in resultados_voraz]
    pasos_aleat = [r["pasos"] for r in resultados_aleatorio]

    num_logros_ida = [r["num_logros"] for r in resultados_ida]
    num_logros_voraz = [r["num_logros"] for r in resultados_voraz]
    num_logros_aleat = [r["num_logros"] for r in resultados_aleatorio]

    comp_pasos = evaluar_comparativa_pareada(pasos_ida, pasos_voraz, "IdA", "Voraz")
    comp_logros = evaluar_comparativa_pareada(num_logros_ida, num_logros_voraz, "IdA", "Voraz")

    resumen = {
        "n_semillas": len(resultados_ida),
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

    print("=" * 80)
    print("RESUMEN DE RESULTADOS: EXPERIMENTO 002")
    print("=" * 80)
    print(f"Crafter Score: IdA = {score_ida:.2f} % | Voraz = {score_voraz:.2f} % | Aleatorio = {score_aleat:.2f} %")
    print(f"Pasos Supervivencia: IdA = {comp_pasos['media_tratamiento']:.1f} vs Voraz = {comp_pasos['media_control']:.1f} | Diff = {comp_pasos['delta_media']:+.1f} [95% CI: {comp_pasos['ci_95'][0]:+.1f}, {comp_pasos['ci_95'][1]:+.1f}] | Wilcoxon p = {comp_pasos['wilcoxon_p']:.6f} | Cliff's delta = {comp_pasos['cliffs_delta']:.4f}")
    print(f"Logros Desbloqueados: IdA = {comp_logros['media_tratamiento']:.2f} vs Voraz = {comp_logros['media_control']:.2f} | Diff = {comp_logros['delta_media']:+.2f} [95% CI: {comp_logros['ci_95'][0]:+.2f}, {comp_logros['ci_95'][1]:+.2f}] | Wilcoxon p = {comp_logros['wilcoxon_p']:.6f} | Cliff's delta = {comp_logros['cliffs_delta']:.4f}")
    print("=" * 80)
    print("Desglose de tasas por logro (%):")
    for ach in ACHIEVEMENTS_22:
        print(f"  {ach:<22}: IdA = {logros_ida[ach]:5.1f}% | Voraz = {logros_voraz[ach]:5.1f}% | Aleat = {logros_aleat[ach]:5.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    procesar()
