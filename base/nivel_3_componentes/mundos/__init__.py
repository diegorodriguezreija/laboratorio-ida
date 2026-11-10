from nivel_3_componentes.mundos.mundo_bosque_archivos.adaptador_bosque import AdaptadorBosqueArchivos
from nivel_3_componentes.mundos.mundo_arcade_snake.adaptador_snake import AdaptadorArcadeSnake
from nivel_3_componentes.mundos.mundo_acompanante_humano.adaptador_acompanante import AdaptadorAcompananteHumano

# El mundo de ajedrez (GPL-3.0-or-later, depende de python-chess) no se importa desde aquí:
# se usa directamente desde nivel_3_componentes.mundos.mundo_ajedrez (ver NOTICE).

__all__ = [
    "AdaptadorBosqueArchivos",
    "AdaptadorArcadeSnake",
    "AdaptadorAcompananteHumano",
]
