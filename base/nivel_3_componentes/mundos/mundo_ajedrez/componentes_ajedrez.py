import asyncio
import concurrent.futures
from typing import Dict, Any, List, Tuple, Set, Optional
import json
import urllib.request
import urllib.error
import chess
import numpy as np

from nivel_1_core.vocabulario import V_Comando, V_Relacion, V_Modalidad, V_Vinculo
from nivel_1_core.contratos import Pieza, Onda
from nivel_2_sistemas.sistema_base import ComponenteCognitivoBase


class CompAjedrezS1(ComponenteCognitivoBase):
    """
    Componente Reactivo S1: CPG de Táctica Inmediata y Supervivencia del Rey.
    1. Ejecuta en < 5 ms.
    2. Su mandato primordial es la no-derrota inmediata (responder a jaques, no colgar piezas vitales).
    3. Captura piezas rivales indefensas de mayor valor (gradiente apetitivo directo).
    4. Consulta ultra-rápida de traumas ancestrales en memoria activa (ej. celadas de apertura).
    """

    VALORES_PIEZA = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000,
    }

    def __init__(self, peso_sinaptico: float = 1.25):
        super().__init__("Comp_AjedrezS1", "S1", peso_sinaptico=peso_sinaptico)

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        prop = onda.reactiva.ev.get("Propiocepcion", {})
        if not prop:
            return False

        p_prop = next(iter(prop.values()))
        nodos_adyacentes: List[str] = list(p_prop.product.get("nodos_adyacentes", []))
        if not nodos_adyacentes:
            return False

        # Caso especial: Reiniciar partida si está terminada
        if "INICIAR_PARTIDA" in nodos_adyacentes:
            p_inicio = Pieza(
                id=f"Imp_Iniciar_Ajedrez_{onda.ciclo}",
                tipo_componente="Impulso",
                arousal=0.96,
                trust=1.0,
                product={"comando": V_Comando.MOVER, "target": "INICIAR_PARTIDA"},
                inputs=[p_prop.id, self.id_componente],
            )
            self.emitir_impulso(onda, p_inicio, coste_amplitud=0)
            return True

        # Extraer estado del entorno
        escena = onda.reactiva.ev.get("Escena", {})
        fen_actual = ""
        en_jaque = False
        for p in escena.values():
            if p.tipo_componente == "Estado_Entorno":
                fen_actual = str(p.product.get("fen", ""))
                en_jaque = bool(p.product.get("en_jaque", False))
                break

        board = chess.Board(fen_actual) if fen_actual else None
        if not board:
            return False

        # ---------------------------------------------------------------------
        # CONSULTA DE MEMORIA ANCESTRAL ACTIVA (TRAUMAS DE APERTURA / CELADAS)
        # ---------------------------------------------------------------------
        activa = ctx.get("activa")
        aversion_pastor = False
        if activa and hasattr(activa, "indice_identidad"):
            for cajon in activa.indice_identidad.values():
                for p in cajon.values():
                    if p.tipo_componente == "Aversion_Traumatica":
                        tt = str(p.product.get("tipo_trauma", ""))
                        if "PASTOR" in tt or "F7" in tt or "F2" in tt:
                            aversion_pastor = True
                            break

        # Personalidad: Arquetipo
        arquetipo = ctx.get("arquetipo")
        responsabilidad = float(getattr(arquetipo, "responsabilidad", 0.70)) if arquetipo else 0.70
        neuroticismo = float(getattr(arquetipo, "neuroticismo", 0.35)) if arquetipo else 0.35
        apertura = float(getattr(arquetipo, "apertura", 0.70)) if arquetipo else 0.70

        peso_cautela = 0.5 + (responsabilidad * 0.4) + (neuroticismo * 0.3)
        peso_apetito = 0.8 + (apertura * 0.5)

        # Evaluar candidatos de S1
        def evaluar_jugada_s1(uci_str: str) -> float:
            try:
                move = chess.Move.from_uci(uci_str)
            except Exception:
                return -999.0

            score = 0.0

            # 1. Si estamos en jaque, salir de jaque es imperativo
            if en_jaque:
                score += 500.0

            # 2. Si captura pieza enemiga, valorar la ganancia de material
            if board.is_capture(move):
                victima = board.piece_at(move.to_square)
                atacante = board.piece_at(move.from_square)
                v_val = self.VALORES_PIEZA.get(victima.piece_type, 0) if victima else 0
                a_val = self.VALORES_PIEZA.get(atacante.piece_type, 0) if atacante else 0
                ganancia = v_val - (a_val if board.is_attacked_by(not board.turn, move.to_square) else 0)
                score += (ganancia * 0.1 * peso_apetito)

            # 3. Penalizar colgar la pieza inmediatamente
            if board.is_attacked_by(not board.turn, move.to_square):
                mi_pieza = board.piece_at(move.from_square)
                val_mi_pieza = self.VALORES_PIEZA.get(mi_pieza.piece_type, 0) if mi_pieza else 0
                score -= (val_mi_pieza * 0.08 * peso_cautela)

            # 4. Reflejo ante trauma ancestral de jaque pastor (vigilar f7 o f2)
            if aversion_pastor:
                casilla_critica = chess.F7 if board.turn == chess.BLACK else chess.F2
                if move.to_square == casilla_critica or move.to_square in (chess.E7, chess.D7, chess.G6):
                    score += 80.0

            return score

        # Ordenar candidatos
        candidatos_ordenados = sorted(nodos_adyacentes, key=evaluar_jugada_s1, reverse=True)
        mejor_uci = candidatos_ordenados[0]
        mejor_score = evaluar_jugada_s1(mejor_uci)

        # Si el mejor movimiento tiene score neutro (0.0, no hay táctica inmediata ni jaque),
        # el Trust de S1 disminuye a 0.65 (incertidumbre posicional), invitando a la intervención de S3
        trust_s1 = 0.95 if en_jaque else (0.85 if mejor_score > 0.0 else 0.65)

        p_imp = Pieza(
            id=f"Imp_S1_Ajedrez_{mejor_uci}",
            tipo_componente="Impulso",
            arousal=0.88 if en_jaque else 0.72,
            trust=trust_s1,
            product={"comando": V_Comando.MOVER, "target": mejor_uci, "origen_sistema": "S1", "score_tactico": mejor_score},
            inputs=[p_prop.id, self.id_componente],
        )
        self.emitir_impulso(onda, p_imp, coste_amplitud=1)
        return True


