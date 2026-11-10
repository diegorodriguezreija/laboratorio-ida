"""
Análisis de E5 sobre los registros de `v14/experimento.py`, fuera del latido (preregistro `v14/preregistro_E5.md`).

    python -m v14.analisis_e5 d --crafter <d_crafter> --ejemplo <d_ejemplo> --bosque <d_bosque>
    python -m v14.analisis_e5 e --base <e_base> --brazo <e_carga> [--p2 <e_p2>]
    python -m v14.analisis_e5 f --base <f_base> --brazo <f_cur>
    python -m v14.analisis_e5 g --g1 <c_base 130-169> --g2 <d_crafter> <d_ejemplo> <d_bosque> --g3 <a1_base> <d_crafter>
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import random
import statistics as st
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from v14.analisis_e2e4 import (  # noqa: E402
    FRANJA, MIEDO, _fin, a1, boot_media, boot_partidas, holm, latidos, leer_brazo, limpio, pares, vigilia, wilcoxon_mayor)

UMBRAL_MARGEN = 0.05


def _q(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * (len(xs) - 1)))] if xs else None


def en_calma(e: Dict[str, Any]) -> bool:
    if e.get("mundo"):
        urg = 1.0 - min(e["mundo"]["comida"], e["mundo"]["bebida"]) / 9.0
        return e.get("peligro_juego", 0.0) < 0.35 and urg < 0.35
    ali = e["cuerpo"]["ali"]
    urg = 0.95 if ali <= 15 else max(0.0, (100.0 - ali) / 100.0)
    return e["cuerpo"]["peligro_s1"] < 0.35 and urg < 0.35


# ---------------------------------------------------------------------------------------------
# D: diagnóstico del arbitraje
# ---------------------------------------------------------------------------------------------

def d_mundo(carpeta: str) -> Dict[str, Any]:
    filas = [e for r in leer_brazo(carpeta)[1].values() for e in latidos(r) if "arbitraje" in e]
    calma = [e for e in filas if en_calma(e)]

    def stats(fs):
        n = len(fs) or 1
        gan = [e["arbitraje"]["ganador"] for e in fs]
        relleno = [e["arbitraje"]["n_candidatos"] == 0 or (g is not None and g["clase"] == "relleno") for e, g in zip(fs, gan)]
        margen = [e["arbitraje"]["margen"] for e in fs if e["arbitraje"]["margen"] is not None]
        estrecho = [e["arbitraje"]["margen"] is not None and e["arbitraje"]["margen"] < UMBRAL_MARGEN for e in fs]
        bif = sum(1 for e in fs if e["arbitraje"]["margen"] is not None and e["arbitraje"]["margen"] <= 0.03
                  and e["arbitraje"]["ganador"] and e["arbitraje"]["mejor"] and e["arbitraje"]["ganador"]["id"] != e["arbitraje"]["mejor"]["id"])
        disc = Counter(a for e in fs for a in e["arbitraje"]["discrepan_de_A0"])
        return {
            "latidos": len(fs),
            "ganador_relleno_o_sin_candidatos": sum(relleno) / n,
            "margen_menor_0_05": sum(estrecho) / n,
            "relleno_o_margen_estrecho": sum(a or b for a, b in zip(relleno, estrecho)) / n,
            "margen": {"p10": _q(margen, .1), "p25": _q(margen, .25), "p50": _q(margen, .5), "p75": _q(margen, .75), "p90": _q(margen, .9),
                       "con_un_solo_candidato": sum(1 for e in fs if e["arbitraje"]["n_candidatos"] == 1) / n},
            "ganador_por_sistema": {k: v / n for k, v in Counter((g or {}).get("sistema", "ninguno") for g in gan).most_common()},
            "ganador_por_clase": {k: v / n for k, v in Counter((g or {}).get("clase", "ninguno") for g in gan).most_common()},
            "acecho": sum(e["arbitraje"]["acecho"] for e in fs) / n,
            "bifurcacion_gana_el_segundo": bif / n,
            "arbitros_que_discrepan_de_A0": {k: v / n for k, v in sorted(disc.items())},
            "candidatos_por_latido": st.fmean(e["arbitraje"]["n_candidatos"] for e in fs) if fs else None,
        }

    out = {"todos": stats(filas), "calma": stats(calma), "fraccion_en_calma": len(calma) / (len(filas) or 1)}
    med = out["calma"]["margen"]["p50"]
    out["umbral_margen"] = {"valor": UMBRAL_MARGEN, "mediana_en_calma": med,
                            "se_mantiene": med is None or 0.005 <= med <= 0.6}
    return out


def d(args) -> Dict[str, Any]:
    res = {"crafter": d_mundo(args.crafter)}
    for nombre, c in (("ejemplo_minimo", args.ejemplo), ("bosque", args.bosque)):
        if c:
            res[nombre] = d_mundo(c)
    hay_margen = res["crafter"]["calma"]["relleno_o_margen_estrecho"] >= 0.20
    res["puerta_D3"] = {"criterio": ">= 20 % de latidos en calma con ganador de relleno o margen < 0,05",
                        "valor": res["crafter"]["calma"]["relleno_o_margen_estrecho"],
                        "punto_de_entrada_sin_nucleo": True,  # candidato nuevo de un Sistema (componente), ver D2
                        "resultado": "hay margen" if hay_margen else "no hay margen"}
    return res


# ---------------------------------------------------------------------------------------------
# E: carga falsa
# ---------------------------------------------------------------------------------------------

def descenso_por_vida(regs) -> List[Dict[str, float]]:
    out = []
    for r in regs.values():
        fs, f = latidos(r), Counter()
        for prev, e in zip(fs, fs[1:]):
            if e["cuerpo"]["afecto"] == "DORMIDO":
                continue
            if prev["cuerpo"]["carga"]:
                f["lastre"] += 0.5
            if not e["ejecutado"]:
                f["no_compensado"] += 0.8
            m0, m1 = prev.get("mundo"), e.get("mundo")
            if m0 and m1:
                f["juego"] += max(0, m0["comida"] - m1["comida"]) * 11.1 + max(0, m0["bebida"] - m1["bebida"]) * 5.5
        out.append(dict(f))
    return out


def e(args) -> Dict[str, Any]:
    res = pares(args.base, args.brazo)
    vb, rb = leer_brazo(args.base)
    va, ra = leer_brazo(args.brazo)
    vidas = descenso_por_vida(ra)
    cociente = lambda vs: sum(v.get("lastre", 0) + v.get("no_compensado", 0) for v in vs) / max(1e-9, sum(sum(v.values()) for v in vs))  # noqa: E731
    rng = random.Random(0)
    sims = sorted(cociente([rng.choice(vidas) for _ in vidas]) for _ in range(2000))
    res["E-H1"] = {"no_explicado_por_el_juego_base": cociente(descenso_por_vida(rb)), "no_explicado_por_el_juego": cociente(vidas),
                   "ic95_superior": sims[int(.95 * 2000)], "cumple": sims[int(.95 * 2000)] < 0.10}
    semillas = sorted(set(vb) & set(va))
    d_log = [(va[s]["total_logros"] or 0) - (vb[s]["total_logros"] or 0) for s in semillas]
    d_lat = [va[s]["latidos"] - vb[s]["latidos"] for s in semillas]
    margen = res["latidos"]["margen"]
    res["E-H2"] = holm({"logros>-0.5": wilcoxon_mayor([x + 0.5 for x in d_log]),
                        "latidos>-10%": wilcoxon_mayor([x - margen for x in d_lat])})
    res["E-H2"]["cumple"] = all(v["cumple"] for v in res["E-H2"].values() if isinstance(v, dict)) \
        and res["logros"]["no_inferior"] and res["latidos"]["no_inferior"]
    res["secundarias"] = {"base": _secundarias(args.base), "brazo": _secundarias(args.brazo)}
    if args.p2:
        r2 = pares(args.base, args.p2)
        res["P2_exploratorio"] = {"logros": r2["logros"], "latidos": r2["latidos"], "cuerpo": r2["cuerpo_brazo"],
                                  "secundarias": _secundarias(args.p2)}
    res["resultado"] = "recomendado" if (res["E-H1"]["cumple"] and res["E-H2"]["cumple"]) else "no recomendado"
    return res


def _secundarias(carpeta: str) -> Dict[str, Any]:
    r = a1(carpeta)
    return {"miedo": r["variables"]["miedo"]["fraccion"], "urgencia_s1_p50": r["variables"]["urgencia_s1"]["p50"],
            "urgencia_s1_extremo": r["variables"]["urgencia_s1"]["extremo"], "entropia_bits": r["entropia_bits"],
            "combinaciones": r["combinaciones_indicadores"], "alimentacion_p50": r["variables"]["alimentacion"]["p50"]}


# ---------------------------------------------------------------------------------------------
# F: curiosidad con regla nueva
# ---------------------------------------------------------------------------------------------

def f(args) -> Dict[str, Any]:
    res = pares(args.base, args.brazo, confirmar=None)
    va, ra = leer_brazo(args.brazo)
    vb, _ = leer_brazo(args.base)
    filas = [e for r in ra.values() for e in latidos(r) if "arbitraje" in e]
    gana = sum(1 for e in filas if (e["arbitraje"]["ganador"] or {}).get("id", "").startswith("impulso_curiosidad"))
    res["curiosidad_gana"] = {"latidos": len(filas), "arbitrajes_ganados": gana, "fraccion": gana / (len(filas) or 1)}
    semillas = sorted(set(vb) & set(va))
    d_log = [(va[s]["total_logros"] or 0) - (vb[s]["total_logros"] or 0) for s in semillas]
    d_lat = [va[s]["latidos"] - vb[s]["latidos"] for s in semillas]
    res["confirmatorias"] = holm({"F-H1_logros>0": wilcoxon_mayor(d_log),
                                  "F-H2_latidos>-10%": wilcoxon_mayor([x - res["latidos"]["margen"] for x in d_lat])})
    if gana == 0:
        res["resultado"] = "no ejercitada"
    else:
        ok = res["confirmatorias"]["F-H1_logros>0"]["cumple"] and res["logros"]["dif"]["ic95"][0] > 0 \
            and res["confirmatorias"]["F-H2_latidos>-10%"]["cumple"]
        res["resultado"] = "recomendado" if ok else "no recomendado"
    return res


# ---------------------------------------------------------------------------------------------
# G
# ---------------------------------------------------------------------------------------------

def _reproducir(reg, aj, clave_extra=None, ali_fn=None, sin_episodios=False):
    from v14.observador.proactiva import Proactiva
    pro = Proactiva(aj)
    cierres = defaultdict(list)
    if not sin_episodios:
        for ev in reg:
            if ev.get("tipo") == "episodio" and ev.get("cierre") != "fin":  # «fin»: lo cierra cerrar()
                cierres[ev["hasta"]].append(ev["id"])
    ultimo = None
    for ev in latidos(reg):
        p = ev.get("proactiva")
        if p is None:
            continue
        m = ev["mundo"]
        vit, ali = float(m["salud"]), (ali_fn(m) if ali_fn else float(m["comida"] + m["bebida"]))
        pro.validar(ev["n"], vit, ali, cierres.get(ev["n"], []))
        clase = p["clase_objetivo"] + (f"|{clave_extra(ev)}" if clave_extra else "")
        pro.anotar(ev["n"], ev["comando"], clase, ev["objetivo"], None if sin_episodios else p["episodio"], vit, ali, p["puede"])
        ultimo = (ev["n"], vit, ali)
    if ultimo:
        pro.validar(ultimo[0], ultimo[1], ultimo[2], [], todas=True)
    return pro


def g1(carpeta: str) -> Dict[str, Any]:
    from v14 import parametros as P
    aj = P.ajustes("crafter", P.RUTA_OBSERVACION)["proactiva"]
    regs = leer_brazo(carpeta)[1]
    out = {}
    for nombre, extra in (("clave_antigua", None), ("con_franja", lambda ev: ev["indicadores"]["franja_peligro"])):
        pros = [_reproducir(r, aj, extra) for r in regs.values()]
        grupos = [[(float(v["acierto"]), float(v["acierto_base"])) for v in p.validadas if v.get("acierto_base") is not None] for p in pros]
        val = [v for p in pros for v in p.validadas]
        calib = []
        for lo, hi in ((0, .5), (.5, .7), (.7, .9), (.9, 1.01)):
            sub = [v for v in val if lo <= v["expectativa"]["frecuencia"] < hi]
            calib.append({"frecuencia": f"[{lo}, {min(hi, 1)}]", "n": len(sub), "acierto": sum(v["acierto"] for v in sub) / len(sub) if sub else None})
        b = boot_partidas(grupos)
        out[nombre] = {"expectativas": len(val), "acierto": sum(v["acierto"] for v in val) / max(1, len(val)),
                       "base": sum(bool(v.get("acierto_base")) for v in val) / max(1, len(val)), "bootstrap": b, "calibracion": calib,
                       "demostradas": sum(1 for p in pros for x in p.eventos_demostracion if x["demostrada"]),
                       "dejan_de_estarlo": sum(1 for p in pros for x in p.eventos_demostracion if not x["demostrada"])}
    online = [[(float(v["acierto"]), float(v["acierto_base"])) for v in _fin(r)["proactiva"]["validaciones"] if v["acierto_base"] is not None] for r in regs.values()]
    out["reproduccion_identica_a_la_online"] = online == [[(float(v["acierto"]), float(v["acierto_base"])) for v in p.validadas if v.get("acierto_base") is not None]
                                                          for p in [_reproducir(r, aj) for r in regs.values()]]
    b = out["con_franja"]["bootstrap"]
    out["G1-H1"] = {"diferencia": b["diferencia"], "ic95": b["ic95"], "p_unilateral": b["p_unilateral_mayor_que_0"],
                    "cumple": b["p_unilateral_mayor_que_0"] < 0.05}
    return out


def g2(carpetas: List[str]) -> Dict[str, Any]:
    out = {}
    for c in carpetas:
        js = [json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(c, "*.creencias.json"))]
        if not js:
            continue
        mundo = os.path.basename(js[0]["partida"]).rsplit("_", 1)[0]
        durs = [x for j in js for x in j["duraciones"]]
        out[mundo] = {"vidas": len(js),
                      "al_morir_media": {k: st.fmean(j["al_morir"][k] for j in js) for k in ("demostrada", "falsada", "dudosa")},
                      "demostraciones": sum(j["demostraciones"] for j in js),
                      "demostraciones_>=20": sum(j["demostraciones_>=20_latidos"] for j in js),
                      "duracion": {"p25": _q(durs, .25), "p50": _q(durs, .5), "p75": _q(durs, .75), "max": max(durs) if durs else None}}
    return out


def g3(carpetas: List[str]) -> Dict[str, Any]:
    from v14 import parametros as P
    aj = P.ajustes("crafter", P.RUTA_OBSERVACION)["proactiva"]
    regs = {}
    for c in carpetas:
        for s, r in leer_brazo(c)[1].items():
            regs.setdefault(s, r)
    variantes = {"publicado": dict(), "bebida_peso_1": dict(ali_fn=lambda m: float(m["comida"] + 2 * m["bebida"])),
                 "inmediato_1_latido": dict(sin_episodios=True)}
    out = {"vidas": len(regs)}
    for nombre, kw in variantes.items():
        a = dict(aj, horizonte_latidos=1) if kw.get("sin_episodios") else aj
        res = defaultdict(Counter)
        for r in regs.values():
            for k, h in _reproducir(r, a, **kw).hipotesis.items():
                res[k].update(h.resultados)
        agua = res.get(("ACC_DEGLUTIR", "water"), Counter())
        resto = Counter()
        for k, c in res.items():
            if k != ("ACC_DEGLUTIR", "water"):
                resto.update(c)
        frac = lambda c: c[1] / max(1, sum(c.values()))  # noqa: E731
        out[nombre] = {"beber_agua_positivo": frac(agua), "beber_agua_n": sum(agua.values()),
                       "resto_positivo": frac(resto), "resto_n": sum(resto.values())}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Análisis de E5 (v14)")
    sub = ap.add_subparsers(dest="orden", required=True)
    sd = sub.add_parser("d"); sd.add_argument("--crafter", required=True); sd.add_argument("--ejemplo"); sd.add_argument("--bosque")
    se = sub.add_parser("e"); se.add_argument("--base", required=True); se.add_argument("--brazo", required=True); se.add_argument("--p2")
    sf = sub.add_parser("f"); sf.add_argument("--base", required=True); sf.add_argument("--brazo", required=True)
    sg = sub.add_parser("g"); sg.add_argument("--g1"); sg.add_argument("--g2", nargs="*"); sg.add_argument("--g3", nargs="*")
    for s in (sd, se, sf, sg):
        s.add_argument("--out")
    a = ap.parse_args(argv)
    if a.orden == "d":
        res = d(a)
    elif a.orden == "e":
        res = e(a)
    elif a.orden == "f":
        res = f(a)
    else:
        res = {}
        if a.g1:
            res["G1"] = g1(a.g1)
        if a.g2:
            res["G2"] = g2(a.g2)
        if a.g3:
            res["G3"] = g3(a.g3)
    res = limpio(res)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
