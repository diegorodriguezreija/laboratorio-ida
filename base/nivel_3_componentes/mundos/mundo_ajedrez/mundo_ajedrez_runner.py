import os
import sys

RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

import json
import time
import asyncio
import argparse
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from nivel_1_core.vocabulario import V_Comando, V_Relacion, V_Estado
from nivel_1_core.contratos import Arquetipo, Pieza, Onda
from nivel_1_core.gestor_onda import GestorOndaCore
from nivel_1_core.calculadoras_estructurales import CalculadorasEstructurales
from nivel_1_core.persistencia.motor_sqlite_wal import MotorSQLiteWAL

from nivel_2_sistemas.plasticidad_td_hebbiana import MatrizHebbianaTresFactores
from nivel_2_sistemas.s1_reactivo import crear_sistema_s1
from nivel_2_sistemas.s2_limbico import crear_sistema_s2
from nivel_2_sistemas.s3_racional import crear_sistema_s3
from nivel_2_sistemas.ciclo_sueno_rem import GestorCicloSuenoREM
from nivel_2_sistemas.consciencia_talamo_dmn import BucleTalamocortical, RedNeuronalPorDefecto
from nivel_2_sistemas.autopoiesis_ast import CirujanoAST

from nivel_3_componentes.mundos.mundo_ajedrez.adaptador_ajedrez import AdaptadorAjedrez
from nivel_3_componentes.mundos.mundo_ajedrez.componentes_ajedrez import (
    CompAjedrezS1,
    CompAjedrezS2,
    CompAjedrezS3,
)


from nivel_3_componentes.rutas_salida import directorio_salidas, asegurar_directorio_de

# Salidas de ejecución fuera de la carpeta de código (IDA_OUT_DIR o ./salidas/ajedrez)
RUTA_DIR_SALIDA = directorio_salidas("ajedrez")
RUTA_TRAZAS = os.path.join(RUTA_DIR_SALIDA, "trazas_ajedrez.log")
RUTA_LINAJE_JSON = os.path.join(RUTA_DIR_SALIDA, "linaje_evolutivo_ajedrez.json")
RUTA_SQLITE = os.path.join(RUTA_DIR_SALIDA, "memoria_linaje_ajedrez.db")