class CompAjedrezS2(ComponenteCognitivoBase):
    """
    Componente Límbico S2: Construcción de la Escalera Ontológica y Tensión Emocional.
    1. Reifica Piezas en Sujetos formales.
    2. Construye Predicados de relación (amenazas, defensas, clavadas).
    3. Construye Proposiciones con Trust y Modalidad (DEMOSTRADO / DUDA).
    4. Modula el estado emocional (Ansiedad ante clavadas, Calma en enroque).
    """

    def __init__(self, peso_sinaptico: float = 1.10):
        super().__init__("Comp_AjedrezS2", "S2", peso_sinaptico=peso_sinaptico)

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        escena = onda.reactiva.ev.get("Escena", {})
        if not escena:
            return False

        p_estado = next((p for p in escena.values() if p.tipo_componente == "Estado_Entorno"), None)
        if not p_estado:
            return False

        fen = str(p_estado.product.get("fen", ""))
        if not fen:
            return False

        board = chess.Board(fen)
        turno = board.turn
        color_rival = not turno

        # Construir Sujetos y Predicados ontológicos
        proposiciones_ontologicas: List[Dict[str, Any]] = []

        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if not p:
                continue

            casilla_str = chess.square_name(sq)
            es_propia = (p.color == turno)
            bando = "PROPIA" if es_propia else "RIVAL"
            tipo_nombre = chess.piece_name(p.piece_type).capitalize()

            # SUJETO
            sujeto_id = f"{tipo_nombre}_{bando}_{casilla_str}"

            # PREDICADOS DE AMENAZA / DEFENSA
            atacantes = list(board.attackers(color_rival if es_propia else turno, sq))
            defensores = list(board.attackers(turno if es_propia else color_rival, sq))

            if atacantes:
                relacion = V_Relacion.ES_LETAL if es_propia else V_Relacion.ES_NUTRITIVO
                modalidad = V_Modalidad.DEMOSTRADO
                trust = 0.95

                predicado = {
                    "accion": "BAJO_AMENAZA",
                    "atacantes_count": len(atacantes),
                    "defensores_count": len(defensores),
                    "relacion": relacion,
                }

                # PROPOSICION
                prop_id = f"Prop_{sujeto_id}_Amenazada"
                proposicion = {
                    "id": prop_id,
                    "sujeto": sujeto_id,
                    "predicado": predicado,
                    "modalidad": modalidad,
                    "trust": trust,
                    "es_propia": es_propia,
                }
                proposiciones_ontologicas.append(proposicion)

                # Emitir Proposicion formal a ev
                p_prop = Pieza(
                    id=prop_id,
                    tipo_componente="Proposicion_Ontologica",
                    arousal=0.85 if es_propia and p.piece_type in (chess.KING, chess.QUEEN) else 0.45,
                    trust=trust,
                    product=proposicion,
                    inputs=[self.id_componente],
                    sistemas_participantes={"S2"},
                )
                self.emitir_reactiva(onda, "Ontologia_Ajedrez", p_prop, proyectar_ev=True, coste_amplitud=1)

        return True


