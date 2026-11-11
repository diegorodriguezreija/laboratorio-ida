"""
Mundo Crafter Runner: Orquestador Evolutivo y Alostático para IdA v12.0.
Ejecuta ciclos vitales generacionales en el entorno procedural Crafter,
consolidando la Barrera de Weismann y la plasticidad triúnica.
"""

import os
import sys

RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

import json
import math
import time
import asyncio
import argparse
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np

from nivel_1_core.vocabulario import V_Comando, V_Relacion
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

from nivel_3_componentes.mundos.mundo_crafter.adaptador_crafter import AdaptadorCrafter
from nivel_3_componentes.mundos.mundo_crafter.componentes_crafter import (
    CompCrafterS1,
    CompCrafterS2,
    CompCrafterS3,
)

from nivel_3_componentes.rutas_salida import directorio_salidas, asegurar_directorio_de

# Salidas de ejecución fuera de la carpeta de código (IDA_OUT_DIR o ./salidas/crafter)
RUTA_DIR_SALIDA = directorio_salidas("crafter")
RUTA_TRAZAS = os.path.join(RUTA_DIR_SALIDA, "trazas_crafter.log")
RUTA_LINAJE_JSON = os.path.join(RUTA_DIR_SALIDA, "linaje_evolutivo_crafter.json")
RUTA_EXPERIMENTO_HEREDABILIDAD = os.path.join(RUTA_DIR_SALIDA, "experimento_heredabilidad_crafter.json")
RUTA_SQLITE = os.path.join(RUTA_DIR_SALIDA, "memoria_linaje_crafter.db")
RUTA_REPLAYS = os.path.join(RUTA_DIR_SALIDA, "replays")


class VisorCrafterTkinter:
    """Visor gráfico interactivo en ventana local en tiempo real usando Tkinter y Pillow."""

    def __init__(self, titulo: str = "IdA v12 - Crafter 2D", tamano: Tuple[int, int] = (600, 600)):
        import tkinter as tk
        from PIL import Image, ImageTk
        self.tk = tk
        self.Image = Image
        self.ImageTk = ImageTk
        self.root = tk.Tk()
        self.root.title(titulo)
        self.root.geometry(f"{tamano[0]}x{tamano[1]}")
        self.root.resizable(False, False)
        self.label = tk.Label(self.root, bg="black")
        self.label.pack(fill="both", expand=True)
        self.tamano = tamano
        self.photo = None
        self._cerrado = False

        def _al_cerrar():
            self._cerrado = True
            try:
                self.root.destroy()
            except Exception:
                pass

        self.root.protocol("WM_DELETE_WINDOW", _al_cerrar)
        self.root.update_idletasks()
        self.root.update()

    def actualizar(self, frame_np: np.ndarray, titulo_info: str = "") -> None:
        if self._cerrado:
            return
        try:
            img = self.Image.fromarray(frame_np)
            if img.size != self.tamano:
                img = img.resize(self.tamano, self.Image.NEAREST)
            self.photo = self.ImageTk.PhotoImage(img)
            self.label.configure(image=self.photo)
            if titulo_info:
                self.root.title(titulo_info)
            self.root.update_idletasks()
            self.root.update()
        except Exception:
            self._cerrado = True

    def cerrar(self) -> None:
        if self._cerrado:
            return
        self._cerrado = True
        try:
            self.root.destroy()
        except Exception:
            pass


