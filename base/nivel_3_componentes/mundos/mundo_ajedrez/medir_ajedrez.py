"""
N3 – Medición del mundo Ajedrez (modo fast, local).

Diseño:
- Agentes: 'ida' (core + componentes de ajedrez; la partida la juega simular_partida del
  propio runner, sin Ollama, sin axiomas heredados y sin autopoiesis) y 'baseline_1ply'
  (elige la jugada con mejor evaluación material/posicional a 1 ply usando la misma función
  de evaluación del rival local; jaque mate inmediato si existe).
- Rivales: Minimax local de niveles 1, 2 y 3 (3 = alfa-beta a 3 ply) y Stockfish con
  UCI_Elo limitado (por defecto 1320 y 1500; necesita IDA_STOCKFISH_PATH).
- Diseño pareado: la partida i de cada rival usa, para los dos agentes, la misma apertura
  aleatoria (4 medias jugadas legales sorteadas con semilla), el mismo color (alterno por i)
  y la misma semilla del RNG del rival.
- Resultado: victoria, tablas (ahogado, material insuficiente, repetición o 50 jugadas,
  reclamables) o derrota; las partidas que llegan al tope de seguridad del runner
  (400 latidos; 400 jugadas propias en el baseline) se registran como 'limite' y se informan
  aparte, sin contarlas como tablas.
- Se cuenta cuántas veces el adaptador sustituyó una jugada de Stockfish por el rival local
  (fallo puntual del motor), para declararlo.

Uso:
    python nivel_3_componentes/mundos/mundo_ajedrez/medir_ajedrez.py --partidas 50 --out salidas/N3/ajedrez.csv
"""

import argparse
import asyncio
import csv
import json
import os
import random
import sys
import time
from typing import Dict, List, Optional

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import chess  # noqa: E402
import numpy as np  # noqa: E402

from nivel_1_core.contratos import Arquetipo  # noqa: E402
from nivel_3_componentes.mundos.mundo_ajedrez import mundo_ajedrez_runner as runner  # noqa: E402
from nivel_3_componentes.mundos.mundo_ajedrez.adaptador_ajedrez import AdaptadorAjedrez, RivalBotLocal  # noqa: E402
from nivel_3_componentes.rutas_salida import asegurar_directorio_de, directorio_salidas  # noqa: E402

LIMITE_JUGADAS_BASELINE = 400


class AdaptadorConApertura(AdaptadorAjedrez):
    """Adaptador que arranca desde una apertura dada y cuenta las sustituciones de Stockfish."""

    apertura_uci: List[str] = []
    ultimo: Optional["AdaptadorConApertura"] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fallbacks_stockfish = 0
        if self.engine_stockfish is not None:
            original = self.rival.elegir_jugada

            def contar(board, _orig=original):
                self.fallbacks_stockfish += 1
                return _orig(board)

            self.rival.elegir_jugada = contar
        # Descarta la jugada inicial que el adaptador base hace si IdA lleva negras y aplica la apertura
        self.board = chess.Board()
        self.historial_jugadas_partida = []
        for uci in type(self).apertura_uci:
            self.board.push_uci(uci)
            self.historial_jugadas_partida.append(uci)
        if self.modo == "fast" and self.board.turn != self.color_ida_bool:
            self._hacer_turno_rival_fast()
        type(self).ultimo = self


def sortear_apertura(semilla: int, medias_jugadas: int = 4) -> List[str]:
    rng = random.Random(semilla)
    b = chess.Board()
    jugadas = []
    for _ in range(medias_jugadas):
        legales = sorted(m.uci() for m in b.legal_moves)
        m = rng.choice(legales)
        b.push_uci(m)
        jugadas.append(m)
    return jugadas


def tipo_final(board: chess.Board, color_ida: chess.Color, limite: bool) -> Dict[str, str]:
    if limite:
        return {"resultado": "limite", "tipo": "tope_de_seguridad"}
    if board.is_checkmate():
        return {"resultado": "derrota" if board.turn == color_ida else "victoria", "tipo": "mate"}
    if board.is_stalemate():
        return {"resultado": "tablas", "tipo": "ahogado"}
    if board.is_insufficient_material():
        return {"resultado": "tablas", "tipo": "material_insuficiente"}
    if board.can_claim_threefold_repetition():
        return {"resultado": "tablas", "tipo": "repeticion"}
    if board.can_claim_fifty_moves():
        return {"resultado": "tablas", "tipo": "50_jugadas"}
    return {"resultado": "tablas", "tipo": "otro"}


