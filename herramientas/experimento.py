"""
Ejecutor de las mediciones de E2â€“E4 (preregistro `v14/preregistro_E2_E4.md`).

    python -m v14.experimento --brazo base --semillas 30-49 --out <carpeta>
    python -m v14.experimento --brazo cal_a --cal 0.0,1.0,4 --semillas 50-89 --out <carpeta>
    python -m v14.experimento --brazo cur_05 --peso 0.5 --semillas 90-129 --out <carpeta>
    python -m v14.experimento --brazo cur_05 --peso 0.5 --mundo ejemplo_minimo --out <carpeta>   # no ruptura

Cada partida corre con los observadores de los pasos 2 y 3 encendidos (`parametros_observacion.json`,
con `peligro_crafter = "juego"`, como fija el preregistro) y con los modificadores del brazo. Escribe
`<brazo>/<mundo>_<semilla>.jsonl.gz` (registro del observador) y aÃ±ade una lÃ­nea por partida a
`<brazo>/vidas.jsonl` (logros, latidos y costes).
"""

from __future__ import annotations

import argparse
import hashlib
import asyncio
import json
import os
import statistics as st
import sys
import time
from multiprocessing import Pool
from typing import Any, Dict, List, Optional

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)


def _pct(xs: List[float], q: float) -> Optional[float]:
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * (len(xs) - 1)))]


def _config(mundo: str, cal: Optional[List[float]], peso: Optional[float], extra: Optional[Dict[str, Any]] = None):
    from herramientas import parametros as P
    flags = P.parametros(mundo, P.RUTA_OBSERVACION)
    ajustes = P.ajustes(mundo, P.RUTA_OBSERVACION)
    ajustes["peligro_crafter"] = "juego"
    if cal is not None:
        flags["calibracion_cuerpo_crafter"] = True
        ajustes["calibracion"] = {"factor_lastre_carga": cal[0], "factor_desgaste_basal": cal[1], "alcance_peligro": cal[2]}
    if peso is not None:
        flags["curiosidad_intrinseca"] = True
        ajustes["curiosidad"] = dict(ajustes["curiosidad"], peso=peso)
    extra = extra or {}
    if extra.get("corregir_carga"):
        flags["corregir_carga_falsa_crafter"] = True
    if extra.get("carga_pesados") is not None:
        ajustes["carga_pesados"] = list(extra["carga_pesados"])
    if extra.get("regla"):
        ajustes["curiosidad"]["regla"] = extra["regla"]
    if extra.get("registrar"):
        ajustes["registrar_arbitraje"] = ajustes["creencias"] = True
    return flags, ajustes


def correr(tarea: Dict[str, Any]) -> Dict[str, Any]:
    from herramientas.analisis_paso0.episodios import EPISODIOS
    from herramientas.modificadores import modificando
    from herramientas.observador.observador import ObservadorV14, observando
    from herramientas.observar import cronometrando
    mundo, semilla, carpeta = tarea["mundo"], tarea["semilla"], tarea["carpeta"]
    flags, ajustes = _config(mundo, tarea["cal"], tarea["peso"], tarea.get("extra"))
    opciones = {"latidos": tarea["latidos"]}
    if mundo == "crafter":
        opciones["semilla"] = semilla
    nombre = f"{mundo}_{semilla}"
    lat: List[float] = []
    obs = ObservadorV14(mundo, flags, ajustes, salida=os.path.join(carpeta, f"{nombre}.jsonl.gz"), partida=nombre)
    t0 = time.perf_counter()
    with modificando(flags, ajustes) as mod, cronometrando(lat), observando(obs):
        res = asyncio.run(EPISODIOS[mundo](aislar_ruido=True, **opciones))
    r = obs.cerrar()
    cur_ms = [x for c in mod["curiosidad"] for x in c.ms]
    return {
        "semilla": semilla, "mundo": mundo, "brazo": tarea["brazo"],
        "latidos": len(res["decisiones"]), "total_logros": res.get("total_logros"), "logros": sorted(res.get("logros") or []),
        "causa_muerte": res.get("causa_muerte"),
        "decisiones_hash": hashlib.sha1("|".join(map(str, res["decisiones"])).encode()).hexdigest()[:16],
        "coste": {"latido_ms": {"p50": _pct(lat, .5), "p99": _pct(lat, .99), "max": max(lat) if lat else None},
                  "observador_ms": {"p50": _pct(r["ms_observador"], .5), "p99": _pct(r["ms_observador"], .99),
                                    "max": max(r["ms_observador"]) if r["ms_observador"] else None},
                  "mantenimiento_ms_max": max(r["ms_mantenimiento"]) if r["ms_mantenimiento"] else None,
                  "curiosidad_ms": {"p50": _pct(cur_ms, .5), "p99": _pct(cur_ms, .99), "max": max(cur_ms) if cur_ms else None,
                                    "n": len(cur_ms)},
                  "plazo_ms": max(r["plazo_ms"]) if r["plazo_ms"] else None},
        "curiosidad_propuestas": sum(c.propuestas for c in mod["curiosidad"]),
        "segundos": round(time.perf_counter() - t0, 1),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mediciones de E2-E4 (v14)")
    ap.add_argument("--brazo", required=True)
    ap.add_argument("--semillas", default="0-0")
    ap.add_argument("--mundo", default="crafter", choices=("crafter", "ejemplo_minimo", "bosque"))
    ap.add_argument("--latidos", type=int, default=None)
    ap.add_argument("--cal", default=None, help="factor_lastre_carga,factor_desgaste_basal,alcance_peligro")
    ap.add_argument("--peso", type=float, default=None)
    ap.add_argument("--corregir-carga", action="store_true", help="E5, bloque E")
    ap.add_argument("--carga-pesados", default=None, help="lista separada por comas; vacÃ­a = sin carga (E6, bloque H)")
    ap.add_argument("--regla", default=None, choices=("bajo_s1", "relleno"), help="regla de la curiosidad (E5, bloque F)")
    ap.add_argument("--registrar", action="store_true", help="registro del arbitraje y creencias (E5, D y G2)")
    ap.add_argument("--procesos", type=int, default=4)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    a, b = (int(x) for x in args.semillas.split("-"))
    latidos = args.latidos or {"crafter": 500, "ejemplo_minimo": 200, "bosque": 100}[args.mundo]
    cal = [float(x) for x in args.cal.split(",")] if args.cal else None
    carpeta = os.path.join(args.out, args.brazo)
    os.makedirs(carpeta, exist_ok=True)
    semillas = list(range(a, b + 1)) if args.mundo == "crafter" else [0]
    tareas = [{"mundo": args.mundo, "semilla": s, "carpeta": carpeta, "latidos": latidos, "cal": cal, "peso": args.peso,
               "brazo": args.brazo, "extra": {"corregir_carga": args.corregir_carga, "regla": args.regla,
                                              "carga_pesados": None if args.carga_pesados is None else [x for x in args.carga_pesados.split(",") if x],
                                              "registrar": args.registrar}} for s in semillas]
    with Pool(min(args.procesos, len(tareas))) as pool:
        vidas = pool.map(correr, tareas)
    with open(os.path.join(carpeta, "vidas.jsonl"), "a", encoding="utf-8") as f:
        for v in vidas:
            f.write(json.dumps(v, ensure_ascii=False, default=float) + "\n")
    print(f"[experimento] {args.brazo} {args.mundo} {args.semillas}: {len(vidas)} partidas; logros medios "
          f"{st.fmean(v['total_logros'] or 0 for v in vidas):.2f}; latidos medios {st.fmean(v['latidos'] for v in vidas):.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

