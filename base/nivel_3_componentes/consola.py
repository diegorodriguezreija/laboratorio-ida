"""Utilidades de consola para los ejecutables (nivel 3)."""

import sys


def configurar_salida_utf8() -> None:
    """
    Fuerza UTF-8 en stdout/stderr. En Windows, al redirigir la salida a un fichero o a una
    tubería, Python usa la página de códigos local (p. ej. cp1252) y los caracteres como
    '★' o 'Φ' provocan UnicodeEncodeError. Con esto la salida no falla en ningún sistema.
    """
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            try:
                flujo.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
