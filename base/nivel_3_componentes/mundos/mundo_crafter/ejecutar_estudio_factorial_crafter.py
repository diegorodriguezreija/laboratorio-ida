"""
Estudio Factorial y de Controles Rigurosos de Heredabilidad en Crafter 2D (IdA v12.0)
===================================================================================
Protocolo Experimental:
  1. Lote de 20 semillas estrictamente nuevas y no vistas: seeds 2000..2019.
  2. Diseño Factorial 2x2:
     - Condición 1 (Récord Completo): Arquetipo Récord (G12) + 33 Axiomas Weismann Récord
     - Condición 2 (Solo Arquetipo):  Arquetipo Récord (G12) + 0 Axiomas (Vacío)
     - Condición 3 (Solo Axiomas):    Arquetipo Fundador (G1) + 33 Axiomas Weismann Récord
     - Condición 4 (Control Vacío):   Arquetipo Fundador (G1) + 0 Axiomas (Vacío)
  3. Controles Adicionales:
     - Condición 5 (Placebo / Sham):  Arquetipo Récord (G12) + 33 Axiomas Placebo (irrelevantes de otros mundos)
     - Condición 6 (Linaje Mediano):  Arquetipo Mediano (G8) + 23 Axiomas G8 (control de maldición del ganador)
  4. Análisis Estadístico:
     - Test de Wilcoxon para diferencias pareadas por semilla
     - Test de Signos (binomial bilateral)
     - Intervalos de confianza Bootstrap al 95% (10.000 remuestreos)
     - Tamaños de efecto: Cliff's delta y correlación biserial por rangos pareados
     - Crafter Score Poblacional Canónico (Hafner, 2021)
  5. Salida de datos en CSV crudo y JSON estructurado.
"""

import argparse
import asyncio
import csv
import json
import math
import os
import sys
from typing import Any, Dict, List, Tuple
import numpy as np
from scipy import stats

# Añadir raíz al sys.path
RUTA_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_RAIZ = os.path.abspath(os.path.join(RUTA_DIR, "..", "..", ".."))
if RUTA_RAIZ not in sys.path:
    sys.path.insert(0, RUTA_RAIZ)

from nivel_1_core.contratos import Arquetipo, Pieza
from nivel_1_core.vocabulario import V_Relacion
from nivel_3_componentes.mundos.mundo_crafter.adaptador_crafter import AdaptadorCrafter
from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import (
    ACHIEVEMENTS_22,
    calcular_crafter_score_poblacional,
    cargar_linaje_ancestral,
    evaluar_individuo_en_semilla,
)
from nivel_3_componentes.rutas_salida import directorio_salidas, asegurar_directorio_de

# Salidas fuera de la carpeta de código (IDA_OUT_DIR o ./salidas/crafter/factorial)
RUTA_DIR_SALIDA = directorio_salidas("crafter", "factorial")
# Linaje de entrada publicado (D10). El estudio usa su generación 12 como "arquetipo seleccionado".
RUTA_LINAJE_EJEMPLO = os.path.join(RUTA_RAIZ, "analisis", "linajes_ejemplo", "linaje_evolutivo_crafter.json")


