"""
El canario distingue igual, distinto y Â«no se puede compararÂ», sin ejecutar H7 (dobles de prueba).
La ejecuciÃ³n real (unos 3 minutos) va en su propio paso de la CI: `python -m v14.canario`.
"""

import pytest

from herramientas import canario


@pytest.fixture
def dobles(monkeypatch, tmp_path):
    contenidos = {"actual": b"a,b\n1,2\n", "referencia": b"a,b\n1,2\n"}

    def git(*args, cwd=None):
        if args[0] == "rev-parse":
            return "0123456789abcdef"
        return ""

    def ejecutar_h7(raiz, csv, semillas, max_pasos, env):
        clave = "actual" if csv.endswith("actual_H7.csv") else "referencia"
        with open(csv, "wb") as f:
            f.write(contenidos[clave])

    monkeypatch.setattr(canario, "_git", git)
    monkeypatch.setattr(canario, "_ejecutar_h7", ejecutar_h7)
    monkeypatch.setattr(canario, "_comprobar_resolucion", lambda raiz, env: None)
    monkeypatch.setattr(canario, "encendidos", lambda: {})
    return contenidos, ["--out-dir", str(tmp_path)]


def test_identicos(dobles):
    _, args = dobles
    assert canario.main(args) == 0


def test_distintos(dobles):
    contenidos, args = dobles
    contenidos["actual"] = b"a,b\n1,3\n"
    assert canario.main(args) == 1


def test_no_compara_con_un_flag_encendido(dobles, monkeypatch):
    _, args = dobles
    monkeypatch.setattr(canario, "encendidos", lambda: {"crafter": {"observar_activa": True}})
    assert canario.main(args) == 2


def test_no_compara_si_el_worktree_importa_codigo_ajeno(dobles, monkeypatch):
    _, args = dobles

    def ajeno(raiz, env):
        raise RuntimeError("el worktree importarÃ­a cÃ³digo de fuera")

    monkeypatch.setattr(canario, "_comprobar_resolucion", ajeno)
    assert canario.main(args) == 2