def log_traza(mensaje: str, escribir_en_consola: bool = True) -> None:
    """Escribe trazas estructuradas en el log persistente y en stdout."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] {mensaje}"
    if escribir_en_consola:
        print(linea)
    with open(asegurar_directorio_de(RUTA_TRAZAS), "a", encoding="utf-8") as f:
        f.write(linea + "\n")


def cargar_linaje_ancestral() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Carga axiomas y el historial de partidas/generaciones previas."""
    if os.path.exists(RUTA_LINAJE_JSON):
        try:
            with open(RUTA_LINAJE_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                axiomas = data.get("axiomas_heredados", [])
                historial = data.get("historial_generaciones", [])
                return axiomas, historial
        except Exception as e:
            log_traza(f"[AVISO] Error leyendo linaje previo: {e}")
    return [], []


def guardar_linaje_ancestral(
    axiomas: List[Dict[str, Any]],
    historial: List[Dict[str, Any]],
    generacion_max: int,
) -> None:
    """Consolida las verdades demostradas y el registro que cruzan la Barrera de Weismann."""
    data = {
        "linaje": "Linaje_Caissa_Evolutivo",
        "generacion_alcanzada": generacion_max,
        "axiomas_heredados": axiomas,
        "historial_generaciones": historial,
        "actualizado": time.time(),
    }
    with open(asegurar_directorio_de(RUTA_LINAJE_JSON), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def calcular_fitness_ajedrez(
    turnos: int,
    resultado: str,
    soma: Any,
    capturas_realizadas: int,
    phi_valores: List[float],
    jugadas_s3: int,
) -> Dict[str, float]:
    """Calcula el fitness triúnico intrínseco y global en ajedrez."""
    # S1: Supervivencia táctica (no recibir jaque mate prematuro)
    bono_resultado_s1 = 100.0 if resultado == "VICTORIA" else (60.0 if resultado == "TABLAS" else 30.0)
    longevidad_turnos = min(100.0, turnos * 2.5)
    f_s1 = float(min(100.0, longevidad_turnos * 0.4 + bono_resultado_s1 * 0.6))

    # S2: Eficiencia homeostática y balance emocional
    balance_hedonico = float(soma.placer - soma.cortisol * 30.0)
    f_s2 = float(max(0.0, min(100.0, 40.0 + balance_hedonico * 0.4 + min(40.0, capturas_realizadas * 8.0))))

    # S3: Maestría estratégica, dominancia de S3 y Phi
    bono_resultado_s3 = 100.0 if resultado == "VICTORIA" else (50.0 if resultado == "TABLAS" else 20.0)
    tasa_s3 = (jugadas_s3 / max(1, turnos)) * 100.0
    phi_prom = float(np.mean(phi_valores)) if phi_valores else 0.0
    f_s3 = float(min(100.0, bono_resultado_s3 * 0.5 + tasa_s3 * 0.3 + phi_prom * 20.0))

    f_global = float(0.30 * f_s1 + 0.30 * f_s2 + 0.40 * f_s3)
    return {
        "fit_s1": round(f_s1, 1),
        "fit_s2": round(f_s2, 1),
        "fit_s3": round(f_s3, 1),
        "fit_global": round(f_global, 1),
    }


async def simular_partida(
    gen: int,
    arquetipo: Arquetipo,
    axiomas_previos: List[Dict[str, Any]],
    modo: str = "fast",
    color_ida: str = "blancas",
    dificultad_rival: int = 1,
    elo_stockfish: Optional[int] = None,
    usar_ollama: bool = True,
    headless: bool = False,
    habilitar_autopoiesis: bool = False,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Ejecuta una partida completa como ciclo vital de un espécimen IdA."""
    log_traza("------------------------------------------------------------------------------------------")
    rival_desc = f"Stockfish ELO {elo_stockfish}" if elo_stockfish else f"Dificultad {dificultad_rival}"
    log_traza(f"[*] Espécimen Nacido: {arquetipo.id_individuo} (Gen {gen}) | Modo: {modo.upper()} | Rival: {rival_desc} | Bando: {color_ida.upper()}")
    log_traza(f"[*] Rasgos Fenotípicos: Apertura={arquetipo.apertura:.2f} | Resp={arquetipo.responsabilidad:.2f} | Neurot={arquetipo.neuroticismo:.2f}")

    adaptador = AdaptadorAjedrez(
        modo=modo,
        color_ida=color_ida,
        dificultad_rival=dificultad_rival,
        elo_stockfish=elo_stockfish,
        headless=headless,
    )
    sqlite = MotorSQLiteWAL(asegurar_directorio_de(RUTA_SQLITE))

    # Construir Mente Triúnica con componentes especializados de Ajedrez
    hebb = MatrizHebbianaTresFactores()
    s1 = crear_sistema_s1(matriz_hebbiana=hebb)
    comp_s1 = CompAjedrezS1(peso_sinaptico=1.25)
    # En Ajedrez, el CPG táctico sustituye los impulsos genéricos de recolección (ACC_DEGLUTIR)
    s1.estaciones["REACCIONAR"] = [comp_s1]

    s2 = crear_sistema_s2()
    comp_s2 = CompAjedrezS2(peso_sinaptico=1.15)
    s2.inyectar_componente("INTERPRETAR", comp_s2)

    s3 = crear_sistema_s3()
    comp_s3 = CompAjedrezS3(peso_sinaptico=1.40, usar_ollama=usar_ollama)
    s3.estaciones["REACCIONAR"] = [
        c for c in s3.estaciones["REACCIONAR"] if c.id_componente != "Comp_Impulso_S3"
    ]
    s3.inyectar_componente("ACTUAR", comp_s3)

    sueno_rem = GestorCicloSuenoREM()
    talamo = BucleTalamocortical()
    dmn = RedNeuronalPorDefecto()
    cirujano = CirujanoAST() if habilitar_autopoiesis else None  # D7: desactivada por defecto

    core = GestorOndaCore(
        sensor=adaptador,
        actuador=adaptador,
        sistemas_cognitivos=[s1, s2, s3],
        arquetipo=arquetipo,
        amplitud_max=250,
        frecuencia_max_ms=5000.0 if modo == "lichess" else 3000.0,
        gestor_sueno_rem=sueno_rem,
        bucle_talamocortical=talamo,
        dmn=dmn,
        cirujano_ast=cirujano,
        sqlite_wal=sqlite,
    )

    # Precargar axiomas ancestrales heredados en la Dimensión Activa
    for ax_data in axiomas_previos:
        p_heredada = Pieza.from_dict(ax_data)
        p_heredada.heredado = True
        core.activa.consolidar_pieza(p_heredada.id, p_heredada)
    log_traza(f"[*] Epigenética: {len(axiomas_previos)} axiomas heredados cruzaron la Barrera de Weismann.")

    # Bucle Vital de la Partida
    latido = 0
    jugadas_s3 = 0
    phi_valores: List[float] = []
    resultado_partida = "EN_JUEGO"
    capturas_totales = 0
    max_latidos_partida = 400  # Permite latidos continuos de deliberación sin agotar prematuramente la partida

    while True:
        latido += 1
        t_inicio = time.perf_counter()
        onda = await core.ejecutar_latido()
        dt_ms = (time.perf_counter() - t_inicio) * 1000.0

        phi_val = float(onda.metricas.get("phi", 0.0))
        phi_valores.append(phi_val)

        # Detectar la jugada efectivamente ejecutada y arbitrada por el Tribunal Motor
        p_ejec = next(iter(onda.reactiva.ef.get("Ejecucion", {}).values()), None)
        target_str = "ninguno"
        cmd_str = "ESPERAR"
        origen_sistema = "S1"
        es_qwen = False
        if p_ejec:
            target_str = str(p_ejec.product.get("target", "ninguno"))
            cmd_str = str(p_ejec.product.get("comando", "ESPERAR"))
            id_ganador = p_ejec.inputs[0] if p_ejec.inputs else ""
            imp_ganador = onda.reactiva.acc.get("Impulso", {}).get(id_ganador)
            if "S3" in id_ganador:
                origen_sistema = "S3"
                if cmd_str in ("MOVER", str(V_Comando.MOVER)):
                    jugadas_s3 += 1
                if imp_ganador and imp_ganador.product.get("hipotesis_ollama"):
                    es_qwen = True
            else:
                origen_sistema = "S1"

        # Log telemetría del turno
        soma = core.soma
        fen_actual = adaptador.board.fen().split(" ")[0]
        etiqueta_sistema = f"{origen_sistema}+Qwen" if es_qwen else origen_sistema
        detalle_accion = f"{cmd_str}:{target_str}" if cmd_str != "MOVER" else target_str
        log_traza(
            f"T{latido:03d} [{dt_ms:5.1f}ms] | Vit={soma.vitalidad:4.0f}% Ene={soma.energia:4.0f}% | "
            f"Dop={soma.dopamina:4.1f} Pla={soma.placer:4.1f} | Accion: {detalle_accion} ({etiqueta_sistema}) | FEN: {fen_actual}"
        )

        # Verificar fin de partida
        if adaptador.board.is_game_over() or adaptador.ultimo_resultado is not None:
            if adaptador.board.is_checkmate():
                if adaptador.board.turn == adaptador.color_ida_bool:
                    resultado_partida = "DERROTA"
                else:
                    resultado_partida = "VICTORIA"
            elif adaptador.board.is_stalemate() or adaptador.board.is_insufficient_material() or adaptador.board.can_claim_draw():
                resultado_partida = "TABLAS"
            else:
                resultado_partida = adaptador.ultimo_resultado or "TABLAS"
            break

        if latido >= max_latidos_partida:  # Límite de seguridad de latidos por partida
            resultado_partida = "TABLAS_POR_LIMITE"
            break

    log_traza(f"[+] FIN DE PARTIDA en turno {latido}: Resultado = {resultado_partida}")

    # =========================================================================
    # SUEÑO REM BORBÉLY-PRIGOGINE: CONSOLIDACIÓN DE APERTURAS Y AVERSIONES
    # =========================================================================
    log_traza("[*] Entrando en Fase de Sueño REM (Consolidación y Poda Sináptica)...")
    core.soma.estado_afectivo = V_Estado.DORMIDO
    onda_sueno = Onda(ciclo=core.ciclo_actual + 1, amplitud_max=30, frecuencia_max_ms=100.0)
    sueno_rem.procesar_sueno_rem(onda_sueno, core.soma, core.activa)
    sqlite.sincronizar_desde_activa(core.activa)

    # Extracción de Aprendizaje Epigenético para la Barrera de Weismann
    nuevos_axiomas: List[Dict[str, Any]] = []

    # 1. Si hubo derrota en apertura (menos de 15 turnos), registrar aversión a la celada
    if resultado_partida == "DERROTA" and latido <= 15:
        ultimas_jugadas = adaptador.historial_jugadas_partida[-4:]
        id_trauma = f"Aversion_Celada_{'_'.join(ultimas_jugadas)}"
        nuevos_axiomas.append({
            "id": id_trauma,
            "tipo_componente": "Aversion_Traumatica",
            "arousal": 0.98,
            "trust": 1.0,
            "product": {
                "sujeto": "IdA",
                "relacion": V_Relacion.ES_LETAL,
                "tipo_trauma": "CELADA_APERTURA_FATAL",
                "secuencia_fatal": ultimas_jugadas,
                "advertencia": "Evitar desproteccion temprana del rey o casilla f7/f2",
            },
        })
        log_traza(f"[*] Epigenética: Grabada aversión ancestral [{id_trauma}] (Trust=1.00)")

    # 2. Si hubo victoria, registrar el patrón de apertura exitoso
    elif resultado_partida == "VICTORIA":
        primeras_jugadas = adaptador.historial_jugadas_partida[:4]
        id_exito = f"Patron_Apertura_Exitosa_{'_'.join(primeras_jugadas)}"
        nuevos_axiomas.append({
            "id": id_exito,
            "tipo_componente": "Patron_Exito_Estrategico",
            "arousal": 0.85,
            "trust": 1.0,
            "product": {
                "sujeto": "IdA",
                "relacion": V_Relacion.ES_SEGURO,
                "tipo_patron": "APERTURA_VICTORIOSA",
                "secuencia": primeras_jugadas,
            },
        })
        log_traza(f"[*] Epigenética: Grabado patrón victorioso [{id_exito}] (Trust=1.00)")

    # Calcular Fitness
    capturas_totales = adaptador.capturas_ida
    adaptador.cerrar()
    fitness = calcular_fitness_ajedrez(
        turnos=latido,
        resultado=resultado_partida,
        soma=core.soma,
        capturas_realizadas=capturas_totales,
        phi_valores=phi_valores,
        jugadas_s3=jugadas_s3,
    )

    log_traza(
        f"[*] Fitness Triúnico: S1={fitness['fit_s1']} | S2={fitness['fit_s2']} | S3={fitness['fit_s3']} | "
        f"GLOBAL={fitness['fit_global']} (Capturas IdA: {capturas_totales})"
    )

    registro_partida = {
        "gen": gen,
        "individuo": arquetipo.id_individuo,
        "turnos": latido,
        "resultado": resultado_partida,
        "capturas": capturas_totales,
        "fit_s1": fitness["fit_s1"],
        "fit_s2": fitness["fit_s2"],
        "fit_s3": fitness["fit_s3"],
        "fit_global": fitness["fit_global"],
        "jugadas_s3": jugadas_s3,
        "axiomas_totales": len(axiomas_previos) + len(nuevos_axiomas),
    }

    return registro_partida, nuevos_axiomas


async def main():
    parser = argparse.ArgumentParser(description="Runner Evolutivo de IdA v12 en Ajedrez (Doble Membrana)")
    parser.add_argument("--modo", type=str, choices=["fast", "lichess"], default="fast", help="fast (local) o lichess (web)")
    parser.add_argument("--partidas", "--generaciones", dest="partidas", type=int, default=3, help="Numero de partidas/generaciones a simular")
    parser.add_argument("--color", type=str, choices=["blancas", "negras"], default="blancas", help="Bando de IdA")
    parser.add_argument("--dificultad", type=int, default=3, help="Dificultad del rival local (0: facil, 1: media, 2: tactica 2-ply, 3: club alfa-beta 3-ply [Recomendado])")
    parser.add_argument("--elo", type=int, default=None, help="Activa Stockfish local calibrado a un ELO exacto (ej. 1350, 1500, 1800)")
    parser.add_argument("--sin-ollama", "--sin-apertura", dest="sin_ollama", action="store_true", help="Desactiva la consulta a Ollama y usa solo heuristica neurosimbolica")
    parser.add_argument("--headless", action="store_true", help="En modo lichess, ejecuta el navegador sin ventana grafica visible")
    parser.add_argument("--tabula-rasa", action="store_true", help="Reinicia memoria ancestral y linaje desde cero")
    parser.add_argument(
        "--habilitar-autopoiesis",
        action="store_true",
        help="EXPERIMENTAL: activa la autopoiesis AST (muta clases en memoria con exec). Desactivada por defecto.",
    )
    args = parser.parse_args()

    log_traza("==========================================================================================")
    log_traza(f"INICIANDO SIMULACION EVOLUTIVA DE IdA v12 EN AJEDREZ (Modo: {args.modo.upper()})")
    log_traza("==========================================================================================")

    if args.tabula_rasa:
        log_traza("[!] --tabula-rasa detectado: Borrando memorias previas...")
        if os.path.exists(RUTA_LINAJE_JSON):
            os.remove(RUTA_LINAJE_JSON)
        if os.path.exists(RUTA_SQLITE):
            os.remove(RUTA_SQLITE)
        if os.path.exists(RUTA_TRAZAS):
            os.remove(RUTA_TRAZAS)

    axiomas_acumulados, historial_previo = cargar_linaje_ancestral()
    gen_inicial = len(historial_previo) + 1

    dicc_axiomas: Dict[str, Dict[str, Any]] = {ax["id"]: ax for ax in axiomas_acumulados}

    # Arquetipo inicial
    arquetipo_act = Arquetipo(
        nombre="Caissa_Natal",
        id_individuo=f"Caissa_G{gen_inicial}",
        linaje="Linaje_Caissa_Evolutivo",
        generacion=gen_inicial,
        apertura=0.75,
        responsabilidad=0.80,
        neuroticismo=0.35,
        umbral_miedo=0.60,
    )

    mejor_arquetipo = arquetipo_act
    mejor_fitness = -1.0

    for i in range(args.partidas):
        gen = gen_inicial + i
        if i > 0:
            # Selección Darwiniana: mutar a partir del mejor reproductor del linaje
            arquetipo_act = mejor_arquetipo.mutar(f"Caissa_G{gen}")

        reg, nuevos_ax = await simular_partida(
            gen=gen,
            arquetipo=arquetipo_act,
            axiomas_previos=list(dicc_axiomas.values()),
            modo=args.modo,
            color_ida=args.color,
            dificultad_rival=args.dificultad,
            elo_stockfish=args.elo,
            usar_ollama=not args.sin_ollama,
            headless=args.headless,
            habilitar_autopoiesis=args.habilitar_autopoiesis,
        )

        if reg["fit_global"] > mejor_fitness:
            mejor_fitness = reg["fit_global"]
            mejor_arquetipo = arquetipo_act
            log_traza(f"[★ NUEVO RÉCORD GENÉTICO] {arquetipo_act.id_individuo} se convierte en el reproductor del linaje (Fit={mejor_fitness:.1f})")

        historial_previo.append(reg)
        for ax in nuevos_ax:
            dicc_axiomas[ax["id"]] = ax

        guardar_linaje_ancestral(list(dicc_axiomas.values()), historial_previo, gen)

    # Imprimir Tabla Resumen Final con Linaje Completo
    log_traza("\n==========================================================================================================")
    log_traza("                         TABLA EVOLUTIVA DE LINAJE AJEDREZ (COMPARATIVA GENERACIONAL)                      ")
    log_traza("==========================================================================================================")
    log_traza(" Gen | Individuo   | Turnos | Resultado | Capts | Fit S1 | Fit S2 | Fit S3 | Fit Global | Jugadas S3 | Axiomas")
    log_traza("----------------------------------------------------------------------------------------------------------")
    for r in historial_previo:
        log_traza(
            f" {r['gen']:3d} | {r['individuo']:11s} | {r['turnos']:6d} | {r['resultado']:9s} | "
            f"{r.get('capturas', 0):5d} | {r['fit_s1']:6.1f} | {r['fit_s2']:6.1f} | {r['fit_s3']:6.1f} | "
            f"{r['fit_global']:10.1f} | {r['jugadas_s3']:10d} | {r.get('axiomas_totales', 0):7d}"
        )
    log_traza("==========================================================================================================")

    # Métricas agregadas de rendimiento del linaje completo
    tot_partidas = len(historial_previo)
    if tot_partidas > 0:
        victorias = sum(1 for r in historial_previo if r.get("resultado") == "VICTORIA")
        derrotas = sum(1 for r in historial_previo if r.get("resultado") == "DERROTA")
        tablas = sum(1 for r in historial_previo if r.get("resultado") in ("TABLAS", "TABLAS_POR_LIMITE"))
        decididas = victorias + derrotas
        pct_victorias_decididas = (victorias / decididas * 100.0) if decididas > 0 else 0.0
        pct_victorias_totales = (victorias / tot_partidas * 100.0)
        fit_medio_global = sum(r.get("fit_global", 0.0) for r in historial_previo) / tot_partidas

        log_traza(f" RESUMEN HISTÓRICO GLOBAL DEL LINAJE ({tot_partidas} partidas acumuladas):")
        log_traza(f" -> Victorias: {victorias} | Derrotas: {derrotas} | Tablas: {tablas}")
        log_traza(f" -> Ratio V vs D (sin tablas): {pct_victorias_decididas:5.1f}% victorias ({victorias}/{decididas})")
        log_traza(f" -> Tasa de Imbatibilidad (V + T): {((victorias + tablas) / tot_partidas * 100.0):5.1f}%")
        log_traza(f" -> Fitness Global Medio del Linaje: {fit_medio_global:.1f} | Axiomas Consolidados: {len(dicc_axiomas)}")
        log_traza("==========================================================================================================")

    log_traza("[FIN DE SIMULACION] Partidas concluidas con exito.")


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    asyncio.run(main())