def generar_axiomas_placebo(n: int = 33) -> List[Dict[str, Any]]:
    """
    Genera n axiomas sham/placebo estructurados válidamente como Pieza,
    pero con contenido semántico totalmente desconectado de Crafter (términos de ajedrez, snake, genéricos).
    """
    placebos = []
    # 2 traumas placebo
    placebos.append(
        Pieza(
            id="Trauma_Colision_Muro_Perimetral_Snake",
            tipo_componente="Aversion_Traumatica",
            arousal=0.95,
            trust=1.0,
            product={
                "sujeto": "IdA_Snake",
                "relacion": str(V_Relacion.ES_LETAL),
                "tipo_trauma": "Colision en muro perimetral",
                "advertencia": "Evitar bordes del tablero DOM",
            },
            demostrado_de_novo=True,
        ).to_dict()
    )
    placebos.append(
        Pieza(
            id="Trauma_Jaque_Mate_Pastor_Ajedrez",
            tipo_componente="Aversion_Traumatica",
            arousal=0.95,
            trust=1.0,
            product={
                "sujeto": "IdA_Ajedrez",
                "relacion": str(V_Relacion.ES_LETAL),
                "tipo_trauma": "Mate del pastor en f7",
                "advertencia": "Defender diagonal h5-f7",
            },
            demostrado_de_novo=True,
        ).to_dict()
    )

    # 16 patrones de éxito placebo (nombres que no existen en los 22 logros de Crafter)
    logros_falsos = [
        "enroque_corto", "capturar_alfil", "comer_manzana_web", "orbitar_cola",
        "salvar_rey", "clavar_caballo", "desentrampe_perimetral", "crear_brote_archivo",
        "purga_cortisol", "apertura_siciliana", "defensa_francesa", "ataque_flanco_dama",
        "jaque_descubierto", "sacrificio_posicional", "esperar_tiempo_rem", "coronar_peon"
    ]
    for logro_falso in logros_falsos:
        placebos.append(
            Pieza(
                id=f"Axioma_Logro_{logro_falso}",
                tipo_componente="Patron_Exito_Estrategico",
                arousal=0.85,
                trust=0.92,
                product={
                    "sujeto": "IdA_Generic",
                    "relacion": str(V_Relacion.ES_SEGURO),
                    "logro_obtenido": logro_falso,
                    "eficacia": "Patron no relevante para Crafter",
                },
                demostrado_de_novo=True,
            ).to_dict()
        )

    # Resto hasta n proposiciones verdad placebo
    idx = 1
    while len(placebos) < n:
        placebos.append(
            Pieza(
                id=f"Axioma_Placebo_Verdad_{idx}",
                tipo_componente="Proposicion_VERDAD",
                arousal=0.88,
                trust=0.90,
                product={
                    "consecuente": str(V_Relacion.ES_SEGURO),
                    "dominio": "desconectado",
                    "iteracion": idx,
                },
                demostrado_de_novo=True,
            ).to_dict()
        )
        idx += 1

    return placebos[:n]


def bootstrap_ci_diferencia(
    a: np.ndarray, b: np.ndarray, num_boot: int = 10000, alpha: float = 0.05
) -> Tuple[float, float, float]:
    """Calcula la media de la diferencia y el IC del 95% bootstrap pareado."""
    dif = a - b
    mean_real = float(np.mean(dif))
    rng = np.random.default_rng(seed=42)
    boot_means = np.zeros(num_boot)
    n = len(dif)
    for i in range(num_boot):
        indices = rng.integers(0, n, size=n)
        boot_means[i] = np.mean(dif[indices])
    low = float(np.percentile(boot_means, 100.0 * (alpha / 2.0)))
    high = float(np.percentile(boot_means, 100.0 * (1.0 - alpha / 2.0)))
    return round(mean_real, 3), round(low, 3), round(high, 3)


def calcular_cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    """Calcula el tamaño del efecto no paramétrico Cliff's delta."""
    n_a = len(a)
    n_b = len(b)
    dominance = 0
    for x in a:
        for y in b:
            if x > y:
                dominance += 1
            elif x < y:
                dominance -= 1
    return round(dominance / (n_a * n_b), 3)


