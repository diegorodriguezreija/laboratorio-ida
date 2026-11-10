"""
Coste de adaptación por mundo: ficheros Python y líneas de código (sin líneas en blanco ni
comentarios de línea completa) de cada carpeta de nivel 3, separando adaptador, componentes
de dominio y runner/herramientas.

Los cambios en los niveles 1 y 2 al integrar cada mundo no se pueden reconstruir con el
historial disponible (el repositorio original integró varios mundos en un solo commit), salvo
para el mundo de ejemplo mínimo, añadido en este repositorio sin tocar los niveles 1 y 2
(ver git log de nivel_3_componentes/mundos/mundo_ejemplo_minimo).

    python analisis/coste_adaptacion.py --out analisis/resultados/coste_adaptacion.csv
"""

import argparse
import csv
import os
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MUNDOS = RAIZ / "nivel_3_componentes" / "mundos"


def lineas_codigo(p: pathlib.Path) -> int:
    n = 0
    en_docstring = False
    for linea in p.read_text(encoding="utf-8").splitlines():
        s = linea.strip()
        if s.count('"""') == 1:
            en_docstring = not en_docstring
            continue
        if en_docstring or not s or s.startswith("#") or (s.startswith('"""') and s.endswith('"""')):
            continue
        n += 1
    return n


def rol(nombre: str) -> str:
    if nombre.startswith("adaptador"):
        return "adaptador"
    if nombre.startswith("componentes"):
        return "componentes"
    if nombre == "__init__.py":
        return "paquete"
    return "runner_y_herramientas"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    filas = []
    for carpeta in sorted(d for d in MUNDOS.iterdir() if d.is_dir() and d.name.startswith("mundo_")):
        por_rol = {"adaptador": 0, "componentes": 0, "runner_y_herramientas": 0, "paquete": 0}
        ficheros = [p for p in carpeta.glob("*.py")]
        for p in ficheros:
            por_rol[rol(p.name)] += lineas_codigo(p)
        filas.append({
            "mundo": carpeta.name,
            "ficheros_py": len(ficheros),
            "lineas_adaptador": por_rol["adaptador"],
            "lineas_componentes_dominio": por_rol["componentes"],
            "lineas_runner_y_herramientas": por_rol["runner_y_herramientas"],
            "lineas_total": sum(por_rol.values()),
        })
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    for fila in filas:
        print(fila)


if __name__ == "__main__":
    main()
