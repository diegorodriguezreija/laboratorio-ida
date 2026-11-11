"""
Genera docs/RESULTADOS_TABLAS.md a partir de los CSV versionados en analisis/resultados/.

Toda cifra pública del repositorio sale de aquí. Cada tabla indica su CSV de origen y su SHA-256.
Las comparaciones pareadas usan analisis/estadistica.py (bootstrap 10 000, Wilcoxon, signos,
delta de Cliff, Holm-Bonferroni). Las proporciones de ajedrez usan el intervalo de Wilson.

    python analisis/generar_tablas.py            # escribe docs/RESULTADOS_TABLAS.md
    python analisis/generar_tablas.py --stdout   # lo imprime
"""

import argparse
import csv
import gzip
import hashlib
import math
import os
import subprocess
import sys
from collections import Counter, defaultdict
from statistics import mean, median
from typing import Dict, List, Optional

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
if os.path.join(RAIZ, "base") not in sys.path:
    sys.path.insert(0, os.path.join(RAIZ, "base"))

import numpy as np  # noqa: E402

from herramientas.estadistica import corregir_holm_bonferroni, evaluar_comparativa_pareada  # noqa: E402
from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import calcular_crafter_score_poblacional  # noqa: E402

RES = os.path.join(RAIZ, "archivo-v14", "resultados_historicos")
N1 = os.path.join(RES, "N1_reserva_3000-3039")
SALIDA = os.path.join(RAIZ, "docs", "RESULTADOS_TABLAS.md")

NOMBRES_ARBITRO = {
    "A0": "A0 Tribunal (ponderación arousal-confianza modulada por estrés)",
    "A1": "A1 Mayor arousal",
    "A2": "A2 Prioridad fija S1 > S2 > S3",
    "A3": "A3 Prioridad fija S3 > S2 > S1",
    "A4": "A4 Muestreo aleatorio ponderado por arousal",
    "A7": "A7 Mayor producto arousal × confianza",
}


# ----------------------------------------------------------------------------- utilidades

def f(x, d=2, signo=False) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    s = f"{x:+.{d}f}" if signo else f"{x:.{d}f}"
    return s.replace(".", ",")


def p_fmt(p: float) -> str:
    return "< 0,001" if p < 0.001 else f(p, 3)


