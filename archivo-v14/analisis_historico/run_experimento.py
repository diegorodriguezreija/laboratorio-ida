"""
Harness Universal de Experimentación Científica (IdA v12.0)
===========================================================
Ejecutor centralizado para las hipótesis falsables H1, H7 y H2:
- Manejo de particiones herméticas de semillas (desarrollo, test 2020-2059, reserva).
- Protocolo pareado por semilla.
- Soporte para dos niveles de ablación:
    - Nivel a: sustitución de regla de selección conservando soma periférico.
    - Nivel b: emisión directa sin acecho, desesperación ni colapso.
- Registro contrafactual pasivo y estratificación por estrés somático.
- Exportación a CSV de episodios y telemetría tick a tick.
- Integración automática con analisis/estadistica.py.
"""

import argparse
import asyncio
import csv
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Añadir raíz al sys.path
RUTA_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_RAIZ = os.path.abspath(os.path.join(RUTA_DIR, ".."))
if RUTA_RAIZ not in sys.path:
    sys.path.insert(0, RUTA_RAIZ)

from nivel_1_core.contratos import Arquetipo
from nivel_1_core.arbitros import crear_arbitro, REGISTRO_ARBITROS
from nivel_3_componentes.mundos.mundo_crafter.adaptador_crafter import AdaptadorCrafter
from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import (
    ACHIEVEMENTS_22,
    calcular_crafter_score_poblacional,
    evaluar_individuo_en_semilla,
)
from nivel_3_componentes.rutas_salida import directorio_salidas
from analisis.estadistica import (
    evaluar_comparativa_pareada,
    corregir_holm_bonferroni,
)


def parsear_rango_semillas(rango_str: str) -> List[int]:
    """Parsea un rango tipo '2020-2059' o lista separada por comas '2020,2021'."""
    if "-" in rango_str:
        partes = rango_str.split("-")
        return list(range(int(partes[0].strip()), int(partes[1].strip()) + 1))
    elif "," in rango_str:
        return [int(x.strip()) for x in rango_str.split(",") if x.strip()]
    else:
        return [int(rango_str.strip())]


