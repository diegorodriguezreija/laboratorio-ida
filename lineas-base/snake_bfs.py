"""
Línea base tradicional para el mundo Snake: Agente BFS puro.
Calcula el primer paso del camino más corto a la comida si deja espacio suficiente;
si no, elige la casilla con mayor área libre accesible (flood fill).
"""

from collections import deque
from typing import Dict, List, Optional, Tuple

DIRECCIONES = {
    "NORTE": (0, -1),
    "SUR": (0, 1),
    "ESTE": (1, 0),
    "OESTE": (-1, 0),
}


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
