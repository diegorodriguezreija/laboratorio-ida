"""
Análisis de E6, fuera del latido (preregistro `v14/preregistro_E6.md`).

    python -m v14.analisis_e6 i --crafter <ij_crafter>
    python -m v14.analisis_e6 j --mundos <ij_crafter> <ij_ejemplo> <ij_bosque>
    python -m v14.analisis_e6 h --base <h_base> --brazo <h_carga>
    python -m v14.analisis_e6 k --base <k_base> --brazo <k_cur>
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import statistics as st
import sys
from collections import Counter
from typing import Any, Dict, List, Optional

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from v14.analisis_e2e4 import latidos, leer_brazo, limpio  # noqa: E402
from v14.analisis_e5 import e as analisis_e, en_calma  # noqa: E402

REJILLA = (0.01, 0.025, 0.05, 0.10, 0.126, 0.25, 0.50)
M_MAX_PUERTA = 0.126
BIFURCACION = 0.03


def ganador_a0(puntos: List[float]) -> Optional[int]:
    """Regla de A0 con la bifurcación del ruido aislado: si las dos mejores están a <= 0,03, gana la segunda."""
    if not puntos:
        return None
    orden = sorted(range(len(puntos)), key=lambda i: -puntos[i])
    if len(orden) >= 2 and puntos[orden[0]] - puntos[orden[1]] <= BIFURCACION:
        return orden[1]
    return orden[0]


# ---------------------------------------------------------------------------------------------
# I: contrafactual de la modulación
# ---------------------------------------------------------------------------------------------

def i(carpeta: str) -> Dict[str, Any]:
    regs = leer_brazo(carpeta)[1]
    dirigida, novedad = [], []  # (fila, delta por candidato, orden y signo recordados)
    for r in regs.values():
        filas = {e["n"]: e for e in latidos(r)}
        eps = {e["id"]: e for e in r if e.get("tipo") == "episodio"}
        visitas: Counter = Counter()
        for n in sorted(filas):
            e = filas[n]
            cands = (e.get("arbitraje") or {}).get("candidatos") or []
            # I2: novedad, en calma, con lo visitado ANTES de este latido
            if cands and en_calma(e):
                nodos = [c["objetivo"] for c in cands if c["objetivo"].startswith("nodo_")]
                if nodos:
                    minimo = min(visitas[x] for x in nodos)
                    marca = [1.0 if c["objetivo"].startswith("nodo_") and visitas[c["objetivo"]] == minimo else 0.0 for c in cands]
                    novedad.append((cands, marca))
            visitas[e["ubicacion"]] += 1
            # I1: recuperación del episodio parecido en este latido → modula el latido siguiente
            for rec in e.get("recuperaciones", []):
                ep = rec.get("episodio_parecido")
                if not ep or ep["coseno"] < 0.95 or abs(ep["balance"]) < 0.5 or ep["id"] not in eps:
                    continue
                rec_ep = eps[ep["id"]]
                ordenes = Counter(filas[k]["comando"] for k in range(rec_ep["desde"], rec_ep["hasta"] + 1) if k in filas)
                if not ordenes:
                    continue
                orden = ordenes.most_common(1)[0][0]
                sig = filas.get(n + 1)
                sc = ((sig or {}).get("arbitraje") or {}).get("candidatos") or []
                if sc:
                    signo = 1.0 if ep["balance"] > 0 else -1.0
                    dirigida.append((sc, [signo if c["comando"] == orden else 0.0 for c in sc], orden, signo, en_calma(sig)))

    def cambios(items, m, con_calma=None):
        sel = [x for x in items if con_calma is None or x[4] == con_calma] if items and len(items[0]) > 2 else items
        n = len(sel)
        cambia = hacia_pos = 0
        for x in sel:
            cands, delta = x[0], x[1]
            base = [c["puntuacion"] for c in cands]
            g0 = ganador_a0(base)
            g1 = ganador_a0([b + m * d for b, d in zip(base, delta)])
            if g0 != g1:
                cambia += 1
                if len(x) > 2 and x[3] > 0 and cands[g1]["comando"] == x[2]:
                    hacia_pos += 1
        return {"latidos": n, "cambia": cambia / n if n else None, "cambios": cambia, "hacia_orden_recordada_positiva": hacia_pos}

    tabla1 = {str(m): {"todos": cambios(dirigida, m), "calma": cambios(dirigida, m, True)} for m in REJILLA}
    tabla2 = {str(m): cambios(novedad, m) for m in REJILLA}
    calma_n = tabla1[str(REJILLA[0])]["calma"]["latidos"]
    base_puerta = "calma" if calma_n >= 30 else "todos"
    ok = [m for m in REJILLA if m <= M_MAX_PUERTA and (tabla1[str(m)][base_puerta]["cambia"] or 0) >= 0.10]
    llega = [m for m in REJILLA if (tabla1[str(m)][base_puerta]["cambia"] or 0) >= 0.10]
    ok2 = [m for m in REJILLA if m <= M_MAX_PUERTA and (tabla2[str(m)]["cambia"] or 0) >= 0.10]
    return {"I1_dirigida": tabla1, "I2_novedad": tabla2,
            "puerta_I": {"evaluada_sobre": base_puerta, "latidos_en_calma_con_recuperacion": calma_n,
                         "resultado": "ejercitable" if ok else "no ejercitable", "m_elegida": min(ok) if ok else None,
                         "menor_m_que_llega_al_10": min(llega) if llega else None},
            "I2_novedad_ejercitable": bool(ok2), "I2_menor_m": min(ok2) if ok2 else None}


# ---------------------------------------------------------------------------------------------
# J: contraste de las creencias del núcleo
# ---------------------------------------------------------------------------------------------

def _latido_de(evid: str) -> Optional[int]:
    try:
        return int(evid.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        return None


def j(carpetas: List[str]) -> Dict[str, Any]:
    out = {}
    for c in carpetas:
        regs = leer_brazo(c)[1]
        creencias = []
        mundo = None
        for ruta in glob.glob(os.path.join(c, "*.creencias.json")):
            d = json.load(open(ruta, encoding="utf-8"))
            sem = int(d["partida"].rsplit("_", 1)[1])
            mundo = d["partida"].rsplit("_", 1)[0]
            filas = latidos(regs[sem])
            for b in d["creencias"]:
                if not (b.get("vivo") and b["categoria"] == "demostrada"):
                    continue
                desde = next((n for n, cat in reversed(b["historial"]) if cat == "demostrada"), 0)
                ev = [x for x in (_latido_de(v) for v in b.get("evidencias", [])) if x is not None]
                opps = [k for k, e in enumerate(filas) if e["n"] > desde and e["objetivo"] == b["sujeto"]]
                contrarias = 0
                for k in opps:
                    if k + 1 < len(filas):
                        a, s = filas[k], filas[k + 1]
                        if a.get("mundo"):
                            sube = (s["mundo"]["comida"] + s["mundo"]["bebida"]) > (a["mundo"]["comida"] + a["mundo"]["bebida"])
                        else:
                            sube = s["cuerpo"]["ali"] > a["cuerpo"]["ali"]
                        contrarias += 0 if sube else 1
                camino = b["tipo"].startswith("Logica") and b.get("fuente") == "vicaria"
                creencias.append({"sujeto": b["sujeto"], "tipo": b["tipo"], "relacion": b.get("relacion", ""), "texto": b["texto"],
                                  "confianza": b["confianza"], "desde": desde, "confirmaciones": len(ev),
                                  "confirmaciones_tras": sum(1 for x in ev if x > desde), "ultima": max(ev) if ev else None,
                                  "oportunidades": len(opps), "contrarias": contrarias if b.get("relacion") == "ES_NUTRITIVO" else None,
                                  "camino_desmentido": camino, "partida": d["partida"]})
        if not creencias:
            continue
        contr = [x["confirmaciones_tras"] + x["oportunidades"] for x in creencias]
        nut = [x for x in creencias if x["contrarias"] is not None and x["oportunidades"]]
        out[mundo] = {
            "demostradas": len(creencias), "vidas": len(glob.glob(os.path.join(c, "*.creencias.json"))),
            "sin_contraste_tras_demostrarse": sum(1 for v in contr if v == 0) / len(creencias),
            "contrastes_mediana": st.median(contr), "confirmaciones_mediana": st.median(x["confirmaciones"] for x in creencias),
            "sin_camino_de_desmentido": sum(1 for x in creencias if not x["camino_desmentido"]) / len(creencias),
            "oportunidades_contrarias": (sum(x["contrarias"] for x in nut) / max(1, sum(x["oportunidades"] for x in nut))),
            "oportunidades_nutritivas": sum(x["oportunidades"] for x in nut),
            "por_relacion": dict(Counter(x["relacion"] for x in creencias).most_common()),
            "ejemplos": sorted(creencias, key=lambda x: (-x["oportunidades"], -x["confirmaciones"]))[:10],
        }
    return out


# ---------------------------------------------------------------------------------------------
# H y K
# ---------------------------------------------------------------------------------------------

def h(base: str, brazo: str) -> Dict[str, Any]:
    r = analisis_e(argparse.Namespace(base=base, brazo=brazo, p2=None))
    h1 = r["E-H1"]["cumple"]
    lim_ok = r["logros"]["no_inferior"] and r["latidos"]["no_inferior"]
    contiene_0 = r["logros"]["dif"]["ic95"][0] <= 0 <= r["logros"]["dif"]["ic95"][1] and r["latidos"]["dif"]["ic95"][0] <= 0 <= r["latidos"]["dif"]["ic95"][1]
    r["resultado"] = ("recomendado" if h1 and lim_ok else
                      ("indeterminado" if h1 and not lim_ok and contiene_0 else "no recomendado"))
    return r


def _expl(reg) -> Dict[str, Any]:
    fs = latidos(reg)
    vis = Counter(e["ubicacion"] for e in fs)
    n = sum(vis.values()) or 1
    return {"claros_distintos": len(vis), "entropia_bits": -sum((v / n) * math.log2(v / n) for v in vis.values()),
            "deglutir_ejecutado": sum(1 for e in fs if e["comando"] == "ACC_DEGLUTIR" and e["ejecutado"]),
            "gana_curiosidad": sum(1 for e in fs if ((e.get("arbitraje") or {}).get("ganador") or {}).get("id", "").startswith("impulso_curiosidad")),
            "latidos": len(fs)}


def k(base: str, brazo: str) -> Dict[str, Any]:
    vb, rb = leer_brazo(base)
    va, ra = leer_brazo(brazo)
    s = sorted(set(vb) & set(va))[0]
    eb, ea = _expl(rb[s]), _expl(ra[s])
    cambia = vb[s]["decisiones_hash"] != va[s]["decisiones_hash"]
    resultado = ("no ejercitado" if ea["gana_curiosidad"] == 0 else
                 ("ejercitado y cambia la exploración" if (ea["claros_distintos"] > eb["claros_distintos"] or ea["entropia_bits"] > eb["entropia_bits"])
                  else "ejercitado sin efecto"))
    return {"base": eb, "curiosidad": ea, "trayectoria_cambia": cambia,
            "fraccion_arbitrajes_ganados": ea["gana_curiosidad"] / (ea["latidos"] or 1), "resultado": resultado,
            "coste_curiosidad_ms": va[s]["coste"]["curiosidad_ms"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Análisis de E6 (v14)")
    sub = ap.add_subparsers(dest="orden", required=True)
    si = sub.add_parser("i"); si.add_argument("--crafter", required=True)
    sj = sub.add_parser("j"); sj.add_argument("--mundos", nargs="+", required=True)
    sh = sub.add_parser("h"); sh.add_argument("--base", required=True); sh.add_argument("--brazo", required=True)
    sk = sub.add_parser("k"); sk.add_argument("--base", required=True); sk.add_argument("--brazo", required=True)
    for s in (si, sj, sh, sk):
        s.add_argument("--out")
    a = ap.parse_args(argv)
    res = {"i": lambda: i(a.crafter), "j": lambda: j(a.mundos), "h": lambda: h(a.base, a.brazo),
           "k": lambda: k(a.base, a.brazo)}[a.orden]()
    res = limpio(res)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
