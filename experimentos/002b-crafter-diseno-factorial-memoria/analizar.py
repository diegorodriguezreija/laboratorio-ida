"""
Script de análisis pre-registrado para el Experimento 002b:
Diseño Factorial 2x2 — Desacoplamiento de Arquitectura Bioinspirada vs. Memoria Espacial en Crafter 2D.

Carga 'episodios_pareados.csv' y evalúa estrictamente las hipótesis pre-registradas en PREGUNTA.md:
- Contraste Primario: IdA Memoria (B4) vs Voraz Memoria (B3) en logros/episodio.
- TOST (Two One-Sided Tests) con margen de equivalencia +/-1.0 logro.
- Contrastes Secundarios: Efecto Arquitectura, Efecto Memoria, Interacción (con ajuste Holm-Bonferroni).
- Crafter Score Poblacional con IC Bootstrap al 95%.
- Clasificación determinista del escenario experimental (Casos A, B, C, D, E, F, G).
"""

import argparse
import csv
import json
import math
import os
import sys
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy import stats

RUTA_EXP = os.path.dirname(os.path.abspath(__file__))
RUTA_LAB = os.path.abspath(os.path.join(RUTA_EXP, "..", ".."))
if RUTA_LAB not in sys.path:
    sys.path.insert(0, RUTA_LAB)
if os.path.join(RUTA_LAB, "base") not in sys.path:
    sys.path.insert(0, os.path.join(RUTA_LAB, "base"))

from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import (
    ACHIEVEMENTS_22,
    calcular_crafter_score_poblacional,
)
from nivel_3_componentes.rutas_salida import directorio_salidas

RUTA_SALIDAS = directorio_salidas("002b-crafter-diseno-factorial-memoria")
CSV_DEFAULT = os.path.join(RUTA_SALIDAS, "episodios_pareados.csv")
JSON_DEFAULT = os.path.join(RUTA_SALIDAS, "resumen_estadistico.json")


def bootstrap_ci_diferencia(
    diffs: List[float], n_boot: int = 10000, ci: float = 0.95, seed: int = 42
) -> Tuple[float, float, float]:
    """Calcula la media puntual y el intervalo de confianza percentil bootstrap al 95%."""
    rng = np.random.default_rng(seed)
    arr = np.array(diffs, dtype=float)
    n = len(arr)
    media_puntual = float(np.mean(arr))
    indices = rng.integers(0, n, size=(n_boot, n))
    muestras_medias = np.mean(arr[indices], axis=1)
    alfa = (1.0 - ci) / 2.0
    lim_inf = float(np.percentile(muestras_medias, alfa * 100))
    lim_sup = float(np.percentile(muestras_medias, (1.0 - alfa) * 100))
    return media_puntual, lim_inf, lim_sup


