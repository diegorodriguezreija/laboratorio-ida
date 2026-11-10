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
from nivel_1_core.contratos import Arquetipo, Pieza
from nivel_1_core.gestor_onda import GestorOndaCore
from nivel_1_core.calculadoras_estructurales import CalculadorasEstructurales
from nivel_1_core.persistencia.motor_sqlite_wal import MotorSQLiteWAL

from nivel_2_sistemas.plasticidad_td_hebbiana import MatrizHebbianaTresFactores
from nivel_2_sistemas.s1_reactivo import crear_sistema_s1
from nivel_2_sistemas.s2_limbico import crear_sistema_s2
from nivel_2_sistemas.s3_racional import crear_sistema_s3
from nivel_2_sistemas.ciclo_sueno_rem import GestorCicloSuenoREM
from nivel_2_sistemas.consciencia_talamo_dmn import (
    BucleTalamocortical,
    RedNeuronalPorDefecto,
)
from nivel_2_sistemas.autopoiesis_ast import CirujanoAST

from nivel_3_componentes.mundos.mundo_arcade_snake.adaptador_snake import AdaptadorSnakeWeb
from nivel_3_componentes.mundos.mundo_arcade_snake.componentes_snake import (
    CompSupervivenciaSnakeS1,
    CompEstrategiaSnakeS3,
)


from nivel_3_componentes.rutas_salida import directorio_salidas, asegurar_directorio_de

# Salidas de ejecución fuera de la carpeta de código (IDA_OUT_DIR o ./salidas/snake)
RUTA_DIR_SALIDA = directorio_salidas("snake")
RUTA_TRAZAS = os.path.join(RUTA_DIR_SALIDA, "trazas_linaje.log")
RUTA_LINAJE_JSON = os.path.join(RUTA_DIR_SALIDA, "linaje_evolutivo.json")
RUTA_SQLITE = os.path.join(RUTA_DIR_SALIDA, "memoria_linaje_snake.db")


