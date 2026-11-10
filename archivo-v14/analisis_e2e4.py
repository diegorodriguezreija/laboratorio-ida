"""
Análisis de E2–E4 sobre los registros de `v14/experimento.py`, fuera del latido (preregistro
`v14/preregistro_E2_E4.md`). No ejecuta el núcleo.

    python -m v14.analisis_e2e4 a1 --base <carpeta>/a1_base
    python -m v14.analisis_e2e4 pares --base <carpeta>/base --brazo <carpeta>/cal_a [--confirmar a|b] [--repetir-23]
    python -m v14.analisis_e2e4 c --crafter <carpeta>/a1_base <carpeta>/a3_base --ejemplo <...> --bosque <...>

Cada orden imprime un JSON con los números y, con `--out`, lo guarda.
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import math
import os
import random
import statistics as st
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

MIEDO = ("MIEDO", "PANICO")
FRANJA = lambda x: "alta" if x >= 0.75 else ("media" if x >= 0.35 else "baja")  # noqa: E731
COMANDOS = ("ACC_MOVER", "ACC_COGER", "ACC_ESPERAR", "ACC_DEGLUTIR", "ACC_ATACAR", "ACC_ACECHAR", "ACC_SOLTAR", "ACC_ASIMILAR")


# ---------------------------------------------------------------------------------------------
# lectura y estadística
# ---------------------------------------------------------------------------------------------

def leer_brazo(carpeta: str) -> Tuple[Dict[int, Dict[str, Any]], Dict[int, List[Dict[str, Any]]]]:
    vidas = {}
    with open(os.path.join(carpeta, "vidas.jsonl"), encoding="utf-8") as f:
        for l in f:
            v = json.loads(l)
            vidas[v["semilla"]] = v
    registros = {}
    for ruta in glob.glob(os.path.join(carpeta, "*.jsonl.gz")):
        sem = int(os.path.basename(ruta).split("_")[-1].split(".")[0])
        registros[sem] = [json.loads(l) for l in gzip.open(ruta, "rt", encoding="utf-8")]
    return vidas, registros


def latidos(reg: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [e for e in reg if e.get("tipo") == "latido"]


def vigilia(reg):
    return [e for e in latidos(reg) if e["cuerpo"]["afecto"] != "DORMIDO" and not (e.get("mundo") or {}).get("duerme")]


def boot_media(xs: List[float], n: int = 2000, semilla: int = 0) -> Dict[str, Any]:
    rng = random.Random(semilla)
    medias = sorted(st.fmean(rng.choice(xs) for _ in xs) for _ in range(n))
    return {"media": st.fmean(xs), "ic95": [medias[int(.025 * n)], medias[int(.975 * n) - 1]], "_medias": medias}


def p_unilateral(medias: List[float], umbral: float, mayor: bool) -> float:
    """Fracción de medias bootstrap que NO cumplen (media > umbral si mayor; media < umbral si no)."""
    malas = sum(1 for m in medias if (m <= umbral if mayor else m >= umbral))
    return max(malas, 1) / len(medias)


def wilcoxon_mayor(xs: List[float]) -> Optional[float]:
    from scipy.stats import wilcoxon
    xs = [x for x in xs if x != 0]
    if len(xs) < 6:
        return None
    return float(wilcoxon(xs, alternative="greater").pvalue)


def holm(pvals: Dict[str, Optional[float]], alfa: float = 0.05) -> Dict[str, Dict[str, Any]]:
    orden = sorted((p if p is not None else 1.0, k) for k, p in pvals.items())
    m, out, sigue = len(orden), {}, True
    for i, (p, k) in enumerate(orden):
        ajustado = min(1.0, p * (m - i))
        sigue = sigue and ajustado < alfa
        out[k] = {"p": pvals[k], "p_holm": ajustado, "cumple": sigue}
    return out


def limpio(d):
    if isinstance(d, dict):
        return {k: limpio(v) for k, v in d.items() if not k.startswith("_")}
    if isinstance(d, list):
        return [limpio(x) for x in d]
    if isinstance(d, float):
        return round(d, 4)
    return d


def corr(a: List[float], b: List[float]) -> Optional[float]:
    if len(a) < 3 or st.pstdev(a) == 0 or st.pstdev(b) == 0:
        return None
    return st.correlation(a, b)


# ---------------------------------------------------------------------------------------------
# A1 diagnóstico
# ---------------------------------------------------------------------------------------------

def extremo(x: float, escala: float) -> bool:
    return x <= 0.1 * escala or x >= 0.9 * escala


def a1(carpeta: str) -> Dict[str, Any]:
    vidas, regs = leer_brazo(carpeta)
    filas = [e for r in regs.values() for e in vigilia(r)]
    n = len(filas)
    var = {"alimentacion": [e["cuerpo"]["ali"] for e in filas], "vitalidad": [e["cuerpo"]["vit"] for e in filas],
           "urgencia_s1": [e["cuerpo"]["urgencia"] for e in filas], "peligro_s1": [e["cuerpo"]["peligro_s1"] for e in filas]}
    escala = {"alimentacion": 100.0, "vitalidad": 100.0, "urgencia_s1": 1.0, "peligro_s1": 1.0}
    dist = {k: {"p10": sorted(v)[int(.1 * (n - 1))], "p50": sorted(v)[int(.5 * (n - 1))], "p90": sorted(v)[int(.9 * (n - 1))],
                "extremo": sum(extremo(x, escala[k]) for x in v) / n} for k, v in var.items()}
    miedo = sum(e["cuerpo"]["afecto"] in MIEDO for e in filas) / n
    dist["miedo"] = {"fraccion": miedo, "extremo": miedo}
    # Relación con el juego, por vida: correlación y desfase (−20..20) que la maximiza
    rel = {"alimentacion~comida+bebida": [], "vitalidad~salud": []}
    for r in regs.values():
        fs = vigilia(r)
        if len(fs) < 40:
            continue
        for clave, a_, b_ in (("alimentacion~comida+bebida", [e["cuerpo"]["ali"] for e in fs], [e["mundo"]["comida"] + e["mundo"]["bebida"] for e in fs]),
                              ("vitalidad~salud", [e["cuerpo"]["vit"] for e in fs], [e["mundo"]["salud"] for e in fs])):
            mejores = [(corr(a_[max(0, d):len(a_) + min(0, d)], b_[max(0, -d):len(b_) - max(0, d)]) or -2, d) for d in range(-20, 21)]
            c0 = corr(a_, b_)
            rel[clave].append({"r": c0, "mejor_r": max(mejores)[0], "desfase": max(mejores)[1]})
    relacion = {k: {"r_mediana": st.median([x["r"] for x in v if x["r"] is not None]) if v else None,
                    "mejor_r_mediana": st.median([x["mejor_r"] for x in v]) if v else None,
                    "desfase_mediano": st.median([x["desfase"] for x in v]) if v else None, "vidas": len(v)} for k, v in rel.items()}
    # Atribución del descenso de la alimentación simulada
    fuentes = Counter()
    for r in regs.values():
        fs = latidos(r)
        for prev, e in zip(fs, fs[1:]):
            if e["cuerpo"]["afecto"] == "DORMIDO":
                continue
            if prev["cuerpo"]["carga"]:
                fuentes["lastre_carga"] += 0.5
            if not e["ejecutado"]:
                fuentes["desgaste_no_compensado"] += 0.8
            m0, m1 = prev.get("mundo"), e.get("mundo")
            if m0 and m1:
                fuentes["caidas_del_juego"] += max(0, m0["comida"] - m1["comida"]) * 11.1 + max(0, m0["bebida"] - m1["bebida"]) * 5.5
    total = sum(fuentes.values()) or 1.0
    atribucion = {k: v / total for k, v in fuentes.most_common()}
    # Atribución del miedo
    fm = [e for e in filas if e["cuerpo"]["afecto"] in MIEDO]
    miedo_causa = {"con_peligro": sum(e["cuerpo"]["peligro_s1"] >= 0.75 for e in fm) / n,
                   "solo_inanicion": sum(e["cuerpo"]["peligro_s1"] < 0.75 and e["cuerpo"]["ali"] <= 15 for e in fm) / n,
                   "otra": sum(e["cuerpo"]["peligro_s1"] < 0.75 and e["cuerpo"]["ali"] > 15 for e in fm) / n}
    acuerdo = sum((e.get("peligro_juego", 0) >= 0.5) == (e["cuerpo"]["peligro_s1"] >= 0.55) for e in filas) / n
    combos = Counter(tuple(e["indicadores"][k] if k == "franja_peligro" else FRANJA(e["indicadores"][k]) for k in ("franja_peligro", "tension", "calma")) for e in filas)
    entropia = -sum((c / n) * math.log2(c / n) for c in combos.values())
    saturadas = [k for k, d in dist.items() if d["extremo"] > 0.5]
    return {"vidas": len(regs), "latidos_vigilia": n, "variables": dist, "relacion_con_el_juego": relacion,
            "atribucion_descenso_alimentacion": atribucion, "miedo": miedo_causa,
            "acuerdo_peligro_juego_vs_s1": acuerdo, "combinaciones_indicadores": len(combos), "entropia_bits": entropia,
            "saturadas": saturadas}


# ---------------------------------------------------------------------------------------------
# Comparación por pares (A2, A3, B)
# ---------------------------------------------------------------------------------------------

def objetivo_cuerpo(regs) -> Dict[str, Any]:
    por_vida_miedo, por_vida_ali = [], []
    for r in regs.values():
        fs = vigilia(r)
        if fs:
            por_vida_miedo.append(sum(e["cuerpo"]["afecto"] in MIEDO for e in fs) / len(fs))
            por_vida_ali.append(sum(extremo(e["cuerpo"]["ali"], 100.0) for e in fs) / len(fs))
    todos = [e for r in regs.values() for e in vigilia(r)]
    return {"miedo_global": sum(e["cuerpo"]["afecto"] in MIEDO for e in todos) / len(todos),
            "ali_extremo_global": sum(extremo(e["cuerpo"]["ali"], 100.0) for e in todos) / len(todos),
            "miedo_por_vida": boot_media(por_vida_miedo), "ali_extremo_por_vida": boot_media(por_vida_ali)}


def cobertura(reg) -> Dict[str, Any]:
    fs = latidos(reg)
    celdas = {tuple(e["pos"]) for e in fs if e.get("pos")}
    pares = {(e["comando"], (e.get("proactiva") or {}).get("clase_objetivo")) for e in fs}
    primero = next((e["n"] for e in fs if (e.get("mundo") or {}).get("logros", 0) >= 1), None)
    return {"celdas": len(celdas), "pares_accion_clase": len(pares), "primer_logro": primero}


def pares(base: str, brazo: str, confirmar: Optional[str] = None) -> Dict[str, Any]:
    vb, rb = leer_brazo(base)
    va, ra = leer_brazo(brazo)
    semillas = sorted(set(vb) & set(va))
    d_log = [(va[s]["total_logros"] or 0) - (vb[s]["total_logros"] or 0) for s in semillas]
    d_lat = [va[s]["latidos"] - vb[s]["latidos"] for s in semillas]
    med_lat = st.median(vb[s]["latidos"] for s in semillas)
    margen_lat = -0.10 * med_lat
    bl, bt = boot_media(d_log), boot_media(d_lat)
    cb = {s: cobertura(rb[s]) for s in semillas}
    ca = {s: cobertura(ra[s]) for s in semillas}
    sec = {"d_celdas": boot_media([ca[s]["celdas"] - cb[s]["celdas"] for s in semillas]),
           "d_pares_accion_clase": boot_media([ca[s]["pares_accion_clase"] - cb[s]["pares_accion_clase"] for s in semillas]),
           "primer_logro_mediana": {"base": st.median([cb[s]["primer_logro"] for s in semillas if cb[s]["primer_logro"]] or [0]),
                                    "brazo": st.median([ca[s]["primer_logro"] for s in semillas if ca[s]["primer_logro"]] or [0])}}
    out = {"semillas": f"{semillas[0]}-{semillas[-1]}", "n": len(semillas),
           "trayectorias_identicas": sum(va[s]["decisiones_hash"] == vb[s]["decisiones_hash"] for s in semillas),
           "logros": {"base": st.fmean(vb[s]["total_logros"] or 0 for s in semillas), "brazo": st.fmean(va[s]["total_logros"] or 0 for s in semillas),
                      "dif": bl, "no_inferior": bl["ic95"][0] >= -0.5},
           "latidos": {"base_mediana": med_lat, "dif": bt, "margen": margen_lat, "no_inferior": bt["ic95"][0] >= margen_lat},
           "cuerpo_base": objetivo_cuerpo(rb), "cuerpo_brazo": objetivo_cuerpo(ra), "secundarias": sec,
           "coste_brazo": coste(va, semillas), "coste_base": coste(vb, semillas),
           "curiosidad_propuestas": sum(va[s].get("curiosidad_propuestas", 0) for s in semillas)}
    cuerpo = out["cuerpo_brazo"]
    out["objetivo_cumple_global"] = cuerpo["miedo_global"] <= 0.40 and cuerpo["ali_extremo_global"] < 0.50
    if confirmar == "a":
        out["confirmatorias"] = holm({
            "A-H1_miedo<0.40": p_unilateral(cuerpo["miedo_por_vida"]["_medias"], 0.40, mayor=False),
            "A-H2_ali_extremo<0.50": p_unilateral(cuerpo["ali_extremo_por_vida"]["_medias"], 0.50, mayor=False),
            "A-H3_logros>-0.5": wilcoxon_mayor([x + 0.5 for x in d_log]),
            "A-H4_latidos>-10%": wilcoxon_mayor([x - margen_lat for x in d_lat])})
    if confirmar == "b":
        out["confirmatorias"] = holm({"B-H1_logros>0": wilcoxon_mayor(d_log),
                                      "B-H2_latidos>-10%": wilcoxon_mayor([x - margen_lat for x in d_lat])})
    return out


def coste(vidas, semillas) -> Dict[str, Any]:
    c = [vidas[s]["coste"] for s in semillas]
    g = lambda k, q: max((x[k][q] or 0) for x in c)  # noqa: E731  (peor partida)
    med = lambda k: st.median([x[k]["p50"] for x in c if x[k]["p50"] is not None] or [0])  # noqa: E731
    return {"observador_p50_mediana": med("observador_ms"), "observador_p99_peor": g("observador_ms", "p99"),
            "curiosidad_p50_mediana": med("curiosidad_ms"), "curiosidad_p99_peor": g("curiosidad_ms", "p99"),
            "latido_p50_mediana": med("latido_ms"), "mantenimiento_max": max((x["mantenimiento_ms_max"] or 0) for x in c),
            "plazo_ms": max((x["plazo_ms"] or 0) for x in c)}


# ---------------------------------------------------------------------------------------------
# Repetición de los pasos 2 y 3 y A-H5 (proactiva reproducida sobre el registro)
# ---------------------------------------------------------------------------------------------

def _fin(reg):
    return next(e for e in reg if e.get("tipo") == "fin")


def boot_partidas(grupos: List[List[Tuple[float, float]]], n: int = 2000) -> Dict[str, Any]:
    from v14.observar import bootstrap_partidas
    r = bootstrap_partidas(grupos, n=n)
    rng = random.Random(1)
    gs = [g for g in grupos if g]
    sims = [sum(a for g in sel for a, _ in g) / max(1, sum(len(g) for g in sel)) - sum(b for g in sel for _, b in g) / max(1, sum(len(g) for g in sel))
            for sel in ([rng.choice(gs) for _ in gs] for _ in range(n))]
    r["p_unilateral_mayor_que_0"] = max(1, sum(1 for x in sims if x <= 0)) / n
    return r


def repetir_23(regs) -> Dict[str, Any]:
    ep = [[(float(x["acierto"]), x["base_misma_vida"]) for x in _fin(r)["episodios_predichos"] if x["base_misma_vida"] is not None] for r in regs.values()]
    pro = [[(float(v["acierto"]), float(v["acierto_base"])) for v in _fin(r)["proactiva"]["validaciones"] if v["acierto_base"] is not None] for r in regs.values()]
    dem = sum(sum(1 for d in _fin(r)["proactiva"]["demostraciones"] if d["demostrada"]) for r in regs.values())
    pierde = sum(sum(1 for d in _fin(r)["proactiva"]["demostraciones"] if not d["demostrada"]) for r in regs.values())
    plano = lambda gs: (sum(a for g in gs for a, _ in g) / max(1, sum(len(g) for g in gs)), sum(b for g in gs for _, b in g) / max(1, sum(len(g) for g in gs)))  # noqa: E731
    return {"episodio_parecido": {"acierto_y_base": plano(ep), "bootstrap": boot_partidas(ep)},
            "expectativas": {"acierto_y_base": plano(pro), "bootstrap": boot_partidas(pro)},
            "demostradas": dem, "dejan_de_estarlo": pierde}


def reproducir_proactiva(reg, ajustes_pro, con_franja: bool) -> List[Tuple[float, float]]:
    """Reproduce la proactiva del observador sobre el registro (misma lógica); con_franja añade la franja
    de peligro del juego a la clase del objetivo. Devuelve (acierto, acierto_base) por expectativa."""
    from v14.observador.proactiva import Proactiva
    pro = Proactiva(ajustes_pro)
    cierres = defaultdict(list)
    for e in reg:
        if e.get("tipo") == "episodio" and e.get("cierre") != "fin":  # «fin» lo cierra cerrar(), tras el último latido
            cierres[e["hasta"]].append(e["id"])
    ultimo = None
    for e in latidos(reg):
        p = e.get("proactiva")
        if p is None:
            continue
        m = e["mundo"]
        vit, ali = float(m["salud"]), float(m["comida"] + m["bebida"])
        pro.validar(e["n"], vit, ali, cierres.get(e["n"], []))
        clase = p["clase_objetivo"] + (f"|{e['indicadores']['franja_peligro']}" if con_franja else "")
        pro.anotar(e["n"], e["comando"], clase, e["objetivo"], p["episodio"], vit, ali, p["puede"])
        ultimo = (e["n"], vit, ali)
    if ultimo:
        pro.validar(ultimo[0], ultimo[1], ultimo[2], [], todas=True)
    return [(float(v["acierto"]), float(v["acierto_base"])) for v in pro.validadas if v.get("acierto_base") is not None]


def a_h5(regs) -> Dict[str, Any]:
    from v14 import parametros as P
    aj = P.ajustes("crafter", P.RUTA_OBSERVACION)["proactiva"]
    sin = [reproducir_proactiva(r, aj, False) for r in regs.values()]
    online = [[(float(v["acierto"]), float(v["acierto_base"])) for v in _fin(r)["proactiva"]["validaciones"] if v["acierto_base"] is not None] for r in regs.values()]
    con = [reproducir_proactiva(r, aj, True) for r in regs.values()]
    return {"reproduccion_identica_a_la_online": sin == online, "con_franja": boot_partidas(con),
            "acierto": sum(a for g in con for a, _ in g) / max(1, sum(len(g) for g in con)),
            "base": sum(b for g in con for _, b in g) / max(1, sum(len(g) for g in con)),
            "expectativas": sum(len(g) for g in con)}


# ---------------------------------------------------------------------------------------------
# Bloque C
# ---------------------------------------------------------------------------------------------

def perfil(fs) -> List[float]:
    n = len(fs) or 1
    cmd = Counter(e["comando"] for e in fs)
    sis = Counter(e["sistema"] for e in fs)
    urg = [e["cuerpo"]["urgencia"] for e in fs] or [0.0]
    return ([cmd[c] / n for c in COMANDOS] + [sis[s] / n for s in ("S1", "S2", "S3")]
            + [st.fmean(urg), st.pstdev(urg), sum(e["indicadores"]["franja_peligro"] == "alta" for e in fs) / n])


def c1(regs_list) -> Dict[str, Any]:
    mitades = []
    for regs in regs_list:
        for sem, r in sorted(regs.items()):
            fs = latidos(r)
            if len(fs) >= 40:
                mitades.append((sem, perfil(fs[: len(fs) // 2]), perfil(fs[len(fs) // 2:])))
    k = len(mitades[0][1])
    todos = [m[1] for m in mitades] + [m[2] for m in mitades]
    mu = [st.fmean(v[j] for v in todos) for j in range(k)]
    sd = [st.pstdev([v[j] for v in todos]) or 1.0 for j in range(k)]
    z = lambda v: [(v[j] - mu[j]) / sd[j] for j in range(k)]  # noqa: E731
    dentro = [corr(z(a), z(b)) for _, a, b in mitades]
    entre = [corr(z(mitades[i][1]), z(mitades[j][2])) for i in range(len(mitades)) for j in range(len(mitades)) if i != j]
    dif = [d - st.fmean(corr(z(mitades[i][1]), z(mitades[j][2])) for j in range(len(mitades)) if j != i) for i, d in enumerate(dentro)]
    icc = []
    for j in range(k):
        pares_ = [(a[j], b[j]) for _, a, b in mitades]
        gm = st.fmean(x for p in pares_ for x in p)
        msb = 2 * sum((st.fmean(p) - gm) ** 2 for p in pares_) / (len(pares_) - 1)
        msw = sum((p[0] - st.fmean(p)) ** 2 + (p[1] - st.fmean(p)) ** 2 for p in pares_) / len(pares_)
        icc.append((msb - msw) / (msb + msw) if (msb + msw) > 0 else 0.0)
    bd = boot_media(dif)
    distinto = bd["ic95"][0] > 0 and st.median(icc) >= 0.40
    return {"vidas": len(mitades), "r_dentro_media": st.fmean(dentro), "r_entre_media": st.fmean(entre),
            "dif_dentro_menos_entre": bd, "icc_mediana": st.median(icc),
            "icc_por_rasgo": dict(zip([*COMANDOS, "gana_S1", "gana_S2", "gana_S3", "urgencia_media", "urgencia_sd", "riesgo"], icc)),
            "conclusion": "se diferencian de forma estable" if distinto else "todos se parecen"}


# Relaciones que el vocabulario y el adaptador de Crafter ya asignan a cada clase
NOMBRADAS = {"water": "ES_NUTRITIVO", "cow": "ES_NUTRITIVO", "plant": "ES_NUTRITIVO", "Nutriente_Agua": "ES_NUTRITIVO",
             "Zombie": "ES_LETAL", "Skeleton": "ES_LETAL", "Arrow": "ES_LETAL", "lava": "ES_LETAL"}
RESULTADO = {1: "mejora", 0: "sigue igual", -1: "empeora"}


def c2(regs_por_mundo: Dict[str, List[Dict[int, List[Dict[str, Any]]]]]) -> Dict[str, Any]:
    inventario, uso = {}, {}
    for mundo, lista in regs_por_mundo.items():
        inv, u = Counter(), Counter()
        for regs in lista:
            for r in regs.values():
                for e in latidos(r):
                    inv.update(e.get("formales") or {})
                    for sel in e.get("seleccion", []):
                        if sel["guardada"] and sel["clase"].startswith(("Sujeto", "Predicado", "Proposicion", "Sentencia", "Logica")):
                            u[sel["clase"]] += 1
                    for rec in e.get("recuperaciones", []):
                        if str(rec.get("clase", "")).startswith(("Sujeto", "Predicado", "Proposicion", "Sentencia", "Logica")):
                            u[rec["clase"] + " (recuperada)"] += 1
        inventario[mundo], uso[mundo] = dict(inv.most_common()), dict(u.most_common())
    # Lagunas en Crafter: pares (acción, clase) con resultado estable que ninguna relación nombra
    resultados = defaultdict(Counter)
    situaciones = defaultdict(Counter)
    for regs in regs_por_mundo.get("crafter", []):
        for r in regs.values():
            for k, h in _fin(r)["proactiva"]["hipotesis"].items():
                for s_, c in h["resultados"].items():
                    resultados[k][int(s_)] += c
            fs = {e["n"]: e for e in latidos(r)}
            for e in r:
                if e.get("tipo") == "episodio" and e["desde"] in fs:
                    a = fs[e["desde"]]
                    situaciones[(a["indicadores"]["franja_peligro"], a["comando"])][e["signo"]] += 1
    lagunas = []
    for k, c in resultados.items():
        n = sum(c.values())
        dom, cd = max(c.items(), key=lambda x: x[1])
        accion, clase = k.split("|", 1)
        nombrada = (dom == 1 and NOMBRADAS.get(clase) == "ES_NUTRITIVO") or (dom == -1 and NOMBRADAS.get(clase) == "ES_LETAL")
        if n >= 20 and cd / n >= 0.70 and not nombrada:
            lagunas.append({"tipo": "accion", "accion": accion, "clase": clase, "n": n, "estabilidad": cd / n,
                            "formula": f"[{accion}({clase})] IMPLICA [BALANCE {RESULTADO[dom].upper()}]"})
    for (franja, cmd), c in situaciones.items():
        n = sum(c.values())
        if n >= 20 and c[-1] / n >= 0.70:
            lagunas.append({"tipo": "situacion", "accion": cmd, "clase": f"peligro {franja}", "n": n, "estabilidad": c[-1] / n,
                            "formula": f"[PELIGRO_{franja.upper()} Y {cmd}] PRECEDE [EPISODIO NEGATIVO]"})
    lagunas.sort(key=lambda x: -x["n"] * x["estabilidad"])
    return {"inventario": inventario, "uso_real": uso, "lagunas": lagunas[:10], "lagunas_candidatas": len(lagunas)}


def c3(regs_list, mundo: str) -> Dict[str, Any]:
    zona = (lambda e: (e["pos"][0] // 4, e["pos"][1] // 4) if e.get("pos") else None) if mundo == "crafter" else (lambda e: e["ubicacion"])
    vecinas = (lambda z, zs: any(abs(z[0] - a[0]) <= 1 and abs(z[1] - a[1]) <= 1 for a in zs)) if mundo == "crafter" else (lambda z, zs: z in zs)
    por_vida, grupos = [], []
    for regs in regs_list:
        for sem, r in sorted(regs.items()):
            fs = {e["n"]: e for e in latidos(r)}
            eps = sorted((e for e in r if e.get("tipo") == "episodio"), key=lambda e: e["hasta"])
            cand, cierres_zona = {}, Counter()
            cerca, lejos = [], []
            for ep in eps:
                ini, fin = fs.get(ep["desde"]), fs.get(ep["hasta"])
                if ini is None or fin is None:
                    continue
                zi = zona(ini)
                ya = [z for z, n_ in cand.items() if n_ < ep["desde"]]
                (cerca if zi is not None and vecinas(zi, ya) else lejos).append(ep["balance"])
                previo = fs.get(ep["desde"] - 1, ini)
                sin_dano = (fin.get("mundo") or {}).get("salud", 0) >= (previo.get("mundo") or {}).get("salud", 0) if mundo == "crafter" else fin["cuerpo"]["vit"] >= previo["cuerpo"]["vit"]
                if ep["cierre"] == "calma" and ep["balance"] >= 0 and sin_dano:
                    zf = zona(fin)
                    if zf is not None:
                        cierres_zona[zf] += 1
                        cand.setdefault(zf, ep["hasta"])
            en_cand = sum(1 for n_, e in fs.items() if zona(e) in cand and cand[zona(e)] <= n_)
            por_vida.append({"semilla": sem, "candidatas": len(cand), "repetidas": sum(1 for c in cierres_zona.values() if c >= 2),
                             "fraccion_latidos_en_candidata": en_cand / max(1, len(fs)),
                             "episodios_cerca": len(cerca), "episodios_lejos": len(lejos)})
            if cerca and lejos:
                grupos.append((st.fmean(cerca), st.fmean(lejos)))
    out = {"vidas": len(por_vida), "candidatas_media": st.fmean(v["candidatas"] for v in por_vida) if por_vida else None,
           "repetidas_media": st.fmean(v["repetidas"] for v in por_vida) if por_vida else None,
           "fraccion_latidos_en_candidata_media": st.fmean(v["fraccion_latidos_en_candidata"] for v in por_vida) if por_vida else None,
           "vidas_con_ambos_tipos": len(grupos)}
    if len(grupos) >= 2:
        out["balance_cerca_menos_lejos"] = boot_media([a - b for a, b in grupos])
    elif grupos:
        out["balance_cerca_y_lejos"] = grupos[0]
    return out


# ---------------------------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Análisis de E2-E4 (v14)")
    sub = ap.add_subparsers(dest="orden", required=True)
    s1 = sub.add_parser("a1"); s1.add_argument("--base", required=True)
    s2 = sub.add_parser("pares"); s2.add_argument("--base", required=True); s2.add_argument("--brazo", required=True)
    s2.add_argument("--confirmar", choices=("a", "b"), default=None); s2.add_argument("--repetir-23", action="store_true")
    s3 = sub.add_parser("c"); s3.add_argument("--crafter", nargs="+", required=True)
    s3.add_argument("--ejemplo", default=None); s3.add_argument("--bosque", default=None)
    for s in (s1, s2, s3):
        s.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    if args.orden == "a1":
        res = a1(args.base)
    elif args.orden == "pares":
        res = pares(args.base, args.brazo, args.confirmar)
        if args.repetir_23:
            rb, ra = leer_brazo(args.base)[1], leer_brazo(args.brazo)[1]
            res["pasos_2_3"] = {"apagado": repetir_23(rb), "encendido": repetir_23(ra)}
            res["A-H5"] = a_h5(ra)
    else:
        cr = [leer_brazo(c)[1] for c in args.crafter]
        mundos = {"crafter": cr}
        if args.ejemplo:
            mundos["ejemplo_minimo"] = [leer_brazo(args.ejemplo)[1]]
        if args.bosque:
            mundos["bosque"] = [leer_brazo(args.bosque)[1]]
        res = {"C1": c1(cr), "C2": c2(mundos), "C3_crafter": c3(cr, "crafter")}
        if args.bosque:
            res["C3_bosque"] = c3(mundos["bosque"], "bosque")
    res = limpio(res)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
