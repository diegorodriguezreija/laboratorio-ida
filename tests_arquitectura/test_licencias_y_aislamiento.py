"""
D2 – Separación de licencias.

1. Ningún fichero fuera de nivel_3_componentes/mundos/mundo_ajedrez/ importa python-chess
   ('chess') de forma estática.
2. El núcleo y el resto de mundos arrancan con python-chess bloqueado (como si no estuviera
   instalado).
3. Ningún fichero con nombre libro_profesor* forma parte del árbol (material privado).
"""

import ast
import os
import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CARPETA_GPL = RAIZ / "base" / "nivel_3_componentes" / "mundos" / "mundo_ajedrez"
EXCLUIR = {".git", ".venv", "venv", "salidas", "__pycache__", ".pytest_cache"}


def _ficheros_python():
    for p in RAIZ.rglob("*.py"):
        if EXCLUIR & set(p.relative_to(RAIZ).parts):
            continue
        yield p


def test_ningun_fichero_fuera_de_mundo_ajedrez_importa_chess():
    infractores = []
    for p in _ficheros_python():
        if CARPETA_GPL in p.parents:
            continue
        for nodo in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(nodo, ast.Import):
                nombres = [a.name for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
                nombres = [nodo.module]
            else:
                continue
            if any(n == "chess" or n.startswith("chess.") for n in nombres):
                infractores.append(f"{p.relative_to(RAIZ)}:{nodo.lineno}")
    assert not infractores, "Importan python-chess fuera de mundo_ajedrez/: " + ", ".join(infractores)


CODIGO_SIN_CHESS = r"""
import importlib.abc, sys

class Bloqueo(importlib.abc.MetaPathFinder):
    def find_spec(self, nombre, ruta=None, objetivo=None):
        if nombre == "chess" or nombre.startswith("chess."):
            raise ImportError("python-chess bloqueado para el test D2")
        return None

sys.meta_path.insert(0, Bloqueo())
import asyncio
import nivel_3_componentes, nivel_3_componentes.mundos
from nivel_3_componentes.mundos.mundo_ejemplo_minimo.ejemplo_minimo_runner import ejecutar
asyncio.run(ejecutar(5))
try:
    import crafter  # noqa: F401
    import nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner  # noqa: F401
except ImportError as e:
    if "chess" in str(e):
        raise
import nivel_3_componentes.mundos.mundo_arcade_snake.mundo_snake_runner  # noqa: F401
assert "chess" not in sys.modules
print("OK_SIN_CHESS")
"""


def test_nucleo_y_otros_mundos_arrancan_sin_python_chess(tmp_path):
    res = subprocess.run(
        [sys.executable, "-c", CODIGO_SIN_CHESS],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
        env={
            **__import__("os").environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONPATH": os.pathsep.join(filter(None, [str(RAIZ / "base"), str(RAIZ), __import__("os").environ.get("PYTHONPATH", "")])),
            "IDA_OUT_DIR": str(tmp_path),
        },
    )
    assert res.returncode == 0 and "OK_SIN_CHESS" in res.stdout, res.stdout[-2000:] + res.stderr[-2000:]


def test_no_hay_material_privado_del_libro_del_profesor():
    encontrados = [str(p.relative_to(RAIZ)) for p in RAIZ.rglob("libro_profesor*") if not (EXCLUIR & set(p.relative_to(RAIZ).parts))]
    assert not encontrados, f"Material privado dentro del repositorio: {encontrados}"
