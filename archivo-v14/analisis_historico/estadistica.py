"""
Módulo Estadístico Central para el Plan de Evaluación del Core (IdA v12.0)
========================================================================
Proporciona análisis inferencial riguroso y automatizado para comparaciones pareadas:
- Test de rangos con signo de Wilcoxon (bilateral).
- Test de signos binomial bilateral (V / E / D).
- Intervalos de confianza al 95% Bootstrap (B >= 10.000 remuestreos).
- Delta de Cliff como tamaño de efecto no paramétrico.
- Corrección de comparaciones múltiples de Holm-Bonferroni.
- Formato tabular limpio para markdown y serialización JSON.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats


def calcular_cliffs_delta(x: List[float], y: List[float]) -> float:
    """Calcula el delta de Cliff para el tamaño del efecto no paramétrico."""
    n_x, n_y = len(x), len(y)
    if n_x == 0 or n_y == 0:
        return 0.0
    mas = 0
    menos = 0
    for xi in x:
        for yj in y:
            if xi > yj:
                mas += 1
            elif xi < yj:
                menos += 1
    return float((mas - menos) / (n_x * n_y))


def bootstrap_ci_diferencia_pareada(
    x: List[float],
    y: List[float],
    n_resamples: int = 10000,
    ci: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """
    Calcula la media de las diferencias pareadas (x - y) y su intervalo de confianza
    al 95% mediante remuestreo Bootstrap con semilla fija.
    """
    diffs = np.array(x) - np.array(y)
    mean_diff = float(np.mean(diffs))
    rng = np.random.RandomState(seed)
    boot_means = []
    n = len(diffs)
    for _ in range(n_resamples):
        sample = rng.choice(diffs, size=n, replace=True)
        boot_means.append(float(np.mean(sample)))
    alpha = (1.0 - ci) / 2.0
    lower = float(np.percentile(boot_means, alpha * 100))
    upper = float(np.percentile(boot_means, (1.0 - alpha) * 100))
    return mean_diff, lower, upper


def evaluar_comparativa_pareada(
    tratamiento: List[float],
    control: List[float],
    nombre_tratamiento: str = "Tratamiento",
    nombre_control: str = "Control",
) -> Dict[str, Any]:
    """
    Ejecuta el protocolo estadístico completo sobre dos muestras pareadas por semilla.
    """
    assert len(tratamiento) == len(control), "Las muestras deben ser pareadas (mismo tamaño)."
    n = len(tratamiento)

    # 1. Deltas y Bootstrap
    mean_diff, ci_low, ci_high = bootstrap_ci_diferencia_pareada(tratamiento, control)

    # 2. Test de Wilcoxon
    diffs = np.array(tratamiento) - np.array(control)
    diffs_no_cero = diffs[diffs != 0]
    if len(diffs_no_cero) > 0:
        try:
            w_stat, w_p = stats.wilcoxon(tratamiento, control, alternative="two-sided")
            w_stat = float(w_stat)
            w_p = float(w_p)
        except Exception:
            w_stat, w_p = 0.0, 1.0
    else:
        w_stat, w_p = 0.0, 1.0

    # 3. Test de Signos (Binomial)
    victorias = int(np.sum(diffs > 0))
    derrotas = int(np.sum(diffs < 0))
    empates = int(np.sum(diffs == 0))
    n_efectivo = victorias + derrotas
    if n_efectivo > 0:
        binom_res = stats.binomtest(victorias, n_efectivo, p=0.5, alternative="two-sided")
        binom_p = float(binom_res.pvalue)
    else:
        binom_p = 1.0

    # 4. Cliff's delta
    cd = calcular_cliffs_delta(tratamiento, control)

    return {
        "n": n,
        "tratamiento": nombre_tratamiento,
        "control": nombre_control,
        "media_tratamiento": float(np.mean(tratamiento)),
        "media_control": float(np.mean(control)),
        "delta_media": round(mean_diff, 4),
        "ci_95": [round(ci_low, 4), round(ci_high, 4)],
        "wilcoxon_w": round(w_stat, 2),
        "wilcoxon_p": round(w_p, 6),
        "victorias": victorias,
        "empates": empates,
        "derrotas": derrotas,
        "sign_test_p": round(binom_p, 6),
        "cliffs_delta": round(cd, 4),
        "significativo_al_5pct": bool(w_p < 0.05 and (ci_low > 0 or ci_high < 0)),
    }


def corregir_holm_bonferroni(p_values: List[float]) -> List[float]:
    """Aplica corrección secuencial de Holm-Bonferroni para comparaciones múltiples."""
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m
    running_max = 0.0
    for rank, (orig_idx, p) in enumerate(indexed):
        adj = p * (m - rank)
        running_max = max(running_max, adj)
        adjusted[orig_idx] = min(1.0, running_max)
    return adjusted
