"""El harness de experimentos falla con un error explícito ante opciones no implementadas (nunca en silencio)."""

import pathlib
import subprocess
import sys

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HARNESS = RAIZ / "analisis" / "run_experimento.py"


@pytest.mark.parametrize(
    "args,mensaje",
    [
        (["--hipotesis", "H1", "--mundo", "snake"], "no implementado"),
        (["--hipotesis", "H7", "--mundo", "ajedrez"], "no implementado"),
        (["--hipotesis", "H1", "--aislar-ruido"], "H1 no admite"),
        (["--hipotesis", "H7", "--modo-ablacion", "nivel_b"], "H7 no admite"),
    ],
)
def test_harness_rechaza_opciones_no_implementadas(args, mensaje, tmp_path):
    pytest.importorskip("crafter")
    pytest.importorskip("scipy")
    res = subprocess.run(
        [sys.executable, str(HARNESS), *args, "--semillas", "3000", "--out", str(tmp_path / "x.csv")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")},
    )
    assert res.returncode == 2, res.stdout + res.stderr
    assert mensaje in res.stderr
    assert not (tmp_path / "x.csv").exists()
