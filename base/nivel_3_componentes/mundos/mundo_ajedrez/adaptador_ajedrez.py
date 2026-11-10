from typing import Dict, Any, List, Tuple, Optional, Set
import os
import shutil
import math
import numpy as np
try:
    import chess
    import chess.engine
except ImportError as exc:  # dependencia opcional (extra [ajedrez], GPL-3.0-or-later)
    raise ImportError('Falta python-chess. Instálalo con: pip install -e ".[ajedrez]"') from exc

from nivel_1_core.vocabulario import V_Comando, V_Relacion
from nivel_1_core.contratos import Pieza, ISensorEntorno, IActuadorEntorno, ResultadoEfectoEntorno


class RivalBotLocal:
    """Rival local integrado para entrenamiento rapido y evolucion transgeneracional."""

    VALORES_PIEZA = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000,
    }

    # Tablas de casillas simplificadas (Peon y Caballo) para valoracion posicional
    PST_CABALLO = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ]

    def __init__(self, dificultad: int = 1):
        self.dificultad = dificultad  # 0: Principiante, 1: Intermedio, 2: Táctico (2-ply), 3: Club Alfa-Beta (3-ply)

    def elegir_jugada(self, board: chess.Board) -> chess.Move:
        legales = list(board.legal_moves)
        if not legales:
            return chess.Move.null()

        # Dificultad 0: Capturas si existen, sino aleatoria
        if self.dificultad == 0:
            capturas = [m for m in legales if board.is_capture(m)]
            if capturas:
                return max(capturas, key=lambda m: self._evaluar_captura(board, m))
            return np.random.choice(legales)

        # Dificultad 3: Minimax Alfa-Beta de Profundidad 3 (3-ply) con ordenacion de jugadas
        if self.dificultad >= 3:
            return self._elegir_jugada_alfabeta(board, profundidad=3)

        # Dificultad 2: Minimax 2 capas
        profundidad = 2 if self.dificultad == 2 else 1

        mejor_jugada = legales[0]
        mejor_score = -999999

        for m in legales:
            board.push(m)
            if profundidad == 1:
                score = -self._evaluar_posicion(board, board.turn)
            else:
                # 2 capas: peor respuesta del rival para IdA
                score = -self._minimax_simple(board, profundidad=1, turno_raiz=board.turn)
            board.pop()

            # Jitter leve
            score += np.random.uniform(-3.0, 3.0)

            if score > mejor_score:
                mejor_score = score
                mejor_jugada = m

        return mejor_jugada

    def _minimax_simple(self, board: chess.Board, profundidad: int, turno_raiz: chess.Color) -> int:
        if board.is_game_over() or profundidad == 0:
            return self._evaluar_posicion(board, turno_raiz)

        peor_score = 999999
        for m in board.legal_moves:
            board.push(m)
            val = self._evaluar_posicion(board, turno_raiz)
            board.pop()
            if val < peor_score:
                peor_score = val
        return peor_score

    def _elegir_jugada_alfabeta(self, board: chess.Board, profundidad: int) -> chess.Move:
        """Búsqueda Alfa-Beta de profundidad N con ordenación de capturas prioritarias."""
        legales = list(board.legal_moves)
        # Ordenación heurística para maximizar podas: capturas primero
        legales.sort(key=lambda m: (board.is_capture(m), self._evaluar_captura(board, m)), reverse=True)

        mejor_jugada = legales[0]
        alfa = -999999
        beta = 999999
        turno_bot = board.turn

        for m in legales:
            board.push(m)
            score = -self._alfabeta(board, profundidad - 1, -beta, -alfa, turno_bot)
            board.pop()

            score += np.random.uniform(-2.0, 2.0)

            if score > alfa:
                alfa = score
                mejor_jugada = m

        return mejor_jugada

    def _alfabeta(self, board: chess.Board, profundidad: int, alfa: int, beta: int, turno_bot: chess.Color) -> int:
        if board.is_game_over() or profundidad == 0:
            return self._evaluar_posicion(board, board.turn if board.turn == turno_bot else not board.turn)

        legales = list(board.legal_moves)
        legales.sort(key=lambda m: board.is_capture(m), reverse=True)

        for m in legales:
            board.push(m)
            score = -self._alfabeta(board, profundidad - 1, -beta, -alfa, turno_bot)
            board.pop()

            if score >= beta:
                return beta  # Poda Beta
            if score > alfa:
                alfa = score

        return alfa

    def _evaluar_captura(self, board: chess.Board, move: chess.Move) -> int:
        victima = board.piece_at(move.to_square)
        atacante = board.piece_at(move.from_square)
        v_val = self.VALORES_PIEZA.get(victima.piece_type, 0) if victima else 0
        a_val = self.VALORES_PIEZA.get(atacante.piece_type, 0) if atacante else 0
        return v_val - (a_val // 10)

    def _evaluar_posicion(self, board: chess.Board, turno_actual: chess.Color) -> int:
        if board.is_checkmate():
            return -90000 if board.turn == turno_actual else 90000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if p:
                val = self.VALORES_PIEZA.get(p.piece_type, 0)
                # Bono por control del centro
                file_idx = chess.square_file(sq)
                rank_idx = chess.square_rank(sq)
                dist_centro = abs(3.5 - file_idx) + abs(3.5 - rank_idx)
                bono_centro = int((7.0 - dist_centro) * 5)

                # PST simple para caballos
                bono_pst = 0
                if p.piece_type == chess.KNIGHT:
                    sq_idx = sq if p.color == chess.WHITE else chess.square_mirror(sq)
                    bono_pst = self.PST_CABALLO[sq_idx] // 5

                total_pieza = val + bono_centro + bono_pst

                if p.color == turno_actual:
                    score += total_pieza
                else:
                    score -= total_pieza
        return score


class AdaptadorAjedrez(ISensorEntorno, IActuadorEntorno):
    """
    Adaptador de Membrana Sensoriomotora para el Mundo Ajedrez.
    Implementa ISensorEntorno e IActuadorEntorno bajo la arquitectura de Doble Membrana:
    1. Modo Fast: python-chess local para entrenamiento acelerado y sueño REM.
    2. Modo Lichess: Conexión web visual con Playwright a Lichess.org.
    """

    VALORES_MATERIAL = {
        chess.PAWN: 0.10,
        chess.KNIGHT: 0.32,
        chess.BISHOP: 0.33,
        chess.ROOK: 0.50,
        chess.QUEEN: 0.90,
        chess.KING: 1.00,
    }

    NOMBRES_PIEZAS = {
        chess.PAWN: "Peon",
        chess.KNIGHT: "Caballo",
        chess.BISHOP: "Alfil",
        chess.ROOK: "Torre",
        chess.QUEEN: "Dama",
        chess.KING: "Rey",
    }

    def __init__(
        self,
        modo: str = "fast",
        color_ida: str = "blancas",
        dificultad_rival: int = 1,
        elo_stockfish: Optional[int] = None,
        ruta_stockfish: Optional[str] = None,
        headless: bool = False,
    ):
        self.modo = modo
        self.color_ida_bool: chess.Color = chess.WHITE if color_ida.lower().startswith("b") else chess.BLACK
        self.color_ida_str = "BLANCAS" if self.color_ida_bool == chess.WHITE else "NEGRAS"
        self.headless = headless
        self.elo_stockfish = elo_stockfish
        # Stockfish no se distribuye: IDA_STOCKFISH_PATH, después 'stockfish' en el PATH y,
        # por compatibilidad, la ruta antigua bin/stockfish/stockfish.exe (relativa al cwd).
        self.ruta_stockfish = (
            ruta_stockfish
            or os.environ.get("IDA_STOCKFISH_PATH", "").strip()
            or shutil.which("stockfish")
            or "bin/stockfish/stockfish.exe"
        )

        # Motor Stockfish UCI opcional si se especifica ELO. Si se pide y no arranca, se
        # falla de forma explícita: nunca se sustituye en silencio por el rival local.
        self.engine_stockfish = None
        if self.elo_stockfish:
            if not os.path.exists(self.ruta_stockfish):
                raise RuntimeError(
                    f"Se pidió Stockfish (ELO {self.elo_stockfish}) pero no se encuentra en '{self.ruta_stockfish}'. "
                    "Descárgalo y define IDA_STOCKFISH_PATH con la ruta del ejecutable."
                )
            try:
                self.engine_stockfish = chess.engine.SimpleEngine.popen_uci(self.ruta_stockfish)
                self.engine_stockfish.configure({"UCI_LimitStrength": True, "UCI_Elo": max(1320, min(3190, self.elo_stockfish))})
            except Exception as exc:
                raise RuntimeError(f"No se pudo arrancar Stockfish en '{self.ruta_stockfish}': {exc}") from exc

        # Estado del juego
        self.board = chess.Board()
        self.rival = RivalBotLocal(dificultad=dificultad_rival)
        self.partidas_jugadas = 0
        self.victorias = 0
        self.derrotas = 0
        self.tablas = 0
        self.capturas_ida = 0
        self.ultimo_resultado: Optional[str] = None
        self.historial_jugadas_partida: List[str] = []

        # Atributos para modo Lichess (Playwright)
        self.page = None
        self.browser = None

        # Si IdA juega con negras, el rival blanco hace la primera jugada en el arranque
        if self.modo == "fast" and self.color_ida_bool == chess.BLACK:
            self._hacer_turno_rival_fast()

    def cerrar(self) -> None:
        """Libera los recursos del motor Stockfish si estaba abierto."""
        if self.engine_stockfish:
            try:
                self.engine_stockfish.quit()
            except Exception:
                pass
            self.engine_stockfish = None

    # =========================================================================
    # PUERTO SENSOR (ISensorEntorno)
    # =========================================================================
    def percibir_mundo(self) -> Tuple[str, List[Pieza], List[str]]:
        """
        Transduce el estado del tablero en tensores 6D, piezas cognitivas y jugadas legales UCI.
        """
        turno_str = "blancas" if self.board.turn == chess.WHITE else "negras"
        n_mov = self.board.fullmove_number
        id_nodo_actual = f"nodo_tablero_{turno_str}_{n_mov}"

        # Nodos adyacentes: todas las jugadas legales en notacion UCI
        if not self.board.is_game_over() and self.board.turn == self.color_ida_bool:
            nodos_adyacentes = [move.uci() for move in self.board.legal_moves]
        else:
            nodos_adyacentes = []

        # Si la partida ha terminado, ofrecer la accion de iniciar nueva partida
        if self.board.is_game_over():
            nodos_adyacentes.append("INICIAR_PARTIDA")

        # Generar piezas de escena con Tensor Sensorial 6D
        piezas_escena: List[Pieza] = []
        piezas_amenazadas_propias: List[str] = []
        piezas_amenazadas_rivales: List[str] = []

        color_rival = not self.color_ida_bool

        for sq in chess.SQUARES:
            p = self.board.piece_at(sq)
            if not p:
                continue

            casilla_str = chess.square_name(sq)
            es_propia = (p.color == self.color_ida_bool)
            bando_str = "PROPIA" if es_propia else "RIVAL"
            nombre_tipo = self.NOMBRES_PIEZAS.get(p.piece_type, "Pieza")
            id_pieza = f"{nombre_tipo}_{bando_str}_{casilla_str}"

            # 1. Fuerza material
            fuerza = self.VALORES_MATERIAL.get(p.piece_type, 0.1)

            # 2. Centralidad (distancia al cuadrante central d4, d5, e4, e5)
            f_idx = chess.square_file(sq)
            r_idx = chess.square_rank(sq)
            dist_centro = abs(3.5 - f_idx) + abs(3.5 - r_idx)
            centralidad = float(max(0.0, 1.0 - (dist_centro / 7.0)))

            # 3. Movilidad y amenazas
            ataques_rivales = len(self.board.attackers(color_rival if es_propia else self.color_ida_bool, sq))
            defensas_aliadas = len(self.board.attackers(p.color, sq))
            vulnerabilidad = float(min(1.0, ataques_rivales * 0.35))

            if es_propia and ataques_rivales > defensas_aliadas:
                piezas_amenazadas_propias.append(id_pieza)
            elif not es_propia and ataques_rivales > defensas_aliadas:
                piezas_amenazadas_rivales.append(id_pieza)

            movilidad = float(min(1.0, len(self.board.attacks(sq)) / 14.0))
            tension = float(min(1.0, (ataques_rivales + defensas_aliadas) * 0.25))
            saliencia = 0.95 if p.piece_type == chess.KING or vulnerabilidad > 0.6 else 0.5

            # En el mundo ajedrez, las piezas no son alimento biológico (dimensión 4 = 0.0 de afinidad nutricional)
            tensor_6d = np.array([fuerza, centralidad, movilidad, vulnerabilidad, 0.0, saliencia], dtype=np.float64)

            relacion_afectiva = V_Relacion.ES_SEGURO if es_propia else V_Relacion.ES_LETAL

            p_cog = Pieza(
                id=id_pieza,
                tipo_componente="Pieza_Tablero",
                arousal=float(min(1.0, 0.3 + 0.7 * vulnerabilidad)),
                trust=0.95,
                tensor_sensorial=tensor_6d,
                product={
                    "sujeto": id_pieza,
                    "casilla": casilla_str,
                    "tipo": nombre_tipo,
                    "bando": bando_str,
                    "es_propia": es_propia,
                    "fuerza_material": fuerza,
                    "centralidad": centralidad,
                    "vulnerabilidad": vulnerabilidad,
                    "ataques_rivales": ataques_rivales,
                    "defensas_aliadas": defensas_aliadas,
                    "relacion": relacion_afectiva,
                },
                inputs=["Sensor_Ajedrez"],
            )
            piezas_escena.append(p_cog)

        # Estado global del entorno de ajedrez
        en_jaque = self.board.is_check()
        es_jaquemate = self.board.is_checkmate()
        es_tablas = self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.can_claim_draw()

        estado_str = "EN_JUEGO"
        if es_jaquemate:
            estado_str = "DERROTA_JAQUEMATE" if self.board.turn == self.color_ida_bool else "VICTORIA_JAQUEMATE"
        elif es_tablas:
            estado_str = "TABLAS"
        elif en_jaque:
            estado_str = "JAQUE_RECIBIDO" if self.board.turn == self.color_ida_bool else "JAQUE_DADO"

        arousal_estado = 0.98 if es_jaquemate or en_jaque else (0.6 if es_tablas else 0.3)

        p_estado = Pieza(
            id="Estado_Partida_Ajedrez",
            tipo_componente="Estado_Entorno",
            arousal=arousal_estado,
            trust=1.0,
            product={
                "fen": self.board.fen(),
                "turno": turno_str,
                "turno_es_ida": (self.board.turn == self.color_ida_bool),
                "estado_partida": estado_str,
                "en_jaque": en_jaque,
                "es_jaquemate": es_jaquemate,
                "es_tablas": es_tablas,
                "numero_movimiento": n_mov,
                "piezas_colgadas_propias": piezas_amenazadas_propias,
                "piezas_colgadas_rivales": piezas_amenazadas_rivales,
                "partidas_jugadas": self.partidas_jugadas,
                "victorias": self.victorias,
                "derrotas": self.derrotas,
                "tablas": self.tablas,
            },
            inputs=["Sensor_Ajedrez"],
        )
        piezas_escena.append(p_estado)

        return id_nodo_actual, piezas_escena, nodos_adyacentes

    # =========================================================================
    # PUERTO ACTUADOR (IActuadorEntorno)
    # =========================================================================
    def ejecutar_comando_fisico(
        self,
        comando: V_Comando,
        target: str,
        factor_fauces: float = 1.0,
        payload_extra: Optional[Dict[str, Any]] = None,
    ) -> ResultadoEfectoEntorno:
        """
        Ejecuta la jugada decidida por el Tribunal Motor en el tablero (Fast o Lichess).
        """
        # Caso A: Comandos de observación atenta / espera deliberativa (ESPERAR / ACECHAR)
        if comando in (V_Comando.ESPERAR, V_Comando.ACECHAR):
            return ResultadoEfectoEntorno(
                exito=True,
                comando=comando,
                target=target,
                delta_alimentacion=0.9,  # Mantiene la homeostasis metabólica durante la reflexión
                delta_energia=1.5,       # Reposo atencional que recupera glucosa/energía
                nueva_ubicacion=target,
            )

        if comando != V_Comando.MOVER:
            return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        # Caso 1: Iniciar o reiniciar partida tras colapso
        if target == "INICIAR_PARTIDA":
            self.board.reset()
            self.historial_jugadas_partida.clear()
            self.ultimo_resultado = None
            if self.color_ida_bool == chess.BLACK:
                self._hacer_turno_rival_fast()
            return ResultadoEfectoEntorno(
                exito=True,
                comando=comando,
                target=target,
                delta_alimentacion=15.0,
                delta_energia=20.0,
                nueva_ubicacion="nodo_tablero_inicio",
            )

        # Caso 2: Jugada ordinaria de ajedrez en notacion UCI
        try:
            move = chess.Move.from_uci(target)
        except Exception:
            return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        if move not in self.board.legal_moves:
            return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        # Evaluar captura y consecuencias antes de ejecutar
        es_captura = self.board.is_capture(move)
        victima = self.board.piece_at(move.to_square)
        val_captura = self.VALORES_MATERIAL.get(victima.piece_type, 0.1) if victima else 0.0
        if es_captura:
            self.capturas_ida += 1

        # Ejecutar jugada de IdA
        self.board.push(move)
        self.historial_jugadas_partida.append(target)

        # Recompensas / Consecuencias fisiológicas somáticas para IdA (Ajustadas a ritmo de ajedrez)
        delta_alim = (val_captura * 35.0) if es_captura else 1.2
        delta_ene = 15.0 if es_captura else 3.0
        dano_sub: Dict[str, float] = {}

        # Verificar si IdA dio jaque mate
        if self.board.is_checkmate():
            self.victorias += 1
            self.partidas_jugadas += 1
            self.ultimo_resultado = "VICTORIA"
            delta_alim += 60.0
            delta_ene += 40.0
            return ResultadoEfectoEntorno(
                exito=True,
                comando=comando,
                target=target,
                delta_alimentacion=delta_alim,
                delta_energia=delta_ene,
                nueva_ubicacion=f"nodo_ajedrez_victoria_{target}",
            )

        # Turno del Rival (Modo Fast)
        if self.modo == "fast" and not self.board.is_game_over():
            self._hacer_turno_rival_fast()

        # Verificar si tras el turno del rival la partida ha terminado
        if self.board.is_checkmate():
            # Derrota de IdA
            self.derrotas += 1
            self.partidas_jugadas += 1
            self.ultimo_resultado = "DERROTA"
            dano_sub = {"core": -50.0, "fauces": -30.0, "sensores": -20.0}
        elif self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.can_claim_draw():
            self.tablas += 1
            self.partidas_jugadas += 1
            self.ultimo_resultado = "TABLAS"

        return ResultadoEfectoEntorno(
            exito=True,
            comando=comando,
            target=target,
            delta_alimentacion=delta_alim,
            delta_energia=delta_ene,
            dano_subsistemas=dano_sub,
            nueva_ubicacion=f"nodo_ajedrez_{target}",
        )

    def _hacer_turno_rival_fast(self) -> None:
        """El rival local o Stockfish UCI realiza su jugada y la ejecuta en el tablero."""
        if self.board.is_game_over():
            return

        mov_rival = None
        # Si Stockfish UCI está configurado, pedirle la jugada
        if self.engine_stockfish:
            try:
                res = self.engine_stockfish.play(self.board, chess.engine.Limit(time=0.05))
                mov_rival = res.move
            except Exception:
                mov_rival = None

        # Fallback a RivalBotLocal si no hay Stockfish o falló
        if not mov_rival or mov_rival == chess.Move.null():
            mov_rival = self.rival.elegir_jugada(self.board)

        if mov_rival and mov_rival != chess.Move.null():
            self.board.push(mov_rival)
            self.historial_jugadas_partida.append(mov_rival.uci())
