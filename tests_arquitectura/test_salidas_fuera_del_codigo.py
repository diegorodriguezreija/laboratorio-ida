"""
Ningún runner escribe dentro de las carpetas de código: sus rutas de salida cuelgan de
IDA_OUT_DIR (o ./salidas, ignorado por git) y calcularlas no crea nada en disco.
"""

import importlib
import os
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CARPETAS_CODIGO = [RAIZ / d for d in ("nivel_1_core", "nivel_2_sistemas", "nivel_3_componentes", "analisis", "tests_arquitectura")]

RUNNERS = [
    ("nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner", None),
    ("nivel_3_componentes.mundos.mundo_arcade_snake.mundo_snake_runner", None),
    ("nivel_3_componentes.mundos.mundo_ajedrez.mundo_ajedrez_runner", "chess"),
]


def _esta_dentro(ruta: pathlib.Path, carpeta: pathlib.Path) -> bool:
    try:
        ruta.resolve().relative_to(carpeta.resolve())
        return True
    except ValueError:
        return False


def test_directorio_salidas_respeta_ida_out_dir(monkeypatch, tmp_path):
    from nivel_3_componentes.rutas_salida import directorio_salidas

    monkeypatch.setenv("IDA_OUT_DIR", str(tmp_path))
    assert pathlib.Path(directorio_salidas("crafter")) == (tmp_path / "crafter").resolve()
    assert not (tmp_path / "crafter").exists(), "calcular la ruta no debe crear el directorio"

    monkeypatch.delenv("IDA_OUT_DIR")
    assert pathlib.Path(directorio_salidas()) == (RAIZ / "salidas").resolve()


@pytest.mark.parametrize("modulo,dependencia", RUNNERS)
def test_rutas_de_los_runners_fuera_del_codigo(modulo, dependencia):
    if dependencia:
        pytest.importorskip(dependencia)
    mod = importlib.import_module(modulo)
    rutas = [getattr(mod, n) for n in dir(mod) if n.startswith("RUTA_") and n not in ("RUTA_DIR", "RUTA_RAIZ")]
    assert rutas, f"{modulo} no expone rutas RUTA_*"
    for r in rutas:
        p = pathlib.Path(r)
        for carpeta in CARPETAS_CODIGO:
            assert not _esta_dentro(p, carpeta), f"{modulo}: {r} cae dentro de {carpeta.name}/"
