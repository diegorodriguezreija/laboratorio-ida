"""Ajedrez: si se pide Stockfish y no está disponible, se falla de forma explícita (nunca se usa otro rival en silencio)."""

import os

import pytest

chess = pytest.importorskip("chess")


def test_stockfish_ausente_da_error_explicito(tmp_path, monkeypatch):
    from nivel_3_componentes.mundos.mundo_ajedrez.adaptador_ajedrez import AdaptadorAjedrez

    monkeypatch.setenv("IDA_STOCKFISH_PATH", str(tmp_path / "no_existe" / "stockfish"))
    with pytest.raises(RuntimeError, match="IDA_STOCKFISH_PATH"):
        AdaptadorAjedrez(modo="fast", elo_stockfish=1350)


def test_sin_elo_no_necesita_stockfish(monkeypatch, tmp_path):
    from nivel_3_componentes.mundos.mundo_ajedrez.adaptador_ajedrez import AdaptadorAjedrez

    monkeypatch.setenv("IDA_STOCKFISH_PATH", str(tmp_path / "no_existe"))
    adaptador = AdaptadorAjedrez(modo="fast", dificultad_rival=1)
    assert adaptador.engine_stockfish is None


@pytest.mark.skipif(not os.environ.get("IDA_STOCKFISH_PATH_TEST"), reason="requiere un Stockfish local (IDA_STOCKFISH_PATH_TEST)")
def test_stockfish_presente_arranca(monkeypatch):
    from nivel_3_componentes.mundos.mundo_ajedrez.adaptador_ajedrez import AdaptadorAjedrez

    monkeypatch.setenv("IDA_STOCKFISH_PATH", os.environ["IDA_STOCKFISH_PATH_TEST"])
    adaptador = AdaptadorAjedrez(modo="fast", elo_stockfish=1350)
    try:
        assert adaptador.engine_stockfish is not None
    finally:
        adaptador.engine_stockfish.quit()
