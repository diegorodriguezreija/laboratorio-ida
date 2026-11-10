"""
Paquete del Mundo Arcade Snake (Playsnake.org) para IdA v12.0.
Implementa el aislamiento de membrana sensoriomotora conforme a ISensorEntorno e IActuadorEntorno.
"""

from .adaptador_snake import AdaptadorSnakeWeb
from .componentes_snake import CompSupervivenciaSnakeS1, CompEstrategiaSnakeS3

__all__ = ["AdaptadorSnakeWeb", "CompSupervivenciaSnakeS1", "CompEstrategiaSnakeS3"]

