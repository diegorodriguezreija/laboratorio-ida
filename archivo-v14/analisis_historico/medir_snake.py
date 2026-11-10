"""
N2 – Medición del mundo Snake web (experimental; depende de https://playsnake.org/).

Diseño:
- Agentes: 'ida' (core + componentes de Snake, igual que mundo_snake_runner.py pero con un
  arquetipo fijo, sin axiomas heredados y sin autopoiesis) y 'bfs' (baseline: camino más
  corto a la comida con comprobación de espacio libre por flood fill).
- Dificultades: 0 (Slug), 1 (Worm), 2 (Python) del propio sitio.
- N episodios por agente y dificultad; el orden de todos los episodios se baraja con una
  semilla registrada.
- Sin tope de latidos. Solo hay un tope de seguridad de tiempo real por episodio
  (--max-segundos); un episodio que lo alcance se marca como censurado.
- Fin de episodio y causa de muerte: misma regla que mundo_snake_runner.py (estado 'ended'
  o caída de la puntuación; muro si la última cabeza viva estaba en el borde).

Uso:
    python analisis/medir_snake.py --episodios 30 --semilla-orden 20261107 --out salidas/N2/snake.csv
    python analisis/medir_snake.py --episodios 1 --dificultades 0 --out salidas/N2/humo.csv   # prueba rápida
"""

import argparse
import asyncio
import csv
import json
import os
import random
import sys
import time
from collections import deque
from typing import Dict, List, Optional, Tuple

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from nivel_1_core.contratos import Arquetipo  # noqa: E402
from nivel_1_core.gestor_onda import GestorOndaCore  # noqa: E402
from nivel_1_core.vocabulario import V_Comando  # noqa: E402
from nivel_2_sistemas.ciclo_sueno_rem import GestorCicloSuenoREM  # noqa: E402
from nivel_2_sistemas.consciencia_talamo_dmn import BucleTalamocortical, RedNeuronalPorDefecto  # noqa: E402
from nivel_2_sistemas.plasticidad_td_hebbiana import MatrizHebbianaTresFactores  # noqa: E402
from nivel_2_sistemas.s1_reactivo import crear_sistema_s1  # noqa: E402
from nivel_2_sistemas.s2_limbico import crear_sistema_s2  # noqa: E402
from nivel_2_sistemas.s3_racional import crear_sistema_s3  # noqa: E402
from nivel_3_componentes.mundos.mundo_arcade_snake.adaptador_snake import AdaptadorSnakeWeb  # noqa: E402
from nivel_3_componentes.mundos.mundo_arcade_snake.componentes_snake import (  # noqa: E402
    CompEstrategiaSnakeS3,
    CompSupervivenciaSnakeS1,
)
from nivel_3_componentes.rutas_salida import asegurar_directorio_de, directorio_salidas  # noqa: E402

DIRECCIONES = {"NORTE": (0, -1), "SUR": (0, 1), "ESTE": (1, 0), "OESTE": (-1, 0)}
NOMBRES_DIF = {0: "slug", 1: "worm", 2: "python"}


# ----------------------------------------------------------------------------- reglas comunes

def fin_de_partida(adaptador: AdaptadorSnakeWeb, puntuacion_maxima: int) -> bool:
    """Misma regla que mundo_snake_runner.py."""
    return adaptador.estado_juego_web == "ended" or (adaptador.puntuacion_actual < puntuacion_maxima and puntuacion_maxima > 0)


def causa_muerte(adaptador: AdaptadorSnakeWeb) -> str:
    """Misma regla que mundo_snake_runner.py: borde del tablero => muro; si no, cuerpo."""
    hx, hy = getattr(adaptador, "ultima_cabeza_viva", adaptador.cabeza_actual)
    es_muro = hx <= 0 or hx >= 20 or hy <= 0 or hy >= 14
    return "muro" if es_muro else "cuerpo"


# ----------------------------------------------------------------------------- baseline BFS

def _vecinos(c: Tuple[int, int], ancho: int, alto: int):
    for nombre, (dx, dy) in DIRECCIONES.items():
        n = (c[0] + dx, c[1] + dy)
        if 0 <= n[0] < ancho and 0 <= n[1] < alto:
            yield nombre, n


def _area_libre(inicio: Tuple[int, int], bloqueadas: set, ancho: int, alto: int) -> int:
    vistos, cola = {inicio}, deque([inicio])
    while cola:
        c = cola.popleft()
        for _, n in _vecinos(c, ancho, alto):
            if n not in bloqueadas and n not in vistos:
                vistos.add(n)
                cola.append(n)
    return len(vistos)


def decidir_bfs(cuerpo: List[Tuple[int, int]], comida: Optional[Tuple[int, int]], ancho: int, alto: int) -> Optional[str]:
    """Primer paso del camino más corto a la comida si deja espacio suficiente; si no, la casilla con más espacio."""
    if not cuerpo:
        return None
    cabeza = cuerpo[0]
    bloqueadas = set(cuerpo[:-1])  # la cola se mueve en el siguiente tick
    candidatos = [(nom, n) for nom, n in _vecinos(cabeza, ancho, alto) if n not in bloqueadas]
    if not candidatos:
        return None

    if comida is not None:
        padre: Dict[Tuple[int, int], Tuple[Tuple[int, int], str]] = {}
        cola = deque([cabeza])
        vistos = {cabeza}
        while cola:
            c = cola.popleft()
            if c == comida:
                break
            for nom, n in _vecinos(c, ancho, alto):
                if n not in bloqueadas and n not in vistos:
                    vistos.add(n)
                    padre[n] = (c, nom)
                    cola.append(n)
        if comida in padre:
            paso = comida
            while padre[paso][0] != cabeza:
                paso = padre[paso][0]
            primer_mov = padre[paso][1]
            if _area_libre(paso, bloqueadas, ancho, alto) >= len(cuerpo):
                return primer_mov

    return max(candidatos, key=lambda nn: _area_libre(nn[1], bloqueadas, ancho, alto))[0]


