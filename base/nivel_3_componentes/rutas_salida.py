"""
Rutas de salida de ejecución (nivel 3).

Ningún programa escribe dentro de las carpetas de código: logs, linajes, bases de datos,
replays y CSV van a IDA_OUT_DIR (variable de entorno) o, si no está definida, a
<raíz del repositorio>/salidas/, que está en .gitignore.

Las funciones solo calculan rutas; el directorio se crea en el momento de escribir
(asegurar_directorio_de), de modo que importar un runner no crea nada en disco.
"""

import os

_dir = os.path.dirname(os.path.abspath(__file__))
_padre = os.path.abspath(os.path.join(_dir, ".."))
if os.path.basename(_padre) == "base":
    RAIZ_PROYECTO = os.path.abspath(os.path.join(_padre, ".."))
else:
    RAIZ_PROYECTO = _padre


def directorio_salidas(*subcarpetas: str) -> str:
    """Devuelve la ruta absoluta de IDA_OUT_DIR (o ./salidas) unida a las subcarpetas dadas."""
    base = os.environ.get("IDA_OUT_DIR", "").strip() or os.path.join(RAIZ_PROYECTO, "salidas")
    return os.path.abspath(os.path.join(base, *subcarpetas))


def asegurar_directorio_de(ruta_fichero: str) -> str:
    """Crea (si falta) el directorio que contendrá ruta_fichero y devuelve la propia ruta."""
    os.makedirs(os.path.dirname(os.path.abspath(ruta_fichero)), exist_ok=True)
    return ruta_fichero