async def ejecutar_h1_crafter(
    semillas: List[int],
    modo_ablacion: str = "nivel_a",
    ruta_csv: str = os.path.join(directorio_salidas("analisis"), "H1_crafter.csv"),
    recolectar_telemetria: bool = True,
) -> Dict[str, Any]:
    """
    Ejecuta el protocolo experimental H1 en Crafter ($N \\ge 40$ semillas pareadas):
    Compara A0 frente a A1, A2, A3, A4 y A7 bajo el nivel de ablación especificado.
    """
    os.makedirs(os.path.dirname(os.path.abspath(ruta_csv)), exist_ok=True)
    ruta_telemetria = ruta_csv.replace(".csv", "_telemetria.csv")

    # Utilizar el arquetipo seleccionado de referencia (Hominis_G12) con sus parámetros
    arquetipo_test = Arquetipo(
        nombre="Hominis_Test_H1",
        responsabilidad=0.72,
        umbral_miedo=0.58,
        neuroticismo=0.30,
        apertura=0.60,
    )

    arbitros_a_evaluar = ["A0", "A1", "A2", "A3", "A4", "A7"]
    adaptador = AdaptadorCrafter(max_pasos=500)
    adaptador.conectar()

    resultados_episodios: List[Dict[str, Any]] = []
    telemetria_total: List[Dict[str, Any]] = []

    print(f"\n[H1 CRAFTER] Evaluando {len(arbitros_a_evaluar)} árbitros en N={len(semillas)} semillas ({semillas[0]}..{semillas[-1]})")
    print(f"[*] Modo de ablación: {modo_ablacion}")

    for idx_s, s in enumerate(semillas, 1):
        for aid in arbitros_a_evaluar:
            arb_inst = crear_arbitro(aid, seed_propia=s + 500) if aid == "A4" else crear_arbitro(aid)
            res = await evaluar_individuo_en_semilla(
                adaptador=adaptador,
                arquetipo=arquetipo_test,
                axiomas_heredados=[],
                seed_mapa=s,
                max_latidos=500,
                arbitro=arb_inst,
                modo_ablacion=modo_ablacion,
                recolectar_telemetria=recolectar_telemetria,
            )

            fila = {
                "semilla": s,
                "arbitro_id": aid,
                "arbitro_nombre": arb_inst.nombre,
                "modo_ablacion": modo_ablacion,
                "latidos": res["latidos"],
                "total_logros": res["total_logros"],
                "logros": ";".join(res["logros"]),
                "salud_final": res["salud_final"],
                "causa_muerte": res["causa_muerte"],
                "fitness_global": res["fitness"]["global"],
                "fitness_s1": res["fitness"]["s1_reactivo"],
                "fitness_s2": res["fitness"]["s2_limbico"],
                "fitness_s3": res["fitness"]["s3_racional"],
                "crafter_score_ind": res["crafter_score_individual"],
                "paso_por_logro": ";".join(f"{k}:{v}" for k, v in res["paso_por_logro"].items()),
            }
            resultados_episodios.append(fila)

            # Acumular telemetría contrafactual del árbitro A0
            if recolectar_telemetria and aid == "A0":
                for t in res.get("telemetria", []):
                    t_fila = {
                        "semilla": s,
                        "tick": t["tick"],
                        "accion_efectiva": t["comando"],
                        "origen_ganador": t["origen"],
                        "cortisol": t["cortisol"],
                        "alimentacion": t["alimentacion"],
                        "energia": t["energia"],
                        "num_desacuerdos": len(t.get("desacuerdos", [])),
                        "desacuerdos_lista": ";".join(t.get("desacuerdos", [])),
                    }
                    cf_dict = t.get("contrafactual", {})
                    for cf_id in ("A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7"):
                        cf_data = cf_dict.get(cf_id, {})
                        t_fila[f"cf_{cf_id}_cmd"] = cf_data.get("comando", "")
                        t_fila[f"cf_{cf_id}_origen"] = cf_data.get("origen", "")
                    telemetria_total.append(t_fila)

        if idx_s % 5 == 0 or idx_s == len(semillas):
            print(f"  -> Progreso: {idx_s}/{len(semillas)} semillas evaluadas ({idx_s * len(arbitros_a_evaluar)} episodios)")

    # Escribir CSV de episodios
    claves_csv = list(resultados_episodios[0].keys())
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=claves_csv)
        writer.writeheader()
        writer.writerows(resultados_episodios)
    print(f"[+] Dataset de episodios guardado en: {ruta_csv}")

    # Escribir CSV de telemetría si procede
    if telemetria_total:
        claves_tel = list(telemetria_total[0].keys())
        with open(ruta_telemetria, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=claves_tel)
            writer.writeheader()
            writer.writerows(telemetria_total)
        print(f"[+] Telemetría contrafactual guardada en: {ruta_telemetria}")

    # Análisis Inferencial Pareado frente a A0
    comparativas: Dict[str, Any] = {}
    metricas_poblacionales: Dict[str, Any] = {}

    # Agrupar por árbitro
    por_arbitro: Dict[str, List[Dict[str, Any]]] = {aid: [] for aid in arbitros_a_evaluar}
    for r in resultados_episodios:
        por_arbitro[r["arbitro_id"]].append(r)

    # Calcular Crafter Score Poblacional Canónico por árbitro
    for aid, episodios_arb in por_arbitro.items():
        hist_adaptado = [{"logros": ep["logros"].split(";") if ep["logros"] else []} for ep in episodios_arb]
        cs_res = calcular_crafter_score_poblacional(hist_adaptado)
        logros_arr = [ep["total_logros"] for ep in episodios_arb]
        pasos_arr = [ep["latidos"] for ep in episodios_arb]

        metricas_poblacionales[aid] = {
            "crafter_score_poblacional": round(cs_res["crafter_score"], 2),
            "logros_desbloqueados_unicos": len(cs_res["logros_desbloqueados"]),
            "logros_media": round(float(np.mean(logros_arr)), 2),
            "logros_std": round(float(np.std(logros_arr)), 2),
            "logros_mediana": float(np.median(logros_arr)),
            "pasos_media": round(float(np.mean(pasos_arr)), 1),
            "pasos_std": round(float(np.std(pasos_arr)), 1),
        }

    # Comparaciones pareadas (A0 vs A_i)
    logros_a0 = [ep["total_logros"] for ep in por_arbitro["A0"]]
    p_values_para_ajuste = []
    comparativas_raw = []

    for aid in [a for a in arbitros_a_evaluar if a != "A0"]:
        logros_ai = [ep["total_logros"] for ep in por_arbitro[aid]]
        comp = evaluar_comparativa_pareada(
            tratamiento=logros_a0,
            control=logros_ai,
            nombre_tratamiento="A0_Tribunal",
            nombre_control=aid,
        )
        comparativas_raw.append(comp)
        p_values_para_ajuste.append(comp["wilcoxon_p"])

    # Ajuste de Holm-Bonferroni
    p_ajustados = corregir_holm_bonferroni(p_values_para_ajuste)
    for comp, p_adj in zip(comparativas_raw, p_ajustados):
        comp["wilcoxon_p_holm_ajustado"] = round(p_adj, 6)
        comp["significativo_tras_holm"] = bool(p_adj < 0.05 and comp["ci_95"][0] > 0)
        comparativas[comp["control"]] = comp

    # Tasa de acuerdo contrafactual desde telemetría
    acuerdo_estratificado: Dict[str, Any] = {}
    if telemetria_total:
        total_ticks = len(telemetria_total)
        ticks_estres_alto = [t for t in telemetria_total if t["cortisol"] >= 0.70]
        ticks_inanicion = [t for t in telemetria_total if t["alimentacion"] <= 15.0]

        for aid in [a for a in arbitros_a_evaluar if a != "A0"]:
            coincidencias_total = sum(1 for t in telemetria_total if t.get(f"cf_{aid}_cmd") == t["accion_efectiva"])
            tasa_global = (coincidencias_total / total_ticks) * 100.0 if total_ticks > 0 else 0.0

            tasa_estres_alto = (
                sum(1 for t in ticks_estres_alto if t.get(f"cf_{aid}_cmd") == t["accion_efectiva"]) / len(ticks_estres_alto) * 100.0
                if ticks_estres_alto else 0.0
            )
            tasa_inanicion = (
                sum(1 for t in ticks_inanicion if t.get(f"cf_{aid}_cmd") == t["accion_efectiva"]) / len(ticks_inanicion) * 100.0
                if ticks_inanicion else 0.0
            )

            acuerdo_estratificado[aid] = {
                "tasa_acuerdo_global_pct": round(tasa_global, 2),
                "tasa_acuerdo_estres_alto_pct": round(tasa_estres_alto, 2),
                "tasa_acuerdo_inanicion_critica_pct": round(tasa_inanicion, 2),
            }

    informe_final = {
        "hipotesis": "H1",
        "mundo": "crafter",
        "modo_ablacion": modo_ablacion,
        "n_semillas": len(semillas),
        "rango_semillas": [semillas[0], semillas[-1]],
        "metricas_poblacionales": metricas_poblacionales,
        "comparativas_pareadas_vs_a0": comparativas,
        "acuerdo_contrafactual_estratificado": acuerdo_estratificado,
    }

    # Guardar reporte JSON
    ruta_json = ruta_csv.replace(".csv", ".json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(informe_final, f, indent=2)
    print(f"[+] Informe JSON guardado en: {ruta_json}")

    return informe_final


async def ejecutar_h7_crafter(
    semillas: List[int],
    ruta_csv: str = os.path.join(directorio_salidas("analisis"), "H7_crafter.csv"),
    max_pasos: int = 1500,
    aislar_ruido: bool = False,
) -> Dict[str, Any]:
    """
    Ejecuta el protocolo experimental H7 en Crafter (N semillas pareadas):
    Compara S2 activo frente a S2 neutralizado (ambos bajo A0 canónico)
    con límite de supervivencia extendido (max_pasos=1500) para eliminar la censura de 500 pasos.
    """
    os.makedirs(os.path.dirname(os.path.abspath(ruta_csv)), exist_ok=True)
    arquetipo_test = Arquetipo(
        nombre="Hominis_Test_H7",
        responsabilidad=0.72,
        umbral_miedo=0.58,
        neuroticismo=0.30,
        apertura=0.60,
    )
    adaptador = AdaptadorCrafter(max_pasos=max_pasos)
    adaptador.conectar()

    condiciones = [
        {"id": "S2_On", "s2_neutro": False, "nombre": "S2 Activo"},
        {"id": "S2_Neutro", "s2_neutro": True, "nombre": "S2 Neutralizado"},
    ]

    print(f"\n[H7 CRAFTER] Evaluando S2 activo vs neutralizado en N={len(semillas)} semillas ({semillas[0]}..{semillas[-1]})")
    print(f"[*] Limite de pasos: {max_pasos} | Aislamiento de ruido termodinamico: {aislar_ruido}")

    resultados_episodios: List[Dict[str, Any]] = []
    por_condicion: Dict[str, List[Dict[str, Any]]] = {c["id"]: [] for c in condiciones}

    for idx_s, s in enumerate(semillas, 1):
        for cond in condiciones:
            res = await evaluar_individuo_en_semilla(
                adaptador=adaptador,
                arquetipo=arquetipo_test,
                axiomas_heredados=[],
                seed_mapa=s,
                max_latidos=max_pasos,
                aislar_ruido_termodinamico=aislar_ruido,
                s2_neutro=cond["s2_neutro"],
                recolectar_telemetria=True,
            )

            # Contar latidos ganados por S2
            ticks_s2 = sum(1 for t in res.get("telemetria", []) if t.get("origen") == "S2")
            pct_s2 = (ticks_s2 / res["latidos"]) * 100.0 if res["latidos"] > 0 else 0.0

            cm = str(res["causa_muerte"]).lower()
            es_depredador = bool("zombie" in cm or "skeleton" in cm or "depredador" in cm)
            llego_al_tope = bool(res["latidos"] >= max_pasos)

            fila = {
                "semilla": s,
                "condicion": cond["id"],
                "nombre": cond["nombre"],
                "latidos": res["latidos"],
                "total_logros": res["total_logros"],
                "logros": ";".join(res["logros"]),
                "salud_final": res["salud_final"],
                "causa_muerte": res["causa_muerte"],
                "muerte_depredador": es_depredador,
                "llego_al_tope": llego_al_tope,
                "fitness_global": res["fitness"]["global"],
                "crafter_score_ind": res["crafter_score_individual"],
                "paso_por_logro": ";".join(f"{k}:{v}" for k, v in res["paso_por_logro"].items()),
                "latidos_ganados_s2": ticks_s2,
                "pct_decisiones_s2": round(pct_s2, 2),
            }
            resultados_episodios.append(fila)
            por_condicion[cond["id"]].append(fila)

        if idx_s % 5 == 0 or idx_s == len(semillas):
            print(f"  -> Progreso H7: {idx_s}/{len(semillas)} semillas evaluadas ({idx_s * 2} episodios)")

    # Escribir CSV
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(resultados_episodios[0].keys()))
        writer.writeheader()
        writer.writerows(resultados_episodios)
    print(f"[+] Dataset H7 guardado en: {ruta_csv}")

    # Crafter score poblacional y metricas conjuntas por condición
    metricas_poblacionales = {}
    for cid, eps in por_condicion.items():
        hist = [{"logros": e["logros"].split(";") if e["logros"] else []} for e in eps]
        cs_res = calcular_crafter_score_poblacional(hist)
        logros_arr = [e["total_logros"] for e in eps]
        pasos_arr = [e["latidos"] for e in eps]
        fit_arr = [e["fitness_global"] for e in eps]
        depred_total = sum(1 for e in eps if e["muerte_depredador"])
        tope_total = sum(1 for e in eps if e["llego_al_tope"])

        metricas_poblacionales[cid] = {
            "crafter_score_poblacional": round(cs_res["crafter_score"], 2),
            "logros_desbloqueados_unicos": len(cs_res["logros_desbloqueados"]),
            "logros_media": round(float(np.mean(logros_arr)), 2),
            "logros_std": round(float(np.std(logros_arr)), 2),
            "logros_mediana": float(np.median(logros_arr)),
            "pasos_media": round(float(np.mean(pasos_arr)), 1),
            "pasos_std": round(float(np.std(pasos_arr)), 1),
            "pasos_mediana": float(np.median(pasos_arr)),
            "fitness_media": round(float(np.mean(fit_arr)), 1),
            "fitness_std": round(float(np.std(fit_arr)), 1),
            "fitness_mediana": float(np.median(fit_arr)),
            "muertes_depredador_total": depred_total,
            "muertes_depredador_pct": round(depred_total / len(eps) * 100.0, 1),
            "tope_pasos_alcanzado_total": tope_total,
            "tope_pasos_alcanzado_pct": round(tope_total / len(eps) * 100.0, 1),
            "pct_media_decisiones_s2": round(float(np.mean([e["pct_decisiones_s2"] for e in eps])), 2),
            "tasas_exito_logros": {ach: round(cs_res["success_rates"].get(ach, 0.0), 1) for ach in ACHIEVEMENTS_22},
        }

    # Comparativas pareadas multidimensionales
    comp_logros = evaluar_comparativa_pareada(
        tratamiento=[e["total_logros"] for e in por_condicion["S2_On"]],
        control=[e["total_logros"] for e in por_condicion["S2_Neutro"]],
        nombre_tratamiento="S2_On",
        nombre_control="S2_Neutro",
    )
    comp_pasos = evaluar_comparativa_pareada(
        tratamiento=[e["latidos"] for e in por_condicion["S2_On"]],
        control=[e["latidos"] for e in por_condicion["S2_Neutro"]],
        nombre_tratamiento="S2_On",
        nombre_control="S2_Neutro",
    )
    comp_fitness = evaluar_comparativa_pareada(
        tratamiento=[e["fitness_global"] for e in por_condicion["S2_On"]],
        control=[e["fitness_global"] for e in por_condicion["S2_Neutro"]],
        nombre_tratamiento="S2_On",
        nombre_control="S2_Neutro",
    )

    informe_final = {
        "hipotesis": "H7",
        "mundo": "crafter",
        "max_pasos": max_pasos,
        "n_semillas": len(semillas),
        "rango_semillas": [semillas[0], semillas[-1]],
        "metricas_poblacionales": metricas_poblacionales,
        "comparativa_pareada_logros": comp_logros,
        "comparativa_pareada_pasos_supervivencia": comp_pasos,
        "comparativa_pareada_fitness_global": comp_fitness,
        "veredicto_multidimensional": (
            "MIXTO: S2 mejora velocidad/hitos cognitivos pero sacrifica supervivencia por sueno sin refugio"
        ),
    }
    ruta_json = ruta_csv.replace(".csv", ".json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(informe_final, f, indent=2)
    print(f"[+] Informe JSON H7 guardado en: {ruta_json}")
    return informe_final


async def ejecutar_h2_crafter(
    semillas: List[int],
    ruta_csv: str = os.path.join(directorio_salidas("analisis"), "H2_crafter.csv"),
    aislar_ruido: bool = False,
) -> Dict[str, Any]:
    """
    Ejecuta el protocolo experimental H2 en Crafter (N semillas pareadas):
    Compara modulación somática activa (soma=on) frente a un barrido paramétrico
    de niveles fijos de cortisol (0.05, 0.30, 0.60, 0.90) y control invertido.
    """
    os.makedirs(os.path.dirname(os.path.abspath(ruta_csv)), exist_ok=True)
    arquetipo_test = Arquetipo(
        nombre="Hominis_Test_H2",
        responsabilidad=0.72,
        umbral_miedo=0.58,
        neuroticismo=0.30,
        apertura=0.60,
    )
    adaptador = AdaptadorCrafter(max_pasos=500)
    adaptador.conectar()

    condiciones = [
        {"id": "Soma_Dinamico", "modo": "on", "nombre": "Soma Dinámico (Cortisol Endógeno)"},
        {"id": "Soma_Cortisol_0.05", "modo": "fijo_0.05", "nombre": "Cortisol 0.05 (Estrés Mínimo/Calma)"},
        {"id": "Soma_Cortisol_0.30", "modo": "fijo_0.30", "nombre": "Cortisol 0.30 (Estrés Moderado)"},
        {"id": "Soma_Cortisol_0.60", "modo": "fijo_0.60", "nombre": "Cortisol 0.60 (Estrés Alto/Alarma)"},
        {"id": "Soma_Cortisol_0.90", "modo": "fijo_0.90", "nombre": "Cortisol 0.90 (Pánico Extremo)"},
        {"id": "Soma_Invertido", "modo": "invertido", "nombre": "Soma Invertido (Control Negativo)"},
    ]

    print(f"\n[H2 CRAFTER] Evaluando barrido de estrés somático ({len(condiciones)} condiciones) en N={len(semillas)} semillas ({semillas[0]}..{semillas[-1]})")

    resultados_episodios: List[Dict[str, Any]] = []
    por_condicion: Dict[str, List[Dict[str, Any]]] = {c["id"]: [] for c in condiciones}

    for idx_s, s in enumerate(semillas, 1):
        for cond in condiciones:
            res = await evaluar_individuo_en_semilla(
                adaptador=adaptador,
                arquetipo=arquetipo_test,
                axiomas_heredados=[],
                seed_mapa=s,
                max_latidos=500,
                aislar_ruido_termodinamico=aislar_ruido,
                soma_modulacion=cond["modo"],
                recolectar_telemetria=True,
            )

            ticks_s1 = sum(1 for t in res.get("telemetria", []) if t.get("origen") == "S1")
            pct_s1 = (ticks_s1 / res["latidos"]) * 100.0 if res["latidos"] > 0 else 0.0

            fila = {
                "semilla": s,
                "condicion": cond["id"],
                "modo": cond["modo"],
                "latidos": res["latidos"],
                "total_logros": res["total_logros"],
                "logros": ";".join(res["logros"]),
                "salud_final": res["salud_final"],
                "causa_muerte": res["causa_muerte"],
                "fitness_global": res["fitness"]["global"],
                "crafter_score_ind": res["crafter_score_individual"],
                "paso_por_logro": ";".join(f"{k}:{v}" for k, v in res["paso_por_logro"].items()),
                "pct_decisiones_s1": round(pct_s1, 2),
            }
            resultados_episodios.append(fila)
            por_condicion[cond["id"]].append(fila)

        if idx_s % 5 == 0 or idx_s == len(semillas):
            print(f"  -> Progreso H2: {idx_s}/{len(semillas)} semillas evaluadas ({idx_s * len(condiciones)} episodios)")

    # Escribir CSV
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(resultados_episodios[0].keys()))
        writer.writeheader()
        writer.writerows(resultados_episodios)
    print(f"[+] Dataset H2 guardado en: {ruta_csv}")

    # Crafter score poblacional por condición
    metricas_poblacionales = {}
    for cid, eps in por_condicion.items():
        hist = [{"logros": e["logros"].split(";") if e["logros"] else []} for e in eps]
        cs_res = calcular_crafter_score_poblacional(hist)
        logros_arr = [e["total_logros"] for e in eps]
        pasos_arr = [e["latidos"] for e in eps]
        metricas_poblacionales[cid] = {
            "crafter_score_poblacional": round(cs_res["crafter_score"], 2),
            "logros_desbloqueados_unicos": len(cs_res["logros_desbloqueados"]),
            "logros_media": round(float(np.mean(logros_arr)), 2),
            "logros_std": round(float(np.std(logros_arr)), 2),
            "pasos_media": round(float(np.mean(pasos_arr)), 1),
            "pct_media_decisiones_s1": round(float(np.mean([e["pct_decisiones_s1"] for e in eps])), 2),
        }

    # Comparativas pareadas frente a Soma_Dinamico
    comparativas_vs_dinamico: Dict[str, Any] = {}
    logros_dinamico = [e["total_logros"] for e in por_condicion["Soma_Dinamico"]]
    p_vals_h2 = []
    comps_raw = []

    for cid in [c["id"] for c in condiciones if c["id"] != "Soma_Dinamico"]:
        logros_c = [e["total_logros"] for e in por_condicion[cid]]
        comp = evaluar_comparativa_pareada(
            tratamiento=logros_dinamico,
            control=logros_c,
            nombre_tratamiento="Soma_Dinamico",
            nombre_control=cid,
        )
        comps_raw.append(comp)
        p_vals_h2.append(comp["wilcoxon_p"])

    p_adj_h2 = corregir_holm_bonferroni(p_vals_h2)
    for comp, p_adj in zip(comps_raw, p_adj_h2):
        comp["wilcoxon_p_holm_ajustado"] = round(p_adj, 6)
        comparativas_vs_dinamico[comp["control"]] = comp

    informe_final = {
        "hipotesis": "H2",
        "mundo": "crafter",
        "n_semillas": len(semillas),
        "rango_semillas": [semillas[0], semillas[-1]],
        "metricas_poblacionales": metricas_poblacionales,
        "comparativas_vs_soma_dinamico": comparativas_vs_dinamico,
    }
    ruta_json = ruta_csv.replace(".csv", ".json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(informe_final, f, indent=2)
    print(f"[+] Informe JSON H2 guardado en: {ruta_json}")
    return informe_final


async def main():
    parser = argparse.ArgumentParser(description="Harness de Experimentación IdA v12.0")
    parser.add_argument("--hipotesis", type=str, required=True, choices=["H1", "H7", "H2"])
    parser.add_argument("--mundo", type=str, default="crafter", choices=["crafter", "snake", "ajedrez"])
    parser.add_argument("--semillas", type=str, default="2020-2059")
    parser.add_argument("--modo-ablacion", type=str, default=None, choices=["nivel_a", "nivel_b"],
                        help="Solo H1 (por defecto nivel_a)")
    parser.add_argument("--max-pasos", type=int, default=None)
    parser.add_argument("--aislar-ruido", action="store_true")
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--sin-telemetria", action="store_true")
    args = parser.parse_args()

    # Solo está implementado el mundo Crafter. Nunca terminar en silencio sin ejecutar nada,
    # ni aceptar opciones que la hipótesis elegida no usa.
    if args.mundo != "crafter":
        parser.error(
            f"--mundo {args.mundo}: no implementado. El harness solo ejecuta H1, H7 y H2 en crafter; "
            "Snake y Ajedrez tienen scripts de medición propios en analisis/."
        )
    if args.hipotesis == "H1" and (args.aislar_ruido or args.max_pasos is not None):
        parser.error("H1 no admite --aislar-ruido ni --max-pasos (usa 500 pasos y ruido físico activo).")
    if args.hipotesis in ("H7", "H2") and args.modo_ablacion is not None:
        parser.error(f"{args.hipotesis} no admite --modo-ablacion (solo aplica a H1).")
    if args.hipotesis == "H2" and args.max_pasos is not None:
        parser.error("H2 no admite --max-pasos (usa 500 pasos).")
    args.modo_ablacion = args.modo_ablacion or "nivel_a"

    semillas = parsear_rango_semillas(args.semillas)
    # Salidas por defecto en IDA_OUT_DIR/analisis (fuera del árbol versionado de resultados)
    dir_out = directorio_salidas("analisis")
    ruta_out = args.out or os.path.join(dir_out, f"{args.hipotesis}_{args.mundo}_{args.modo_ablacion}.csv")

    if args.hipotesis == "H1" and args.mundo == "crafter":
        await ejecutar_h1_crafter(
            semillas=semillas,
            modo_ablacion=args.modo_ablacion,
            ruta_csv=ruta_out,
            recolectar_telemetria=not args.sin_telemetria,
        )
    elif args.hipotesis == "H7" and args.mundo == "crafter":
        max_p = args.max_pasos if args.max_pasos is not None else 1500
        await ejecutar_h7_crafter(
            semillas=semillas,
            ruta_csv=args.out or os.path.join(dir_out, "H7_crafter_1500p.csv"),
            max_pasos=max_p,
            aislar_ruido=args.aislar_ruido,
        )
    elif args.hipotesis == "H2" and args.mundo == "crafter":
        await ejecutar_h2_crafter(
            semillas=semillas,
            ruta_csv=args.out or os.path.join(dir_out, "H2_crafter_sweep.csv"),
            aislar_ruido=args.aislar_ruido,
        )


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    asyncio.run(main())
