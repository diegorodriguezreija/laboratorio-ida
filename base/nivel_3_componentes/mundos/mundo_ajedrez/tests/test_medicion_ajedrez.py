"""Lógica pura del script de medición de ajedrez (nivel_3_componentes/mundos/mundo_ajedrez/medir_ajedrez.py)."""

import pytest

chess = pytest.importorskip("chess")
from nivel_3_componentes.mundos.mundo_ajedrez.medir_ajedrez import jugada_1ply, sortear_apertura, tipo_final  # noqa: E402
from nivel_3_componentes.mundos.mundo_ajedrez.adaptador_ajedrez import RivalBotLocal  # noqa: E402


def test_apertura_reproducible_y_legal():
    a1, a2 = sortear_apertura(123), sortear_apertura(123)
    assert a1 == a2 and len(a1) == 4
    b = chess.Board()
    for uci in a1:
        assert chess.Move.from_uci(uci) in b.legal_moves
        b.push_uci(uci)


def test_tipo_final_distingue_limite_de_tablas():
    assert tipo_final(chess.Board(), chess.WHITE, limite=True)["resultado"] == "limite"
    mate = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")  # mate del loco
    assert tipo_final(mate, chess.WHITE, limite=False) == {"resultado": "derrota", "tipo": "mate"}
    assert tipo_final(mate, chess.BLACK, limite=False)["resultado"] == "victoria"


def test_baseline_1ply_da_mate_en_una():
    b = chess.Board("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1")  # Ra8#
    assert jugada_1ply(b, RivalBotLocal(dificultad=1)).uci() == "a1a8"
