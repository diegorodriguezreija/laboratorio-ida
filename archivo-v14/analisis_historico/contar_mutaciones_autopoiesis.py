"""
P-3 – ¿Cuántas mutaciones de autopoiesis hubo en la configuración anterior?

Las cifras de la fase de diagnóstico (analisis/resultados/diagnostico/) se midieron con la
autopoiesis AST activa. Este script repite el protocolo H1 de Crafter (mismos árbitros, mismo
arquetipo, 500 pasos, nivel_a) sobre las mismas semillas de diagnóstico con
habilitar_autopoiesis=True y cuenta mutaciones y rollbacks por episodio.

Con ruido físico activo no reproduce cada trayectoria exacta: estima la frecuencia de mutación.

    python analisis/contar_mutaciones_autopoiesis.py --semillas 2020-2059 --out salidas/P3_mutaciones.csv
"""

import argparse
import asyncio
import csv
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from nivel_1_core.arbitros import crear_arbitro  # noqa: E402
from nivel_1_core.contratos import Arquetipo  # noqa: E402
from nivel_3_componentes.mundos.mundo_crafter.adaptador_crafter import AdaptadorCrafter  # noqa: E402
from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import evaluar_individuo_en_semilla  # noqa: E402
from nivel_3_componentes.rutas_salida import asegurar_directorio_de, directorio_salidas  # noqa: E402

ARBITROS_H1 = ["A0", "A1", "A2", "A3", "A4", "A7"]


async def medir(semillas):
    ad = AdaptadorCrafter(max_pasos=500)
    ad.conectar()
    arq = Arquetipo(nombre="Hominis_Test_H1", responsabilidad=0.72, umbral_miedo=0.58, neuroticismo=0.30, apertura=0.60)
    filas = []
    for s in semillas:
        for aid in ARBITROS_H1:
            arb = crear_arbitro(aid, seed_propia=s + 500) if aid == "A4" else crear_arbitro(aid)
            res = await evaluar_individuo_en_semilla(
                adaptador=ad, arquetipo=arq, axiomas_heredados=[], seed_mapa=s, max_latidos=500,
                arbitro=arb, modo_ablacion="nivel_a", habilitar_autopoiesis=True,
            )
            filas.append({"semilla": s, "arbitro_id": aid, "latidos": res["latidos"], "total_logros": res["total_logros"],
                          "mutaciones_autopoiesis": res["mutaciones_autopoiesis"], "rollbacks_autopoiesis": res["rollbacks_autopoiesis"]})
        print(f"semilla {s}: mutaciones={sum(f['mutaciones_autopoiesis'] for f in filas if f['semilla'] == s)}", flush=True)
    return filas


def main():
    ap = argparse.ArgumentParser(description="Cuenta mutaciones de autopoiesis en la configuración previa de H1")
    ap.add_argument("--semillas", default="2020-2059")
    ap.add_argument("--out", default=os.path.join(directorio_salidas("analisis"), "P3_mutaciones_autopoiesis.csv"))
    args = ap.parse_args()
    ini, fin = (int(x) for x in args.semillas.split("-"))
    filas = asyncio.run(medir(list(range(ini, fin + 1))))
    with open(asegurar_directorio_de(args.out), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    n = len(filas)
    con = sum(1 for f in filas if f["mutaciones_autopoiesis"] > 0)
    print(f"[+] {n} episodios; con al menos una mutación: {con}; mutaciones totales: {sum(f['mutaciones_autopoiesis'] for f in filas)}; "
          f"rollbacks: {sum(f['rollbacks_autopoiesis'] for f in filas)} -> {args.out}")


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    main()
