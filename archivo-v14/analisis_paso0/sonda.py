"""
Sonda de solo lectura para la línea base del paso 0 (encargo v14, sección 2.C).

El registro de latidos de la v13 no guarda la latencia, el arousal máximo de la Onda ni el
reparto del presupuesto por Componente. Esta sonda los mide con el mismo método que N5 y que
`escaparate.registro_latido.grabando`: envuelve métodos durante el episodio, sin cambiar ningún
fichero del núcleo, y los restaura al salir. Lee la Onda y el soma, nunca escribe en ellos.

Antes de guardar nada comprueba que la trayectoria de cada episodio es idéntica con y sin sonda
(mismo criterio que E-1). Si no lo es, se detiene.

    python -m v14.analisis_paso0.sonda --out-dir <carpeta>      # Crafter 0-9, ejemplo mínimo y Bosque

Salida: un `<mundo>_<semilla>.jsonl.gz` por episodio, una fila por latido.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import gzip
import json
import os
import sys
import time
from collections import Counter
from typing import Any, Dict, List, Optional

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from nivel_1_core.gestor_onda import GestorOndaCore  # noqa: E402
from nivel_1_core.persistencia.memoria_tridimensional import DimensionActiva  # noqa: E402
from nivel_1_core.persistencia.motor_sqlite_wal import MotorSQLiteWAL  # noqa: E402
from nivel_2_sistemas.ciclo_sueno_rem import GestorCicloSuenoREM  # noqa: E402
from nivel_2_sistemas.sistema_base import SistemaCognitivoTriunico  # noqa: E402
from v14.analisis_paso0.episodios import EPISODIOS, jugador_crafter  # noqa: E402


class _Estado:
    """Acumuladores del latido en curso (se vacían al empezar cada latido)."""

    def __init__(self) -> None:
        self.filas: List[Dict[str, Any]] = []
        self.mundo: Optional[str] = None
        self.reset()

    def reset(self) -> None:
        self.componentes: List[Dict[str, Any]] = []
        self.llamadas: Counter = Counter()
        self.ms_sqlite = 0.0
        self.ms_rem = 0.0


@contextlib.contextmanager
def sondeando(estado: _Estado):
    originales = []

    def poner(cls, nombre, nuevo):
        originales.append((cls, nombre, cls.__dict__[nombre]))
        setattr(cls, nombre, nuevo)

    barridos = SistemaCognitivoTriunico.__dict__["_ejecutar_tres_barridos"].__func__

    async def barridos_medidos(comp, onda, ctx):
        a0, t0 = onda.amplitud_consumida, time.perf_counter()
        try:
            await barridos(comp, onda, ctx)
        finally:
            estado.componentes.append({
                "sistema": comp.sistema, "componente": comp.id_componente,
                "ms": (time.perf_counter() - t0) * 1000.0, "amplitud": onda.amplitud_consumida - a0,
            })

    poner(SistemaCognitivoTriunico, "_ejecutar_tres_barridos", staticmethod(barridos_medidos))

    latido = GestorOndaCore.__dict__["ejecutar_latido"]

    async def latido_medido(self, *a, **k):
        estado.reset()
        t0 = time.perf_counter()
        onda = await latido(self, *a, **k)
        ms = (time.perf_counter() - t0) * 1000.0
        estado.filas.append(_fila(self, onda, ms, estado))
        return onda

    poner(GestorOndaCore, "ejecutar_latido", latido_medido)

    for nombre in ("consolidar_pieza", "obtener_pieza", "verificar_hipotesis_empirica", "registrar_enlace_causal",
                   "registrar_transicion_topologica", "registrar_hito_alocentrico", "consultar_hitos_alocentricos"):
        original = DimensionActiva.__dict__[nombre]

        def contado(*a, _o=original, _n=nombre, **k):
            estado.llamadas[_n] += 1
            return _o(*a, **k)

        poner(DimensionActiva, nombre, contado)

    sinc = MotorSQLiteWAL.__dict__["sincronizar_desde_activa"]

    def sinc_medido(self, activa):
        t0 = time.perf_counter()
        try:
            return sinc(self, activa)
        finally:
            estado.ms_sqlite += (time.perf_counter() - t0) * 1000.0

    poner(MotorSQLiteWAL, "sincronizar_desde_activa", sinc_medido)

    rem = GestorCicloSuenoREM.__dict__["procesar_sueno_rem"]

    def rem_medido(self, *a, **k):
        t0 = time.perf_counter()
        try:
            return rem(self, *a, **k)
        finally:
            estado.ms_rem += (time.perf_counter() - t0) * 1000.0

    poner(GestorCicloSuenoREM, "procesar_sueno_rem", rem_medido)
    try:
        yield estado
    finally:
        for cls, nombre, original in reversed(originales):
            setattr(cls, nombre, original)


def _num(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _fila(core: Any, onda: Any, ms: float, estado: _Estado) -> Dict[str, Any]:
    soma = core.soma
    ev = onda.reactiva.ev
    piezas_ev = [(canal, p) for canal, d in ev.items() for p in d.values()]
    max_ar = max((p.arousal for _, p in piezas_ev), default=0.0)
    sup = ev.get("Supervivencia", {}).get("Alarma_Supervivencia")
    ejec = onda.reactiva.ef.get("Ejecucion", {}).get("Ejecucion")
    # Piezas de la Onda (ef) con su arousal, clase y sistemas: lo que el Core podría guardar (top 12)
    piezas_ef = sorted(
        ((p.arousal, str(p.tipo_componente), str(p.id), sorted(p.sistemas_participantes), canal)
         for canal, d in onda.reactiva.ef.items() for p in d.values()),
        key=lambda x: -x[0])
    fila = {
        "n": onda.ciclo,
        "ms": round(ms, 4),
        "plazo_ms": onda.frecuencia_max_ms,
        "amp_max": onda.amplitud_max,
        "amp_usada": onda.amplitud_consumida,
        "guillotina": bool(onda.guillotina_disparada),
        "componentes": [{**c, "ms": round(c["ms"], 4)} for c in estado.componentes],
        "max_arousal_ev": round(max_ar, 4),
        "sorpresa": "Sorpresa" in ev,
        "urgencia_s1": round(sup.arousal, 4) if sup else None,
        "nivel_peligro": _num(sup.product.get("nivel_peligro")) if sup else None,
        "inanicion": bool(sup.product.get("inanicion_critica")) if sup else None,
        "vitalidad": round(soma.vitalidad, 4),
        "alimentacion": round(soma.alimentacion, 4),
        "energia": round(soma.energia, 4),
        "descanso": round(soma.descanso, 4),
        "cortisol": round(soma.cortisol, 4),
        "afecto": str(soma.estado_afectivo),
        "vivo": bool(soma.esta_vivo),
        "comando": str(ejec.product.get("comando")) if ejec else "ACC_ESPERAR",
        "comando_latente": str(ejec.product.get("comando_latente", "")) if ejec else "",
        "sistema_ganador": str(onda.metricas.get("sistema_ganador", "")),
        "componente_ganador": str(onda.metricas.get("componente_ganador", "")),
        "impulsos": [{"comp": str(p.product.get("id_componente", "")), "comando": str(p.product.get("comando", "")),
                      "arousal": round(p.arousal, 4)} for p in onda.reactiva.acc.get("Impulso", {}).values()],
        "ev_por_canal": {c: len(d) for c, d in ev.items()},
        "ef_total": sum(len(d) for d in onda.reactiva.ef.values()),
        "ef_top": [{"arousal": round(a, 4), "clase": t, "id": i, "sistemas": s, "canal": c} for a, t, i, s, c in piezas_ef[:12]],
        "llamadas_memoria": dict(estado.llamadas),
        "ms_sqlite": round(estado.ms_sqlite, 4),
        "ms_rem": round(estado.ms_rem, 4),
        "memoria": {
            "identidad": sum(len(c) for c in core.activa.indice_identidad.values()),
            "episodios": len(core.activa.banco_episodico),
            "causales": sum(len(v) for v in core.activa.indice_causal.values()),
            "hitos": sum(len(v) for v in core.activa.mapa_alocentrico.values()),
            "expectativas": len(core.proactiva.expectativas),
        },
    }
    if estado.mundo == "crafter":
        fila["mundo"] = jugador_crafter(core)
    return fila


def episodio(mundo: str, opciones: Dict[str, Any]) -> Dict[str, Any]:
    """Ejecuta el episodio sin sonda y con sonda; exige la misma trayectoria."""
    sin = asyncio.run(EPISODIOS[mundo](aislar_ruido=True, **opciones))
    estado = _Estado()
    estado.mundo = mundo
    with sondeando(estado):
        con = asyncio.run(EPISODIOS[mundo](aislar_ruido=True, **opciones))
    if sin["decisiones"] != con["decisiones"]:
        raise SystemExit(f"[sonda] {mundo} {opciones}: la trayectoria cambia con la sonda. Se detiene.")
    return {"filas": estado.filas, "res": con}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Sonda de solo lectura del paso 0 de la v14")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--semillas-crafter", default="0-9")
    ap.add_argument("--latidos-crafter", type=int, default=500)
    ap.add_argument("--latidos-ejemplo", type=int, default=200)
    ap.add_argument("--latidos-bosque", type=int, default=100)
    args = ap.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)

    a, b = (int(x) for x in args.semillas_crafter.split("-"))
    trabajos = [("ejemplo_minimo", "unico", {"latidos": args.latidos_ejemplo}),
                ("bosque", "unico", {"latidos": args.latidos_bosque})]
    trabajos += [("crafter", str(s), {"latidos": args.latidos_crafter, "semilla": s}) for s in range(a, b + 1)]

    for mundo, etiqueta, opciones in trabajos:
        t0 = time.perf_counter()
        r = episodio(mundo, opciones)
        ruta = os.path.join(args.out_dir, f"{mundo}_{etiqueta}.jsonl.gz")
        with gzip.open(ruta, "wt", encoding="utf-8") as f:
            resumen = {k: v for k, v in r["res"].items() if k != "decisiones"}
            f.write(json.dumps({"tipo": "cabecera", "mundo": mundo, "opciones": opciones, "resumen": resumen,
                                "trayectoria_identica_sin_sonda": True}, ensure_ascii=False) + "\n")
            for fila in r["filas"]:
                f.write(json.dumps({"tipo": "latido", **fila}, ensure_ascii=False) + "\n")
        print(f"[sonda] {mundo} {etiqueta}: {len(r['filas'])} latidos, trayectoria idéntica sin sonda "
              f"({time.perf_counter() - t0:.1f} s) -> {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
