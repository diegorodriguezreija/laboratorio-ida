"""
R1 – Verificación de la manipulación de cortisol en H2 (Crafter).

Pregunta: cuando H2 fija el cortisol a un valor (p. ej. 0,90) al principio de cada latido,
¿es ese el valor que usa el Tribunal (árbitro A0) al decidir?

Método: se envuelve A0_TribunalMotorDefault.seleccionar para registrar, en cada tick, el
cortisol del soma en el momento exacto del arbitraje, y se compara con el valor fijado.
Solo observa: no cambia ninguna decisión.

Uso:
    python analisis/verificar_manipulacion_cortisol.py --semillas 0-4 --max-pasos 200 --out salidas/R1.csv
Por defecto usa semillas de desarrollo (0-999), nunca de test ni de reserva.
"""

import argparse
import asyncio
import csv
import os
import sys
from statistics import mean

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from nivel_1_core import arbitros  # noqa: E402
from nivel_1_core.contratos import Arquetipo  # noqa: E402
from nivel_3_componentes.mundos.mundo_crafter.adaptador_crafter import AdaptadorCrafter  # noqa: E402
from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import evaluar_individuo_en_semilla  # noqa: E402
from nivel_3_componentes.rutas_salida import directorio_salidas, asegurar_directorio_de  # noqa: E402

MODOS = ["fijo_0.05", "fijo_0.30", "fijo_0.60", "fijo_0.90"]


async def medir(semillas, max_pasos):
    registro = []
    original = arbitros.A0_TribunalMotorDefault.seleccionar

    def espia(self, impulsos, soma, cosechador=None, contexto=None):
        registro.append(float(soma.cortisol))
        return original(self, impulsos, soma, cosechador, contexto)

    arbitros.A0_TribunalMotorDefault.seleccionar = espia
    filas = []
    try:
        adaptador = AdaptadorCrafter(max_pasos=max_pasos)
        adaptador.conectar()
        arq = Arquetipo(nombre="R1", responsabilidad=0.72, umbral_miedo=0.58, neuroticismo=0.30, apertura=0.60)
        for s in semillas:
            for modo in MODOS:
                fijado = float(modo.split("_")[1])
                registro.clear()
                res = await evaluar_individuo_en_semilla(
                    adaptador=adaptador, arquetipo=arq, axiomas_heredados=[], seed_mapa=s,
                    max_latidos=max_pasos, soma_modulacion=modo,
                )
                n = len(registro)
                iguales = sum(1 for c in registro if abs(c - fijado) < 1e-9)
                filas.append({
                    "semilla": s, "modo": modo, "cortisol_fijado": fijado, "arbitrajes": n,
                    "arbitrajes_con_valor_fijado": iguales,
                    "pct_con_valor_fijado": round(100.0 * iguales / n, 2) if n else "",
                    "cortisol_medio_en_arbitraje": round(mean(registro), 4) if n else "",
                    "cortisol_min": round(min(registro), 4) if n else "",
                    "cortisol_max": round(max(registro), 4) if n else "",
                    "latidos": res["latidos"], "total_logros": res["total_logros"],
                })
                print(filas[-1])
    finally:
        arbitros.A0_TribunalMotorDefault.seleccionar = original
    return filas


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--semillas", default="0-4", help="Rango de semillas de desarrollo (por defecto 0-4)")
    ap.add_argument("--max-pasos", type=int, default=200)
    ap.add_argument("--out", default=os.path.join(directorio_salidas("analisis"), "R1_manipulacion_cortisol.csv"))
    args = ap.parse_args()
    ini, fin = (int(x) for x in args.semillas.split("-"))
    filas = asyncio.run(medir(list(range(ini, fin + 1)), args.max_pasos))
    with open(asegurar_directorio_de(args.out), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"[+] {args.out}")


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    main()