class CompAjedrezS3(ComponenteCognitivoBase):
    """
    Componente Deliberativo S3: Estrategia Neurosimbólica, Sentencias y Consultor Ollama.
    1. Construye Sentencias intencionales (ej. Control del Centro, Seguridad del Rey).
    2. Construye Lógicas / Silogismos causales.
    3. Consulta asíncrona local a Ollama (qwen2.5:3b) para generar hipótesis tácticas (V_Modalidad.HIPOTESIS).
    4. Valida rigurosamente la hipótesis contra las reglas de ajedrez (cero alucinaciones).
    5. Emite Impulso Estratégico de alto Trust en el canal acc.
    """

    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODELO_OLLAMA = "qwen2.5:3b"

    TABLA_PEON = [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]

    TABLA_CABALLO = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ]

    def __init__(self, peso_sinaptico: float = 1.35, usar_ollama: bool = True):
        super().__init__("Comp_AjedrezS3", "S3", peso_sinaptico=peso_sinaptico)
        self.usar_ollama = usar_ollama
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="S3_Ollama_Worker")
        self._future_consulta: Optional[concurrent.futures.Future] = None
        self._fen_en_deliberacion: Optional[str] = None
        self._ultima_estrategia_global: str = "Control central y desarrollo armonico"
        self._jugada_intuitiva_cache: Optional[str] = None
        self._fens_visitados: Set[str] = set()
        self._ultima_jugada_propia: Optional[str] = None

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        prop = onda.reactiva.ev.get("Propiocepcion", {})
        if not prop:
            return False

        p_prop = next(iter(prop.values()))
        nodos_adyacentes: List[str] = list(p_prop.product.get("nodos_adyacentes", []))
        if not nodos_adyacentes or "INICIAR_PARTIDA" in nodos_adyacentes:
            return False

        escena = onda.reactiva.ev.get("Escena", {})
        fen_actual = ""
        for p in escena.values():
            if p.tipo_componente == "Estado_Entorno":
                fen_actual = str(p.product.get("fen", ""))
                break

        board = chess.Board(fen_actual) if fen_actual else None
        if not board:
            return False

        if board.fullmove_number <= 1:
            self._fens_visitados.clear()
            self._ultima_jugada_propia = None
        self._fens_visitados.add(" ".join(fen_actual.split()[:4]))

        # ---------------------------------------------------------------------
        # DELIBERACIÓN ESTRATÉGICA ASÍNCRONA DE LARGO PLAZO (SIN ESPERAS)
        # ---------------------------------------------------------------------
        # Comprobar si el worker de Ollama ha devuelto una nueva hipótesis estratégica
        if self._future_consulta is not None and self._future_consulta.done():
            try:
                uci_sug, razon = self._future_consulta.result()
                if uci_sug:
                    self._jugada_intuitiva_cache = uci_sug
                    self._ultima_estrategia_global = razon
            except Exception:
                pass
            self._future_consulta = None

        # Si no hay consulta activa y tenemos Ollama, lanzar reflexión estratégica en background
        if self.usar_ollama and self._future_consulta is None and self._fen_en_deliberacion != fen_actual:
            self._fen_en_deliberacion = fen_actual
            fen_copia = fen_actual
            legales_copia = list(board.legal_moves)
            self._future_consulta = self._executor.submit(
                self._consultar_hipotesis_ollama_sync, fen_copia, legales_copia
            )

        # ---------------------------------------------------------------------
        # CONSULTA DE MEMORIA ANCESTRAL ACTIVA (PATRONES VICTORIOSOS Y AVERSIONES)
        # ---------------------------------------------------------------------
        jugadas_ancestrales_exitosas: Set[str] = set()
        activa = ctx.get("activa")
        if activa and hasattr(activa, "indice_identidad"):
            for cajon in activa.indice_identidad.values():
                for p in cajon.values():
                    if p.tipo_componente == "Patron_Exito_Estrategico":
                        sec = p.product.get("secuencia", [])
                        idx = len(board.move_stack)
                        if idx < len(sec):
                            jugadas_ancestrales_exitosas.add(sec[idx])

        # ---------------------------------------------------------------------
        # EVALUACIÓN NEUROSIMBÓLICA LOCAL DE CANDIDATOS (EN TIEMPO REAL O(N))
        # ---------------------------------------------------------------------
        evaluaciones: List[Dict[str, Any]] = []
        for uci_str in nodos_adyacentes:
            try:
                move = chess.Move.from_uci(uci_str)
            except Exception:
                continue

            score = self._evaluar_posicional_neurosimbolico(board, move)

            # Si coincide con la hipótesis intuitiva de Ollama en caché, aplicar bono de armonía
            if self._jugada_intuitiva_cache and uci_str == self._jugada_intuitiva_cache:
                score += 150.0

            # Si coincide con un patrón victorioso ancestral heredado en apertura
            if uci_str in jugadas_ancestrales_exitosas:
                score += 250.0

            evaluaciones.append({
                "uci": uci_str,
                "score": score,
                "es_hipotesis_ollama": (uci_str == self._jugada_intuitiva_cache),
                "es_patron_ancestral": (uci_str in jugadas_ancestrales_exitosas),
            })

        if not evaluaciones:
            return False

        evaluaciones.sort(key=lambda x: x["score"], reverse=True)
        mejor = evaluaciones[0]
        self._ultima_jugada_propia = mejor["uci"]

        # ---------------------------------------------------------------------
        # CRITERIO BIOLÓGICO: INTERVENCIÓN DE S3 ANTE INCERTIDUMBRE DE S1
        # ---------------------------------------------------------------------
        # Si S1 tiene un impulso con bajo trust o no ve táctica clara, o si S3 tiene
        # una ventaja estratégica notable (score posicional alto), S3 proyecta su impulso.
        impulso_s1 = next(
            (p for p in onda.reactiva.acc.get("Impulso", {}).values() if "S1" in p.id),
            None
        )

        trust_s1 = impulso_s1.trust if impulso_s1 else 0.5
        target_s1 = str(impulso_s1.product.get("target", "")) if impulso_s1 else ""
        debe_intervenir_s3 = (
            trust_s1 < 0.90
            or mejor["uci"] != target_s1
            or mejor["es_hipotesis_ollama"]
            or mejor["es_patron_ancestral"]
            or mejor["score"] >= 30.0
        )

        if not debe_intervenir_s3:
            return False  # Deja vía libre a los reflejos directos de S1

        # Si S1 propuso una jugada táctica inferior o que cuelga material, S3 atenúa el impulso de S1
        if impulso_s1 is not None and target_s1 != mejor["uci"]:
            impulso_s1.arousal = min(impulso_s1.arousal, 0.45)
            impulso_s1.trust = min(impulso_s1.trust, 0.50)

        # Construcción formal de Sentencia Lógica en Nivel 2
        sentencia_id = f"Sentencia_Estrategica_{mejor['uci']}"
        p_sentencia = Pieza(
            id=sentencia_id,
            tipo_componente="Sentencia_Intencional",
            arousal=0.92,
            trust=0.94,
            product={
                "agente": "IdA",
                "actitud": V_Modalidad.DESEA,
                "meta": "MAXIMIZAR_VENTAJA_POSICIONAL",
                "vinculo": V_Vinculo.IMPLICA,
                "jugada_elegida": mejor["uci"],
                "hipotesis_llm": self._ultima_estrategia_global,
            },
            inputs=[self.id_componente],
            sistemas_participantes={"S3"},
        )
        self.emitir_reactiva(onda, "Sentencias_S3", p_sentencia, proyectar_ev=True, coste_amplitud=1)

        # Emitir Impulso Motor S3 con alta dominancia al Tribunal Motor
        p_imp = Pieza(
            id=f"Imp_S3_Ajedrez_{mejor['uci']}",
            tipo_componente="Impulso",
            arousal=0.94,
            trust=0.96,
            product={
                "comando": V_Comando.MOVER,
                "target": mejor["uci"],
                "origen_sistema": "S3",
                "evaluacion_posicional": mejor["score"],
                "hipotesis_ollama": mejor["es_hipotesis_ollama"],
            },
            inputs=[p_prop.id, self.id_componente],
            sistemas_participantes={"S3"},
        )
        self.emitir_impulso(onda, p_imp, coste_amplitud=1)
        return True

    def _evaluar_posicional_neurosimbolico(self, board: chess.Board, move: chess.Move) -> float:
        """Evaluación formal de armonía, control central, capturas, seguridad táctica a 2-plies y anti-repetición."""
        score = 0.0
        turno_ida = board.turn

        # 1. Capturas favorables y coronación
        if board.is_capture(move):
            if board.is_en_passant(move):
                v_val = 100
            else:
                victima = board.piece_at(move.to_square)
                v_val = CompAjedrezS1.VALORES_PIEZA.get(victima.piece_type, 0) if victima else 0
            atacante = board.piece_at(move.from_square)
            a_val = CompAjedrezS1.VALORES_PIEZA.get(atacante.piece_type, 0) if atacante else 0
            score += (v_val * 1.45 - a_val * 0.15)

        if move.promotion:
            score += float(CompAjedrezS1.VALORES_PIEZA.get(move.promotion, 900)) * 1.25

        # 2. Enroque (protección vital del rey)
        if board.is_castling(move):
            score += 120.0

        # 3. Posicionamiento en tabla de piezas y desarrollo armónico
        pieza = board.piece_at(move.from_square)
        if pieza:
            sq_to = move.to_square
            sq_from = move.from_square
            sq_idx = sq_to if turno_ida == chess.WHITE else chess.square_mirror(sq_to)
            from_idx = sq_from if turno_ida == chess.WHITE else chess.square_mirror(sq_from)

            if pieza.piece_type == chess.PAWN:
                score += (self.TABLA_PEON[sq_idx] - self.TABLA_PEON[from_idx] * 0.5)
            elif pieza.piece_type == chess.KNIGHT:
                score += (self.TABLA_CABALLO[sq_idx] - self.TABLA_CABALLO[from_idx] * 0.8)
            elif pieza.piece_type == chess.BISHOP:
                if chess.square_rank(from_idx) == 0 and chess.square_rank(sq_idx) > 0:
                    score += 25.0
                if chess.square_file(sq_idx) in (2, 3, 4, 5) and chess.square_rank(sq_idx) in (2, 3, 4, 5):
                    score += 15.0
            elif pieza.piece_type == chess.QUEEN and len(board.move_stack) < 8 and not board.is_capture(move):
                score -= 25.0  # Evitar sacar la dama prematuramente en apertura sin captura

        # Penalizar oscilación inmediata de ida y vuelta (ej. d5c4 -> c4d5) sin captura
        uci_cand = move.uci()
        if (
            self._ultima_jugada_propia
            and len(uci_cand) >= 4
            and len(self._ultima_jugada_propia) >= 4
            and uci_cand[:2] == self._ultima_jugada_propia[2:4]
            and uci_cand[2:4] == self._ultima_jugada_propia[:2]
            and not board.is_capture(move)
        ):
            score -= 480.0

        # 4. Simulación prospectiva (1-ply propio + respuesta táctica rival)
        board.push(move)
        if board.is_checkmate():
            board.pop()
            return 100000.0  # Jaque mate directo a favor de IdA

        fen_post_key = " ".join(board.fen().split()[:4])

        # Penalización fuerte de tablas por ahogado o repetición de posición para evitar bucles oscilatorios
        if (
            board.is_stalemate()
            or board.is_insufficient_material()
            or board.is_repetition(2)
            or board.can_claim_draw()
            or fen_post_key in self._fens_visitados
        ):
            score -= 650.0

        respuestas_rival = list(board.legal_moves)
        if board.is_check():
            score += 45.0 + max(0, 8 - len(respuestas_rival)) * 18.0

        # Evaluación de la mejor respuesta táctica inmediata del rival (evitar colgar piezas o recibir mate en 1)
        max_perdida_rival = 0.0
        for r_move in board.legal_moves:
            if board.gives_check(r_move):
                board.push(r_move)
                es_mate_rival = board.is_checkmate()
                board.pop()
                if es_mate_rival:
                    max_perdida_rival = max(max_perdida_rival, 50000.0)
                    break

            if board.is_capture(r_move):
                if board.is_en_passant(r_move):
                    v_vic = 100.0
                else:
                    vic_p = board.piece_at(r_move.to_square)
                    v_vic = float(CompAjedrezS1.VALORES_PIEZA.get(vic_p.piece_type, 100)) if vic_p else 100.0
                atk_p = board.piece_at(r_move.from_square)
                v_atk = float(CompAjedrezS1.VALORES_PIEZA.get(atk_p.piece_type, 100)) if atk_p else 100.0
                defendida = board.is_attacked_by(turno_ida, r_move.to_square)
                perdida_neta = v_vic - (0.85 * v_atk if defendida else 0.0)
                if perdida_neta > max_perdida_rival:
                    max_perdida_rival = perdida_neta

        score -= max_perdida_rival * 1.25

        # Impulso de conversión en finales: acorralar al rey enemigo cuando queda poco material
        rey_rival = board.king(board.turn)
        rey_propio = board.king(turno_ida)
        if rey_rival is not None and rey_propio is not None and len(board.piece_map()) <= 12:
            r_file, r_rank = chess.square_file(rey_rival), chess.square_rank(rey_rival)
            dist_centro_rival = abs(3.5 - r_file) + abs(3.5 - r_rank)
            dist_reyes = chess.square_distance(rey_propio, rey_rival)
            score += dist_centro_rival * 12.0 + (14.0 - dist_reyes) * 6.0

        board.pop()
        return score

    def _consultar_hipotesis_ollama_sync(self, fen: str, legales: List[chess.Move]) -> Tuple[Optional[str], str]:
        """
        Ejecución síncrona en Worker Thread de fondo (ThreadPoolExecutor).
        NO bloquea el bucle de latidos de IdA bajo ninguna circunstancia.
        """
        movimientos_legales = [m.uci() for m in legales]

        prompt = (
            f"Act as a chess tactical advisor for an AI cognitive system. "
            f"Current FEN: {fen}. "
            f"Legal moves (UCI format): {json.dumps(movimientos_legales[:20])}. "
            f"Suggest the single best strategic UCI move and a 1-sentence reason. "
            f"Respond ONLY in JSON format: {{\"move\": \"<uci_move>\", \"reason\": \"<sentence>\"}}"
        )

        payload = json.dumps({
            "model": self.MODELO_OLLAMA,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "keep_alive": "30m",
            "options": {"temperature": 0.1, "num_predict": 35}
        }).encode("utf-8")

        req = urllib.request.Request(
            self.OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                response_text = data.get("response", "{}")
                parsed = json.loads(response_text)
                uci_sugerido = str(parsed.get("move", "")).strip().lower()
                razon = str(parsed.get("reason", "Hipotesis Ollama generada"))

                # Verificación formal: la jugada DEBE ser legal
                if uci_sugerido in movimientos_legales:
                    return uci_sugerido, razon
        except Exception:
            pass

        return None, "Fallback neurosimbolico"