def jugada_1ply(board: chess.Board, evaluador: RivalBotLocal) -> chess.Move:
    mejor, mejor_score = None, None
    for m in sorted(board.legal_moves, key=lambda x: x.uci()):
        board.push(m)
        score = 10**9 if board.is_checkmate() else -evaluador._evaluar_posicion(board, board.turn)
        board.pop()
        if mejor_score is None or score > mejor_score:
            mejor, mejor_score = m, score
    return mejor


async def partida_ida(color: str, dificultad: int, elo: Optional[int]) -> Dict:
    arq = Arquetipo(nombre="Caissa_Medicion", id_individuo="Caissa_Medicion", linaje="Medicion_N3",
                    apertura=0.75, responsabilidad=0.80, neuroticismo=0.35, umbral_miedo=0.60)
    reg, _ = await runner.simular_partida(
        gen=1, arquetipo=arq, axiomas_previos=[], modo="fast", color_ida=color,
        dificultad_rival=dificultad, elo_stockfish=elo, usar_ollama=False, habilitar_autopoiesis=False,
    )
    ad = AdaptadorConApertura.ultimo
    limite = reg["resultado"] == "TABLAS_POR_LIMITE"
    return {**tipo_final(ad.board, ad.color_ida_bool, limite), "turnos": reg["turnos"],
            "jugadas_totales": len(ad.board.move_stack), "fallbacks_stockfish": ad.fallbacks_stockfish}


def partida_baseline(color: str, dificultad: int, elo: Optional[int]) -> Dict:
    ad = AdaptadorConApertura(modo="fast", color_ida=color, dificultad_rival=dificultad, elo_stockfish=elo)
    evaluador = RivalBotLocal(dificultad=1)
    propias, limite = 0, False
    try:
        while not ad.board.is_game_over() and not (ad.board.can_claim_threefold_repetition() or ad.board.can_claim_fifty_moves()):
            if propias >= LIMITE_JUGADAS_BASELINE:
                limite = True
                break
            ad.board.push(jugada_1ply(ad.board, evaluador))
            propias += 1
            if ad.board.is_game_over() or ad.board.can_claim_draw():
                break
            ad._hacer_turno_rival_fast()
        return {**tipo_final(ad.board, ad.color_ida_bool, limite), "turnos": propias,
                "jugadas_totales": len(ad.board.move_stack), "fallbacks_stockfish": ad.fallbacks_stockfish}
    finally:
        ad.cerrar()


async def medir(args) -> List[Dict]:
    runner.AdaptadorAjedrez = AdaptadorConApertura  # simular_partida usa el adaptador con apertura
    rivales = [("minimax", d, None) for d in args.niveles] + [("stockfish", 1, e) for e in args.elos]
    filas: List[Dict] = []
    for tipo_rival, dif, elo in rivales:
        nombre_rival = f"minimax_n{dif}" if tipo_rival == "minimax" else f"stockfish_{elo}"
        for i in range(args.partidas):
            semilla = args.semilla + 1000 * (dif if elo is None else elo) + i
            apertura = sortear_apertura(semilla)
            color = "blancas" if i % 2 == 0 else "negras"
            for agente in ("ida", "baseline_1ply"):
                AdaptadorConApertura.apertura_uci = apertura
                np.random.seed(semilla % (2**32))  # RNG del rival local: mismo para los dos agentes
                t0 = time.perf_counter()
                if agente == "ida":
                    res = await partida_ida(color, dif, elo)
                else:
                    res = partida_baseline(color, dif, elo)
                fila = {"rival": nombre_rival, "partida": i, "agente": agente, "color_agente": color,
                        "apertura": " ".join(apertura), "semilla": semilla, **res,
                        "duracion_s": round(time.perf_counter() - t0, 2)}
                filas.append(fila)
                print(json.dumps(fila, ensure_ascii=False), flush=True)
        with open(asegurar_directorio_de(args.out), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
            w.writeheader()
            w.writerows(filas)
    return filas


def main():
    ap = argparse.ArgumentParser(description="N3: medición de ajedrez (IdA frente a baseline de 1 ply)")
    ap.add_argument("--partidas", type=int, default=50, help="Partidas por rival y agente (por defecto 50)")
    ap.add_argument("--niveles", type=int, nargs="*", default=[1, 2, 3], help="Niveles del Minimax local")
    ap.add_argument("--elos", type=int, nargs="*", default=[1320, 1500], help="UCI_Elo de Stockfish (vacío para omitir)")
    ap.add_argument("--semilla", type=int, default=20261107)
    ap.add_argument("--out", default=os.path.join(directorio_salidas("analisis"), "N3_ajedrez.csv"))
    args = ap.parse_args()
    filas = asyncio.run(medir(args))
    print(f"[+] {len(filas)} partidas en {args.out}")


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    main()
