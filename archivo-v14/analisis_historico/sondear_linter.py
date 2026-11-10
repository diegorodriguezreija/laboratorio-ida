"""
N7 – Sondeo de la cobertura del linter arquitectónico (tests_arquitectura/test_linter_pureza.py).

Pasa a auditar_ast_pureza una colección de fragmentos que intentan colar vocabulario de dominio,
imports prohibidos o constantes calibradas en los niveles 1-2, y registra si cada uno se detecta.
El resultado documenta qué cubre el linter (análisis léxico del AST con plegado de constantes)
y qué no cubre. No modifica el linter.

    python analisis/sondear_linter.py --out analisis/resultados/N7_cobertura_linter.csv
"""

import argparse
import csv
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from tests_arquitectura.test_linter_pureza import auditar_ast_pureza  # noqa: E402

# (id, categoría, descripción, código)
CASOS = [
    ("lit_directo", "literal", "Literal de texto con término de dominio", 'x = "crafter"'),
    ("lit_concat", "literal", "Concatenación de literales ('cra' + 'fter')", 'x = "cra" + "fter"'),
    ("lit_fstring", "literal", "f-string con partes literales alrededor de una variable", 'x = f"cra{v}fter"'),
    ("lit_bytes", "literal", "Literal de bytes con escapes", 'x = b"\\x63\\x72\\x61\\x66\\x74\\x65\\x72"'),
    ("docstring", "literal", "Término en un docstring", 'def f():\n    """usa el tablero"""\n'),
    ("clave_dict", "literal", "Término como clave de diccionario", 'd = {"ajedrez": 1}'),
    ("ident_variable", "identificador", "Nombre de variable con término", "espora_activa = 1"),
    ("ident_funcion", "identificador", "Nombre de función con término", "def mover_alfil():\n    pass"),
    ("ident_atributo", "identificador", "Atributo con término", "obj.tablero = 1"),
    ("import_prohibido", "import", "import de librería de mundo", "import chess"),
    ("import_nivel3", "import", "import desde nivel 3", "from nivel_3_componentes.mundos import x"),
    ("constante_asignada", "constante", "Constante calibrada en asignación (22 logros)", "LOGROS = 22"),
    ("join_lista", "evasion", "''.join de trozos", 'x = "".join(["cra", "fter"])'),
    ("invertida", "evasion", "Cadena invertida en tiempo de ejecución", 'x = "retfarc"[::-1]'),
    ("chr_codigos", "evasion", "Construcción con chr()", "x = ''.join(chr(c) for c in (99, 114, 97, 102, 116, 101, 114))"),
    ("format", "evasion", "str.format con trozos", 'x = "{}{}".format("cra", "fter")'),
    ("importlib", "evasion", "Import dinámico por cadena partida", 'import importlib\nm = importlib.import_module("ch" + "ess")'),
    ("dunder_import", "evasion", "__import__ con cadena partida", 'm = __import__("ch" + "ess")'),
    ("importlib_io", "evasion", "Import dinámico de un módulo de E/S prohibido (no es vocabulario de dominio)",
     'import importlib\nm = importlib.import_module("sub" + "process")'),
    ("constante_comparacion", "evasion", "Constante calibrada usada en comparación, no asignada", "if n == 22:\n    pass"),
    ("constante_default", "evasion", "Constante calibrada como valor por defecto", "def f(n=22):\n    return n"),
    ("sinonimo", "semantica", "Sinónimo no listado ('peón' -> 'soldado')", "soldado_avanza = 1"),
    ("umbral_tuneado", "semantica", "Umbral afinado para un mundo sin vocabulario", "UMBRAL_HAMBRE = 0.37"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    filas = []
    for cid, cat, desc, codigo in CASOS:
        violaciones = auditar_ast_pureza(codigo, nombre_archivo=f"<{cid}>")
        filas.append({"id": cid, "categoria": cat, "descripcion": desc, "codigo": codigo.replace("\n", "\\n"),
                      "detectado": bool(violaciones), "num_violaciones": len(violaciones)})
        print(f"{'DETECTA ' if violaciones else 'NO DETECTA'}  {cid:<22} {desc}")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    main()
