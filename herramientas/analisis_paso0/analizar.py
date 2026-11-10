"""
Análisis de la línea base del paso 0 (encargo v14, sección 2.C).

Lee las salidas de `v14.analisis_paso0.sonda` y, donde los campos existen, las grabaciones
publicadas de la v13 (`docs/episodios/*.jsonl.gz`). No ejecuta el núcleo.

    python -m v14.analisis_paso0.analizar --sonda <carpeta de la sonda> --out <resumen.json>

Imprime las tablas en Markdown y guarda todos los números en JSON.
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import math
import os
import statistics as st
import sys
from collections import Counter, defaultdict
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MUNDOS = ("ejemplo_minimo", "bosque", "crafter")
QUIETO = ("ACC_ESPERAR", "ACC_ACECHAR")
CANALES_NO_PERCEPTIVOS = ("Impulso", "Ejecucion", "Expresion")

# Reglas del Episodio según el manual (plan v14, sección 4.4)
MANUAL = {"abre_arousal": 0.65, "abre_dvit": 2.0, "abre_dali": 12.0,
          "cierra_arousal": 0.55, "cierra_dvit": 0.5, "longitud": 6}


# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------

def pct(xs: List[float], q: float) -> Optional[float]:
    if not xs:
        return None
    xs = sorted(xs)
    pos = q * (len(xs) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def resumen(xs: List[float]) -> Dict[str, Optional[float]]:
    if not xs:
        return {"n": 0}
    media = st.fmean(xs)
    sd = st.pstdev(xs) if len(xs) > 1 else 0.0
    return {"n": len(xs), "media": media, "sd": sd, "cv": (sd / media if media else None),
            "p50": pct(xs, .5), "p90": pct(xs, .9), "p95": pct(xs, .95), "max": max(xs), "min": min(xs)}


def f(x: Any, nd: int = 3) -> str:
    if x is None:
        return "—"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def leer_sonda(carpeta: str, mundo: str) -> List[Tuple[str, List[Dict[str, Any]]]]:
    eps = []
    for ruta in sorted(glob.glob(os.path.join(carpeta, f"{mundo}_*.jsonl.gz"))):
        filas = [json.loads(l) for l in gzip.open(ruta, "rt", encoding="utf-8")]
        eps.append((os.path.basename(ruta), [r for r in filas if r.get("tipo") == "latido"]))
    return eps


def leer_registro(ruta: str) -> List[Dict[str, Any]]:
    return [json.loads(l) for l in gzip.open(ruta, "rt", encoding="utf-8")]


def dormido(r: Dict[str, Any]) -> bool:
    return r.get("afecto") == "DORMIDO" or bool((r.get("mundo") or {}).get("duerme"))


def max_arousal_perceptivo(r: Dict[str, Any]) -> float:
    """Arousal máximo de la Onda sin interocepción ni canales motores (a partir de las 12 piezas de mayor arousal)."""
    return max((p["arousal"] for p in r.get("ef_top", [])
                if p["clase"] != "Interocepcion" and p["canal"] not in CANALES_NO_PERCEPTIVOS), default=0.0)


# ---------------------------------------------------------------------------
# C.1 presupuesto y latencia
# ---------------------------------------------------------------------------

def presupuesto(eps) -> Dict[str, Any]:
    filas = [r for _, fs in eps for r in fs if not dormido(r) and r["amp_max"]]
    usado = [r["amp_usada"] / r["amp_max"] for r in filas]
    tiempo = [r["ms"] / r["plazo_ms"] for r in filas]
    por_sis: Dict[str, List[float]] = defaultdict(list)
    por_comp: Dict[str, List[float]] = defaultdict(list)
    ms_comp: Dict[str, float] = defaultdict(float)
    restante_al_empezar: Dict[str, List[float]] = defaultdict(list)
    for r in filas:
        tot_sis: Dict[str, float] = defaultdict(float)
        consumido = 0
        vistos = set()
        for c in r["componentes"]:
            if c["sistema"] not in vistos:
                restante_al_empezar[c["sistema"]].append(1.0 - consumido / r["amp_max"])
                vistos.add(c["sistema"])
            consumido += c["amplitud"]
            tot_sis[c["sistema"]] += c["amplitud"]
            clave = f'{c["sistema"]}·{c["componente"]}'
            por_comp[clave].append(c["amplitud"] / r["amp_max"])
            ms_comp[clave] += c["ms"]
        for s in ("S1", "S2", "S3"):
            por_sis[s].append(tot_sis.get(s, 0.0) / r["amp_max"])
    total_ms_comp = sum(ms_comp.values()) or 1.0
    total_ms = sum(r["ms"] for r in filas) or 1.0
    return {
        "latidos_despierto": len(filas),
        "amp_max": sorted({r["amp_max"] for r in filas}),
        "plazo_ms": sorted({r["plazo_ms"] for r in filas}),
        "fraccion_amplitud_usada": resumen(usado),
        "sobrante_amplitud": resumen([1 - u for u in usado]),
        "fraccion_plazo_usada": resumen(tiempo),
        "amplitud_por_sistema_media": {s: st.fmean(v) for s, v in por_sis.items()},
        "amplitud_restante_al_empezar_sistema_media": {s: st.fmean(v) for s, v in restante_al_empezar.items()},
        "amplitud_por_componente_media": {k: st.fmean(v) for k, v in sorted(por_comp.items())},
        "tiempo_por_componente_fraccion": {k: v / total_ms_comp for k, v in sorted(ms_comp.items(), key=lambda x: -x[1])},
        "tiempo_componentes_fraccion_del_latido": total_ms_comp / total_ms,
        "latencia_ms": resumen([r["ms"] for r in filas]),
        "latencia_ms_dormido": resumen([r["ms"] for _, fs in eps for r in fs if dormido(r)]),
        "guillotinas": sum(r["guillotina"] for _, fs in eps for r in fs),
    }


def memoria(eps) -> Dict[str, Any]:
    filas = [r for _, fs in eps for r in fs]
    llamadas = Counter()
    for r in filas:
        llamadas.update(r["llamadas_memoria"])
    finales = [fs[-1]["memoria"] for _, fs in eps if fs]
    return {
        "llamadas_por_latido": {k: v / len(filas) for k, v in sorted(llamadas.items())},
        "ms_sqlite_total": sum(r["ms_sqlite"] for r in filas),
        "latidos_con_sqlite": sum(1 for r in filas if r["ms_sqlite"] > 0),
        "ms_rem_total": sum(r["ms_rem"] for r in filas),
        "latidos_rem": sum(1 for r in filas if r["ms_rem"] > 0),
        "memoria_final_media": {k: st.fmean(m[k] for m in finales) for k in finales[0]} if finales else {},
        "episodios_del_core_por_latido": (sum(m["episodios"] for m in finales) / len(filas)) if filas else None,
    }


# ---------------------------------------------------------------------------
# C.2 quieto estando saciado
# ---------------------------------------------------------------------------

def quieto_saciado_sonda(eps, mundo: str) -> Dict[str, Any]:
    filas = [r for _, fs in eps for r in fs if not dormido(r)]
    es_dormir = lambda r: r["componente_ganador"] == "Comp_CrafterS2"  # en Crafter, S2 solo propone dormir
    out = {}
    criterios = {"soma (alimentación >= 60)": lambda r: r["alimentacion"] >= 60}
    if mundo == "crafter":
        criterios["juego (comida y bebida >= 6 de 9)"] = lambda r: r["mundo"]["comida"] >= 6 and r["mundo"]["bebida"] >= 6
    for nombre, saciado in criterios.items():
        sac = [r for r in filas if saciado(r)]
        quietos = [r for r in sac if r["comando"] in QUIETO and not es_dormir(r)]
        out[nombre] = {"latidos_saciado_despierto": len(sac),
                       "quieto": len(quietos),
                       "fraccion_quieto": (len(quietos) / len(sac)) if sac else None,
                       "desglose": dict(Counter(r["comando"] for r in quietos))}
    return out


def quieto_saciado_publicados() -> Dict[str, Any]:
    out = {}
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "docs", "episodios", "*.jsonl.gz"))):
        filas = [e for e in leer_registro(ruta) if e.get("tipo") == "latido"]
        if not filas:
            continue
        despiertos = [e for e in filas if e["cuerpo"].get("estado_afectivo") != "DORMIDO"
                      and not (e.get("mundo") or {}).get("duerme")]
        nombre = os.path.basename(ruta)
        res = {}
        crit = {"soma": lambda e: (e["cuerpo"].get("alimentacion") or 0) >= 60}
        if despiertos and "comida" in (despiertos[0].get("mundo") or {}):
            crit["juego"] = lambda e: e["mundo"]["comida"] >= 6 and e["mundo"]["bebida"] >= 6
        for c, fn in crit.items():
            sac = [e for e in despiertos if fn(e)]
            q = [e for e in sac if e["decision"]["comando"] in QUIETO and e["decision"].get("objetivo") != "DORMIR"]
            res[c] = {"saciado": len(sac), "quieto": len(q), "fraccion": (len(q) / len(sac)) if sac else None}
        out[nombre] = res
    return out


# ---------------------------------------------------------------------------
# C.3 episodios fuera de línea
# ---------------------------------------------------------------------------

class Senales:
    """De dónde salen las señales del Episodio. Por defecto, las del manual (soma y Onda)."""
    arousal = staticmethod(lambda r: r["max_arousal_ev"])
    vit = staticmethod(lambda r: r["vitalidad"])
    ali = staticmethod(lambda r: r["alimentacion"])
    sorpresa_abre = True
    colapso = staticmethod(lambda r: (not r["vivo"]) or r["comando"] == "ACC_COLAPSO" or dormido(r))


class SenalesMundoCrafter(Senales):
    """Crafter con señales del mundo: el soma está saturado (ver informe), así que se usan el peligro
    externo de S1, la salud y la comida+bebida del juego, y la muerte o el sueño en el juego."""
    arousal = staticmethod(lambda r: float(r["nivel_peligro"] or 0.0))
    vit = staticmethod(lambda r: float(r["mundo"]["salud"]))
    ali = staticmethod(lambda r: float(r["mundo"]["comida"] + r["mundo"]["bebida"]))
    sorpresa_abre = False
    colapso = staticmethod(lambda r: r["mundo"]["salud"] <= 0 or bool(r["mundo"]["duerme"]))


def segmentar(filas: List[Dict[str, Any]], u: Dict[str, float], s=Senales) -> List[Dict[str, Any]]:
    eps, abierto, prev = [], None, None
    for r in filas:
        dvit = abs(s.vit(r) - s.vit(prev)) if prev else 0.0
        dali = abs(s.ali(r) - s.ali(prev)) if prev else 0.0
        a = s.arousal(r)
        sorpresa = r["sorpresa"] and s.sorpresa_abre
        if abierto is None:
            motivos = [m for m, c in (("arousal", a >= u["abre_arousal"]), ("sorpresa", sorpresa),
                                      ("vitalidad", dvit >= u["abre_dvit"]), ("alimentacion", dali >= u["abre_dali"])) if c]
            if motivos:
                base = prev or r
                abierto = {"desde": r["n"], "motivos": motivos, "filas": [], "vit0": s.vit(base), "ali0": s.ali(base)}
        if abierto is not None:
            abierto["filas"].append(r)
            calma = a < u["cierra_arousal"] and not sorpresa and dvit < u["cierra_dvit"]
            colapso = s.colapso(r)
            if calma or colapso or len(abierto["filas"]) >= u["longitud"]:
                fs = abierto.pop("filas")
                dv, da = s.vit(r) - abierto["vit0"], s.ali(r) - abierto["ali0"]
                abierto.update({
                    "hasta": r["n"], "longitud": len(fs), "cierre": "calma" if calma else ("colapso_o_sueno" if colapso else "longitud"),
                    "d_vit": dv, "d_ali": da, "balance": dv + 0.5 * da,
                    "rasgos": rasgos_episodio(fs, abierto["motivos"]),
                    "rasgos_apertura": rasgos_apertura(fs[0], abierto["motivos"]),
                })
                eps.append(abierto)
                abierto = None
        prev = r
    return eps


COMANDOS = ("ACC_MOVER", "ACC_COGER", "ACC_ESPERAR", "ACC_DEGLUTIR", "ACC_ATACAR", "ACC_ACECHAR", "ACC_SOLTAR", "ACC_ASIMILAR")


def rasgos_apertura(r: Dict[str, Any], motivos: List[str], s=None) -> List[float]:
    """Huella con lo que se sabe al ABRIR el episodio (primer latido): lo único que tendría una recuperación real."""
    v = [1.0 if m in motivos else 0.0 for m in ("arousal", "sorpresa", "vitalidad", "alimentacion")]
    v += [r["alimentacion"] / 100.0, r["vitalidad"] / 100.0, float(r["nivel_peligro"] or 0)]
    if r.get("mundo"):
        m = r["mundo"]
        v += [m["salud"] / 9.0, m["comida"] / 9.0, m["bebida"] / 9.0, m["energia"] / 9.0, float(m["luz"])]
    v += [1.0 if r["comando"] == c else 0.0 for c in COMANDOS]
    v += [1.0 if r["sistema_ganador"] == s_ else 0.0 for s_ in ("S1", "S2", "S3")]
    return v


def rasgos_episodio(fs: List[Dict[str, Any]], motivos: List[str]) -> List[float]:
    """Huella del episodio, solo con lo que se sabe al abrirlo y durante él (no el resultado)."""
    n = len(fs)
    cmd = Counter(r["comando"] for r in fs)
    sis = Counter(r["sistema_ganador"] for r in fs)
    v = [1.0 if m in motivos else 0.0 for m in ("arousal", "sorpresa", "vitalidad", "alimentacion")]
    v += [fs[0]["alimentacion"] / 100.0, fs[0]["vitalidad"] / 100.0, max(r["nivel_peligro"] or 0 for r in fs)]
    v += [cmd[c] / n for c in COMANDOS]
    v += [sis[s] / n for s in ("S1", "S2", "S3")]
    return v


def coseno(a: List[float], b: List[float]) -> float:
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0


def signo(x: float, tol: float = 0.25) -> int:
    return 0 if abs(x) <= tol else (1 if x > 0 else -1)


def parecidos(eps: List[Dict[str, Any]], umbral: float = 0.95) -> Dict[str, Any]:
    pares = list(combinations(eps, 2))
    if not pares:
        return {"pares": 0}
    sims = [(coseno(a["rasgos"], b["rasgos"]), signo(a["balance"]) == signo(b["balance"])) for a, b in pares]
    cerca = [ig for s, ig in sims if s >= umbral]
    return {"episodios": len(eps), "pares": len(pares), "umbral_coseno": umbral,
            "pares_parecidos": len(cerca), "fraccion_pares_parecidos": len(cerca) / len(pares),
            "mismo_signo_de_balance_entre_parecidos": (sum(cerca) / len(cerca)) if cerca else None,
            "mismo_signo_de_balance_entre_todos": sum(ig for _, ig in sims) / len(sims)}


def episodios(eps_mundo, mundo: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    todos_m = []
    for _, fs in eps_mundo:
        todos_m += segmentar(fs, MANUAL)
    lat = sum(len(fs) for _, fs in eps_mundo)
    out["manual"] = _resumen_eps(todos_m, lat)
    filas = [r for _, fs in eps_mundo for r in fs]
    out["distribuciones_manual"] = {
        "max_arousal_ev": resumen([r["max_arousal_ev"] for r in filas]),
        "max_arousal_perceptivo": resumen([max_arousal_perceptivo(r) for r in filas]),
        "abs_d_vitalidad_soma": resumen([abs(b["vitalidad"] - a["vitalidad"]) for _, fs in eps_mundo for a, b in zip(fs, fs[1:])]),
        "abs_d_alimentacion_soma": resumen([abs(b["alimentacion"] - a["alimentacion"]) for _, fs in eps_mundo for a, b in zip(fs, fs[1:])]),
        "fraccion_sorpresa": sum(r["sorpresa"] for r in filas) / len(filas),
        "fraccion_soma_no_vivo": sum(not r["vivo"] for r in filas) / len(filas),
    }
    if mundo == "crafter":
        # Calibración inicial con señales del mundo (unidades del juego: salud 0-9, comida+bebida 0-18).
        # Peligro externo binario (0 o 1) con el umbral que ya usa S1 (s1_reactivo.py:143).
        cal = {"abre_arousal": 0.55, "cierra_arousal": 0.55, "abre_dvit": 1.0, "abre_dali": 2.0,
               "cierra_dvit": 1.0, "longitud": 12}
        out["distribuciones_mundo"] = {
            "fraccion_peligro_externo": sum((r["nivel_peligro"] or 0) >= 0.55 for r in filas) / len(filas),
            "d_salud": dict(Counter(int(b["mundo"]["salud"] - a["mundo"]["salud"]) for _, fs in eps_mundo for a, b in zip(fs, fs[1:]))),
            "d_comida_bebida": dict(Counter(int(SenalesMundoCrafter.ali(b) - SenalesMundoCrafter.ali(a)) for _, fs in eps_mundo for a, b in zip(fs, fs[1:]))),
        }
        todos_c = []
        for nombre, fs in eps_mundo:
            for i, e in enumerate(segmentar(fs, cal, SenalesMundoCrafter)):
                e["partida"], e["orden"] = nombre, i
                todos_c.append(e)
        out["calibrado_mundo"] = {"umbrales": cal, "senales": "peligro externo de S1; salud y comida+bebida del juego; "
                                  "muerte o sueño en el juego; la sorpresa no abre", **_resumen_eps(todos_c, lat)}
        out["calibrado_mundo"]["controles_parecidos"] = parecidos_controlados(todos_c)
    return out


def parecidos_controlados(eps: List[Dict[str, Any]], umbral: float = 0.95, separacion_latidos: int = 50) -> Dict[str, Any]:
    """¿El acuerdo de signo entre episodios parecidos se debe a que sean consecutivos o de la misma partida?

    Para cada huella (completa = con lo que pasa durante el episodio; apertura = solo su primer latido)
    y cada estrato de pares, compara el acuerdo de signo entre los parecidos con el de TODOS los pares
    del mismo estrato (la línea base correcta para ese estrato).
    """
    estratos = {
        "todos": lambda a, b: True,
        "distinta_partida": lambda a, b: a["partida"] != b["partida"],
        "misma_partida_no_consecutivos": lambda a, b: a["partida"] == b["partida"] and abs(a["orden"] - b["orden"]) > 1
        and abs(a["desde"] - b["desde"]) >= separacion_latidos,
        "misma_partida_consecutivos": lambda a, b: a["partida"] == b["partida"] and abs(a["orden"] - b["orden"]) == 1,
    }
    out: Dict[str, Any] = {"umbral_coseno": umbral, "separacion_latidos": separacion_latidos}
    pares = list(combinations(eps, 2))
    for huella in ("rasgos", "rasgos_apertura"):
        sims = [(coseno(a[huella], b[huella]) >= umbral, signo(a["balance"]) == signo(b["balance"]), a, b) for a, b in pares]
        res = {}
        for nombre, cond in estratos.items():
            sub = [(p, ig) for p, ig, a, b in sims if cond(a, b)]
            cerca = [ig for p, ig in sub if p]
            res[nombre] = {"pares": len(sub), "parecidos": len(cerca),
                           "acuerdo_parecidos": (sum(cerca) / len(cerca)) if cerca else None,
                           "acuerdo_todos": (sum(ig for _, ig in sub) / len(sub)) if sub else None}
        out[huella] = res
        out[huella]["bootstrap_distinta_partida"] = bootstrap_partidas(eps, huella, umbral)
    return out


def bootstrap_partidas(eps: List[Dict[str, Any]], huella: str, umbral: float, n: int = 2000, semilla: int = 0) -> Dict[str, Any]:
    """Intervalo del 95 % (bootstrap por partidas, que son las unidades independientes) de la diferencia
    «acuerdo entre parecidos − acuerdo entre todos», solo en pares de distinta partida."""
    import numpy as np
    X = np.array([e[huella] for e in eps], dtype=float)
    X = X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-12)
    sim = X @ X.T >= umbral
    sg = np.array([signo(e["balance"]) for e in eps])
    igual = sg[:, None] == sg[None, :]
    partidas = sorted({e["partida"] for e in eps})
    pid = np.array([partidas.index(e["partida"]) for e in eps])
    idx_por = [np.where(pid == k)[0] for k in range(len(partidas))]
    rng = np.random.default_rng(semilla)

    def diferencia(eleccion) -> Optional[float]:
        filas = np.concatenate([idx_por[k] for k in eleccion])
        etiqueta = np.concatenate([[j] * len(idx_por[k]) for j, k in enumerate(eleccion)])
        cruz = etiqueta[:, None] != etiqueta[None, :]
        cruz &= ~np.eye(len(filas), dtype=bool)
        s, g = sim[np.ix_(filas, filas)] & cruz, igual[np.ix_(filas, filas)]
        if s.sum() == 0 or cruz.sum() == 0:
            return None
        return float(g[s].mean() - g[cruz].mean())

    obs = diferencia(list(range(len(partidas))))
    dif = [d for d in (diferencia(rng.integers(0, len(partidas), len(partidas))) for _ in range(n)) if d is not None]
    return {"diferencia": obs, "ic95": [float(np.percentile(dif, 2.5)), float(np.percentile(dif, 97.5))],
            "remuestreos": len(dif), "partidas": len(partidas)}


def _resumen_eps(eps: List[Dict[str, Any]], latidos: int) -> Dict[str, Any]:
    if not eps:
        return {"episodios": 0}
    dentro = sum(e["longitud"] for e in eps)
    return {
        "episodios": len(eps), "latidos": latidos, "fraccion_latidos_en_episodio": dentro / latidos,
        "longitud": resumen([e["longitud"] for e in eps]),
        "motivo_apertura": dict(Counter(m for e in eps for m in e["motivos"])),
        "cierre": dict(Counter(e["cierre"] for e in eps)),
        "balance": resumen([e["balance"] for e in eps]),
        "signo_balance": dict(Counter({1: "positivo", 0: "neutro", -1: "negativo"}[signo(e["balance"])] for e in eps)),
        "parecidos": parecidos(eps),
    }


# ---------------------------------------------------------------------------
# C.4 indicadores generales (solo observación)
# ---------------------------------------------------------------------------

def indicadores(eps) -> Dict[str, Any]:
    filas = [r for _, fs in eps for r in fs]
    pel, ten, cal = [], [], []
    por_afecto: Dict[str, List[Tuple[float, float, float]]] = defaultdict(list)
    for r in filas:
        p = float(r["urgencia_s1"] if r["urgencia_s1"] is not None else 0.0)
        t = r["amp_usada"] / r["amp_max"] if r["amp_max"] else 0.0
        c = 1.0 if dormido(r) else (1 - p) * (1 - r["cortisol"])
        pel.append(p); ten.append(t); cal.append(c)
        por_afecto[r["afecto"]].append((p, t, c))
    dominante = Counter(max((("peligro", a), ("tension", b), ("calma", c)), key=lambda x: x[1])[0]
                        for a, b, c in zip(pel, ten, cal))
    externo = [float(r["nivel_peligro"] or 0.0) for r in filas]
    return {
        "peligro_externo_fraccion_latidos": sum(x >= 0.55 for x in externo) / len(filas),
        "inanicion_soma_fraccion_latidos": sum(bool(r["inanicion"]) for r in filas) / len(filas),
        "peligro_urgencia": resumen(pel), "tension_concentracion": resumen(ten), "calma_sueno": resumen(cal),
        "correlacion": {"peligro~tension": correl(pel, ten), "peligro~calma": correl(pel, cal), "tension~calma": correl(ten, cal)},
        "dominante": {k: v / len(filas) for k, v in dominante.items()},
        "medias_por_afecto": {k: [st.fmean(x[i] for x in v) for i in range(3)] + [len(v)] for k, v in sorted(por_afecto.items())},
    }


def correl(a: List[float], b: List[float]) -> Optional[float]:
    if len(a) < 3 or st.pstdev(a) == 0 or st.pstdev(b) == 0:
        return None
    return st.correlation(a, b)


# ---------------------------------------------------------------------------
# Pregunta A.5: quién gana y la curiosidad
# ---------------------------------------------------------------------------

def ganadores(eps) -> Dict[str, Any]:
    filas = [r for _, fs in eps for r in fs]
    n = len(filas)
    s2 = [r for r in filas if r["sistema_ganador"] == "S2"]
    imp_s2 = Counter((i["comp"], i["comando"]) for r in filas for i in r["impulsos"] if "S2" in i["comp"] or i["comp"] in ("Comp_ImpulsoS2",))
    return {
        "latidos": n,
        "componente_ganador": {k: v / n for k, v in Counter(r["componente_ganador"] or "(dormido)" for r in filas).most_common()},
        "sistema_ganador": {k: v / n for k, v in Counter(r["sistema_ganador"] or "(dormido)" for r in filas).most_common()},
        "afecto": {k: v / n for k, v in Counter(r["afecto"] for r in filas).most_common()},
        "s2_gana_con": dict(Counter((r["componente_ganador"], r["comando"]) for r in s2).most_common()) and
                       {f"{a} -> {b}": c for (a, b), c in Counter((r["componente_ganador"], r["comando"]) for r in s2).most_common()},
        "impulsos_s2_propuestos": {f"{a} -> {b}": c for (a, b), c in imp_s2.most_common()},
        "curiosidad_y_gana": dict(Counter(r["componente_ganador"] for r in filas if r["afecto"] == "CURIOSIDAD")),
    }


def ganadores_publicados() -> Dict[str, Any]:
    out = {}
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "docs", "episodios", "crafter_*.jsonl.gz"))):
        filas = [e for e in leer_registro(ruta) if e.get("tipo") == "latido"]
        n = len(filas)
        out[os.path.basename(ruta)] = {
            "latidos": n,
            "sistema_ganador": {k: v / n for k, v in Counter(e["decision"]["sistema"] or "(dormido)" for e in filas).most_common()},
            "s2_gana_con": {f'{e["decision"]["componente"]} -> {e["decision"]["comando"]} ({e["decision"]["objetivo"]})': 1 for e in filas if e["decision"]["sistema"] == "S2"} and
                           dict(Counter(f'{e["decision"]["componente"]} -> {e["decision"]["comando"]} ({e["decision"]["objetivo"]})' for e in filas if e["decision"]["sistema"] == "S2")),
            "curiosidad": sum(1 for e in filas if e["cuerpo"].get("estado_afectivo") == "CURIOSIDAD"),
        }
    return out


# ---------------------------------------------------------------------------
# salida
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sonda", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    res: Dict[str, Any] = {"mundos": {}, "publicados": {}}
    for mundo in MUNDOS:
        eps = leer_sonda(args.sonda, mundo)
        if not eps:
            continue
        res["mundos"][mundo] = {
            "episodios_sonda": [n for n, _ in eps],
            "presupuesto": presupuesto(eps),
            "memoria": memoria(eps),
            "quieto_saciado": quieto_saciado_sonda(eps, mundo),
            "episodios": episodios(eps, mundo),
            "indicadores": indicadores(eps),
            "ganadores": ganadores(eps),
        }
    res["publicados"]["quieto_saciado"] = quieto_saciado_publicados()
    res["publicados"]["ganadores_crafter"] = ganadores_publicados()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    imprimir(res)
    return 0


def imprimir(res: Dict[str, Any]) -> None:
    M = res["mundos"]
    print("## Presupuesto y latencia (latidos despierto)\n")
    print("| Mundo | Plazo ms | Amplitud | Usada p50 | Usada p90 | Sobrante p50 | Plazo usado p50 | Plazo usado max | Latencia ms p50 | p95 | max | CV |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for m, d in M.items():
        p = d["presupuesto"]
        u, s, t, lat = p["fraccion_amplitud_usada"], p["sobrante_amplitud"], p["fraccion_plazo_usada"], p["latencia_ms"]
        print(f"| {m} | {p['plazo_ms']} | {p['amp_max']} | {f(u['p50'])} | {f(u['p90'])} | {f(s['p50'])} | {f(t['p50'],4)} | {f(t['max'],4)} | {f(lat['p50'],2)} | {f(lat['p95'],2)} | {f(lat['max'],2)} | {f(lat['cv'],2)} |")
    for m, d in M.items():
        p = d["presupuesto"]
        print(f"\n### {m}: reparto\n")
        print("Amplitud media gastada por Sistema (fracción del presupuesto del latido): " +
              ", ".join(f"{k} {f(v)}" for k, v in sorted(p["amplitud_por_sistema_media"].items())))
        print("Amplitud restante al empezar cada Sistema (media): " +
              ", ".join(f"{k} {f(v)}" for k, v in sorted(p["amplitud_restante_al_empezar_sistema_media"].items())))
        print(f"Tiempo en Componentes / tiempo del latido: {f(p['tiempo_componentes_fraccion_del_latido'])}")
        print("\n| Componente | Amplitud media (fracción) | Tiempo (fracción del de Componentes) |\n|---|---:|---:|")
        for k in sorted(p["amplitud_por_componente_media"], key=lambda k: -p["tiempo_por_componente_fraccion"].get(k, 0)):
            print(f"| {k} | {f(p['amplitud_por_componente_media'][k])} | {f(p['tiempo_por_componente_fraccion'].get(k), 3)} |")
    print("\n## Memoria\n")
    for m, d in M.items():
        print(f"- **{m}**: {json.dumps(d['memoria'], ensure_ascii=False)}")
    print("\n## Quieto estando saciado\n")
    for m, d in M.items():
        print(f"- **{m}** (sonda): {json.dumps(d['quieto_saciado'], ensure_ascii=False)}")
    for n, d in res["publicados"]["quieto_saciado"].items():
        print(f"- publicado {n}: {json.dumps(d, ensure_ascii=False)}")
    print("\n## Episodios fuera de línea\n")
    for m, d in M.items():
        print(f"- **{m}**: {json.dumps(d['episodios'], ensure_ascii=False, default=str)}")
    print("\n## Indicadores\n")
    for m, d in M.items():
        print(f"- **{m}**: {json.dumps(d['indicadores'], ensure_ascii=False)}")
    print("\n## Ganadores y curiosidad\n")
    for m, d in M.items():
        print(f"- **{m}**: {json.dumps(d['ganadores'], ensure_ascii=False)}")
    for n, d in res["publicados"]["ganadores_crafter"].items():
        print(f"- publicado {n}: {json.dumps(d, ensure_ascii=False)}")


if __name__ == "__main__":
    sys.exit(main())