def leer(ruta: str) -> Optional[List[Dict[str, str]]]:
    if not os.path.exists(ruta):
        return None
    abrir = gzip.open if ruta.endswith(".gz") else open
    with abrir(ruta, "rt", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def sha(ruta: str) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()[:16]


def fuente(ruta: str) -> str:
    rel = os.path.relpath(ruta, RAIZ).replace(os.sep, "/")
    return f"Fuente: [`{rel}`](../{rel}) · SHA-256 `{sha(ruta)}…`"


def wilson(exitos: float, n: int, z: float = 1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = exitos / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    margen = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, centro - margen), min(1.0, centro + margen)


def bootstrap_diferencia_no_pareada(a, b, n=10000, seed=42):
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    difs = rng.choice(a, (n, len(a))).mean(1) - rng.choice(b, (n, len(b))).mean(1)
    return float(a.mean() - b.mean()), float(np.percentile(difs, 2.5)), float(np.percentile(difs, 97.5))


def por_semilla(filas, clave_cond, cond, valor):
    return {int(r["semilla"]): float(r[valor]) for r in filas if r[clave_cond] == cond}


def score_poblacional(filas) -> float:
    return calcular_crafter_score_poblacional([{"logros": [x for x in r["logros"].split(";") if x]} for r in filas])["crafter_score"]


def commit_actual() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    except Exception:
        return "desconocido"


# ----------------------------------------------------------------------------- secciones

def seccion_h1(nivel: str) -> List[str]:
    ruta = os.path.join(N1, f"H1_crafter_{nivel}.csv")
    filas = leer(ruta)
    if filas is None:
        return [f"_H1 {nivel}: CSV no disponible._", ""]
    out = [f"### H1 · Crafter · ablación {nivel.replace('_', ' ')}", "", fuente(ruta), ""]
    out += ["| Árbitro | N | Logros (media) | Crafter Score poblacional (%) | Pasos (mediana) |", "|---|---:|---:|---:|---:|"]
    for aid in NOMBRES_ARBITRO:
        sub = [r for r in filas if r["arbitro_id"] == aid]
        if not sub:
            continue
        out.append(f"| {NOMBRES_ARBITRO[aid]} | {len(sub)} | {f(mean(float(r['total_logros']) for r in sub))} | "
                   f"{f(score_poblacional(sub))} | {f(median(float(r['latidos']) for r in sub), 0)} |")
    a0 = por_semilla(filas, "arbitro_id", "A0", "total_logros")
    comps = []
    for aid in [a for a in NOMBRES_ARBITRO if a != "A0"]:
        otro = por_semilla(filas, "arbitro_id", aid, "total_logros")
        sem = sorted(set(a0) & set(otro))
        if sem:
            comps.append((aid, evaluar_comparativa_pareada([a0[s] for s in sem], [otro[s] for s in sem], "A0", aid)))
    holm = corregir_holm_bonferroni([c["wilcoxon_p"] for _, c in comps])
    out += ["", "Comparación pareada por semilla del total de logros: A0 menos el árbitro alternativo.", "",
            "| A0 frente a | N | Δ logros (A0 − alt.) | IC 95 % bootstrap | Wilcoxon p | p Holm | V/E/D (A0) | δ de Cliff |",
            "|---|---:|---:|---|---:|---:|---|---:|"]
    for (aid, c), ph in zip(comps, holm):
        out.append(f"| {NOMBRES_ARBITRO[aid]} | {c['n']} | {f(c['delta_media'], 2, True)} | "
                   f"[{f(c['ci_95'][0], 2, True)}, {f(c['ci_95'][1], 2, True)}] | {p_fmt(c['wilcoxon_p'])} | {p_fmt(ph)} | "
                   f"{c['victorias']}/{c['empates']}/{c['derrotas']} | {f(c['cliffs_delta'])} |")
    out.append("")
    ruta_tele = os.path.join(N1, f"H1_crafter_{nivel}_telemetria.csv.gz")
    if not os.path.exists(ruta_tele):
        ruta_tele = ruta_tele[:-3]
    tele = leer(ruta_tele)
    if tele:
        out += ["Acuerdo contrafactual (telemetría de los episodios A0): porcentaje de latidos en que el árbitro "
                "alternativo habría elegido el mismo comando que A0 ante los mismos candidatos.", "", fuente(ruta_tele), "",
                "| Árbitro | Latidos | Acuerdo con A0 |", "|---|---:|---:|"]
        for aid in ("A1", "A2", "A3", "A4", "A5", "A6", "A7"):
            col = f"cf_{aid}_cmd"
            if col not in tele[0]:
                continue
            n = len(tele)
            iguales = sum(1 for t in tele if t[col] == t["cf_A0_cmd"])
            out.append(f"| {aid} | {n} | {f(100 * iguales / n, 1)} % |")
        out.append("")
    return out


def seccion_h7() -> List[str]:
    ruta = os.path.join(N1, "H7_crafter_1500p.csv")
    filas = leer(ruta)
    if filas is None:
        return ["_H7: CSV no disponible._", ""]
    out = ["### H7 · Crafter · S2 activo frente a S2 neutralizado (tope 1500 pasos)", "", fuente(ruta), "",
           "| Condición | N | Logros (media) | Pasos (mediana) | Muertes por depredador | Llegan al tope | Crafter Score poblacional (%) |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for cond, nombre in (("S2_On", "S2 activo"), ("S2_Neutro", "S2 neutralizado")):
        sub = [r for r in filas if r["condicion"] == cond]
        dep = sum(1 for r in sub if r["muerte_depredador"] in ("True", "1", "true"))
        tope = sum(1 for r in sub if r["llego_al_tope"] in ("True", "1", "true"))
        out.append(f"| {nombre} | {len(sub)} | {f(mean(float(r['total_logros']) for r in sub))} | "
                   f"{f(median(float(r['latidos']) for r in sub), 0)} | {dep}/{len(sub)} | {tope}/{len(sub)} | {f(score_poblacional(sub))} |")
    out += ["", "| Variable (S2 activo − S2 neutralizado) | N | Δ media | IC 95 % bootstrap | Wilcoxon p | V/E/D |", "|---|---:|---:|---|---:|---|"]
    for var, nombre in (("total_logros", "Logros"), ("latidos", "Pasos vividos")):
        on = por_semilla(filas, "condicion", "S2_On", var)
        neu = por_semilla(filas, "condicion", "S2_Neutro", var)
        sem = sorted(set(on) & set(neu))
        c = evaluar_comparativa_pareada([on[s] for s in sem], [neu[s] for s in sem])
        out.append(f"| {nombre} | {c['n']} | {f(c['delta_media'], 2, True)} | [{f(c['ci_95'][0], 2, True)}, {f(c['ci_95'][1], 2, True)}] | "
                   f"{p_fmt(c['wilcoxon_p'])} | {c['victorias']}/{c['empates']}/{c['derrotas']} |")
    out.append("")
    return out


def seccion_h2() -> List[str]:
    ruta = os.path.join(N1, "H2_crafter_sweep.csv")
    filas = leer(ruta)
    if filas is None:
        return ["_H2: CSV no disponible._", ""]
    conds = list(dict.fromkeys(r["condicion"] for r in filas))
    out = ["### H2 · Crafter · cortisol fijo frente a dinámico (manipulación verificada, R1)", "", fuente(ruta), "",
           "| Condición | N | Logros (media) | % decisiones de S1 (media) | Pasos (mediana) |", "|---|---:|---:|---:|---:|"]
    for c in conds:
        sub = [r for r in filas if r["condicion"] == c]
        out.append(f"| {c} | {len(sub)} | {f(mean(float(r['total_logros']) for r in sub))} | "
                   f"{f(mean(float(r['pct_decisiones_s1']) for r in sub), 1)} | {f(median(float(r['latidos']) for r in sub), 0)} |")
    base = por_semilla(filas, "condicion", "Soma_Dinamico", "total_logros")
    comps = []
    for c in conds:
        if c == "Soma_Dinamico":
            continue
        otro = por_semilla(filas, "condicion", c, "total_logros")
        sem = sorted(set(base) & set(otro))
        comps.append((c, evaluar_comparativa_pareada([otro[s] for s in sem], [base[s] for s in sem])))
    holm = corregir_holm_bonferroni([x["wilcoxon_p"] for _, x in comps])
    out += ["", "| Condición − dinámico (logros) | N | Δ media | IC 95 % bootstrap | Wilcoxon p | p Holm |", "|---|---:|---:|---|---:|---:|"]
    for (c, x), ph in zip(comps, holm):
        out.append(f"| {c} | {x['n']} | {f(x['delta_media'], 2, True)} | [{f(x['ci_95'][0], 2, True)}, {f(x['ci_95'][1], 2, True)}] | "
                   f"{p_fmt(x['wilcoxon_p'])} | {p_fmt(ph)} |")
    out.append("")
    return out


def seccion_factorial() -> List[str]:
    ruta = os.path.join(N1, "experimento_factorial_heredabilidad_crafter.csv")
    filas = leer(ruta)
    if filas is None:
        return ["_Estudio factorial: CSV no disponible._", ""]
    conds = list(dict.fromkeys(r["condicion_id"] for r in filas))
    out = ["### Herencia · Crafter · estudio factorial arquetipo × axiomas", "", fuente(ruta), "",
           "| Condición | N | Logros (media) | Crafter Score poblacional (%) |", "|---|---:|---:|---:|"]
    for c in conds:
        sub = [r for r in filas if r["condicion_id"] == c]
        sc = calcular_crafter_score_poblacional([{"logros": [x for x in r["logros_desbloqueados"].split(";") if x]} for r in sub])["crafter_score"]
        out.append(f"| {sub[0]['condicion_nombre']} | {len(sub)} | {f(mean(float(r['total_logros']) for r in sub))} | {f(sc)} |")
    ctrl = {int(r["seed"]): float(r["total_logros"]) for r in filas if r["condicion_id"] == "C4_Control_Vacio"}
    comps = []
    for c in conds:
        if c == "C4_Control_Vacio":
            continue
        otro = {int(r["seed"]): float(r["total_logros"]) for r in filas if r["condicion_id"] == c}
        sem = sorted(set(ctrl) & set(otro))
        comps.append((c, evaluar_comparativa_pareada([otro[s] for s in sem], [ctrl[s] for s in sem])))
    holm = corregir_holm_bonferroni([x["wilcoxon_p"] for _, x in comps])
    out += ["", "| Condición − C4 control vacío (logros) | N | Δ media | IC 95 % bootstrap | Wilcoxon p | p Holm |", "|---|---:|---:|---|---:|---:|"]
    for (c, x), ph in zip(comps, holm):
        out.append(f"| {c} | {x['n']} | {f(x['delta_media'], 2, True)} | [{f(x['ci_95'][0], 2, True)}, {f(x['ci_95'][1], 2, True)}] | "
                   f"{p_fmt(x['wilcoxon_p'])} | {p_fmt(ph)} |")
    # Efecto de los axiomas manteniendo el arquetipo: C1 (arq+ax) frente a C2 (solo arq)
    c1 = {int(r["seed"]): float(r["total_logros"]) for r in filas if r["condicion_id"] == "C1_Record_Completo"}
    c2 = {int(r["seed"]): float(r["total_logros"]) for r in filas if r["condicion_id"] == "C2_Solo_Arquetipo"}
    sem = sorted(set(c1) & set(c2))
    if sem:
        iguales = sum(1 for s in sem if c1[s] == c2[s])
        x = evaluar_comparativa_pareada([c1[s] for s in sem], [c2[s] for s in sem])
        out += ["", f"Axiomas con el mismo arquetipo (C1 − C2): Δ = {f(x['delta_media'], 2, True)} logros, "
                f"IC 95 % [{f(x['ci_95'][0], 2, True)}, {f(x['ci_95'][1], 2, True)}], Wilcoxon p = {p_fmt(x['wilcoxon_p'])}; "
                f"{iguales} de {len(sem)} semillas con el mismo número de logros."]
    out.append("")
    return out


def seccion_mutaciones() -> List[str]:
    ruta = os.path.join(RES, "P3_autopoiesis", "P3_mutaciones_autopoiesis.csv")
    filas = leer(ruta)
    if filas is None:
        return ["_Recuento de mutaciones de la configuración previa: CSV no disponible._", ""]
    n = len(filas)
    con = sum(1 for r in filas if int(r["mutaciones_autopoiesis"]) > 0)
    tot = sum(int(r["mutaciones_autopoiesis"]) for r in filas)
    rb = sum(int(r["rollbacks_autopoiesis"]) for r in filas)
    sem = sorted({r["semilla"] for r in filas})
    return ["### Autopoiesis en la configuración previa (P-3)", "", fuente(ruta), "",
            f"Protocolo H1 nivel A con la autopoiesis activa, semillas {sem[0]}–{sem[-1]}: {n} episodios; "
            f"{con} con al menos una mutación; {tot} mutaciones en total; {rb} rollbacks.", ""]


def seccion_snake() -> List[str]:
    ruta = os.path.join(RES, "N2_snake", "N2_snake.csv")
    filas = leer(ruta)
    if filas is None:
        return ["_N2 Snake: CSV no disponible._", ""]
    validas = [r for r in filas if r["causa_muerte"] != "error"]
    out = ["### N2 · Snake web · IdA frente a baseline BFS", "", fuente(ruta), "",
           f"Episodios registrados: {len(filas)}; con error del sitio o del navegador: {len(filas) - len(validas)}.", "",
           "| Dificultad | Agente | N | Puntuación media | Mediana | Muerte muro / cuerpo / censurado |", "|---|---|---:|---:|---:|---|"]
    grupos = defaultdict(list)
    for r in validas:
        grupos[(r["dificultad_nombre"], r["agente"])].append(r)
    for (dif, ag), sub in sorted(grupos.items()):
        cnt = Counter(r["causa_muerte"] for r in sub)
        out.append(f"| {dif} | {ag} | {len(sub)} | {f(mean(float(r['puntuacion']) for r in sub), 1)} | "
                   f"{f(median(float(r['puntuacion']) for r in sub), 0)} | {cnt.get('muro', 0)} / {cnt.get('cuerpo', 0)} / {cnt.get('censurado', 0)} |")
    out += ["", "| Dificultad | Δ puntuación media (IdA − BFS) | IC 95 % bootstrap (no pareado) |", "|---|---:|---|"]
    for dif in sorted({d for d, _ in grupos}):
        a = [float(r["puntuacion"]) for r in grupos.get((dif, "ida"), [])]
        b = [float(r["puntuacion"]) for r in grupos.get((dif, "bfs"), [])]
        if a and b:
            d, lo, hi = bootstrap_diferencia_no_pareada(a, b)
            out.append(f"| {dif} | {f(d, 1, True)} | [{f(lo, 1, True)}, {f(hi, 1, True)}] |")
    out.append("")
    return out


def seccion_ajedrez() -> List[str]:
    ruta = os.path.join(RES, "N3_ajedrez", "N3_ajedrez.csv")
    filas = leer(ruta)
    if filas is None:
        return ["_N3 Ajedrez: CSV no disponible._", ""]
    out = ["### N3 · Ajedrez · IdA frente a baseline de 1 ply", "", fuente(ruta), "",
           "Puntuación = (victorias + tablas/2) / partidas terminadas, con intervalo de Wilson al 95 %. "
           "Las partidas que llegan al tope de seguridad se cuentan aparte y no entran en la puntuación.", "",
           "| Rival | Agente | Partidas | V / T / D | Tope | Puntuación | IC 95 % Wilson | Tablas por repetición | Sustituciones de Stockfish |",
           "|---|---|---:|---|---:|---:|---|---:|---:|"]
    rivales = list(dict.fromkeys(r["rival"] for r in filas))
    for rv in rivales:
        for ag in ("ida", "baseline_1ply"):
            sub = [r for r in filas if r["rival"] == rv and r["agente"] == ag]
            v = sum(r["resultado"] == "victoria" for r in sub)
            t = sum(r["resultado"] == "tablas" for r in sub)
            d = sum(r["resultado"] == "derrota" for r in sub)
            lim = sum(r["resultado"] == "limite" for r in sub)
            rep = sum(r["tipo"] == "repeticion" for r in sub)
            fb = sum(int(r["fallbacks_stockfish"] or 0) for r in sub)
            p, lo, hi = wilson(v + 0.5 * t, v + t + d)
            out.append(f"| {rv} | {ag} | {len(sub)} | {v} / {t} / {d} | {lim} | {f(p, 3)} | [{f(lo, 3)}, {f(hi, 3)}] | {rep} | {fb} |")
    out += ["", "Comparación pareada por partida (misma apertura, color y semilla del rival): puntos de IdA menos puntos del baseline "
            "(1 victoria, ½ tablas, 0 derrota; tope = ½).", "",
            "| Rival | N | Δ puntos medios | IC 95 % bootstrap | Wilcoxon p |", "|---|---:|---:|---|---:|"]
    pts = {"victoria": 1.0, "tablas": 0.5, "derrota": 0.0, "limite": 0.5}
    for rv in rivales:
        ida = {int(r["partida"]): pts[r["resultado"]] for r in filas if r["rival"] == rv and r["agente"] == "ida"}
        bas = {int(r["partida"]): pts[r["resultado"]] for r in filas if r["rival"] == rv and r["agente"] == "baseline_1ply"}
        sem = sorted(set(ida) & set(bas))
        x = evaluar_comparativa_pareada([ida[s] for s in sem], [bas[s] for s in sem])
        out.append(f"| {rv} | {x['n']} | {f(x['delta_media'], 3, True)} | [{f(x['ci_95'][0], 3, True)}, {f(x['ci_95'][1], 3, True)}] | {p_fmt(x['wilcoxon_p'])} |")
    out.append("")
    return out


def main():
    ap = argparse.ArgumentParser(description="Genera docs/RESULTADOS_TABLAS.md desde los CSV versionados")
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args()
    lineas = [
        "# Tablas de resultados (generadas)",
        "",
        f"Generado por `python analisis/generar_tablas.py` en el commit `{commit_actual()}`. No editar a mano: "
        "cualquier cambio se hace en el script o en los datos y se regenera. Decimales con coma.",
        "",
        "## Crafter (N1: semillas de reserva 3000–3039, usadas una sola vez)",
        "",
    ]
    lineas += seccion_h1("nivel_a") + seccion_h1("nivel_b") + seccion_h7() + seccion_h2() + seccion_factorial() + seccion_mutaciones()
    lineas += ["## Snake web (N2)", ""] + seccion_snake()
    lineas += ["## Ajedrez (N3)", ""] + seccion_ajedrez()
    texto = "\n".join(lineas) + "\n"
    if args.stdout:
        print(texto)
    else:
        os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
        with open(SALIDA, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(texto)
        print(f"[+] {os.path.relpath(SALIDA, RAIZ)}")


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    main()