async def main(ruta_linaje: str = RUTA_LINAJE_EJEMPLO, semillas: List[int] = None):
    print("=" * 95)
    print("ESTUDIO FACTORIAL 2x2 Y CONTROLES DE HEREDABILIDAD EN CRAFTER 2D (IdA v12.0)")
    print("Evaluación pareada por semilla (rango indicado más abajo)")
    print("=" * 95)

    axiomas_acumulados, historial = cargar_linaje_ancestral(ruta_linaje)
    if not historial:
        raise SystemExit(f"[ERROR] No se encontró linaje en {ruta_linaje}")

    # 1. Definición de Arquetipos y Acervos
    # Especímen Récord (G12)
    rec_info = historial[11]  # G12
    rasgos_g12 = rec_info["arquetipo_rasgos"]
    arq_record_base = Arquetipo(
        nombre="Hominis_G12_Record",
        id_individuo="Record_G12",
        linaje="Linaje_Hominis_Crafter",
        generacion=12,
        apertura=rasgos_g12["apertura"],
        responsabilidad=rasgos_g12["responsabilidad"],
        neuroticismo=rasgos_g12["neuroticismo"],
        umbral_miedo=rasgos_g12["umbral_miedo"],
    )

    # Especímen Fundador / Ingenuo (G1)
    fnd_info = historial[0]  # G1
    rasgos_g1 = fnd_info["arquetipo_rasgos"]
    arq_founder_base = Arquetipo(
        nombre="Fundador_Ingenuo_G1",
        id_individuo="Founder_G1",
        linaje="Linaje_Founder",
        generacion=1,
        apertura=rasgos_g1["apertura"],
        responsabilidad=rasgos_g1["responsabilidad"],
        neuroticismo=rasgos_g1["neuroticismo"],
        umbral_miedo=rasgos_g1["umbral_miedo"],
    )

    # Especímen Mediano (G8)
    med_info = historial[7]  # G8
    rasgos_g8 = med_info["arquetipo_rasgos"]
    arq_mediano_base = Arquetipo(
        nombre="Hominis_G8_Mediano",
        id_individuo="Mediano_G8",
        linaje="Linaje_Mediano",
        generacion=8,
        apertura=rasgos_g8["apertura"],
        responsabilidad=rasgos_g8["responsabilidad"],
        neuroticismo=rasgos_g8["neuroticismo"],
        umbral_miedo=rasgos_g8["umbral_miedo"],
    )

    axiomas_crafter_record = axiomas_acumulados  # 33 axiomas
    axiomas_crafter_g8 = axiomas_acumulados[:23]  # 23 axiomas hasta G8
    axiomas_placebo_33 = generar_axiomas_placebo(33)

    # Configuración de condiciones experimentales
    condiciones_def = [
        {
            "id": "C1_Record_Completo",
            "nombre": "C1: Arq Récord + Axiomas Récord (2x2 Récord)",
            "arquetipo_base": arq_record_base,
            "axiomas": axiomas_crafter_record,
            "tipo_control": "Experimental Récord",
        },
        {
            "id": "C2_Solo_Arquetipo",
            "nombre": "C2: Arq Récord + Axiomas Vacíos (Ablación Axiomas)",
            "arquetipo_base": arq_record_base,
            "axiomas": [],
            "tipo_control": "Factorial Arquetipo Solo",
        },
        {
            "id": "C3_Solo_Axiomas",
            "nombre": "C3: Arq Fundador + Axiomas Récord (Ablación Arquetipo)",
            "arquetipo_base": arq_founder_base,
            "axiomas": axiomas_crafter_record,
            "tipo_control": "Factorial Axiomas Solo",
        },
        {
            "id": "C4_Control_Vacio",
            "nombre": "C4: Arq Fundador + Axiomas Vacíos (Control Negativo Base)",
            "arquetipo_base": arq_founder_base,
            "axiomas": [],
            "tipo_control": "Control Negativo Base",
        },
        {
            "id": "C5_Placebo_Sham",
            "nombre": "C5: Arq Récord + 33 Axiomas Placebo (Control Sham)",
            "arquetipo_base": arq_record_base,
            "axiomas": axiomas_placebo_33,
            "tipo_control": "Control Placebo Sham",
        },
        {
            "id": "C6_Linaje_Mediano",
            "nombre": "C6: Arq Mediano G8 + 23 Axiomas G8 (Control Mediano)",
            "arquetipo_base": arq_mediano_base,
            "axiomas": axiomas_crafter_g8,
            "tipo_control": "Control Linaje Mediano",
        },
    ]

    semillas = semillas or [2000 + i for i in range(20)]
    max_latidos = 500

    adaptador = AdaptadorCrafter(seed=semillas[0], max_pasos=max_latidos)
    adaptador.conectar()

    filas_csv = []
    resultados_por_condicion: Dict[str, List[Dict[str, Any]]] = {
        c["id"]: [] for c in condiciones_def
    }

    total_corridas = len(condiciones_def) * len(semillas)
    corrida_idx = 0

    print(f"\nIniciando ejecución de {total_corridas} simulaciones...")
    print(f"Semillas: {semillas[0]}..{semillas[-1]} (N={len(semillas)}) | Condiciones: {len(condiciones_def)}\n")

    for s_map in semillas:
        rng_desc = np.random.default_rng(seed=s_map * 17)

        for cond in condiciones_def:
            corrida_idx += 1
            arq_base = cond["arquetipo_base"]
            # Pequeña variación genética natural de descendiente
            arq_desc = Arquetipo(
                nombre=f"{cond['id']}_S{s_map}",
                id_individuo=f"{cond['id']}_S{s_map}",
                id_padre=arq_base.id_individuo,
                linaje=arq_base.linaje,
                generacion=arq_base.generacion + 1,
                apertura=round(float(np.clip(arq_base.apertura + rng_desc.normal(0, 0.015), 0.35, 0.95)), 2),
                responsabilidad=round(float(np.clip(arq_base.responsabilidad + rng_desc.normal(0, 0.015), 0.35, 0.95)), 2),
                neuroticismo=round(float(np.clip(arq_base.neuroticismo + rng_desc.normal(0, 0.015), 0.20, 0.80)), 2),
                umbral_miedo=round(float(np.clip(arq_base.umbral_miedo + rng_desc.normal(0, 0.015), 0.30, 0.85)), 2),
            )

            res = await evaluar_individuo_en_semilla(
                adaptador=adaptador,
                arquetipo=arq_desc,
                axiomas_heredados=cond["axiomas"],
                seed_mapa=s_map,
                max_latidos=max_latidos,
                aislar_ruido_termodinamico=True,
            )

            res_clean = {k: v for k, v in res.items() if k != "secuencia_completa"}
            resultados_por_condicion[cond["id"]].append(res_clean)

            filas_csv.append({
                "seed": s_map,
                "condicion_id": cond["id"],
                "condicion_nombre": cond["nombre"],
                "tipo_control": cond["tipo_control"],
                "latidos_pasos": res["latidos"],
                "salud_final": res["salud_final"],
                "total_logros": res["total_logros"],
                "crafter_score_individual": res["crafter_score_individual"],
                "fitness_global": res["fitness"]["global"],
                "fitness_s1": res["fitness"]["s1_reactivo"],
                "fitness_s2": res["fitness"]["s2_limbico"],
                "fitness_s3": res["fitness"]["s3_racional"],
                "causa_muerte": res["causa_muerte"],
                "logros_desbloqueados": ";".join(res["logros"]),
                "num_axiomas_heredados": len(cond["axiomas"]),
            })

            sys.stdout.write(f"\r[{corrida_idx:3d}/{total_corridas}] Seed {s_map} | {cond['id'][:18]:18s} -> Logros={res['total_logros']:2d} Pasos={res['latidos']:3d} Fit={res['fitness']['global']:4.1f}")
            sys.stdout.flush()

    adaptador.desconectar()
    print("\n\nSimulaciones completadas exitosamente.")

    # Guardar CSV crudo
    ruta_csv = os.path.join(RUTA_DIR_SALIDA, "experimento_factorial_heredabilidad_crafter.csv")
    with open(asegurar_directorio_de(ruta_csv), "w", newline="", encoding="utf-8") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=list(filas_csv[0].keys()))
        writer.writeheader()
        writer.writerows(filas_csv)
    print(f"[*] Dataset crudo persistido en: {ruta_csv}")

    # =========================================================================
    # ANALISIS ESTADISTICO COMPLETO
    # =========================================================================
    analisis_resumen: Dict[str, Any] = {
        "metodologia": f"Diseno Factorial 2x2 + Controles Placebo y Mediano en N={len(semillas)} semillas ({semillas[0]}..{semillas[-1]})",
        "semillas_evaluadas": semillas,
        "condiciones": {},
        "comparativas_contra_control_vacio": {},
        "analisis_factorial_2x2": {},
    }

    # Métricas agregadas por condición
    print("\n" + "=" * 105)
    print(f"{'Condición':<32} | {'Crafter Score':^13} | {'Logros (Med±DE)':^15} | {'Logros [Med,IQR]':^16} | {'Fit Global':^12} | {'Pasos':^10}")
    print("-" * 105)

    arr_datos = {}
    for cond in condiciones_def:
        cid = cond["id"]
        res_list = resultados_por_condicion[cid]
        bench = calcular_crafter_score_poblacional(res_list)

        log_arr = np.array([r["total_logros"] for r in res_list], dtype=float)
        fit_arr = np.array([r["fitness"]["global"] for r in res_list], dtype=float)
        pas_arr = np.array([r["latidos"] for r in res_list], dtype=float)

        arr_datos[cid] = {"logros": log_arr, "fitness": fit_arr, "pasos": pas_arr, "score": bench["crafter_score"]}

        med_log = float(np.median(log_arr))
        iqr_log = [float(np.percentile(log_arr, 25)), float(np.percentile(log_arr, 75))]

        analisis_resumen["condiciones"][cid] = {
            "nombre": cond["nombre"],
            "tipo_control": cond["tipo_control"],
            "crafter_score_poblacional": round(bench["crafter_score"], 2),
            "sum_ln": round(bench["sum_ln"], 4),
            "logros_desbloqueados_unicos": len(bench["logros_desbloqueados"]),
            "lista_logros": bench["logros_desbloqueados"],
            "logros_media": round(float(np.mean(log_arr)), 2),
            "logros_std": round(float(np.std(log_arr)), 2),
            "logros_mediana": med_log,
            "logros_iqr": iqr_log,
            "fitness_media": round(float(np.mean(fit_arr)), 2),
            "fitness_std": round(float(np.std(fit_arr)), 2),
            "fitness_mediana": round(float(np.median(fit_arr)), 2),
            "pasos_media": round(float(np.mean(pas_arr)), 1),
            "pasos_std": round(float(np.std(pas_arr)), 1),
        }

        print(
            f"{cond['nombre']:<32} | {bench['crafter_score']:6.2f}% ({len(bench['logros_desbloqueados']):2d}/22) | "
            f"{np.mean(log_arr):5.2f} ± {np.std(log_arr):4.2f} | {med_log:4.1f} [{iqr_log[0]:3.1f}-{iqr_log[1]:3.1f}] | "
            f"{np.mean(fit_arr):5.1f} ± {np.std(fit_arr):4.1f} | {np.mean(pas_arr):5.1f} ± {np.std(pas_arr):4.1f}"
        )
    print("=" * 105)

    # Pruebas estadísticas pareadas contra Control Vacío (C4)
    print("\nPRUEBAS ESTADISTICAS PAREADAS CONTRA CONTROL VACIO (C4):")
    print("-" * 105)
    print(f"{'Comparativa vs C4_Control_Vacio':<30} | {'Δ Logros (Media [95% CI])':^25} | {'Wilcoxon W':^11} | {'p-value':^10} | {'Sign Test (V/T/D)':^16} | {'Cliff d':^8}")
    print("-" * 105)

    base_log = arr_datos["C4_Control_Vacio"]["logros"]
    base_fit = arr_datos["C4_Control_Vacio"]["fitness"]

    for cid in ["C1_Record_Completo", "C2_Solo_Arquetipo", "C3_Solo_Axiomas", "C5_Placebo_Sham", "C6_Linaje_Mediano"]:
        comp_log = arr_datos[cid]["logros"]
        comp_fit = arr_datos[cid]["fitness"]

        # Bootstrap IC 95%
        d_mean, ci_low, ci_high = bootstrap_ci_diferencia(comp_log, base_log)

        # Wilcoxon signed-rank test
        dif = comp_log - base_log
        dif_no_zero = dif[dif != 0]
        if len(dif_no_zero) > 0:
            w_stat, w_pval = stats.wilcoxon(comp_log, base_log, alternative="two-sided")
        else:
            w_stat, w_pval = 0.0, 1.0

        # Sign Test
        vics = int(np.sum(dif > 0))
        ties = int(np.sum(dif == 0))
        defs = int(np.sum(dif < 0))
        n_effective = vics + defs
        sign_pval = float(stats.binomtest(vics, n_effective, 0.5).pvalue) if n_effective > 0 else 1.0

        # Cliff's Delta
        cd = calcular_cliffs_delta(comp_log, base_log)

        # Wilcoxon para fitness
        dif_fit = comp_fit - base_fit
        if len(dif_fit[dif_fit != 0]) > 0:
            w_fit_stat, w_fit_pval = stats.wilcoxon(comp_fit, base_fit, alternative="two-sided")
        else:
            w_fit_stat, w_fit_pval = 0.0, 1.0

        analisis_resumen["comparativas_contra_control_vacio"][cid] = {
            "delta_crafter_score": round(arr_datos[cid]["score"] - arr_datos["C4_Control_Vacio"]["score"], 2),
            "delta_logros_media": d_mean,
            "bootstrap_ci_95": [ci_low, ci_high],
            "wilcoxon_w": float(w_stat),
            "wilcoxon_p_value": float(w_pval),
            "sign_test": {"victorias": vics, "empates": ties, "derrotas": defs, "binomial_p_value": sign_pval},
            "cliffs_delta": cd,
            "fitness_wilcoxon_p_value": float(w_fit_pval),
        }

        print(
            f"{cid:<30} | {d_mean:+5.2f} [{ci_low:+5.2f}, {ci_high:+5.2f}] | "
            f"{w_stat:10.1f} | {w_pval:10.4f} | {f'{vics}V / {ties}T / {defs}D':^16} | {cd:+7.3f}"
        )
    print("=" * 105)

    # Análisis Factorial 2x2 (Efecto Principal Arquetipo, Efecto Principal Axiomas, Interacción)
    # y = b0 + b1*Arquetipo + b2*Axiomas + b3*(Arquetipo * Axiomas)
    X = []
    y_log = []
    for s_idx in range(len(semillas)):
        # C4: Arq=0, Ax=0
        X.append([1, 0, 0, 0])
        y_log.append(arr_datos["C4_Control_Vacio"]["logros"][s_idx])
        # C2: Arq=1, Ax=0
        X.append([1, 1, 0, 0])
        y_log.append(arr_datos["C2_Solo_Arquetipo"]["logros"][s_idx])
        # C3: Arq=0, Ax=1
        X.append([1, 0, 1, 0])
        y_log.append(arr_datos["C3_Solo_Axiomas"]["logros"][s_idx])
        # C1: Arq=1, Ax=1
        X.append([1, 1, 1, 1])
        y_log.append(arr_datos["C1_Record_Completo"]["logros"][s_idx])

    X_mat = np.array(X, dtype=float)
    y_vec = np.array(y_log, dtype=float)
    beta, residuals, rank, s = np.linalg.lstsq(X_mat, y_vec, rcond=None)

    # Error estándar y significación de coeficientes
    n_obs = len(y_vec)
    p_vars = X_mat.shape[1]
    res_sum = np.sum((y_vec - X_mat @ beta) ** 2)
    s2 = res_sum / (n_obs - p_vars)
    cov_beta = s2 * np.linalg.inv(X_mat.T @ X_mat)
    se_beta = np.sqrt(np.diag(cov_beta))
    t_vals = beta / se_beta
    p_vals = [2.0 * (1.0 - stats.t.cdf(abs(t), df=n_obs - p_vars)) for t in t_vals]

    analisis_resumen["analisis_factorial_2x2"] = {
        "intercepto_c4_base": {"beta": round(float(beta[0]), 3), "se": round(float(se_beta[0]), 3), "p_value": round(float(p_vals[0]), 4)},
        "efecto_principal_arquetipo": {"beta": round(float(beta[1]), 3), "se": round(float(se_beta[1]), 3), "p_value": round(float(p_vals[1]), 4)},
        "efecto_principal_axiomas": {"beta": round(float(beta[2]), 3), "se": round(float(se_beta[2]), 3), "p_value": round(float(p_vals[2]), 4)},
        "interaccion_arquetipo_x_axiomas": {"beta": round(float(beta[3]), 3), "se": round(float(se_beta[3]), 3), "p_value": round(float(p_vals[3]), 4)},
    }

    print("\nDESCOMPOSICION FACTORIAL 2x2 (REGRESION MCO SOBRE LOGROS):")
    print(f"  * Intercepto (C4 Base Vacía)       : β = {beta[0]:+.3f} (SE = {se_beta[0]:.3f}, p = {p_vals[0]:.4f})")
    print(f"  * Efecto Principal Arquetipo (C2) : β = {beta[1]:+.3f} (SE = {se_beta[1]:.3f}, p = {p_vals[1]:.4f})")
    print(f"  * Efecto Principal Axiomas (C3)   : β = {beta[2]:+.3f} (SE = {se_beta[2]:.3f}, p = {p_vals[2]:.4f})")
    print(f"  * Interacción Arquetipo x Axiomas : β = {beta[3]:+.3f} (SE = {se_beta[3]:.3f}, p = {p_vals[3]:.4f})")

    # Guardar resumen JSON
    ruta_json = os.path.join(RUTA_DIR_SALIDA, "experimento_factorial_heredabilidad_crafter.json")
    with open(asegurar_directorio_de(ruta_json), "w", encoding="utf-8") as f_json:
        json.dump(analisis_resumen, f_json, indent=2, ensure_ascii=False)
    print(f"\n[*] Informe estadístico estructurado persistido en: {ruta_json}")


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    parser = argparse.ArgumentParser(description="Estudio factorial de herencia (arquetipo x axiomas) en Crafter")
    parser.add_argument("--linaje", default=RUTA_LINAJE_EJEMPLO, help="JSON de linaje de entrada (por defecto, el linaje de ejemplo publicado)")
    parser.add_argument("--semillas", default="2000-2019", help="Rango de semillas, p. ej. 3000-3039 (por defecto 2000-2019, el usado originalmente)")
    args = parser.parse_args()
    ini, fin = (int(x) for x in args.semillas.split("-"))
    asyncio.run(main(ruta_linaje=args.linaje, semillas=list(range(ini, fin + 1))))
