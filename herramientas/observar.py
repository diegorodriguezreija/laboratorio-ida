"""
Mide los pasos 2 y 3 de la v14 con el observador encendido (solo observaciÃ³n).

    python -m v14.observar --out-dir <carpeta>                       # Crafter 10-29, ejemplo mÃ­nimo y Bosque
    python -m v14.observar --out-dir <carpeta> --semillas-crafter 10-12

Lee los flags y ajustes de `v14/parametros_observacion.json` (o `--parametros`). Un mundo con
`observar_activa` y `observar_proactiva` apagados y memoria Â«apagadaÂ» no se observa.

Cada episodio se ejecuta dos veces: sin observador (solo se cronometra el latido) y con Ã©l. Si las
decisiones difieren, se detiene: un observador no puede cambiar la trayectoria (tope duro).
Salidas: un `<mundo>_<semilla>.jsonl.gz` por episodio, `biografias/*.md`, `resumen_observacion.json`
y `resumen_observacion.md`.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import statistics as st
import sys
import time
from typing import Any, Dict, List, Optional

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from herramientas import parametros as P  # noqa: E402
from herramientas.analisis_paso0.episodios import EPISODIOS  # noqa: E402
from herramientas.observador.observador import ObservadorV14, observando  # noqa: E402


@contextlib.contextmanager
def cronometrando(lista: List[float]):
    """Solo mide la duraciÃ³n de cada latido (para la latencia de referencia sin observador)."""
    from nivel_1_core.gestor_onda import GestorOndaCore
    original = GestorOndaCore.__dict__["ejecutar_latido"]

    async def medido(self, *a, **k):
        t0 = time.perf_counter()
        onda = await original(self, *a, **k)
        lista.append((time.perf_counter() - t0) * 1000.0)
        return onda

    GestorOndaCore.ejecutar_latido = medido
    try:
        yield
    finally:
        GestorOndaCore.ejecutar_latido = original


def pct(xs: List[float], q: float) -> Optional[float]:
    if not xs:
        return None
    xs = sorted(xs)
    i = q * (len(xs) - 1)
    lo, hi = int(i), min(len(xs) - 1, int(i) + 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def episodio(mundo: str, opciones: Dict[str, Any], flags: Dict[str, Any], ajustes: Dict[str, Any],
             salida: Optional[str], partida: str) -> Dict[str, Any]:
    lat_base: List[float] = []
    with cronometrando(lat_base):
        sin = asyncio.run(EPISODIOS[mundo](aislar_ruido=True, **opciones))
    obs = ObservadorV14(mundo, flags, ajustes, salida=salida, partida=partida)
    with observando(obs):
        con = asyncio.run(EPISODIOS[mundo](aislar_ruido=True, **opciones))
    res = obs.cerrar()
    if sin["decisiones"] != con["decisiones"]:
        raise SystemExit(f"[observar] {mundo} {opciones}: la trayectoria cambia con el observador. TOPE DURO: se detiene.")
    res["latencia_base_ms"] = lat_base
    res["juego"] = {k: v for k, v in con.items() if k != "decisiones"}
    return res


def biografia(nombre: str, res: Dict[str, Any]) -> str:
    pro = res["proactiva"]
    lineas = [f"# {nombre}: lo que anticipÃ³", ""]
    if not pro["validadas"]:
        lineas.append(f"{nombre} no llegÃ³ a anticipar nada: sus acciones aÃºn no tenÃ­an resultado conocido.")
        return "\n".join(lineas) + "\n"
    lineas.append(f"{nombre} anotÃ³ {pro['creadas']} expectativas y {pro['validadas']} se pudieron comprobar: "
                  f"acertÃ³ {pro['aciertos']} ({100.0 * pro['aciertos'] / pro['validadas']:.0f} %).")
    dem = [d for d in pro["demostraciones"] if d["demostrada"]]
    perd = [d for d in pro["demostraciones"] if not d["demostrada"]]
    if dem:
        lineas += ["", "Lo que la experiencia le demostrÃ³:", ""]
        lineas += [f"- Latido {d['n']}: Â«{d['frase']}Â» (confianza {d['confianza']:.2f})." for d in dem]
    if perd:
        lineas += ["", "Lo que dejÃ³ de darse por demostrado al fallar:", ""]
        lineas += [f"- Latido {d['n']}: Â«{d['frase']}Â»." for d in perd]
    lineas += ["", "Son frases del observador de la v14: no cambiaron ninguna decisiÃ³n."]
    return "\n".join(lineas) + "\n"


def bootstrap_partidas(grupos: List[List[tuple]], n: int = 2000, semilla: int = 0) -> Dict[str, Any]:
    """Diferencia media (acierto âˆ’ base) remuestreando partidas, que son las unidades independientes.
    Cada grupo es la lista de pares (acierto, acierto_base) de una partida."""
    import random
    grupos = [g for g in grupos if g]
    if not grupos:
        return {"partidas": 0}

    def dif(sel):
        pares = [p for g in sel for p in g]
        return sum(a for a, _ in pares) / len(pares) - sum(b for _, b in pares) / len(pares)

    rng = random.Random(semilla)
    obs = dif(grupos)
    if len(grupos) < 2:
        return {"partidas": 1, "diferencia": obs, "ic95": None}
    sims = sorted(dif([rng.choice(grupos) for _ in grupos]) for _ in range(n))
    return {"partidas": len(grupos), "pares": sum(len(g) for g in grupos), "diferencia": obs,
            "ic95": [sims[int(0.025 * n)], sims[int(0.975 * n) - 1]]}


def agregar(mundo: str, eps: List[Dict[str, Any]], ajustes: Dict[str, Any]) -> Dict[str, Any]:
    ms = [x for r in eps for x in r["ms_observador"]]
    base = [x for r in eps for x in r["latencia_base_ms"]]
    plazo = max(p for r in eps for p in r["plazo_ms"])
    t = ajustes["tope_coste"]
    tope_lat = t["fraccion_latencia"] * (pct(base, .5) or 0.0)
    tope_plazo = t["fraccion_plazo"] * plazo
    tope = min(tope_lat, tope_plazo)
    pred = [x for r in eps for x in r["episodios_predichos"]]
    con_base = [x for x in pred if x["base_misma_vida"] is not None]
    val = [x for r in eps for x in r["proactiva"]["validaciones"]]
    bins = [(0.0, 0.5), (0.5, 0.7), (0.7, 0.9), (0.9, 1.01)]
    calib = []
    for lo, hi in bins:
        sub = [v for v in val if lo <= v["frecuencia"] < hi]
        calib.append({"frecuencia": f"[{lo:.1f}, {min(hi, 1.0):.1f}]", "n": len(sub),
                      "frecuencia_media": (st.fmean(v["frecuencia"] for v in sub) if sub else None),
                      "acierto": (sum(v["acierto"] for v in sub) / len(sub)) if sub else None})
    edades = sorted(v["edad"] for v in val)
    cortes = [pct(edades, 1 / 3), pct(edades, 2 / 3)] if edades else []
    por_edad = []
    if edades:
        tramos = [(None, cortes[0]), (cortes[0], cortes[1]), (cortes[1], None)]
        for lo, hi in tramos:
            sub = [v for v in val if (lo is None or v["edad"] > lo) and (hi is None or v["edad"] <= hi)]
            por_edad.append({"latidos": f"({lo}, {hi}]", "n": len(sub), "acierto": (sum(v["acierto"] for v in sub) / len(sub)) if sub else None})
    ind = [x for r in eps for x in r["indicadores"]]
    s3 = {k: sum(r["s3_existente"][k] for r in eps) for k in ("proyectadas", "consumidas", "sorpresas")}
    s3["abiertas_al_final_media"] = st.fmean(r["s3_existente"]["abiertas_final"] for r in eps)
    s3["fraccion_consumidas"] = s3["consumidas"] / s3["proyectadas"] if s3["proyectadas"] else None
    guard = {k: sum(r["guardadas"][k] for r in eps) for k in ("Core", "S1", "S2", "S3")}
    clases: Dict[str, int] = {}
    for r in eps:
        for k, v in r["clases_guardadas"].items():
            clases[k] = clases.get(k, 0) + v
    epis = [e for r in eps for e in r["episodios"]]
    return {
        "mundo": mundo, "episodios_juego": len(eps), "latidos": sum(r["latidos"] for r in eps),
        "coste": {"observador_ms": {"p50": pct(ms, .5), "p95": pct(ms, .95), "max": max(ms) if ms else None},
                  "latencia_base_ms": {"p50": pct(base, .5), "p95": pct(base, .95)}, "plazo_ms": plazo,
                  "tope_5pc_latencia_ms": tope_lat, "tope_1pc_plazo_ms": tope_plazo, "tope_ms": tope,
                  "p50_dentro_del_tope": (pct(ms, .5) or 0) <= tope, "p95_dentro_del_tope": (pct(ms, .95) or 0) <= tope,
                  "fraccion_latidos_sobre_tope": (sum(x > tope for x in ms) / len(ms)) if ms else None,
                  "mantenimiento_ms": {"n": sum(len(r["ms_mantenimiento"]) for r in eps),
                                       "p50": pct([x for r in eps for x in r["ms_mantenimiento"]], .5),
                                       "max": max((x for r in eps for x in r["ms_mantenimiento"]), default=None)}},
        "memoria": {"guardadas": guard, "descartadas_presupuesto": sum(r["descartadas_presupuesto"] for r in eps),
                    "clases_guardadas": dict(sorted(clases.items(), key=lambda kv: -kv[1])),
                    "registros_final_media": st.fmean(r["almacen"]["registros"] for r in eps),
                    "olvidados_media": st.fmean(r["almacen"]["olvidados_total"] for r in eps),
                    "episodios_almacen_final_media": st.fmean(r["almacen"]["episodios"] for r in eps),
                    "uso_virtual_medio": {k: st.fmean(r["uso_virtual_medio"][k] for r in eps) for k in ("S1", "S2", "S3")}},
        "episodios": {"n": len(epis), "longitud_media": st.fmean(e["longitud"] for e in epis) if epis else None,
                      "signo": {str(k): sum(1 for e in epis if e["signo"] == k) for k in (1, 0, -1)}},
        "activa": {"recuperaciones": sum(r["recuperaciones"] for r in eps),
                   "piezas_validadas": sum(r["recuperaciones_validadas"] for r in eps),
                   "piezas_acierto": (sum((r["recuperaciones_acierto"] or 0) * r["recuperaciones_validadas"] for r in eps)
                                      / max(1, sum(r["recuperaciones_validadas"] for r in eps))),
                   "episodios_predichos": len(pred),
                   "episodios_acierto": (sum(x["acierto"] for x in pred) / len(pred)) if pred else None,
                   "episodios_base_misma_vida": (st.fmean(x["base_misma_vida"] for x in con_base)) if con_base else None,
                   "episodios_acierto_con_base": (sum(x["acierto"] for x in con_base) / len(con_base)) if con_base else None,
                   "n_con_base": len(con_base),
                   "episodios_bootstrap": bootstrap_partidas(
                       [[(float(x["acierto"]), x["base_misma_vida"]) for x in r["episodios_predichos"] if x["base_misma_vida"] is not None]
                        for r in eps])},
        "proactiva": {"creadas": sum(r["proactiva"]["creadas"] for r in eps),
                      "validadas": len(val), "acierto": (sum(v["acierto"] for v in val) / len(val)) if val else None,
                      "acierto_base_mas_frecuente": (sum(bool(v["acierto_base"]) for v in val if v["acierto_base"] is not None)
                                                     / max(1, sum(1 for v in val if v["acierto_base"] is not None))),
                      "bootstrap_frente_a_base": bootstrap_partidas(
                          [[(float(v["acierto"]), float(v["acierto_base"])) for v in r["proactiva"]["validaciones"] if v["acierto_base"] is not None]
                           for r in eps]),
                      "acciones_mas_frecuentes": dict(sorted(
                          {f"{a}|{c}": sum(1 for v in val if v["clave"] == [a, c]) for a, c in {tuple(v["clave"]) for v in val}}.items(),
                          key=lambda kv: -kv[1])[:10]),
                      "sin_hipotesis": sum(r["proactiva"]["sin_hipotesis"] for r in eps),
                      "omitidas_por_tope": sum(r["proactiva"]["omitidas_por_tope"] for r in eps),
                      "max_abiertas": max(r["proactiva"]["max_abiertas"] for r in eps),
                      "max_pendientes": max(r["proactiva"]["max_pendientes"] for r in eps),
                      "pendientes_al_final": sum(r["proactiva"]["pendientes_al_final"] for r in eps),
                      "validadas_por": {m: sum(1 for v in val if v["motivo"] == m) for m in ("episodio", "horizonte", "fin")},
                      "calibracion": calib, "por_edad": por_edad,
                      "demostradas": sum(1 for r in eps for d in r["proactiva"]["demostraciones"] if d["demostrada"]),
                      "dejan_de_estar_demostradas": sum(1 for r in eps for d in r["proactiva"]["demostraciones"] if not d["demostrada"]),
                      "ejemplos_demostradas": sorted({d["frase"] for r in eps for d in r["proactiva"]["demostraciones"] if d["demostrada"]})[:12]},
        "s3_existente": s3,
        "indicadores": {k: {"p10": pct([i[k] for i in ind], .1), "p50": pct([i[k] for i in ind], .5), "p90": pct([i[k] for i in ind], .9)}
                        for k in ("peligro", "tension", "calma")} if ind else {},
        "franja_peligro": {f: sum(1 for i in ind if i["franja_peligro"] == f) / len(ind) for f in ("baja", "media", "alta")} if ind else {},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mide los pasos 2 y 3 de la v14 (solo observaciÃ³n)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--parametros", default=P.RUTA_OBSERVACION)
    ap.add_argument("--semillas-crafter", default="10-29")
    ap.add_argument("--latidos-crafter", type=int, default=500)
    ap.add_argument("--latidos-ejemplo", type=int, default=200)
    ap.add_argument("--latidos-bosque", type=int, default=100)
    args = ap.parse_args(argv)
    os.makedirs(os.path.join(args.out_dir, "biografias"), exist_ok=True)
    a, b = (int(x) for x in args.semillas_crafter.split("-"))
    trabajos = [("ejemplo_minimo", "unico", {"latidos": args.latidos_ejemplo}),
                ("bosque", "unico", {"latidos": args.latidos_bosque})]
    trabajos += [("crafter", str(s), {"latidos": args.latidos_crafter, "semilla": s}) for s in range(a, b + 1)]
    por_mundo: Dict[str, List[Dict[str, Any]]] = {}
    for mundo, etiqueta, opciones in trabajos:
        flags = P.parametros(mundo, args.parametros)
        ajustes = P.ajustes(mundo, args.parametros)
        if flags["memoria_experiencia"] == "apagada" and not (flags["observar_activa"] or flags["observar_proactiva"]):
            print(f"[observar] {mundo}: observadores apagados en {os.path.basename(args.parametros)}; no se observa")
            continue
        t0 = time.perf_counter()
        nombre = f"{mundo}_{etiqueta}"
        res = episodio(mundo, opciones, flags, ajustes, os.path.join(args.out_dir, f"{nombre}.jsonl.gz"), nombre)
        with open(os.path.join(args.out_dir, "biografias", f"{nombre}.md"), "w", encoding="utf-8") as f:
            f.write(biografia(f"Individuo {nombre}", res))
        por_mundo.setdefault(mundo, []).append(res)
        print(f"[observar] {nombre}: {res['latidos']} latidos, trayectoria idÃ©ntica sin observador, "
              f"observador p50 {pct(res['ms_observador'], .5):.3f} ms ({time.perf_counter() - t0:.1f} s)")
    resumen = {m: agregar(m, eps, P.ajustes(m, args.parametros)) for m, eps in por_mundo.items()}
    with open(os.path.join(args.out_dir, "resumen_observacion.json"), "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=1, default=float)
    print(json.dumps(resumen, ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())

