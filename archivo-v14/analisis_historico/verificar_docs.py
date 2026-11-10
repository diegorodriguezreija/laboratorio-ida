"""
Comprobaciones de la documentación (sección 7.9 de la especificación de publicación):

1. Cada enlace relativo de los .md apunta a un fichero o carpeta que existe.
2. Cada ruta entre comillas invertidas que parece un fichero del repositorio existe.
3. Términos prohibidos (lenguaje enfático y afirmaciones no respaldadas) fuera de
   docs/MANIFIESTO.md. Las apariciones permitidas son negaciones explícitas o nombres de
   ficheros del código, y se listan en PERMITIDOS con su motivo.

Termina con código 1 si hay problemas.  python analisis/verificar_docs.py
"""

import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
EXCLUIR = {".git", ".venv", "salidas", "node_modules"}
PROHIBIDOS = ["histórico", "contundente", "concluyente", "extraordinari", "rotund", "impecable",
              "revolucionari", "techo somático", "emergencia", "consciencia"]
# (fichero, término, fragmento que debe contener la línea) -> motivo
PERMITIDOS = [
    ("", "consciencia", "consciencia_talamo_dmn", "nombre de un módulo del código"),
    ("README.md", "consciencia", "ni una afirmación sobre consciencia", "negación explícita (sección 7.1)"),
    ("README.en.md", "consciousness", "", ""),
    ("docs/RESULTADOS_Y_VERIFICACION.md", "consciencia", "Φ de Tononi / consciencia", "fila de la fe de erratas"),
    ("docs/RESULTADOS_Y_VERIFICACION.md", "consciencia", "Consciencia ni", "lista «Qué no se afirma»"),
    ("docs/RESULTADOS_Y_VERIFICACION.md", "emergencia", "emergencia de inteligencia", "lista «Qué no se afirma»"),
    ("docs/GLOSARIO.md", "consciencia", "ni mide consciencia", "negación explícita"),
    ("analisis/preregistro/H1_H7_H2.md", "", "", "preregistro: registro previo que no se reescribe"),
]


def ficheros_md():
    for p in RAIZ.rglob("*.md"):
        if not (EXCLUIR & set(p.relative_to(RAIZ).parts)):
            yield p


def permitido(rel: str, termino: str, linea: str) -> bool:
    for f, t, frag, _ in PERMITIDOS:
        if (not f or f == rel) and (not t or t == termino) and (not frag or frag in linea):
            return True
    return False


def main() -> int:
    problemas = []
    for p in ficheros_md():
        rel = p.relative_to(RAIZ).as_posix()
        texto = p.read_text(encoding="utf-8")
        en_codigo = False
        for n, linea in enumerate(texto.splitlines(), 1):
            if linea.strip().startswith("```"):
                en_codigo = not en_codigo
            for destino in re.findall(r"\]\(([^)\s]+)\)", linea):
                if destino.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                objetivo = (p.parent / destino.split("#")[0]).resolve()
                if not objetivo.exists():
                    problemas.append(f"{rel}:{n}: enlace roto -> {destino}")
            if not en_codigo:
                for ruta in re.findall(r"`([\w./-]+\.(?:py|md|csv|json|yml|cff|txt|gz|ini|sql|tf))`", linea):
                    candidatos = [RAIZ / ruta, p.parent / ruta]
                    if "/" in ruta and not any(c.exists() for c in candidatos):
                        problemas.append(f"{rel}:{n}: ruta inexistente -> {ruta}")
            if rel == "docs/MANIFIESTO.md":
                continue
            bajo = linea.lower()
            for termino in PROHIBIDOS:
                if termino in bajo and not permitido(rel, termino, linea):
                    problemas.append(f"{rel}:{n}: término prohibido '{termino}'")
    for pr in problemas:
        print(pr)
    print(f"{len(problemas)} problemas")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
