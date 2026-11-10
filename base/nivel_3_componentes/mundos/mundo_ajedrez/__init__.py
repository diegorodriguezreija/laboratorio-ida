"""
Mundo Ajedrez (Chess) para IdA v12.0.
Arquitectura de Doble Membrana: Modo Fast local (python-chess) y Modo Lichess web (Playwright).
"""

from .adaptador_ajedrez import AdaptadorAjedrez
from .componentes_ajedrez import CompAjedrezS1, CompAjedrezS2, CompAjedrezS3

__all__ = [
    "AdaptadorAjedrez",
    "CompAjedrezS1",
    "CompAjedrezS2",
    "CompAjedrezS3",
]

