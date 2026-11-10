"""Baseline BFS de Snake (analisis/medir_snake.py): lógica pura, sin red ni navegador."""

import importlib
import pytest

pytest.importorskip("playwright")
_mod = importlib.import_module("lineas-base.snake_bfs")
decidir_bfs = _mod.decidir_bfs


def test_bfs_va_hacia_la_comida_por_el_camino_mas_corto():
    cuerpo = [(5, 5), (5, 4), (5, 3)]
    assert decidir_bfs(cuerpo, (8, 5), 21, 15) == "ESTE"
    assert decidir_bfs(cuerpo, (5, 9), 21, 15) == "SUR"


def test_bfs_no_se_mete_en_un_bolsillo_sin_salida():
    # Bolsillo cerrado al ESTE (mismo escenario que el test del flood fill de S3): la comida está dentro
    cuerpo = [(5, 5), (5, 4), (6, 4), (7, 4), (8, 4), (8, 5), (8, 6), (7, 6), (6, 7), (5, 7), (5, 6), (4, 6), (4, 7), (4, 8)]
    mov = decidir_bfs(cuerpo, (7, 5), 21, 15)
    assert mov == "OESTE"


def test_bfs_sin_movimientos_posibles_devuelve_none():
    cuerpo = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 2)]
    assert decidir_bfs(cuerpo, (5, 5), 21, 15) is None