def log_traza(mensaje: str, escribir_en_consola: bool = True) -> None:
    """Escribe trazas estructuradas tanto en el log persistente como en stdout."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] {mensaje}"
    if escribir_en_consola:
        print(linea)
    with open(asegurar_directorio_de(RUTA_TRAZAS), "a", encoding="utf-8") as f:
        f.write(linea + "\n")


def cargar_linaje_ancestral(ruta: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Carga axiomas y el historial de generaciones previas desde disco (por defecto, el linaje de salidas)."""
    ruta_linaje = ruta or RUTA_LINAJE_JSON
    if os.path.exists(ruta_linaje):
        try:
            with open(ruta_linaje, "r", encoding="utf-8") as f:
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
        "linaje": "Linaje_Hominis_Crafter",
        "generacion_alcanzada": generacion_max,
        "axiomas_heredados": axiomas,
        "historial_generaciones": historial,
        "actualizado": time.time(),
    }
    with open(asegurar_directorio_de(RUTA_LINAJE_JSON), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def calcular_fitness_crafter(
    latidos: int,
    muerte: bool,
    salud: int,
    comida: int,
    bebida: int,
    energia: int,
    logros: Set[str],
    latidos_s3: int,
    axiomas_demostrados: int,
) -> Dict[str, float]:
    """
    Calcula el fitness triúnico intrínseco y global para Crafter:
    - S1 (Supervivencia & Reflejos): longevidad en pasos + salud remanente.
    - S2 (Afecto & Alostasis): equilibrio homeostático (comida, bebida, energía).
    - S3 (Razon & Logros): cantidad y complejidad de logros tecnológicos del Tech Tree.
    - Global: síntesis ponderada 0.30*S1 + 0.30*S2 + 0.40*S3.
    """
    # S1: Longevidad asintótica (200 latidos = ~63%, 500 = ~92%)
    longevidad_base = 100.0 * (1.0 - float(np.exp(-latidos / 200.0)))
    factor_salud = float(salud / 9.0) * 100.0
    penalizacion_muerte = 0.80 if muerte else 1.0
    f_s1 = float(min(100.0, (longevidad_base * 0.60 + factor_salud * 0.40) * penalizacion_muerte))

    # S2: Homeostasis media (comida, bebida, energía sobre 9)
    media_homeostatica = ((comida + bebida + energia) / 27.0) * 100.0
    f_s2 = float(min(100.0, media_homeostatica))

    # S3: Logros del Tech Tree
    puntos_logros = len(logros) * 12.0
    # Bonus especiales por hitos clave de crafting
    if "make_wood_pickaxe" in logros:
        puntos_logros += 15.0
    if "make_stone_pickaxe" in logros:
        puntos_logros += 20.0
    if "make_stone_sword" in logros:
        puntos_logros += 20.0
    if "defeat_zombie" in logros or "defeat_skeleton" in logros:
        puntos_logros += 25.0

    ratio_s3 = (latidos_s3 / max(1, latidos)) * 40.0
    f_s3 = float(min(100.0, puntos_logros + ratio_s3 + axiomas_demostrados * 5.0))

    f_global = float(0.30 * f_s1 + 0.30 * f_s2 + 0.40 * f_s3)

    return {
        "s1_reactivo": round(f_s1, 1),
        "s2_limbico": round(f_s2, 1),
        "s3_racional": round(f_s3, 1),
        "global": round(f_global, 1),
    }


ACHIEVEMENTS_22 = [
    "collect_coal", "collect_diamond", "collect_drink", "collect_iron",
    "collect_sapling", "collect_stone", "collect_wood", "defeat_skeleton",
    "defeat_zombie", "eat_cow", "eat_plant", "make_iron_pickaxe",
    "make_iron_sword", "make_stone_pickaxe", "make_stone_sword",
    "make_wood_pickaxe", "make_wood_sword", "place_furnace", "place_plant",
    "place_stone", "place_table", "wake_up"
]


def calcular_crafter_score_desde_tasas(success_rates: Dict[str, float]) -> Tuple[float, float]:
    """
    Función canónica única para el Crafter Score (Hafner, 2021):
        S = exp( (1 / 22) * sum_{i=1}^{22} ln(1 + s_i) ) - 1
    donde s_i en [0, 100] es el porcentaje de episodios en que se desbloqueó el logro i.
    Retorna (crafter_score, sum_ln).
    """
    log_sum = sum(math.log(1.0 + float(success_rates.get(ach, 0.0))) for ach in ACHIEVEMENTS_22)
    crafter_score = float(math.exp(log_sum / len(ACHIEVEMENTS_22)) - 1.0)
    return crafter_score, log_sum


def calcular_crafter_score_poblacional(historial: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extrae la matriz de logros por episodio desde `historial`, calcula las 22 tasas s_i
    y evalúa el Crafter Score con `calcular_crafter_score_desde_tasas`.
    """
    n_ep = len(historial)
    matriz_episodios: List[Dict[str, int]] = []
    for h in historial:
        logros_ep = set(h.get("logros", []))
        matriz_episodios.append({ach: (1 if ach in logros_ep else 0) for ach in ACHIEVEMENTS_22})

    success_rates: Dict[str, float] = {}
    conteos: Dict[str, int] = {}
    for ach in ACHIEVEMENTS_22:
        c = sum(fila[ach] for fila in matriz_episodios)
        conteos[ach] = c
        success_rates[ach] = (c / n_ep) * 100.0 if n_ep > 0 else 0.0

    crafter_score, log_sum = calcular_crafter_score_desde_tasas(success_rates)
    logros_desbloqueados = [ach for ach, r in success_rates.items() if r > 0.0]

    return {
        "num_episodios": n_ep,
        "matriz_episodios": matriz_episodios,
        "conteos": conteos,
        "success_rates": success_rates,
        "sum_ln": log_sum,
        "crafter_score": crafter_score,
        "logros_desbloqueados": logros_desbloqueados,
    }


def calcular_crafter_score_episodio(logros: List[str]) -> float:
    """
    Crafter Score de un único episodio, calculado con la función canónica (tasas 0 % o 100 %).
    Es un indicador por individuo; la cifra comparable con la literatura es la poblacional.
    """
    return calcular_crafter_score_poblacional([{"logros": list(logros)}])["crafter_score"]


def imprimir_tabla_evolutiva(historial: List[Dict[str, Any]]) -> None:
    """Imprime una tabla comparativa clara con el progreso intergeneracional y el Crafter Score oficial."""
    if not historial:
        return
    log_traza("")
    log_traza("=" * 100)
    log_traza("               TABLA EVOLUTIVA CRAFTER (COMPARATIVA GENERACIONAL)               ")
    log_traza("=" * 100)
    log_traza(f"{'Gen':^5} | {'Individuo':^14} | {'Pasos':^6} | {'Salud':^5} | {'Logros':^6} | {'Fit S1':^7} | {'Fit S2':^7} | {'Fit S3':^7} | {'Global':^8} | {'Heredables':^10}")
    log_traza("-" * 100)
    for h in historial:
        fit = h["fitness"]
        log_traza(
            f"{h['generacion']:^5} | {h['individuo']:^14} | {h['latidos']:^6} | {h.get('salud_final', 0):^5} | {h.get('total_logros', 0):^6} | "
            f"{fit['s1_reactivo']:^7.1f} | {fit['s2_limbico']:^7.1f} | {fit['s3_racional']:^7.1f} | "
            f"{fit['global']:^8.1f} | {h['axiomas_heredables']:^10}"
        )
    log_traza("=" * 100)

    # Cálculo oficial del Crafter Score mediante la función canónica única
    res_bench = calcular_crafter_score_poblacional(historial)
    success_rates = res_bench["success_rates"]
    crafter_score = res_bench["crafter_score"]
    logros_desbloqueados = res_bench["logros_desbloqueados"]

    # Identificar el espécimen cumbre (Mejor Individuo del Linaje)
    mejor_ind = None
    mejor_ind_score = 0.0
    if historial:
        def score_individual(h: Dict[str, Any]) -> float:
            return calcular_crafter_score_episodio(h.get("logros", []))

        mejor_ind = max(
            historial,
            key=lambda h: (
                len(h.get("logros", [])),
                h.get("fitness", {}).get("global", 0.0) if isinstance(h.get("fitness"), dict) else 0.0
            )
        )
        mejor_ind_score = score_individual(mejor_ind)

    log_traza("")
    log_traza("=" * 100)
    log_traza("             BENCHMARK OFICIAL CRAFTER (Hafner et al., 2021) - RESULTADOS GLOBALES             ")
    log_traza("=" * 100)
    log_traza(f"  * CRAFTER SCORE GLOBAL (POBLACIÓN): {crafter_score:.2f}%  (Evaluado sobre {len(historial)} generaciones / {sum(h['latidos'] for h in historial)} latidos)")
    if mejor_ind:
        m_nom = mejor_ind.get("individuo", "Desconocido")
        m_gen = mejor_ind.get("generacion", "?")
        m_pasos = mejor_ind.get("latidos", 0)
        m_salud = mejor_ind.get("salud_final", 0)
        m_fit = mejor_ind.get("fitness", {})
        m_fg = m_fit.get("global", 0.0) if isinstance(m_fit, dict) else 0.0
        m_logros = mejor_ind.get("logros", [])
        log_traza(f"  * MEJOR CANDIDATO (PICO DEL LINAJE): {m_nom} (Gen {m_gen})")
        log_traza(f"      - Crafter Score Individual: {mejor_ind_score:.2f}%")
        log_traza(f"      - Total Logros ({len(m_logros)}/22): {m_logros}")
        log_traza(f"      - Latidos vividos: {m_pasos} | Salud final: {m_salud}/9 | Fitness Global: {m_fg:.1f}")
    log_traza("-" * 100)
    # Distribución Estadística Completa (Media, SD, Mediana, IQR, Rango y Evolución por Bloques)
    fits_globales = [
        float(h.get("fitness", {}).get("global", 0.0)) if isinstance(h.get("fitness"), dict) else 0.0
        for h in historial
    ]
    logros_counts = [int(h.get("total_logros", len(h.get("logros", [])))) for h in historial]
    pasos_counts = [int(h.get("latidos", 0)) for h in historial]

    if fits_globales:
        fg_arr = np.array(fits_globales, dtype=float)
        lg_arr = np.array(logros_counts, dtype=float)
        ps_arr = np.array(pasos_counts, dtype=float)
        fg_q25, fg_med, fg_q75 = np.percentile(fg_arr, [25, 50, 75])
        lg_q25, lg_med, lg_q75 = np.percentile(lg_arr, [25, 50, 75])
        log_traza("  * DISTRIBUCION ESTADISTICA DE LA POBLACION (NO SOLO EL PICO):")
        log_traza(
            f"      - Fitness Global : Media = {np.mean(fg_arr):.2f} ± {np.std(fg_arr):.2f} | "
            f"Mediana = {fg_med:.2f} (IQR: {fg_q25:.2f}–{fg_q75:.2f}) | Rango = [{np.min(fg_arr):.1f}, {np.max(fg_arr):.1f}]"
        )
        log_traza(
            f"      - Logros / Gen   : Media = {np.mean(lg_arr):.2f} ± {np.std(lg_arr):.2f} | "
            f"Mediana = {lg_med:.1f} (IQR: {lg_q25:.1f}–{lg_q75:.1f}) | Rango = [{int(np.min(lg_arr))}, {int(np.max(lg_arr))}]"
        )
        log_traza(
            f"      - Pasos / Gen    : Media = {np.mean(ps_arr):.1f} ± {np.std(ps_arr):.1f} | "
            f"Mediana = {np.median(ps_arr):.1f} | Rango = [{int(np.min(ps_arr))}, {int(np.max(ps_arr))}]"
        )

        # Desglose por terciles/bloques generacionales si hay >= 6 generaciones
        n_total = len(historial)
        if n_total >= 6:
            tam_bloque = max(2, n_total // 3)
            log_traza("  * PROGRESION DE LA DISTRIBUCION POR BLOQUES GENERACIONALES:")
            for b_idx in range(0, n_total, tam_bloque):
                sub = historial[b_idx:b_idx + tam_bloque]
                if not sub:
                    continue
                g_ini = sub[0].get("generacion", b_idx + 1)
                g_fin = sub[-1].get("generacion", b_idx + len(sub))
                sub_fg = [float(x["fitness"]["global"]) for x in sub]
                sub_lg = [int(x.get("total_logros", len(x.get("logros", [])))) for x in sub]
                sub_cs = calcular_crafter_score_poblacional(sub)["crafter_score"]
                log_traza(
                    f"      - Bloque G{g_ini:02d}–G{g_fin:02d} (n={len(sub):2d}): "
                    f"Fit Media={np.mean(sub_fg):5.2f}±{np.std(sub_fg):4.2f} (Med={np.median(sub_fg):5.2f}, Pico={np.max(sub_fg):5.1f}) | "
                    f"Logros Media={np.mean(sub_lg):4.2f} (Pico={int(np.max(sub_lg)):2d}) | Crafter Score Bloque={sub_cs:5.2f}%"
                )
    log_traza("-" * 100)
    log_traza(f"  * Logros Desbloqueados por la Población ({len(logros_desbloqueados)}/22): {sorted(logros_desbloqueados)}")
    log_traza("  * Tasas de Exito por Logro:")
    for ach in sorted(logros_desbloqueados, key=lambda a: -success_rates[a]):
        log_traza(f"      - {ach:20s}: {success_rates[ach]:5.1f}%")
    log_traza("=" * 100)
    log_traza("")


async def ejecutar_simulacion_crafter(
    modo_fast: bool = False,
    tabula_rasa: bool = False,
    generaciones: int = 3,
    max_latidos_por_gen: int = 400,
    seed: Optional[int] = None,
    gui: bool = False,
    guardar_gif: bool = False,
    fps: int = 12,
    habilitar_autopoiesis: bool = False,
) -> None:
    """Orquesta el ciclo evolutivo de IdA en Crafter con soporte epigenético y visualización opcional."""

    # Gestión de reinicio y Tabula Rasa
    if tabula_rasa:
        for r in (RUTA_TRAZAS, RUTA_LINAJE_JSON, RUTA_SQLITE):
            if os.path.exists(r):
                try:
                    os.remove(r)
                except Exception:
                    pass
        log_traza("=" * 90)
        log_traza("[TABULA RASA] Todos los linajes y memorias anteriores purgados. Generación 1 nace virgen.")
        log_traza("=" * 90)
    else:
        log_traza("=" * 90)
        log_traza("[CONTINUACION EVOLUTIVA] Cargando linaje histórico de IdA en Crafter...")
        log_traza("=" * 90)

    # 1. Instanciar Adaptador de Membrana
    adaptador = AdaptadorCrafter(seed=seed, max_pasos=max_latidos_por_gen)
    try:
        adaptador.conectar()
    except Exception as e:
        log_traza(f"[ERROR CRITICO] No se pudo inicializar Crafter: {e}")
        raise SystemExit(1)

    # Visor gráfico opcional
    visor: Optional[VisorCrafterTkinter] = None
    if gui:
        try:
            visor = VisorCrafterTkinter()
            log_traza("[*] GUI Activa: Ventana gráfica abierta a 600x600 px.")
        except Exception as e:
            log_traza(f"[AVISO] No se pudo abrir GUI Tkinter: {e}")

    if guardar_gif:
        os.makedirs(RUTA_REPLAYS, exist_ok=True)

    sqlite_db = MotorSQLiteWAL(asegurar_directorio_de(RUTA_SQLITE))
    axiomas_acumulados, historial_generaciones = cargar_linaje_ancestral()
    gen_inicial = len(historial_generaciones) + 1 if historial_generaciones and not tabula_rasa else 1

    # Reconstruir el mejor arquetipo del linaje si continuamos una evolución previa
    mejor_arquetipo: Optional[Arquetipo] = None
    mejor_fitness_linaje: float = -1.0
    if historial_generaciones and not tabula_rasa:
        mejor_reg = max(
            historial_generaciones,
            key=lambda h: (
                len(h.get("logros", [])),
                float(h.get("fitness", {}).get("global", 0.0)) if isinstance(h.get("fitness"), dict) else 0.0,
            ),
        )
        mejor_fitness_linaje = float(mejor_reg.get("fitness", {}).get("global", 0.0))
        arq_dict = mejor_reg.get("arquetipo_rasgos", {})
        mejor_arquetipo = Arquetipo(
            nombre=str(mejor_reg.get("individuo", "Hominis_Ancestral")),
            id_individuo=str(mejor_reg.get("individuo", "Hominis_Ancestral")),
            linaje="Linaje_Hominis_Crafter",
            generacion=int(mejor_reg.get("generacion", 1)),
            apertura=float(arq_dict.get("apertura", 0.72)),
            responsabilidad=float(arq_dict.get("responsabilidad", 0.76)),
            neuroticismo=float(arq_dict.get("neuroticismo", 0.38)),
            umbral_miedo=float(arq_dict.get("umbral_miedo", 0.62)),
        )

    for gen in range(gen_inicial, gen_inicial + generaciones):
        nombre_arquetipo = f"Hominis_G{gen}"
        rng = np.random.default_rng(seed=(seed or 42) + gen * 31)

        if gen == 1 or mejor_arquetipo is None:
            # Fundador Tabula Rasa: rasgos iniciales ingenuos (aún sin selección ni axiomas)
            apertura = float(np.clip(0.48 + rng.normal(0, 0.03), 0.35, 0.60))
            responsabilidad = float(np.clip(0.46 + rng.normal(0, 0.03), 0.35, 0.58))
            neuroticismo = float(np.clip(0.56 + rng.normal(0, 0.04), 0.35, 0.75))
            umbral_miedo = float(np.clip(0.42 + rng.normal(0, 0.03), 0.30, 0.55))
            id_padre = None
        else:
            # Selección Darwiniana gradual + deriva adaptativa acoplada al acervo epigenético
            n_ax = len(axiomas_acumulados)
            progreso_gen = min(1.0, (gen - 1) / 8.0)
            impulso_epigenetico = min(0.08, n_ax * 0.004) * progreso_gen
            apertura = float(np.clip(mejor_arquetipo.apertura + 0.035 + impulso_epigenetico * 0.4 + rng.normal(0.0, 0.015), 0.40, 0.92))
            responsabilidad = float(np.clip(mejor_arquetipo.responsabilidad + 0.042 + impulso_epigenetico * 0.5 + rng.normal(0.0, 0.015), 0.42, 0.94))
            neuroticismo = float(np.clip(mejor_arquetipo.neuroticismo - 0.020 - impulso_epigenetico * 0.2 + rng.normal(0.0, 0.015), 0.22, 0.78))
            umbral_miedo = float(np.clip(mejor_arquetipo.umbral_miedo + 0.030 + impulso_epigenetico * 0.3 + rng.normal(0.0, 0.015), 0.35, 0.85))
            id_padre = mejor_arquetipo.id_individuo

        arquetipo = Arquetipo(
            nombre=nombre_arquetipo,
            id_individuo=f"Hominis_G{gen}_{int(time.time())}",
            id_padre=id_padre,
            linaje="Linaje_Hominis_Crafter",
            generacion=gen,
            apertura=round(apertura, 2),
            responsabilidad=round(responsabilidad, 2),
            neuroticismo=round(neuroticismo, 2),
            umbral_miedo=round(umbral_miedo, 2),
        )

        # 2. Configurar Sistemas Triúnicos e inyectar componentes de Crafter
        hebb = MatrizHebbianaTresFactores()
        s1 = crear_sistema_s1(matriz_hebbiana=hebb)
        s2 = crear_sistema_s2()
        s3 = crear_sistema_s3()

        comp_s1_crafter = CompCrafterS1(peso_sinaptico=1.25)
        comp_s2_crafter = CompCrafterS2(peso_sinaptico=1.15)
        comp_s3_crafter = CompCrafterS3(peso_sinaptico=1.35)

        s1.estaciones["REACCIONAR"] = [comp_s1_crafter]
        s2.inyectar_componente("INTERPRETAR", comp_s2_crafter)
        s3.estaciones["REACCIONAR"] = [
            c for c in s3.estaciones["REACCIONAR"] if c.id_componente != "Comp_Impulso_S3"
        ]
        s3.inyectar_componente("ACTUAR", comp_s3_crafter)

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
            frecuencia_max_ms=2500.0,
            amplitud_max=250,
        )

        # Inyectar axiomas ancestrales heredados
        for ax in axiomas_acumulados:
            p_heredada = Pieza.from_dict(ax)
            p_heredada.heredado = True
            core.activa.consolidar_pieza(p_heredada.id, p_heredada)

        seed_episodio = (seed or 42) + gen * 17
        adaptador.reiniciar(seed=seed_episodio)

        log_traza("-" * 90)
        log_traza(
            f"[*] Especimen Nacido: {arquetipo.nombre} (Gen {gen}) | Axiomas ancestrales heredados: {len(axiomas_acumulados)}"
        )
        log_traza(
            f"[*] Rasgos de Personalidad: Apertura={arquetipo.apertura:.2f} | Resp={arquetipo.responsabilidad:.2f} | "
            f"Neuroticismo={arquetipo.neuroticismo:.2f} | Umbral Miedo={arquetipo.umbral_miedo:.2f}"
        )

        latidos_vividos = 0
        latidos_s3_dominante = 0
        phi_acumulado: List[float] = []
        muerte_detectada = False
        causa_muerte_str = "Desconocida"
        frames_episodio: List[np.ndarray] = []

        latido = 0
        while not muerte_detectada:
            latido += 1
            if max_latidos_por_gen and latido > max_latidos_por_gen:
                log_traza(f"[*] Limite maximo alcanzado ({max_latidos_por_gen} latidos).")
                break

            t0_latido = time.perf_counter()

            try:
                onda = await core.ejecutar_latido()
            except Exception as e:
                import traceback
                log_traza(f"[ERROR LATIDO] Excepcion en ciclo {latido}: {e}\n{traceback.format_exc()}")
                break

            latidos_vividos += 1
            t_ms = (time.perf_counter() - t0_latido) * 1000.0

            # Extraer acción decidida por el Tribunal Motor
            p_ejec = next(iter(onda.reactiva.ef.get("Ejecucion", {}).values()), None)
            cmd_str = "ACC_ESPERAR"
            target_str = ""
            origen_sistema = str(onda.metricas.get("sistema_ganador", "S1"))

            if p_ejec:
                cmd_str = str(p_ejec.product.get("comando", "ACC_ESPERAR"))
                target_str = str(p_ejec.product.get("target", ""))
                if origen_sistema == "S3":
                    latidos_s3_dominante += 1

            phi = float(onda.metricas.get("phi", 0.0))
            phi_acumulado.append(phi)

            # Extraer estado del entorno desde el adaptador
            player = adaptador.env._player
            salud_act = int(player.health)
            comida_act = int(player.inventory.get("food", 9))
            bebida_act = int(player.inventory.get("drink", 9))
            energia_act = int(player.inventory.get("energy", 9))
            daylight_act = float(adaptador.env._world.daylight)
            fase_dia = "NOCHE" if daylight_act < 0.25 else ("DIA" if daylight_act > 0.60 else "CREP")

            fit_vivo = calcular_fitness_crafter(
                latidos=latidos_vividos,
                muerte=False,
                salud=salud_act,
                comida=comida_act,
                bebida=bebida_act,
                energia=energia_act,
                logros=adaptador.logros_desbloqueados,
                latidos_s3=latidos_s3_dominante,
                axiomas_demostrados=0,
            )

            # Extraer impulsos competidores en acc
            acc_impulsos = onda.reactiva.acc.get("Impulso", {})
            sistemas_voces = []
            for p in acc_impulsos.values():
                sis = list(p.sistemas_participantes or ["S1"])
                sistemas_voces.append(f"{sis[0]}:{str(p.product.get('comando', ''))}:{str(p.product.get('target', ''))}(A={p.arousal:.2f})")
            voces_str = " | ".join(sistemas_voces)

            # Telemetría cada paso
            logros_str = f"[{len(adaptador.logros_desbloqueados)} logros]"
            log_traza(
                f"L{latido:03d} [{t_ms:4.1f}ms] | H={salud_act}/9 F={comida_act}/9 D={bebida_act}/9 E={energia_act}/9 | "
                f"Luz={daylight_act:.2f}({fase_dia}) | {logros_str} | "
                f"Fit=[S1:{fit_vivo['s1_reactivo']:4.1f} S2:{fit_vivo['s2_limbico']:4.1f} S3:{fit_vivo['s3_racional']:4.1f} -> {fit_vivo['global']:4.1f}] | "
                f"Accion: {cmd_str}({target_str}) | Voces: [{voces_str}]"
            )

            # Detección de colapso somático / muerte
            if salud_act <= 0 or adaptador.partida_terminada:
                if salud_act <= 0:
                    if comida_act <= 0:
                        causa_muerte_str = "Inanicion / Hambre extrema"
                    elif bebida_act <= 0:
                        causa_muerte_str = "Deshidratacion / Sed extrema"
                    elif adaptador.env._world[player.pos][0] == "lava":
                        causa_muerte_str = "Muerte termica instantanea (Lava)"
                    else:
                        causa_muerte_str = "Ataque letal de Depredador (Zombie/Esqueleto)"
                else:
                    causa_muerte_str = "Limite de pasos o fin de episodio"

                log_traza(f"[+] COLAPSO SOMATICO / MUERTE en latido {latido}. Causa: {causa_muerte_str}.")
                muerte_detectada = True
                break

            # Renderizado gráfico opcional en vivo o captura de replay
            if visor is not None and not getattr(visor, "_cerrado", False):
                frame_visor = adaptador.env.render((600, 600))
                h_sub = int(getattr(player, "_hunger", 0))
                t_sub = int(getattr(player, "_thirst", 0))
                titulo_hud = (
                    f"IdA Crafter {arquetipo.nombre} | L:{latido:03d} | "
                    f"H:{salud_act}/9 F:{comida_act}({h_sub}/25) D:{bebida_act}({t_sub}/20) E:{energia_act} | "
                    f"{fase_dia} | {cmd_str}"
                )
                visor.actualizar(frame_visor, titulo_hud)
                delay_fps = 1.0 / max(1, fps)
                await asyncio.sleep(delay_fps)
            elif not modo_fast:
                t_restante = max(0.0, 0.08 - (t_ms / 1000.0))
                if t_restante > 0:
                    await asyncio.sleep(t_restante)

            if guardar_gif:
                frame_rec = adaptador.env.render((512, 512))
                frames_episodio.append(frame_rec)

        log_traza(
            f"[*] Fin del ciclo vital de {arquetipo.nombre}: Pasos={latidos_vividos} | "
            f"Logros={len(adaptador.logros_desbloqueados)}: {sorted(list(adaptador.logros_desbloqueados))}"
        )

        if guardar_gif and frames_episodio:
            try:
                import imageio
                ruta_gif_gen = os.path.join(RUTA_REPLAYS, f"replay_{arquetipo.nombre}.gif")
                imageio.mimsave(ruta_gif_gen, frames_episodio, fps=fps)
                log_traza(f"[*] Replay visual guardado con exito: {ruta_gif_gen} ({len(frames_episodio)} frames)")
            except Exception as e:
                log_traza(f"[AVISO] Error guardando GIF de replay: {e}")

        # =====================================================================
        # TRANSMISION EPIGENETICA POR LA BARRERA DE WEISMANN
        # =====================================================================
        axiomas_dict = {ax["id"]: ax for ax in axiomas_acumulados}
        nuevos_axiomas = 0

        # 1. Epigenética del Trauma de Mortalidad
        if muerte_detectada and "Limite" not in causa_muerte_str:
            trauma_id = f"Trauma_{causa_muerte_str.replace(' ', '_').replace('/', '_')}"
            pieza_trauma = Pieza(
                id=trauma_id,
                tipo_componente="Aversion_Traumatica",
                arousal=0.97,
                trust=0.95,
                product={
                    "sujeto": "IdA_Crafter",
                    "relacion": str(V_Relacion.ES_LETAL),
                    "tipo_trauma": causa_muerte_str,
                    "advertencia": f"Evitar condicion fatal de {causa_muerte_str}",
                },
                demostrado_de_novo=True,
            )
            if trauma_id not in axiomas_dict:
                axiomas_dict[trauma_id] = pieza_trauma.to_dict()
                nuevos_axiomas += 1
                log_traza(f"[*] Epigenetica: Registrado nuevo trauma ancestral [{trauma_id}]")
            else:
                axiomas_dict[trauma_id]["trust"] = min(1.0, axiomas_dict[trauma_id]["trust"] + 0.03)

        # 2. Epigenética de Logros y Éxitos Tecnológicos
        for logro in adaptador.logros_desbloqueados:
            logro_id = f"Axioma_Logro_{logro}"
            pieza_logro = Pieza(
                id=logro_id,
                tipo_componente="Patron_Exito_Estrategico",
                arousal=0.85,
                trust=0.92,
                product={
                    "sujeto": "IdA_Crafter",
                    "relacion": str(V_Relacion.ES_SEGURO),
                    "logro_obtenido": logro,
                    "eficacia": "Patron exitoso verificado en Crafter",
                },
                demostrado_de_novo=True,
            )
            if logro_id not in axiomas_dict:
                axiomas_dict[logro_id] = pieza_logro.to_dict()
                nuevos_axiomas += 1
                log_traza(f"[*] Epigenetica: Consolidado logro ancestral [{logro}]")

        # 3. Axioma de Supervivencia Circadiana
        if latidos_vividos >= 50:
            regla_id = f"Axioma_Supervivencia_Gen{gen}"
            pieza_superv = Pieza(
                id=regla_id,
                tipo_componente="Proposicion_VERDAD",
                arousal=0.88,
                trust=0.90,
                product={
                    "consecuente": str(V_Relacion.ES_SEGURO),
                    "pasos_sobrevividos": latidos_vividos,
                    "logros_totales": len(adaptador.logros_desbloqueados),
                },
                demostrado_de_novo=True,
            )
            axiomas_dict[regla_id] = pieza_superv.to_dict()
            nuevos_axiomas += 1

        axiomas_acumulados = list(axiomas_dict.values())

        # Cálculo formal de Fitness
        player = adaptador.env._player
        fitness_final = calcular_fitness_crafter(
            latidos=latidos_vividos,
            muerte=muerte_detectada,
            salud=int(player.health),
            comida=int(player.inventory.get("food", 9)),
            bebida=int(player.inventory.get("drink", 9)),
            energia=int(player.inventory.get("energy", 9)),
            logros=adaptador.logros_desbloqueados,
            latidos_s3=latidos_s3_dominante,
            axiomas_demostrados=nuevos_axiomas,
        )

        if fitness_final["global"] > mejor_fitness_linaje:
            mejor_fitness_linaje = float(fitness_final["global"])
            mejor_arquetipo = arquetipo
            log_traza(
                f"[★ NUEVO RECORD GENETICO] {arquetipo.nombre} se convierte en el reproductor del linaje "
                f"(Fit={mejor_fitness_linaje:.1f}, Logros={len(adaptador.logros_desbloqueados)}, Seed={seed_episodio})"
            )

        registro_gen = {
            "generacion": gen,
            "individuo": arquetipo.nombre,
            "seed_episodio": seed_episodio,
            "arquetipo_rasgos": {
                "apertura": arquetipo.apertura,
                "responsabilidad": arquetipo.responsabilidad,
                "neuroticismo": arquetipo.neuroticismo,
                "umbral_miedo": arquetipo.umbral_miedo,
            },
            "latidos": latidos_vividos,
            "salud_final": int(player.health),
            "total_logros": len(adaptador.logros_desbloqueados),
            "logros": sorted(list(adaptador.logros_desbloqueados)),
            "causa_muerte": causa_muerte_str,
            "fitness": fitness_final,
            "axiomas_heredables": len(axiomas_acumulados),
            "timestamp": time.time(),
        }
        historial_generaciones.append(registro_gen)
        guardar_linaje_ancestral(axiomas_acumulados, historial_generaciones, gen)

        log_traza(
            f"[*] Generación {gen} finalizada | Fitness Global: {fitness_final['global']} "
            f"(S1:{fitness_final['s1_reactivo']} S2:{fitness_final['s2_limbico']} S3:{fitness_final['s3_racional']}) | "
            f"Axiomas acumulados: {len(axiomas_acumulados)}"
        )

    if visor is not None:
        visor.cerrar()
    adaptador.desconectar()
    imprimir_tabla_evolutiva(historial_generaciones)


def fijar_cortisol(soma: Any, valor: float) -> None:
    """
    Manipulación experimental de H2 (nivel 3): deja el cortisol del soma fijo en `valor`
    durante todo el episodio. Las escrituras del propio core (soma, S2, DMN) se ignoran, de
    modo que el Tribunal arbitra siempre con ese valor.

    Corrige R1: fijar el valor solo al principio de cada latido no bastaba, porque el core lo
    reescribía antes del arbitraje (con 'fijo_0.90' el Tribunal veía de media 0.47).
    """
    clase_original = type(soma)
    soma.__class__ = type(
        f"{clase_original.__name__}CortisolFijo",
        (clase_original,),
        {"cortisol": property(lambda self: valor, lambda self, _nuevo: None)},
    )


async def evaluar_individuo_en_semilla(
    adaptador: AdaptadorCrafter,
    arquetipo: Arquetipo,
    axiomas_heredados: List[Dict[str, Any]],
    seed_mapa: int,
    max_latidos: int = 500,
    aislar_ruido_termodinamico: bool = False,
    arbitro: Optional[Any] = None,
    modo_ablacion: str = "nivel_a",
    s2_neutro: bool = False,
    soma_modulacion: str = "on",
    recolectar_telemetria: bool = False,
    habilitar_autopoiesis: bool = False,
    memoria_alocentrica: bool = True,
) -> Dict[str, Any]:
    """
    Evalúa de forma limpia y aislada un individuo (con su Arquetipo y su lista de axiomas Weismann)
    sobre una semilla procedural exacta de Crafter, con soporte completo para árbitros intercambiables,
    niveles de ablación (a vs b), s2 neutro y modulación somática.
    """
    hebb = MatrizHebbianaTresFactores()
    s1 = crear_sistema_s1(matriz_hebbiana=hebb)
    s2 = crear_sistema_s2()
    s3 = crear_sistema_s3()

    comp_s1_crafter = CompCrafterS1(peso_sinaptico=1.25)
    comp_s2_crafter = CompCrafterS2(peso_sinaptico=0.0 if s2_neutro else 1.15)
    comp_s3_crafter = CompCrafterS3(peso_sinaptico=1.35)

    s1.estaciones["REACCIONAR"] = [comp_s1_crafter]
    if not s2_neutro:
        s2.inyectar_componente("INTERPRETAR", comp_s2_crafter)
    s3.estaciones["REACCIONAR"] = [
        c for c in s3.estaciones["REACCIONAR"] if c.id_componente != "Comp_Impulso_S3"
    ]
    s3.inyectar_componente("ACTUAR", comp_s3_crafter)

    # D7: autopoiesis AST solo si se pide expresamente
    cirujano = CirujanoAST() if habilitar_autopoiesis else None
    core = GestorOndaCore(
        sensor=adaptador,
        actuador=adaptador,
        arquetipo=arquetipo,
        sistemas_cognitivos=[s1, s2, s3],
        bucle_talamocortical=BucleTalamocortical(),
        dmn=RedNeuronalPorDefecto(),
        gestor_sueno_rem=GestorCicloSuenoREM(),
        cirujano_ast=cirujano,
        sqlite_wal=None,
        frecuencia_max_ms=2500.0,
        amplitud_max=250,
        arbitro=arbitro,
        modo_ablacion=modo_ablacion,
    )
    if aislar_ruido_termodinamico:
        core.cosechador.amplitud_basal = 0.0
        core.cosechador.cosechar_unidad_uniforme = lambda: 0.5

    for ax in axiomas_heredados:
        p_heredada = Pieza.from_dict(ax)
        p_heredada.heredado = True
        core.activa.consolidar_pieza(p_heredada.id, p_heredada)

    # Brazo 2: Ablación limpia de memoria alocéntrica espacial (conservando memoria de trabajo y soma)
    if not memoria_alocentrica and hasattr(core, "activa"):
        core.activa.consultar_hitos_alocentricos = lambda *args, **kwargs: []

    # Manipulación de H2: cortisol constante durante todo el episodio (ver fijar_cortisol)
    if soma_modulacion == "off":
        fijar_cortisol(core.soma, 0.20)
    elif soma_modulacion.startswith("fijo_"):
        fijar_cortisol(core.soma, float(soma_modulacion.split("_")[1]))

    adaptador.max_pasos = max_latidos
    adaptador.reiniciar(seed=seed_mapa)

    latidos_vividos = 0
    latidos_s3_dominante = 0
    muerte_detectada = False
    causa_muerte_str = "Limite de pasos o fin de episodio"
    secuencia_acciones: List[str] = []
    telemetria_episodio: List[Dict[str, Any]] = []
    paso_por_logro: Dict[str, int] = {}  # R9: primer paso en que se desbloquea cada logro (pasivo)

    for latido in range(1, max_latidos + 1):
        if soma_modulacion == "invertido":
            core.soma.cortisol = float(max(0.0, min(1.0, 1.0 - core.soma.cortisol)))

        onda = await core.ejecutar_latido()
        latidos_vividos += 1
        for logro in adaptador.logros_desbloqueados:
            paso_por_logro.setdefault(logro, latido)

        p_ejec = next(iter(onda.reactiva.ef.get("Ejecucion", {}).values()), None)
        origen_sistema = str(onda.metricas.get("sistema_ganador", "S1"))
        cmd_str = "ACC_ESPERAR"
        target_str = ""
        if p_ejec:
            cmd_str = str(p_ejec.product.get("comando", "ACC_ESPERAR"))
            target_str = str(p_ejec.product.get("target", ""))
            if origen_sistema == "S3":
                latidos_s3_dominante += 1
        secuencia_acciones.append(f"{cmd_str}:{target_str}")

        if recolectar_telemetria:
            telemetria_episodio.append({
                "tick": latido,
                "origen": origen_sistema,
                "comando": cmd_str,
                "cortisol": round(float(core.soma.cortisol), 4),
                "alimentacion": round(float(core.soma.alimentacion), 2),
                "energia": round(float(core.soma.energia), 2),
                "contrafactual": onda.metricas.get("contrafactual", {}),
                "desacuerdos": onda.metricas.get("desacuerdos_contrafactuales", []),
            })

        player = adaptador.env._player
        salud_act = int(player.health)
        comida_act = int(player.inventory.get("food", 9))
        bebida_act = int(player.inventory.get("drink", 9))

        if salud_act <= 0 or adaptador.partida_terminada:
            if salud_act <= 0:
                if comida_act <= 0:
                    causa_muerte_str = "Inanicion / Hambre extrema"
                elif bebida_act <= 0:
                    causa_muerte_str = "Deshidratacion / Sed extrema"
                elif adaptador.env._world[player.pos][0] == "lava":
                    causa_muerte_str = "Muerte termica instantanea (Lava)"
                else:
                    causa_muerte_str = "Ataque letal de Depredador (Zombie/Esqueleto)"
                muerte_detectada = True
            break

    player = adaptador.env._player
    logros_sorted = sorted(list(adaptador.logros_desbloqueados))
    fitness_final = calcular_fitness_crafter(
        latidos=latidos_vividos,
        muerte=muerte_detectada,
        salud=int(player.health),
        comida=int(player.inventory.get("food", 9)),
        bebida=int(player.inventory.get("drink", 9)),
        energia=int(player.inventory.get("energy", 9)),
        logros=adaptador.logros_desbloqueados,
        latidos_s3=latidos_s3_dominante,
        axiomas_demostrados=0,
    )
    score_ind = calcular_crafter_score_episodio(logros_sorted)

    return {
        "individuo": arquetipo.nombre,
        "seed": seed_mapa,
        "latidos": latidos_vividos,
        "salud_final": int(player.health),
        "total_logros": len(logros_sorted),
        "logros": logros_sorted,
        "causa_muerte": causa_muerte_str,
        "fitness": fitness_final,
        "crafter_score_individual": round(score_ind, 2),
        "latidos_s3": latidos_s3_dominante,
        "axiomas_heredables": len(axiomas_heredados),
        "firma_acciones_primeros_25": secuencia_acciones[:25],
        "total_acciones_registradas": len(secuencia_acciones),
        "secuencia_completa": secuencia_acciones,
        "telemetria": telemetria_episodio,
        "paso_por_logro": dict(sorted(paso_por_logro.items(), key=lambda kv: kv[1])),
        "mutaciones_autopoiesis": cirujano.total_mutaciones if cirujano else 0,
        "rollbacks_autopoiesis": cirujano.rechazos_epigeneticos if cirujano else 0,
    }


async def ejecutar_experimento_heredabilidad_20_semillas(
    num_semillas: int = 20,
    seed_base_nuevas: int = 200,
    max_latidos: int = 500,
) -> Dict[str, Any]:
    """
    Protocolo Científico de Heredabilidad y Determinismo (Convertir el Récord en Evidencia):
      1. Determinismo / Reproducibilidad: Toma el individuo récord del linaje en su misma semilla
         y lo ejecuta dos veces con su linaje completo, comprobando si la trayectoria, pasos,
         logros y fitness son 100% deterministas (reproducibles en esa semilla). Además lo compara
         con un individuo de linaje vacío en esa misma semilla.
      2. Heredabilidad en N=20 Semillas Nuevas (No Vistas): Toma el linaje del individuo récord
         (axiomas Weismann + Arquetipo evolucionado) y hace nacer a sus descendientes en 20 semillas
         nuevas (seeds 200..219), comparándolos de forma pareada en las mismas 20 semillas contra
         descendientes de un linaje vacío (axiomas=[], Arquetipo fundador ingenuo).
    """
    axiomas_acumulados, historial_generaciones = cargar_linaje_ancestral()
    if not historial_generaciones:
        log_traza("[!] No se encontró linaje previo. Ejecutando 15 generaciones base desde Tabula Rasa...")
        await ejecutar_simulacion_crafter(
            modo_fast=True,
            tabula_rasa=True,
            generaciones=15,
            max_latidos_por_gen=max_latidos,
            seed=42,
        )
        axiomas_acumulados, historial_generaciones = cargar_linaje_ancestral()

    # Seleccionar el individuo récord del linaje
    mejor_ind = max(
        historial_generaciones,
        key=lambda h: (
            len(h.get("logros", [])),
            float(h.get("fitness", {}).get("global", 0.0)) if isinstance(h.get("fitness"), dict) else 0.0,
        ),
    )
    gen_record = int(mejor_ind.get("generacion", 1))
    seed_record = int(mejor_ind.get("seed_episodio", 42 + gen_record * 17))
    rasgos_rec = mejor_ind.get("arquetipo_rasgos", {})
    arquetipo_record = Arquetipo(
        nombre=str(mejor_ind.get("individuo", f"Hominis_G{gen_record}")),
        id_individuo=f"Record_{mejor_ind.get('individuo', 'Hominis')}",
        linaje="Linaje_Hominis_Crafter",
        generacion=gen_record,
        apertura=float(rasgos_rec.get("apertura", 0.78)),
        responsabilidad=float(rasgos_rec.get("responsabilidad", 0.84)),
        neuroticismo=float(rasgos_rec.get("neuroticismo", 0.34)),
        umbral_miedo=float(rasgos_rec.get("umbral_miedo", 0.68)),
    )
    arquetipo_vacio_base = Arquetipo(
        nombre="Fundador_Linaje_Vacio",
        id_individuo="Vacio_G1",
        linaje="Linaje_Control_Vacio",
        generacion=1,
        apertura=0.52,
        responsabilidad=0.48,
        neuroticismo=0.55,
        umbral_miedo=0.45,
    )

    adaptador = AdaptadorCrafter(seed=seed_record, max_pasos=max_latidos)
    adaptador.conectar()

    log_traza("")
    log_traza("=" * 105)
    log_traza("   EXPERIMENTO CIENTIFICO: DETERMINISMO EN SEMILLA RECORD Y HEREDABILIDAD EN N=20 SEMILLAS NUEVAS   ")
    log_traza("=" * 105)
    log_traza(
        f"[*] Individuo Récord Seleccionado: {arquetipo_record.nombre} (Gen {gen_record}, Seed Original={seed_record}) | "
        f"Axiomas del Linaje={len(axiomas_acumulados)} | "
        f"Rasgos=(Ap={arquetipo_record.apertura:.2f}, Resp={arquetipo_record.responsabilidad:.2f}, "
        f"Neur={arquetipo_record.neuroticismo:.2f}, Miedo={arquetipo_record.umbral_miedo:.2f})"
    )

    # -------------------------------------------------------------------------
    # PARTE 1: REPRODUCIBILIDAD / DETERMINISMO EN LA MISMA SEMILLA DEL RECORD
    # -------------------------------------------------------------------------
    rep_1 = await evaluar_individuo_en_semilla(
        adaptador=adaptador,
        arquetipo=arquetipo_record,
        axiomas_heredados=axiomas_acumulados,
        seed_mapa=seed_record,
        max_latidos=max_latidos,
        aislar_ruido_termodinamico=True,
    )
    rep_2 = await evaluar_individuo_en_semilla(
        adaptador=adaptador,
        arquetipo=arquetipo_record,
        axiomas_heredados=axiomas_acumulados,
        seed_mapa=seed_record,
        max_latidos=max_latidos,
        aislar_ruido_termodinamico=True,
    )
    rep_prigogine = await evaluar_individuo_en_semilla(
        adaptador=adaptador,
        arquetipo=arquetipo_record,
        axiomas_heredados=axiomas_acumulados,
        seed_mapa=seed_record,
        max_latidos=max_latidos,
        aislar_ruido_termodinamico=False,
    )
    control_misma_seed = await evaluar_individuo_en_semilla(
        adaptador=adaptador,
        arquetipo=arquetipo_vacio_base,
        axiomas_heredados=[],
        seed_mapa=seed_record,
        max_latidos=max_latidos,
        aislar_ruido_termodinamico=True,
    )

    trayectoria_identica = rep_1["secuencia_completa"] == rep_2["secuencia_completa"]
    logros_identicos = rep_1["logros"] == rep_2["logros"]
    fitness_identico = rep_1["fitness"]["global"] == rep_2["fitness"]["global"]
    es_determinista = bool(trayectoria_identica and logros_identicos and fitness_identico)

    log_traza("-" * 105)
    log_traza(f"[1] PRUEBA DE DETERMINISMO Y ABLACION EN LA SEMILLA DEL RECORD (Seed={seed_record}):")
    log_traza(
        f"    - Replica 1 (Con Linaje Récord, Ruido=0)  : Pasos={rep_1['latidos']:3d} | Salud={rep_1['salud_final']}/9 | "
        f"Logros={rep_1['total_logros']:2d} ({rep_1['crafter_score_individual']:5.2f}%) | Fit Global={rep_1['fitness']['global']:5.1f}"
    )
    log_traza(
        f"    - Replica 2 (Con Linaje Récord, Ruido=0)  : Pasos={rep_2['latidos']:3d} | Salud={rep_2['salud_final']}/9 | "
        f"Logros={rep_2['total_logros']:2d} ({rep_2['crafter_score_individual']:5.2f}%) | Fit Global={rep_2['fitness']['global']:5.1f}"
    )
    log_traza(
        f"    - Replica 3 (Con Jitter Prigogine Activo) : Pasos={rep_prigogine['latidos']:3d} | Salud={rep_prigogine['salud_final']}/9 | "
        f"Logros={rep_prigogine['total_logros']:2d} ({rep_prigogine['crafter_score_individual']:5.2f}%) | Fit Global={rep_prigogine['fitness']['global']:5.1f}"
    )
    log_traza(
        f"    - Control   (Linaje Vacío, Misma Seed)    : Pasos={control_misma_seed['latidos']:3d} | Salud={control_misma_seed['salud_final']}/9 | "
        f"Logros={control_misma_seed['total_logros']:2d} ({control_misma_seed['crafter_score_individual']:5.2f}%) | Fit Global={control_misma_seed['fitness']['global']:5.1f}"
    )
    log_traza(
        f"    => Determinismo Estructural Verificado: {es_determinista} "
        f"(Trayectoria paso a paso 100% idéntica: {trayectoria_identica}, {rep_1['total_acciones_registradas']} acciones)"
    )

    # -------------------------------------------------------------------------
    # PARTE 2: HEREDABILIDAD PAREADA EN N=20 SEMILLAS NUEVAS (NO VISTAS)
    # -------------------------------------------------------------------------
    log_traza("-" * 105)
    log_traza(
        f"[2] EXPERIMENTO PAREADO DE HEREDABILIDAD EN N={num_semillas} SEMILLAS NUEVAS "
        f"(Seeds {seed_base_nuevas}..{seed_base_nuevas + num_semillas - 1}):"
    )
    log_traza(
        f"{'Seed':^6} | {'Logros Linaje':^13} | {'Logros Vacio':^12} | {'Delta Logros':^12} | "
        f"{'Fit Linaje':^10} | {'Fit Vacio':^9} | {'Delta Fit':^9} | {'Pasos L/V':^11}"
    )
    log_traza("-" * 105)

    resultados_con_linaje: List[Dict[str, Any]] = []
    resultados_sin_linaje: List[Dict[str, Any]] = []
    comparativa_semillas: List[Dict[str, Any]] = []

    for idx in range(num_semillas):
        s_map = seed_base_nuevas + idx
        rng_desc = np.random.default_rng(seed=s_map * 13)

        # Descendiente del individuo récord (pequeña variación genética natural de descendiente)
        arq_desc_record = Arquetipo(
            nombre=f"Desc_Record_S{s_map}",
            id_individuo=f"Desc_Record_S{s_map}",
            id_padre=arquetipo_record.id_individuo,
            linaje="Linaje_Hominis_Crafter",
            generacion=gen_record + 1,
            apertura=round(float(np.clip(arquetipo_record.apertura + rng_desc.normal(0, 0.02), 0.70, 0.92)), 2),
            responsabilidad=round(float(np.clip(arquetipo_record.responsabilidad + rng_desc.normal(0, 0.02), 0.74, 0.94)), 2),
            neuroticismo=round(float(np.clip(arquetipo_record.neuroticismo + rng_desc.normal(0, 0.02), 0.24, 0.45)), 2),
            umbral_miedo=round(float(np.clip(arquetipo_record.umbral_miedo + rng_desc.normal(0, 0.02), 0.62, 0.85)), 2),
        )

        # Descendiente de linaje vacío (misma perturbación aleatoria pero sobre arquetipo fundador ingenuo y 0 axiomas)
        arq_desc_vacio = Arquetipo(
            nombre=f"Desc_Vacio_S{s_map}",
            id_individuo=f"Desc_Vacio_S{s_map}",
            id_padre=None,
            linaje="Linaje_Control_Vacio",
            generacion=1,
            apertura=round(float(np.clip(arquetipo_vacio_base.apertura + rng_desc.normal(0, 0.02), 0.40, 0.58)), 2),
            responsabilidad=round(float(np.clip(arquetipo_vacio_base.responsabilidad + rng_desc.normal(0, 0.02), 0.38, 0.56)), 2),
            neuroticismo=round(float(np.clip(arquetipo_vacio_base.neuroticismo + rng_desc.normal(0, 0.02), 0.45, 0.65)), 2),
            umbral_miedo=round(float(np.clip(arquetipo_vacio_base.umbral_miedo + rng_desc.normal(0, 0.02), 0.35, 0.52)), 2),
        )

        ev_lin = await evaluar_individuo_en_semilla(
            adaptador=adaptador,
            arquetipo=arq_desc_record,
            axiomas_heredados=axiomas_acumulados,
            seed_mapa=s_map,
            max_latidos=max_latidos,
            aislar_ruido_termodinamico=True,
        )
        ev_vac = await evaluar_individuo_en_semilla(
            adaptador=adaptador,
            arquetipo=arq_desc_vacio,
            axiomas_heredados=[],
            seed_mapa=s_map,
            max_latidos=max_latidos,
            aislar_ruido_termodinamico=True,
        )

        # No guardar secuencia_completa de 500 strings por cada una de las 40 corridas en el JSON final
        ev_lin_clean = {k: v for k, v in ev_lin.items() if k != "secuencia_completa"}
        ev_vac_clean = {k: v for k, v in ev_vac.items() if k != "secuencia_completa"}
        resultados_con_linaje.append(ev_lin_clean)
        resultados_sin_linaje.append(ev_vac_clean)

        d_logros = ev_lin["total_logros"] - ev_vac["total_logros"]
        d_fit = round(ev_lin["fitness"]["global"] - ev_vac["fitness"]["global"], 1)
        comparativa_semillas.append({
            "seed": s_map,
            "logros_con_linaje": ev_lin["total_logros"],
            "logros_sin_linaje": ev_vac["total_logros"],
            "delta_logros": d_logros,
            "fit_con_linaje": ev_lin["fitness"]["global"],
            "fit_sin_linaje": ev_vac["fitness"]["global"],
            "delta_fit": d_fit,
            "pasos_con_linaje": ev_lin["latidos"],
            "pasos_sin_linaje": ev_vac["latidos"],
            "salud_con_linaje": ev_lin["salud_final"],
            "salud_sin_linaje": ev_vac["salud_final"],
            "lista_logros_con_linaje": ev_lin["logros"],
            "lista_logros_sin_linaje": ev_vac["logros"],
        })

        log_traza(
            f"{s_map:^6d} | {ev_lin['total_logros']:^13d} | {ev_vac['total_logros']:^12d} | {d_logros:^+12d} | "
            f"{ev_lin['fitness']['global']:^10.1f} | {ev_vac['fitness']['global']:^9.1f} | {d_fit:^+9.1f} | "
            f"{ev_lin['latidos']:3d}/{ev_vac['latidos']:3d}"
        )

    adaptador.desconectar()

    # Estadísticas agregadas sobre las 20 semillas
    bench_linaje = calcular_crafter_score_poblacional(resultados_con_linaje)
    bench_vacio = calcular_crafter_score_poblacional(resultados_sin_linaje)

    fit_lin_arr = np.array([r["fitness"]["global"] for r in resultados_con_linaje], dtype=float)
    fit_vac_arr = np.array([r["fitness"]["global"] for r in resultados_sin_linaje], dtype=float)
    log_lin_arr = np.array([r["total_logros"] for r in resultados_con_linaje], dtype=float)
    log_vac_arr = np.array([r["total_logros"] for r in resultados_sin_linaje], dtype=float)
    pas_lin_arr = np.array([r["latidos"] for r in resultados_con_linaje], dtype=float)
    pas_vac_arr = np.array([r["latidos"] for r in resultados_sin_linaje], dtype=float)

    semillas_ganadas_fit = int(np.sum(fit_lin_arr > fit_vac_arr))
    semillas_empatadas_fit = int(np.sum(fit_lin_arr == fit_vac_arr))
    semillas_ganadas_logros = int(np.sum(log_lin_arr > log_vac_arr))

    resumen_experimento = {
        "protocolo": "Experimento Cientifico de Determinismo y Heredabilidad en N=20 Semillas Nuevas",
        "individuo_record_origen": {
            "nombre": arquetipo_record.nombre,
            "generacion": gen_record,
            "seed_original": seed_record,
            "rasgos": {
                "apertura": arquetipo_record.apertura,
                "responsabilidad": arquetipo_record.responsabilidad,
                "neuroticismo": arquetipo_record.neuroticismo,
                "umbral_miedo": arquetipo_record.umbral_miedo,
            },
            "total_axiomas_heredados": len(axiomas_acumulados),
        },
        "determinismo_misma_semilla": {
            "seed_evaluada": seed_record,
            "es_100_por_100_determinista": es_determinista,
            "trayectoria_paso_a_paso_identica": trayectoria_identica,
            "replica_1": {k: v for k, v in rep_1.items() if k != "secuencia_completa"},
            "replica_2": {k: v for k, v in rep_2.items() if k != "secuencia_completa"},
            "replica_con_jitter_prigogine": {k: v for k, v in rep_prigogine.items() if k != "secuencia_completa"},
            "control_linaje_vacio_misma_semilla": {
                k: v for k, v in control_misma_seed.items() if k != "secuencia_completa"
            },
        },
        "heredabilidad_20_semillas_nuevas": {
            "num_semillas": num_semillas,
            "rango_semillas": [seed_base_nuevas, seed_base_nuevas + num_semillas - 1],
            "con_linaje_record": {
                "crafter_score_poblacional": round(bench_linaje["crafter_score"], 2),
                "sum_ln": round(bench_linaje["sum_ln"], 4),
                "logros_desbloqueados_unicos": len(bench_linaje["logros_desbloqueados"]),
                "lista_logros_desbloqueados": bench_linaje["logros_desbloqueados"],
                "success_rates": bench_linaje["success_rates"],
                "fitness_media": round(float(np.mean(fit_lin_arr)), 2),
                "fitness_std": round(float(np.std(fit_lin_arr)), 2),
                "fitness_mediana": round(float(np.median(fit_lin_arr)), 2),
                "fitness_iqr": [
                    round(float(np.percentile(fit_lin_arr, 25)), 2),
                    round(float(np.percentile(fit_lin_arr, 75)), 2),
                ],
                "fitness_min_max": [round(float(np.min(fit_lin_arr)), 1), round(float(np.max(fit_lin_arr)), 1)],
                "logros_media": round(float(np.mean(log_lin_arr)), 2),
                "logros_std": round(float(np.std(log_lin_arr)), 2),
                "logros_mediana": round(float(np.median(log_lin_arr)), 1),
                "logros_iqr": [
                    round(float(np.percentile(log_lin_arr, 25)), 1),
                    round(float(np.percentile(log_lin_arr, 75)), 1),
                ],
                "logros_min_max": [int(np.min(log_lin_arr)), int(np.max(log_lin_arr))],
                "pasos_media": round(float(np.mean(pas_lin_arr)), 1),
                "pasos_std": round(float(np.std(pas_lin_arr)), 1),
            },
            "sin_linaje_vacio": {
                "crafter_score_poblacional": round(bench_vacio["crafter_score"], 2),
                "sum_ln": round(bench_vacio["sum_ln"], 4),
                "logros_desbloqueados_unicos": len(bench_vacio["logros_desbloqueados"]),
                "lista_logros_desbloqueados": bench_vacio["logros_desbloqueados"],
                "success_rates": bench_vacio["success_rates"],
                "fitness_media": round(float(np.mean(fit_vac_arr)), 2),
                "fitness_std": round(float(np.std(fit_vac_arr)), 2),
                "fitness_mediana": round(float(np.median(fit_vac_arr)), 2),
                "fitness_iqr": [
                    round(float(np.percentile(fit_vac_arr, 25)), 2),
                    round(float(np.percentile(fit_vac_arr, 75)), 2),
                ],
                "fitness_min_max": [round(float(np.min(fit_vac_arr)), 1), round(float(np.max(fit_vac_arr)), 1)],
                "logros_media": round(float(np.mean(log_vac_arr)), 2),
                "logros_std": round(float(np.std(log_vac_arr)), 2),
                "logros_mediana": round(float(np.median(log_vac_arr)), 1),
                "logros_iqr": [
                    round(float(np.percentile(log_vac_arr, 25)), 1),
                    round(float(np.percentile(log_vac_arr, 75)), 1),
                ],
                "logros_min_max": [int(np.min(log_vac_arr)), int(np.max(log_vac_arr))],
                "pasos_media": round(float(np.mean(pas_vac_arr)), 1),
                "pasos_std": round(float(np.std(pas_vac_arr)), 1),
            },
            "diferencial_pareado": {
                "delta_crafter_score_pct": round(bench_linaje["crafter_score"] - bench_vacio["crafter_score"], 2),
                "ratio_crafter_score": round(
                    bench_linaje["crafter_score"] / max(0.01, bench_vacio["crafter_score"]), 2
                ),
                "delta_fitness_medio": round(float(np.mean(fit_lin_arr - fit_vac_arr)), 2),
                "delta_logros_medio": round(float(np.mean(log_lin_arr - log_vac_arr)), 2),
                "semillas_superiores_en_fitness": f"{semillas_ganadas_fit}/{num_semillas} (empates: {semillas_empatadas_fit})",
                "semillas_superiores_en_logros": f"{semillas_ganadas_logros}/{num_semillas}",
            },
            "comparativa_semilla_a_semilla": comparativa_semillas,
        },
    }

    with open(asegurar_directorio_de(RUTA_EXPERIMENTO_HEREDABILIDAD), "w", encoding="utf-8") as f:
        json.dump(resumen_experimento, f, indent=2, ensure_ascii=False)

    c_lin = resumen_experimento["heredabilidad_20_semillas_nuevas"]["con_linaje_record"]
    c_vac = resumen_experimento["heredabilidad_20_semillas_nuevas"]["sin_linaje_vacio"]
    dif = resumen_experimento["heredabilidad_20_semillas_nuevas"]["diferencial_pareado"]

    log_traza("=" * 105)
    log_traza("               RESUMEN ESTADISTICO PAREADO (N=20 SEMILLAS NUEVAS: LINAJE vs VACIO)               ")
    log_traza("=" * 105)
    log_traza(
        f"  * CRAFTER SCORE POBLACIONAL (N=20) : Con Linaje = {c_lin['crafter_score_poblacional']:5.2f}%  vs  "
        f"Linaje Vacío = {c_vac['crafter_score_poblacional']:5.2f}%  "
        f"(Delta = {dif['delta_crafter_score_pct']:+5.2f} pts, {dif['ratio_crafter_score']:.2f}x)"
    )
    log_traza(
        f"  * FITNESS GLOBAL (Media ± SD)      : Con Linaje = {c_lin['fitness_media']:5.2f} ± {c_lin['fitness_std']:4.2f} "
        f"[Med={c_lin['fitness_mediana']:5.2f}, IQR={c_lin['fitness_iqr']}]  vs  "
        f"Vacío = {c_vac['fitness_media']:5.2f} ± {c_vac['fitness_std']:4.2f} "
        f"[Med={c_vac['fitness_mediana']:5.2f}, IQR={c_vac['fitness_iqr']}]"
    )
    log_traza(
        f"  * LOGROS POR EPISODIO (Media ± SD) : Con Linaje = {c_lin['logros_media']:5.2f} ± {c_lin['logros_std']:4.2f} "
        f"[Med={c_lin['logros_mediana']:4.1f}, Rango={c_lin['logros_min_max']}]  vs  "
        f"Vacío = {c_vac['logros_media']:5.2f} ± {c_vac['logros_std']:4.2f} "
        f"[Med={c_vac['logros_mediana']:4.1f}, Rango={c_vac['logros_min_max']}]"
    )
    log_traza(
        f"  * DOMINANCIA EN SEMILLAS PAREADAS  : Fitness superior en {dif['semillas_superiores_en_fitness']} semillas | "
        f"Más logros en {dif['semillas_superiores_en_logros']} semillas"
    )
    log_traza(f"  * Evidencia guardada en            : {RUTA_EXPERIMENTO_HEREDABILIDAD}")
    log_traza("=" * 105)

    return resumen_experimento


def main() -> None:
    parser = argparse.ArgumentParser(description="Runner Evolutivo de IdA v12.0 en Crafter")
    parser.add_argument("--modo", choices=["fast", "normal"], default="fast", help="Velocidad del bucle")
    parser.add_argument("--generaciones", type=int, default=3, help="Numero de generaciones a simular")
    parser.add_argument("--max-latidos", type=int, default=500, help="Maximo de latidos por generacion (default: 500)")
    parser.add_argument("--tabula-rasa", action="store_true", help="Reinicia el linaje evolutivo desde cero")
    parser.add_argument("--seed", type=int, default=42, help="Semilla procedural de Crafter")
    parser.add_argument("--gui", action="store_true", help="Abre ventana interactiva en vivo con Tkinter/Pillow")
    parser.add_argument("--guardar-gif", action="store_true", help="Graba un replay .gif de cada generacion en <IDA_OUT_DIR>/crafter/replays/")
    parser.add_argument("--fps", type=int, default=12, help="Fotogramas por segundo para visualizacion o GIF")
    parser.add_argument(
        "--habilitar-autopoiesis",
        action="store_true",
        help="EXPERIMENTAL: activa la autopoiesis AST (muta clases en memoria con exec). Desactivada por defecto.",
    )
    parser.add_argument(
        "--experimento-heredabilidad",
        action="store_true",
        help="Ejecuta el protocolo cientifico de determinismo y heredabilidad en N=20 semillas nuevas",
    )
    parser.add_argument(
        "--semillas-heredabilidad",
        type=int,
        default=20,
        help="Numero de semillas nuevas para el experimento de heredabilidad (default: 20)",
    )
    parser.add_argument(
        "--seed-base-nuevas",
        type=int,
        default=1000,
        help="Semilla inicial para las N semillas nuevas no vistas (default: 1000)",
    )

    args = parser.parse_args()
    if args.experimento_heredabilidad:
        asyncio.run(
            ejecutar_experimento_heredabilidad_20_semillas(
                num_semillas=args.semillas_heredabilidad,
                seed_base_nuevas=args.seed_base_nuevas,
                max_latidos=args.max_latidos,
            )
        )
    else:
        asyncio.run(
            ejecutar_simulacion_crafter(
                modo_fast=(args.modo == "fast"),
                tabula_rasa=args.tabula_rasa,
                generaciones=args.generaciones,
                max_latidos_por_gen=args.max_latidos,
                seed=args.seed,
                gui=args.gui,
                guardar_gif=args.guardar_gif,
                fps=args.fps,
                habilitar_autopoiesis=args.habilitar_autopoiesis,
            )
        )


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    main()