def log_traza(mensaje: str, escribir_en_consola: bool = True) -> None:
    """Escribe trazas estructuradas tanto en el log persistente como en stdout."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] {mensaje}"
    if escribir_en_consola:
        print(linea)
    with open(asegurar_directorio_de(RUTA_TRAZAS), "a", encoding="utf-8") as f:
        f.write(linea + "\n")


def cargar_linaje_ancestral() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Carga axiomas y el historial de generaciones previas desde disco."""
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
    """Consolida las verdades demostradas y el registro de linaje que cruzan Weismann."""
    data = {
        "linaje": "Linaje_Ophidia_Arcade",
        "generacion_alcanzada": generacion_max,
        "axiomas_heredados": axiomas,
        "historial_generaciones": historial,
        "actualizado": time.time(),
    }
    with open(asegurar_directorio_de(RUTA_LINAJE_JSON), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def calcular_fitness_especimen(
    latidos: int,
    muerte: bool,
    soma: Any,
    score_juego: int,
    phi_valores: List[float],
    latidos_s3: int,
    axiomas_demostrados: int,
) -> Dict[str, float]:
    """
    Calcula el fitness triunico intrinseco y el fitness global del organismo sin limite artificial de latidos:
    - S1 (Supervivencia & Reflejos): longevidad real alcanzada en latidos e integridad somatica.
    - S2 (Afecto & Homeostasis): eficiencia metabolica (nutricion vs inanicion) y balance hedonico.
    - S3 (Razon & Estrategia): volumen de nutricion acumulado, axiomas demostrados y dominancia racional.
    - Global: sintesis ponderada 0.35*S1 + 0.25*S2 + 0.40*S3.
    """
    # S1: Curva asintotica de longevidad real (250 latidos = ~63%, 500 = ~86%, 1000 = ~98%)
    longevidad_base = 100.0 * (1.0 - float(np.exp(-latidos / 250.0)))
    factor_vitalidad = float(soma.vitalidad / 100.0)
    penalizacion_muerte = 0.85 if muerte else 1.0
    f_s1 = float(min(100.0, (longevidad_base * 0.70 + factor_vitalidad * 30.0) * penalizacion_muerte))

    # S2: Balance hedonico y tasa metabolica (nutricion por latido)
    tasa_nutricion = (score_juego / max(1, latidos)) * 10.0
    balance_hedonico = float(soma.placer - soma.cortisol * 40.0)
    autoestima = float(getattr(soma, "autoestima_cognitiva", 0.50))
    f_s2 = float(max(0.0, min(100.0, 30.0 + balance_hedonico * 0.3 + min(40.0, tasa_nutricion * 8.0) + autoestima * 20.0)))

    # S3: Razon, volumen de alimento, dominancia de planificacion y Phi
    nutricion_factor = 100.0 * (1.0 - float(np.exp(-score_juego / 800.0)))
    tasa_dominancia_s3 = float(latidos_s3 / max(1, latidos))
    phi_prom = float(np.mean(phi_valores)) if phi_valores else 0.0
    f_s3 = float(min(100.0, (nutricion_factor * 0.65) + (tasa_dominancia_s3 * 15.0) + (phi_prom * 35.0) + (axiomas_demostrados * 2.0)))

    f_global = float(0.35 * f_s1 + 0.25 * f_s2 + 0.40 * f_s3)

    return {
        "s1_reactivo": round(f_s1, 1),
        "s2_limbico": round(f_s2, 1),
        "s3_racional": round(f_s3, 1),
        "global": round(f_global, 1),
        "phi_promedio": round(phi_prom, 3),
    }


def imprimir_tabla_evolutiva(historial: List[Dict[str, Any]]) -> None:
    """Imprime una tabla comparativa clara con el progreso intergeneracional."""
    if not historial:
        return
    log_traza("")
    log_traza("=" * 90)
    log_traza("                 TABLA EVOLUTIVA DE LINAJE (COMPARATIVA GENERACIONAL)                 ")
    log_traza("=" * 90)
    log_traza(f"{'Gen':^5} | {'Individuo':^14} | {'Latidos':^7} | {'Score':^5} | {'Fit S1':^7} | {'Fit S2':^7} | {'Fit S3':^7} | {'Fit Global':^10} | {'Axiomas':^7}")
    log_traza("-" * 90)
    for h in historial:
        fit = h["fitness"]
        log_traza(
            f"{h['generacion']:^5} | {h['individuo']:^14} | {h['latidos']:^7} | {h['score']:^5} | "
            f"{fit['s1_reactivo']:^7.1f} | {fit['s2_limbico']:^7.1f} | {fit['s3_racional']:^7.1f} | "
            f"{fit['global']:^10.1f} | {h['axiomas_heredables']:^7}"
        )
    log_traza("=" * 90)
    log_traza("")


async def ejecutar_simulacion_snake(
    headless: bool = True,
    tabula_rasa: bool = False,
    generaciones: int = 2,
    max_latidos_por_gen: int = 0,
    nivel_dificultad: int = 0,
    habilitar_autopoiesis: bool = False,
) -> None:
    """Orquesta el ciclo evolutivo de IdA en Playsnake.org con soporte epigenetico."""

    # Gestion de reinicio y Tabula Rasa
    if tabula_rasa:
        for r in (RUTA_TRAZAS, RUTA_LINAJE_JSON, RUTA_SQLITE):
            if os.path.exists(r):
                try:
                    os.remove(r)
                except Exception:
                    pass
        log_traza("=" * 90)
        log_traza("[TABULA RASA] Todos los linajes y memorias anteriores han sido purgados. Generacion 1 nace virgen.")
        log_traza("=" * 90)
    else:
        log_traza("=" * 90)
        log_traza("[CONTINUACION EVOLUTIVA] Cargando linaje historico de IdA...")
        log_traza("=" * 90)

    # 1. Instanciar Adaptador de Membrana
    adaptador = AdaptadorSnakeWeb(headless=headless, nivel_dificultad=nivel_dificultad)
    nombres_dif = {0: "Slug (Babosa)", 1: "Worm (Gusano)", 2: "Python (Piton)"}
    nombre_dif_str = nombres_dif.get(nivel_dificultad, str(nivel_dificultad))
    log_traza(f"[*] Dificultad seleccionada: {nombre_dif_str} (data-level={nivel_dificultad})")

    try:
        adaptador.conectar()
    except Exception as e:
        log_traza(f"[ERROR CRITICO] No se pudo inicializar Playwright en {adaptador.URL_SNAKE}: {e}")
        raise SystemExit(1)

    sqlite_db = MotorSQLiteWAL(asegurar_directorio_de(RUTA_SQLITE))
    axiomas_acumulados, historial_generaciones = cargar_linaje_ancestral()
    gen_inicial = len(historial_generaciones) + 1 if historial_generaciones and not tabula_rasa else 1

    for gen in range(gen_inicial, gen_inicial + generaciones):
        nombre_arquetipo = f"Ophidia_G{gen}"
        # Variación biológica de personalidad por individuo (deriva ontogenética)
        rng = np.random.default_rng(seed=int(time.time() * 1000) % 100000 + gen * 37)
        apertura = float(np.clip(0.65 + rng.normal(0, 0.08), 0.30, 0.95))
        responsabilidad = float(np.clip(0.80 + rng.normal(0, 0.06), 0.40, 0.95))
        neuroticismo = float(np.clip(0.35 + rng.normal(0, 0.10), 0.15, 0.85))
        umbral_miedo = float(np.clip(0.60 + rng.normal(0, 0.08), 0.25, 0.85))

        arquetipo = Arquetipo(
            nombre=nombre_arquetipo,
            id_individuo=f"Ophidia_G{gen}_{int(time.time())}",
            linaje="Linaje_Ophidia_Arcade",
            generacion=gen,
            apertura=round(apertura, 2),
            responsabilidad=round(responsabilidad, 2),
            neuroticismo=round(neuroticismo, 2),
            umbral_miedo=round(umbral_miedo, 2),
        )

        # 2. Configurar Sistemas Triunicos e inyectar componentes especializados
        hebb = MatrizHebbianaTresFactores()
        s1 = crear_sistema_s1(matriz_hebbiana=hebb)
        s2 = crear_sistema_s2()
        s3 = crear_sistema_s3()

        comp_s1_snake = CompSupervivenciaSnakeS1(peso_sinaptico=1.25)
        comp_s3_snake = CompEstrategiaSnakeS3(peso_sinaptico=1.35)
        s1.estaciones["REACCIONAR"] = [comp_s1_snake]
        s3.estaciones["REACCIONAR"] = [comp_s3_snake]

        # 3. Orquestador del Core
        core = GestorOndaCore(
            sensor=adaptador,
            actuador=adaptador,
            arquetipo=arquetipo,
            sistemas_cognitivos=[s1, s2, s3],
            bucle_talamocortical=BucleTalamocortical(),
            dmn=RedNeuronalPorDefecto(),
            gestor_sueno_rem=GestorCicloSuenoREM(),
            cirujano_ast=CirujanoAST() if habilitar_autopoiesis else None,
            sqlite_wal=sqlite_db,
            frecuencia_max_ms=120.0,
            amplitud_max=200,
        )

        # Si hay recuerdos ancestrales heredados, inyectarlos a traves de la Barrera de Weismann
        for ax in axiomas_acumulados:
            p_heredada = Pieza.from_dict(ax)
            p_heredada.heredado = True
            core.activa.consolidar_pieza(p_heredada.id, p_heredada)

        log_traza("-" * 90)
        log_traza(
            f"[*] Especimen Nacido: {arquetipo.nombre} (Gen {gen}) | Axiomas ancestrales heredados: {len(axiomas_acumulados)}"
        )
        log_traza(
            f"[*] Rasgos de Personalidad: Apertura={arquetipo.apertura:.2f} | Resp={arquetipo.responsabilidad:.2f} | "
            f"Neuroticismo={arquetipo.neuroticismo:.2f} | Umbral Miedo={arquetipo.umbral_miedo:.2f}"
        )
        log_traza(f"[*] Chasis Somatico Inicial: Vitalidad={core.soma.vitalidad:.1f}% | Energia={core.soma.energia:.1f}")

        puntuacion_maxima_gen = 0
        latidos_vividos = 0
        latidos_s3_dominante = 0
        phi_acumulado: List[float] = []
        muerte_detectada = False

        latido = 0
        while not muerte_detectada:
            latido += 1
            if max_latidos_por_gen and max_latidos_por_gen > 0 and latido > max_latidos_por_gen:
                log_traza(f"[*] Limite maximo alcanzado ({max_latidos_por_gen} latidos).")
                break

            t0_latido = time.perf_counter()

            try:
                onda = await core.ejecutar_latido()
            except Exception as e:
                log_traza(f"[ERROR LATIDO] Excepcion en ciclo {latido}: {e}")
                break

            latidos_vividos += 1
            t_ms = (time.perf_counter() - t0_latido) * 1000.0

            # Extraer accion decidida por el Tribunal Motor
            ef_dict = onda.reactiva.ef
            pieza_accion = None
            if "Ejecucion" in ef_dict and ef_dict["Ejecucion"]:
                pieza_accion = next(iter(ef_dict["Ejecucion"].values()))
            elif "Impulso" in ef_dict and ef_dict["Impulso"]:
                pieza_accion = next(iter(ef_dict["Impulso"].values()))
            elif "Accion" in ef_dict and ef_dict["Accion"]:
                pieza_accion = next(iter(ef_dict["Accion"].values()))

            cmd_str = str(pieza_accion.product.get("comando", "N/A")) if pieza_accion else "ACC_ESPERAR"
            target_str = str(pieza_accion.product.get("target", "")) if pieza_accion else ""

            # Verificar si la accion ganadora fue originada o respaldada por S3
            if (
                onda.metricas.get("sistema_ganador") == "S3"
                or (pieza_accion and ("S3" in pieza_accion.sistemas_participantes or pieza_accion.product.get("origen_sistema") == "S3"))
            ):
                latidos_s3_dominante += 1

            # Extraer impulsos competidores en acc
            acc_impulsos = onda.reactiva.acc.get("Impulso", {})
            sistemas_voces = []
            for p in acc_impulsos.values():
                sis = list(p.sistemas_participantes or ["S1"])
                sistemas_voces.append(f"{sis[0]}:{p.product.get('target', '')}(A={p.arousal:.2f})")
            voces_str = " | ".join(sistemas_voces)

            # Informacion Integrada Phi
            phi = CalculadorasEstructurales.calcular_phi_tononi(onda)
            phi_acumulado.append(phi)

            score_act = adaptador.puntuacion_actual
            if score_act > puntuacion_maxima_gen:
                puntuacion_maxima_gen = score_act

            # Fitness en vivo del latido
            fit_vivo = calcular_fitness_especimen(
                latidos=latidos_vividos,
                muerte=False,
                soma=core.soma,
                score_juego=score_act,
                phi_valores=phi_acumulado,
                latidos_s3=latidos_s3_dominante,
                axiomas_demostrados=0,
            )

            # Telemetria limpia y legible por consola
            log_traza(
                f"L{latido:03d} [{t_ms:4.1f}ms] | Vit={core.soma.vitalidad:4.0f}% Ene={core.soma.energia:4.0f}% | "
                f"Dop={core.soma.dopamina:4.1f} Pla={core.soma.placer:4.1f} | "
                f"Fit=[S1:{fit_vivo['s1_reactivo']:4.1f} S2:{fit_vivo['s2_limbico']:4.1f} S3:{fit_vivo['s3_racional']:4.1f} -> Global:{fit_vivo['global']:4.1f}] | "
                f"Acción: {cmd_str}({target_str}) | Score={score_act}"
            )

            # Comprobar muerte o fin de partida en web
            es_muerte_web = adaptador.estado_juego_web == "ended" or (score_act < puntuacion_maxima_gen and puntuacion_maxima_gen > 0)
            if core.soma.vitalidad <= 0.0 or es_muerte_web:
                hx, hy = getattr(adaptador, "ultima_cabeza_viva", adaptador.cabeza_actual)
                es_muro = (hx <= 0 or hx >= 20 or hy <= 0 or hy >= 14)
                causa_muerte = "Colisión en muro perimetral" if es_muro else "Colisión corporal / Autoencierro"
                log_traza(f"[+] COLAPSO SOMATICO / MUERTE en latido {latido}. Causa: {causa_muerte} en ({hx},{hy}).")
                adaptador.iniciar_partida_web()
                muerte_detectada = True
                break

            # El sensor esta sincronizado en fase con el tick del DOM en Chromium
            await asyncio.sleep(0.005)

        log_traza(f"[*] Fin del ciclo vital de {arquetipo.nombre}: Latidos={latidos_vividos} | Puntuacion={puntuacion_maxima_gen}")

        # =====================================================================
        # TRANSMISION EPIGENETICA POR LA BARRERA DE WEISMANN (SIN DUPLICADOS)
        # =====================================================================
        axiomas_dict = {ax["id"]: ax for ax in axiomas_acumulados}
        nuevos_axiomas = 0
        for cajon in core.activa.indice_identidad.values():
            for p in cajon.values():
                if (p.demostrado_de_novo or p.trust >= 0.85) and not p.heredado:
                    if p.id not in axiomas_dict:
                        axiomas_dict[p.id] = p.to_dict()
                        nuevos_axiomas += 1
                    else:
                        axiomas_dict[p.id]["trust"] = min(1.0, axiomas_dict[p.id]["trust"] + 0.02)

        # 1. Registro Epigenético del Trauma de Mortalidad (Patrón Negativo de Aversión)
        if muerte_detectada:
            hx, hy = adaptador.cabeza_actual
            es_muro = (hx <= 0 or hx >= 20 or hy <= 0 or hy >= 14)
            tipo_trauma = "COLISION_MURO_PERIMETRAL" if es_muro else "AUTOENCERRONA_ESPACIAL"
            trauma_id = f"Aversion_Mortal_{tipo_trauma}"
            pieza_trauma = Pieza(
                id=trauma_id,
                tipo_componente="Aversion_Traumatica",
                arousal=0.96,
                trust=0.92,
                product={
                    "sujeto": "IdA",
                    "relacion": str(V_Relacion.ES_LETAL),
                    "tipo_trauma": tipo_trauma,
                    "nodo_fatal": f"nodo_{hx}_{hy}",
                    "buffer_seguridad_recomendado": 2 if es_muro else 1,
                    "advertencia": "Evitar aproximacion perimetral a alta velocidad sin giro anticipado" if es_muro else "Evitar corredores cerrados",
                },
                demostrado_de_novo=True,
            )
            if trauma_id not in axiomas_dict:
                axiomas_dict[trauma_id] = pieza_trauma.to_dict()
                nuevos_axiomas += 1
                log_traza(f"[*] Epigenetica: Registrado nuevo trauma ancestral [{trauma_id}]")
            else:
                axiomas_dict[trauma_id]["trust"] = min(1.0, axiomas_dict[trauma_id]["trust"] + 0.04)
                log_traza(f"[*] Epigenetica: Reforzada aversion ancestral [{trauma_id}] (Trust={axiomas_dict[trauma_id]['trust']:.2f})")

        # 2. Registro Epigenético de Éxito Táctico (Patrón Positivo de Desentrampe)
        if puntuacion_maxima_gen >= 200 and latidos_vividos >= 40:
            exito_id = "Patron_Desentrampe_Circulante"
            pieza_exito = Pieza(
                id=exito_id,
                tipo_componente="Patron_Exito_Estrategico",
                arousal=0.88,
                trust=0.94,
                product={
                    "sujeto": "IdA",
                    "relacion": str(V_Relacion.ES_SEGURO),
                    "estrategia": "DESAHOGO_PERIMETRAL_AMPLIO",
                    "umbral_longitud": 6,
                    "peso_area_libre_bonus": 1.6,
                    "explicacion": "Con cuerpo largo, priorizar bolsas de espacio amplio para desahogar la cola",
                },
                demostrado_de_novo=True,
            )
            if exito_id not in axiomas_dict:
                axiomas_dict[exito_id] = pieza_exito.to_dict()
                nuevos_axiomas += 1
                log_traza(f"[*] Epigenetica: Consolidado patron de exito estrategico [{exito_id}]")
            else:
                axiomas_dict[exito_id]["trust"] = min(1.0, axiomas_dict[exito_id]["trust"] + 0.03)
                log_traza(f"[*] Epigenetica: Reforzado patron de exito estrategico [{exito_id}] (Trust={axiomas_dict[exito_id]['trust']:.2f})")

        # 3. Axioma de Supervivencia Generacional
        if latidos_vividos >= 20:
            regla_id = f"Axioma_Supervivencia_Gen{gen}"
            regla_supervivencia = Pieza(
                id=regla_id,
                tipo_componente="Proposicion_VERDAD",
                arousal=0.88,
                trust=0.92,
                product={
                    "consecuente": str(V_Relacion.ES_SEGURO),
                    "motivo": f"Supervivencia natural {latidos_vividos} latidos",
                    "puntuacion": puntuacion_maxima_gen,
                },
                demostrado_de_novo=True,
            )
            axiomas_dict[regla_id] = regla_supervivencia.to_dict()
            nuevos_axiomas += 1

        axiomas_acumulados = list(axiomas_dict.values())

        # Calculo formal de Fitness Triunico y Global
        fitness_dict = calcular_fitness_especimen(
            latidos=latidos_vividos,
            muerte=muerte_detectada,
            soma=core.soma,
            score_juego=puntuacion_maxima_gen,
            phi_valores=phi_acumulado,
            latidos_s3=latidos_s3_dominante,
            axiomas_demostrados=nuevos_axiomas,
        )

        registro_gen = {
            "generacion": gen,
            "individuo": arquetipo.nombre,
            "latidos": latidos_vividos,
            "score": puntuacion_maxima_gen,
            "fitness": fitness_dict,
            "axiomas_heredables": len(axiomas_acumulados),
            "timestamp": time.time(),
        }
        historial_generaciones.append(registro_gen)
        guardar_linaje_ancestral(axiomas_acumulados, historial_generaciones, generacion_max=gen)

        log_traza(f"[*] Barrera de Weismann: {nuevos_axiomas} nuevos axiomas ({len(axiomas_acumulados)} totales acumulados).")
        log_traza(
            f"[*] Fitness Triunico: S1={fitness_dict['s1_reactivo']} | S2={fitness_dict['s2_limbico']} | "
            f"S3={fitness_dict['s3_racional']} | GLOBAL={fitness_dict['global']}"
        )

        # Imprimir tabla comparativa actualizada
        imprimir_tabla_evolutiva(historial_generaciones)

        # Reiniciar tablero web para la siguiente generacion
        if gen < gen_inicial + generaciones - 1:
            log_traza("[*] Reiniciando entorno web para la siguiente generacion...")
            adaptador.iniciar_partida_web()
            await asyncio.sleep(1.0)

    adaptador.desconectar()
    await asyncio.sleep(0.1)
    log_traza("=" * 90)
    log_traza("[FIN DE SIMULACION] Experimento de linajes concluido con exito.")
    log_traza("=" * 90)


def mapear_dificultad(valor: str) -> int:
    """Mapea nombres o enteros de dificultad a los data-level de playsnake.org (0: Slug, 1: Worm, 2: Python)."""
    val = str(valor).strip().lower()
    mapping = {
        "0": 0, "slug": 0, "babosa": 0,
        "1": 1, "worm": 1, "gusano": 1,
        "2": 2, "python": 2, "piton": 2, "pitón": 2,
    }
    if val in mapping:
        return mapping[val]
    raise argparse.ArgumentTypeError(
        f"Dificultad inválida '{valor}'. Opciones válidas: 0/slug/babosa, 1/worm/gusano, 2/python/piton."
    )


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    parser = argparse.ArgumentParser(description="Runner Evolutivo de IdA v12 en Playsnake.org")
    parser.add_argument("--tabula-rasa", action="store_true", help="Reinicia linaje y memorias desde cero absoluto")
    parser.add_argument("--headed", action="store_true", help="Abre el navegador de forma visible")
    parser.add_argument("--generaciones", type=int, default=2, help="Numero de generaciones a simular")
    parser.add_argument(
        "--max-latidos",
        type=int,
        default=0,
        help="Maximo de latidos por generacion (0 = sin limite, vive hasta su muerte natural)",
    )
    parser.add_argument(
        "--dificultad",
        type=mapear_dificultad,
        default=0,
        help="Nivel de dificultad: 0/slug/babosa, 1/worm/gusano, 2/python/piton (default: 0)",
    )

    parser.add_argument(
        "--habilitar-autopoiesis",
        action="store_true",
        help="EXPERIMENTAL: activa la autopoiesis AST (muta clases en memoria con exec). Desactivada por defecto.",
    )

    args = parser.parse_args()

    asyncio.run(
        ejecutar_simulacion_snake(
            headless=not args.headed,
            tabula_rasa=args.tabula_rasa,
            generaciones=args.generaciones,
            max_latidos_por_gen=args.max_latidos,
            nivel_dificultad=args.dificultad,
            habilitar_autopoiesis=args.habilitar_autopoiesis,
        )
    )