# ----------------------------------------------------------------------------- episodios

def construir_ida(adaptador: AdaptadorSnakeWeb) -> GestorOndaCore:
    """Mismos componentes y parámetros que mundo_snake_runner.py; arquetipo fijo (centro de su distribución)."""
    arq = Arquetipo(nombre="Ophidia_Medicion", linaje="Medicion_N2", apertura=0.65, responsabilidad=0.80, neuroticismo=0.35, umbral_miedo=0.60)
    s1 = crear_sistema_s1(matriz_hebbiana=MatrizHebbianaTresFactores())
    s2 = crear_sistema_s2()
    s3 = crear_sistema_s3()
    s1.estaciones["REACCIONAR"] = [CompSupervivenciaSnakeS1(peso_sinaptico=1.25)]
    s3.estaciones["REACCIONAR"] = [CompEstrategiaSnakeS3(peso_sinaptico=1.35)]
    return GestorOndaCore(
        sensor=adaptador, actuador=adaptador, arquetipo=arq, sistemas_cognitivos=[s1, s2, s3],
        bucle_talamocortical=BucleTalamocortical(), dmn=RedNeuronalPorDefecto(), gestor_sueno_rem=GestorCicloSuenoREM(),
        cirujano_ast=None, sqlite_wal=None, frecuencia_max_ms=120.0, amplitud_max=200,
    )


async def episodio(adaptador: AdaptadorSnakeWeb, agente: str, max_segundos: float) -> Dict:
    adaptador.iniciar_partida_web()
    core = construir_ida(adaptador) if agente == "ida" else None
    t0 = time.perf_counter()
    latidos, punt_max, censurado = 0, 0, False
    while True:
        if time.perf_counter() - t0 > max_segundos:
            censurado = True
            break
        latidos += 1
        if core is not None:
            await core.ejecutar_latido()
        else:
            adaptador.percibir_mundo()
            mov = decidir_bfs(list(adaptador.cuerpo_actual), adaptador.comida_actual, adaptador.ANCHO_TABLERO, adaptador.ALTO_TABLERO)
            if mov:
                adaptador.ejecutar_comando_fisico(V_Comando.MOVER, mov)
        punt_max = max(punt_max, adaptador.puntuacion_actual)
        if fin_de_partida(adaptador, punt_max):
            break
        await asyncio.sleep(0.005)
    return {
        "puntuacion": punt_max,
        "latidos": latidos,
        "duracion_s": round(time.perf_counter() - t0, 2),
        "causa_muerte": "censurado" if censurado else causa_muerte(adaptador),
        "censurado": censurado,
    }


async def medir(args) -> List[Dict]:
    plan = [(a, d) for a in args.agentes for d in args.dificultades for _ in range(args.episodios)]
    random.Random(args.semilla_orden).shuffle(plan)
    adaptador = AdaptadorSnakeWeb(headless=not args.visible, nivel_dificultad=plan[0][1])
    adaptador.conectar()
    filas = []
    try:
        for i, (agente, dif) in enumerate(plan, 1):
            adaptador.nivel_dificultad = dif
            try:
                res = await episodio(adaptador, agente, args.max_segundos)
                error = ""
            except Exception as exc:  # el sitio de terceros puede fallar: se registra, no se oculta
                res = {"puntuacion": "", "latidos": "", "duracion_s": "", "causa_muerte": "error", "censurado": ""}
                error = repr(exc)[:200]
            fila = {"orden": i, "agente": agente, "dificultad": dif, "dificultad_nombre": NOMBRES_DIF.get(dif, dif), **res, "error": error}
            filas.append(fila)
            print(json.dumps(fila, ensure_ascii=False), flush=True)
            with open(asegurar_directorio_de(args.out), "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(fila.keys()))
                w.writeheader()
                w.writerows(filas)
    finally:
        adaptador.desconectar()
    return filas


def main():
    ap = argparse.ArgumentParser(description="N2: medición de Snake web (IdA frente a baseline BFS)")
    ap.add_argument("--episodios", type=int, default=30, help="Episodios por agente y dificultad (por defecto 30)")
    ap.add_argument("--dificultades", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--agentes", nargs="+", default=["ida", "bfs"], choices=["ida", "bfs"])
    ap.add_argument("--semilla-orden", type=int, default=20261107, help="Semilla para barajar el orden de los episodios")
    ap.add_argument("--max-segundos", type=float, default=600.0, help="Tope de seguridad por episodio; si se alcanza, se marca censurado")
    ap.add_argument("--visible", action="store_true", help="Muestra el navegador")
    ap.add_argument("--out", default=os.path.join(directorio_salidas("analisis"), "N2_snake.csv"))
    args = ap.parse_args()
    filas = asyncio.run(medir(args))
    print(f"[+] {len(filas)} episodios en {args.out}")


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    main()