def tost_equivalencia(
    diffs: List[float], margen: float = 1.0, alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Two One-Sided Tests (TOST) para evaluar equivalencia estadística dentro de [-margen, +margen].
    H01: mu <= -margen vs H11: mu > -margen
    H02: mu >= +margen vs H12: mu < +margen
    Rechaza ambas si t1 > t_crit y t2 < -t_crit.
    """
    arr = np.array(diffs, dtype=float)
    n = len(arr)
    m = float(np.mean(arr))
    s = float(np.std(arr, ddof=1))
    se = s / math.sqrt(n) if n > 1 else 0.0

    if se == 0.0:
        equiv = (-margen <= m <= margen)
        return {
            "margen": margen,
            "equivalente": equiv,
            "p_tost": 0.0 if equiv else 1.0,
            "t1": 0.0,
            "t2": 0.0,
            "p1": 0.0 if m > -margen else 1.0,
            "p2": 0.0 if m < margen else 1.0,
        }

    # Test inferior: H0: mu <= -margen
    t1 = (m - (-margen)) / se
    p1 = 1.0 - float(stats.t.cdf(t1, df=n - 1))

    # Test superior: H0: mu >= +margen
    t2 = (m - margen) / se
    p2 = float(stats.t.cdf(t2, df=n - 1))

    p_tost = max(p1, p2)
    equivalente = bool(p_tost < alpha)

    return {
        "margen": margen,
        "media": m,
        "se": se,
        "t1": t1,
        "p1": p1,
        "t2": t2,
        "p2": p2,
        "p_tost": p_tost,
        "equivalente": equivalente,
    }


def calcular_crafter_score_bootstrap_diff(
    logros_a: List[List[str]],
    logros_b: List[List[str]],
    n_boot: int = 2000,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Bootstrap pareado de la diferencia de Crafter Score poblacional (A - B)."""
    rng = np.random.default_rng(seed)
    n = len(logros_a)

    score_a_orig = calcular_crafter_score_poblacional(logros_a)["crafter_score"]
    score_b_orig = calcular_crafter_score_poblacional(logros_b)["crafter_score"]
    diff_orig = score_a_orig - score_b_orig

    diffs_boot = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        sub_a = [logros_a[i] for i in idx]
        sub_b = [logros_b[i] for i in idx]
        sa = calcular_crafter_score_poblacional(sub_a)["crafter_score"]
        sb = calcular_crafter_score_poblacional(sub_b)["crafter_score"]
        diffs_boot.append(sa - sb)

    lim_inf = float(np.percentile(diffs_boot, 2.5))
    lim_sup = float(np.percentile(diffs_boot, 97.5))
    return float(diff_orig), lim_inf, lim_sup


def analizar_datos(ruta_csv: str) -> Dict[str, Any]:
    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(f"No se encontró el archivo de datos: {ruta_csv}")

    filas = []
    with open(ruta_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            filas.append(r)

    # Agrupar por semilla y brazo
    # Brazos esperados:
    # 1: Voraz_Reactivo (Sin Memoria)
    # 2: IdA_SinMemoria (Sin Memoria)
    # 3: Voraz_Memoria (Con Memoria)
    # 4: IdA_Canonica (Con Memoria)
    datos_por_semilla: Dict[int, Dict[str, Dict[str, Any]]] = {}
    for r in filas:
        semilla = int(r["semilla"])
        brazo = r["brazo"]
        logros_lista = [x.strip() for x in r["desglose_logros"].split(";") if x.strip()]
        info = {
            "num_logros": int(r["logros"]),
            "crafter_score_ind": float(r["crafter_score_individual"]),
            "pasos": int(r["duracion_pasos"]),
            "retornos": int(r.get("retornos_fuera_de_vista", 0)),
            "desglose": logros_lista,
        }
        if semilla not in datos_por_semilla:
            datos_por_semilla[semilla] = {}
        datos_por_semilla[semilla][brazo] = info

    semillas = sorted(list(datos_por_semilla.keys()))
    n_semillas = len(semillas)

    # Vectores por brazo
    b1_logros, b2_logros, b3_logros, b4_logros = [], [], [], []
    b1_desglose, b2_desglose, b3_desglose, b4_desglose = [], [], [], []
    b1_retornos, b2_retornos, b3_retornos, b4_retornos = [], [], [], []

    for s in semillas:
        d = datos_por_semilla[s]
        b1_logros.append(d["Voraz_Reactivo"]["num_logros"])
        b1_desglose.append(d["Voraz_Reactivo"]["desglose"])
        b1_retornos.append(d["Voraz_Reactivo"]["retornos"])

        b2_logros.append(d["IdA_SinMemoria"]["num_logros"])
        b2_desglose.append(d["IdA_SinMemoria"]["desglose"])
        b2_retornos.append(d["IdA_SinMemoria"]["retornos"])

        b3_logros.append(d["Voraz_Memoria"]["num_logros"])
        b3_desglose.append(d["Voraz_Memoria"]["desglose"])
        b3_retornos.append(d["Voraz_Memoria"]["retornos"])

        b4_logros.append(d["IdA_Canonica"]["num_logros"])
        b4_desglose.append(d["IdA_Canonica"]["desglose"])
        b4_retornos.append(d["IdA_Canonica"]["retornos"])

    # 1. CONTRASTE PRIMARIO: H1 (IdA_Canonica vs Voraz_Memoria)
    diff_primario = [b4 - b3 for b4, b3 in zip(b4_logros, b3_logros)]
    m_prim, inf_prim, sup_prim = bootstrap_ci_diferencia(diff_primario)
    
    # Wilcoxon signed-rank
    try:
        w_res = stats.wilcoxon(diff_primario, alternative="two-sided")
        p_prim_wilcoxon = float(w_res.pvalue)
        stat_prim_wilcoxon = float(w_res.statistic)
    except Exception:
        p_prim_wilcoxon = 1.0
        stat_prim_wilcoxon = 0.0

    # TOST equivalencia contra +/- 1.0 logro
    res_tost = tost_equivalencia(diff_primario, margen=1.0, alpha=0.05)

    # 2. CONTRASTES SECUNDARIOS FACTORIALES (2x2)
    # Efecto Principal de Arquitectura: 0.5 * ((B4 - B3) + (B2 - B1))
    diff_arq = [0.5 * ((b4 - b3) + (b2 - b1)) for b1, b2, b3, b4 in zip(b1_logros, b2_logros, b3_logros, b4_logros)]
    m_arq, inf_arq, sup_arq = bootstrap_ci_diferencia(diff_arq)
    try:
        p_arq = float(stats.wilcoxon(diff_arq, alternative="two-sided").pvalue)
    except Exception:
        p_arq = 1.0

    # Efecto Principal de Memoria: 0.5 * ((B4 - B2) + (B3 - B1))
    diff_mem = [0.5 * ((b4 - b2) + (b3 - b1)) for b1, b2, b3, b4 in zip(b1_logros, b2_logros, b3_logros, b4_logros)]
    m_mem, inf_mem, sup_mem = bootstrap_ci_diferencia(diff_mem)
    try:
        p_mem = float(stats.wilcoxon(diff_mem, alternative="two-sided").pvalue)
    except Exception:
        p_mem = 1.0

    # Interacción Arquitectura x Memoria: (B4 - B3) - (B2 - B1)
    diff_int = [((b4 - b3) - (b2 - b1)) for b1, b2, b3, b4 in zip(b1_logros, b2_logros, b3_logros, b4_logros)]
    m_int, inf_int, sup_int = bootstrap_ci_diferencia(diff_int)
    try:
        p_int = float(stats.wilcoxon(diff_int, alternative="two-sided").pvalue)
    except Exception:
        p_int = 1.0

    # Control de multiplicidad Holm-Bonferroni sobre los 3 contrastes secundarios
    contrastes_sec = [
        ("Efecto_Arquitectura", p_arq, m_arq, inf_arq, sup_arq),
        ("Efecto_Memoria", p_mem, m_mem, inf_mem, sup_mem),
        ("Interaccion_Arq_Mem", p_int, m_int, inf_int, sup_int),
    ]
    contrastes_sec.sort(key=lambda x: x[1])

    p_holm_dict = {}
    m = len(contrastes_sec)
    for rank, (nombre, p_val, _, _, _) in enumerate(contrastes_sec):
        alpha_ajustado = 0.05 / (m - rank)
        p_ajustado = min(1.0, p_val * (m - rank))
        sig = bool(p_val <= alpha_ajustado)
        p_holm_dict[nombre] = {
            "p_crudo": p_val,
            "p_holm": p_ajustado,
            "alpha_k": alpha_ajustado,
            "significativo": sig,
        }

    # 3. CRAFTER SCORE POBLACIONAL
    cs_b1 = calcular_crafter_score_poblacional(b1_desglose)
    cs_b2 = calcular_crafter_score_poblacional(b2_desglose)
    cs_b3 = calcular_crafter_score_poblacional(b3_desglose)
    cs_b4 = calcular_crafter_score_poblacional(b4_desglose)

    cs_diff_puntual, cs_inf, cs_sup = calcular_crafter_score_bootstrap_diff(b4_desglose, b3_desglose)

    # 4. DETERMINACIÓN DETERMINISTA DEL ESCENARIO EXPERIMENTAL
    # Casos A - G según PREGUNTA.md
    caso_detectado = "G"
    motivo_caso = ""

    # Condición Caso E: Avería de la ablación (B2 < B1 - 1.0)
    diff_b2_b1 = [b2 - b1 for b2, b1 in zip(b2_logros, b1_logros)]
    m_b2_b1, inf_b2_b1, _ = bootstrap_ci_diferencia(diff_b2_b1)
    if inf_b2_b1 < -1.0 and p_holm_dict["Efecto_Arquitectura"]["significativo"]:
        caso_detectado = "E"
        motivo_caso = f"Avería de la ablación: IdA sin memoria rinde significativamente peor que Voraz sin memoria ({m_b2_b1:.2f} logros)."
    
    # Condición Caso D: Interacción sinérgica
    elif inf_int > 0.0 and p_holm_dict["Interaccion_Arq_Mem"]["significativo"]:
        caso_detectado = "D"
        motivo_caso = f"Interacción sinérgica confirmada: IdA aprovecha la memoria con mayor eficacia que el voraz (Int = {m_int:.2f}, IC [{inf_int:.2f}, {sup_int:.2f}])."

    # Condición Caso B: Excedente Bioinspirado Demostrado
    elif inf_prim > 1.0 and p_prim_wilcoxon < 0.05:
        caso_detectado = "B"
        motivo_caso = f"Excedente Bioinspirado demostrado: Límite inferior IC 95% = {inf_prim:.2f} > +1.0 logro (p = {p_prim_wilcoxon:.4e})."

    # Condición Caso A: Solo Memoria (Equivalencia Demostrada)
    elif res_tost["equivalente"] and p_holm_dict["Efecto_Memoria"]["significativo"] and m_mem > 0:
        caso_detectado = "A"
        motivo_caso = f"Solo Memoria (Equivalencia Demostrada): IC 95% [{inf_prim:.2f}, {sup_prim:.2f}] enteramente contenido en [-1.0, +1.0] (p_TOST = {res_tost['p_tost']:.4e}) y memoria significativa (p_Holm = {p_holm_dict['Efecto_Memoria']['p_holm']:.4e})."

    # Condición Caso C: Diferencia Pequeña / Sub-clínica
    elif p_prim_wilcoxon < 0.05 and m_prim > 0 and (inf_prim <= 1.0 or sup_prim >= 1.0):
        caso_detectado = "C"
        motivo_caso = f"Diferencia pequeña/sub-clínica: Ventaja estadísticamente significativa (p = {p_prim_wilcoxon:.4e}) pero IC [{inf_prim:.2f}, {sup_prim:.2f}] no supera holgadamente el margen de +1.0 logro."

    # Condición Caso F: Ineficacia de la Memoria
    elif res_tost["equivalente"] and not p_holm_dict["Efecto_Memoria"]["significativo"]:
        caso_detectado = "F"
        motivo_caso = f"Ineficacia de la Memoria: Equivalencia en primario pero efecto memoria no significativo (p_Holm = {p_holm_dict['Efecto_Memoria']['p_holm']:.4e})."

    else:
        caso_detectado = "G"
        motivo_caso = f"No concluyente: p = {p_prim_wilcoxon:.4e}, IC [{inf_prim:.2f}, {sup_prim:.2f}] desborda [-1.0, +1.0]."

    resumen = {
        "n_semillas": n_semillas,
        "semillas": [min(semillas), max(semillas)],
        "brazos": {
            "B1_Voraz_Reactivo": {
                "media_logros": float(np.mean(b1_logros)),
                "mediana_logros": float(np.median(b1_logros)),
                "std_logros": float(np.std(b1_logros, ddof=1)),
                "crafter_score": cs_b1["crafter_score"],
                "retornos_fuera_de_vista_total": sum(b1_retornos),
            },
            "B2_IdA_SinMemoria": {
                "media_logros": float(np.mean(b2_logros)),
                "mediana_logros": float(np.median(b2_logros)),
                "std_logros": float(np.std(b2_logros, ddof=1)),
                "crafter_score": cs_b2["crafter_score"],
                "retornos_fuera_de_vista_total": sum(b2_retornos),
            },
            "B3_Voraz_Memoria": {
                "media_logros": float(np.mean(b3_logros)),
                "mediana_logros": float(np.median(b3_logros)),
                "std_logros": float(np.std(b3_logros, ddof=1)),
                "crafter_score": cs_b3["crafter_score"],
                "retornos_fuera_de_vista_total": sum(b3_retornos),
            },
            "B4_IdA_Canonica": {
                "media_logros": float(np.mean(b4_logros)),
                "mediana_logros": float(np.median(b4_logros)),
                "std_logros": float(np.std(b4_logros, ddof=1)),
                "crafter_score": cs_b4["crafter_score"],
                "retornos_fuera_de_vista_total": sum(b4_retornos),
            },
        },
        "contraste_primario": {
            "comparativa": "IdA_Canonica (B4) - Voraz_Memoria (B3)",
            "media_diff": m_prim,
            "ic_95": [inf_prim, sup_prim],
            "wilcoxon_stat": stat_prim_wilcoxon,
            "wilcoxon_p": p_prim_wilcoxon,
            "tost_equivalencia": res_tost,
            "crafter_score_diff": {
                "puntual_pp": cs_diff_puntual,
                "ic_95_pp": [cs_inf, cs_sup],
            },
        },
        "contrastes_secundarios_factoriales": {
            "efecto_arquitectura": {
                "media_diff": m_arq,
                "ic_95": [inf_arq, sup_arq],
                "stats_holm": p_holm_dict["Efecto_Arquitectura"],
            },
            "efecto_memoria": {
                "media_diff": m_mem,
                "ic_95": [inf_mem, sup_mem],
                "stats_holm": p_holm_dict["Efecto_Memoria"],
            },
            "interaccion": {
                "media_diff": m_int,
                "ic_95": [inf_int, sup_int],
                "stats_holm": p_holm_dict["Interaccion_Arq_Mem"],
            },
        },
        "veredicto_escenario": {
            "caso": caso_detectado,
            "motivo": motivo_caso,
        },
    }

    return resumen


def main():
    parser = argparse.ArgumentParser(description="Análisis estadístico pre-registrado Exp 002b")
    parser.add_argument("--csv", default=CSV_DEFAULT, help="Ruta al archivo episodios_pareados.csv")
    parser.add_argument("--json", default=JSON_DEFAULT, help="Ruta de guardado para resumen_estadistico.json")
    args = parser.parse_args()

    resumen = analizar_datos(args.csv)

    os.makedirs(os.path.dirname(args.json), exist_ok=True)
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print("ANÁLISIS ESTADÍSTICO FORMAL — EXPERIMENTO 002b")
    print(f"Semillas evaluadas: {resumen['semillas'][0]} a {resumen['semillas'][1]} (N = {resumen['n_semillas']})")
    print("=" * 80)
    b = resumen["brazos"]
    print(f"Brazo 1 (Voraz Reactivo)  : Media {b['B1_Voraz_Reactivo']['media_logros']:.2f} logros | Crafter Score {b['B1_Voraz_Reactivo']['crafter_score']:.2f}%")
    print(f"Brazo 2 (IdA Sin Memoria)  : Media {b['B2_IdA_SinMemoria']['media_logros']:.2f} logros | Crafter Score {b['B2_IdA_SinMemoria']['crafter_score']:.2f}%")
    print(f"Brazo 3 (Voraz con Memoria): Media {b['B3_Voraz_Memoria']['media_logros']:.2f} logros | Crafter Score {b['B3_Voraz_Memoria']['crafter_score']:.2f}% (Retornos: {b['B3_Voraz_Memoria']['retornos_fuera_de_vista_total']})")
    print(f"Brazo 4 (IdA Canónica)     : Media {b['B4_IdA_Canonica']['media_logros']:.2f} logros | Crafter Score {b['B4_IdA_Canonica']['crafter_score']:.2f}%")
    print("-" * 80)
    cp = resumen["contraste_primario"]
    print(f"CONTRASTE PRIMARIO (B4 vs B3):")
    print(f"  Diferencia Media Logros : {cp['media_diff']:+.2f} logros (IC 95% [{cp['ic_95'][0]:+.2f}, {cp['ic_95'][1]:+.2f}])")
    print(f"  Wilcoxon signed-rank    : p = {cp['wilcoxon_p']:.4e}")
    print(f"  TOST Equivalencia (+/-1): p = {cp['tost_equivalencia']['p_tost']:.4e} -> Equivalente: {cp['tost_equivalencia']['equivalente']}")
    print(f"  Crafter Score Diff      : {cp['crafter_score_diff']['puntual_pp']:+.2f} pp (IC 95% [{cp['crafter_score_diff']['ic_95_pp'][0]:+.2f}, {cp['crafter_score_diff']['ic_95_pp'][1]:+.2f}] pp)")
    print("-" * 80)
    cs = resumen["contrastes_secundarios_factoriales"]
    print("CONTRASTES SECUNDARIOS FACTORIALES (Holm-Bonferroni):")
    print(f"  Efecto Arquitectura : {cs['efecto_arquitectura']['media_diff']:+.2f} (IC [{cs['efecto_arquitectura']['ic_95'][0]:+.2f}, {cs['efecto_arquitectura']['ic_95'][1]:+.2f}]) | p_Holm = {cs['efecto_arquitectura']['stats_holm']['p_holm']:.4e} (Sig: {cs['efecto_arquitectura']['stats_holm']['significativo']})")
    print(f"  Efecto Memoria      : {cs['efecto_memoria']['media_diff']:+.2f} (IC [{cs['efecto_memoria']['ic_95'][0]:+.2f}, {cs['efecto_memoria']['ic_95'][1]:+.2f}]) | p_Holm = {cs['efecto_memoria']['stats_holm']['p_holm']:.4e} (Sig: {cs['efecto_memoria']['stats_holm']['significativo']})")
    print(f"  Interacción Arq x Mem: {cs['interaccion']['media_diff']:+.2f} (IC [{cs['interaccion']['ic_95'][0]:+.2f}, {cs['interaccion']['ic_95'][1]:+.2f}]) | p_Holm = {cs['interaccion']['stats_holm']['p_holm']:.4e} (Sig: {cs['interaccion']['stats_holm']['significativo']})")
    print("=" * 80)
    v = resumen["veredicto_escenario"]
    print(f"VEREDICTO FORMAL: CASO {v['caso']}")
    print(f"Motivo: {v['motivo']}")
    print(f"Guardado resumen estadístico en: {args.json}")


if __name__ == "__main__":
    main()
