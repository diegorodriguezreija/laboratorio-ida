import ast
import pathlib
from typing import List, Optional
import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
RUTAS_SAGRADAS = [RAIZ / "base" / "nivel_1_core", RAIZ / "base" / "nivel_2_sistemas"]

IMPORTS_PROHIBIDOS_EN_MENTE = {
    "os", "sys", "subprocess", "shutil", "socket", "http", "urllib",
    "requests", "httpx", "fastapi", "flask", "pygame", "selenium",
    "playwright", "openai", "anthropic", "ollama", "mcp", "scapy",
    "chess", "crafter", "tkinter",
}

TERMINOS_DOMINIO_PROHIBIDOS = {
    ".exe", ".txt", ".brote", ".env", "html", "dom_node",
    "snake", "pacman", "fantasma", "manzana", "ransomware",
    "crafter", "ajedrez", "chess", "lichess", "stockfish",
    "brote", "espora", "tablilla", "monolito", "oraculo",
    "santuario", "alcaloide", "conium", "amanita", "taxonom",
    "tablero", "jaque", "peon", "alfil", "pickaxe", "zombie",
    "acc_consumir",  # Erradicado en v11.0 en favor de DEGLUTIR / ASIMILAR / CENSURAR
}

CONSTANTES_NUMERICAS_DOMINIO_SOSPECHOSAS = {
    22,     # 22 logros del benchmark Crafter
    64,     # 64 casillas de tablero de ajedrez / 64x64 grid
    315,    # 21x15 celdas de Playsnake.org
    1320,   # UCI_Elo minimo de Stockfish
    1350,
    1450,
    1500,
}


def obtener_archivos_python(directorios):
    archivos = []
    for d in directorios:
        if d.exists():
            archivos.extend(sorted(d.rglob("*.py")))
    return archivos


def _plegar_literales_str(nodo: ast.AST) -> Optional[str]:
    """
    Plegado de constantes (constant folding) sobre el AST para detectar
    cadenas partidas mediante concatenacion (ej. 'bro' + 'te'), f-strings,
    o literales codificados en bytes (ej. b'\\x63\\x72\\x61\\x66\\x74\\x65\\x72').
    """
    if isinstance(nodo, ast.Constant):
        if isinstance(nodo.value, str):
            return nodo.value
        elif isinstance(nodo.value, bytes):
            try:
                return nodo.value.decode("utf-8", errors="ignore")
            except Exception:
                return None
    if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Add):
        izq = _plegar_literales_str(nodo.left)
        der = _plegar_literales_str(nodo.right)
        if izq is not None and der is not None:
            return izq + der
    if isinstance(nodo, ast.JoinedStr):
        partes: List[str] = []
        for val in nodo.values:
            s = _plegar_literales_str(val)
            if s is not None:
                partes.append(s)
        return "".join(partes) if partes else None
    return None


def auditar_ast_pureza(
    codigo: str,
    nombre_archivo: str = "<memoria>",
    es_persistencia_o_termo: bool = False,
) -> List[str]:
    """
    Analiza estaticamente un arbol AST de Nivel 1 o Nivel 2 y devuelve la lista
    de violaciones detectadas:
    1. Importaciones de I/O, motores externos o Nivel 3.
    2. Literales de texto, f-strings y concatenaciones plegadas ('bro' + 'te').
    3. Identificadores (variables, atributos, argumentos, funciones, clases) con
       vocabulario de dominio (botanica/archivos, snake, ajedrez, crafter).
    4. Asignaciones de constantes numericas calibradas para un mundo especifico.
    """
    arbol = ast.parse(codigo, filename=nombre_archivo)
    violaciones: List[str] = []

    for nodo in ast.walk(arbol):
        # 1. Verificacion de Importaciones Prohibidas
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                modulo_raiz = alias.name.split(".")[0]
                if not es_persistencia_o_termo and modulo_raiz in IMPORTS_PROHIBIDOS_EN_MENTE:
                    violaciones.append(
                        f"VIOLACION DE AISLAMIENTO I/O en {nombre_archivo}: "
                        f"Importacion prohibida '{alias.name}'."
                    )
                if alias.name.startswith("nivel_3_componentes"):
                    violaciones.append(
                        f"VIOLACION DE INVERSION DE CONTROL en {nombre_archivo}: "
                        f"Nivel 1/2 jamas puede importar de Nivel 3."
                    )

        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulo_raiz = nodo.module.split(".")[0]
            if not es_persistencia_o_termo and modulo_raiz in IMPORTS_PROHIBIDOS_EN_MENTE:
                violaciones.append(
                    f"VIOLACION DE AISLAMIENTO I/O en {nombre_archivo}: "
                    f"Importacion prohibida desde '{nodo.module}'."
                )
            if nodo.module.startswith("nivel_3_componentes"):
                violaciones.append(
                    f"VIOLACION DE INVERSION DE CONTROL en {nombre_archivo}: "
                    f"Nivel 1/2 jamas puede importar desde Nivel 3."
                )

        # 2. Verificacion de Literales y Cadenas Partidas ('bro' + 'te')
        cadena_plegada = _plegar_literales_str(nodo)
        if cadena_plegada is not None:
            valor_lower = cadena_plegada.lower()
            for termino in TERMINOS_DOMINIO_PROHIBIDOS:
                if termino in valor_lower:
                    violaciones.append(
                        f"CONTAMINACION SEMANTICA DE LITERAL en {nombre_archivo}: "
                        f"Termino prohibido '{termino}' detectado en '{cadena_plegada}'."
                    )

        # 3. Verificacion de Nombres de Variables, Atributos, Funciones y Clases
        identificadores_nodo: List[str] = []
        if isinstance(nodo, ast.Name):
            identificadores_nodo.append(nodo.id)
        elif isinstance(nodo, ast.Attribute):
            identificadores_nodo.append(nodo.attr)
        elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            identificadores_nodo.append(nodo.name)
        elif isinstance(nodo, ast.arg):
            identificadores_nodo.append(nodo.arg)

        for ident in identificadores_nodo:
            ident_lower = ident.lower()
            for termino in TERMINOS_DOMINIO_PROHIBIDOS:
                t_clean = termino.lstrip(".")
                if len(t_clean) >= 4 and t_clean in ident_lower:
                    violaciones.append(
                        f"CONTAMINACION EN IDENTIFICADOR en {nombre_archivo}: "
                        f"Identificador '{ident}' contiene termino de dominio '{t_clean}'."
                    )

        # 4. Verificacion de Constantes Numericas Calibradas a un Mundo en Asignaciones
        if isinstance(nodo, (ast.Assign, ast.AnnAssign)):
            valor_ast = nodo.value
            if isinstance(valor_ast, ast.Constant) and isinstance(valor_ast.value, (int, float)) and not isinstance(valor_ast.value, bool):
                if valor_ast.value in CONSTANTES_NUMERICAS_DOMINIO_SOSPECHOSAS and not es_persistencia_o_termo:
                    violaciones.append(
                        f"CONSTANTE NUMERICA DE DOMINIO SOSPECHOSA en {nombre_archivo}: "
                        f"Valor magico {valor_ast.value} calibrado para un mundo especifico."
                    )

    return violaciones


@pytest.mark.parametrize("ruta_archivo", obtener_archivos_python(RUTAS_SAGRADAS))
def test_pureza_arquitectonica_niveles_1_y_2(ruta_archivo: pathlib.Path):
    codigo = ruta_archivo.read_text(encoding="utf-8")
    es_persistencia_o_termo = ruta_archivo.name in {
        "cosechador_termodinamico.py", "motor_sqlite_wal.py", "motor_pgvector.py"
    }
    violaciones = auditar_ast_pureza(
        codigo,
        nombre_archivo=ruta_archivo.name,
        es_persistencia_o_termo=es_persistencia_o_termo,
    )
    assert not violaciones, "\n".join(violaciones)


def test_negativo_trampa_cadena_partida():
    """Verifica que el linter detecta una cadena de dominio partida ('bro' + 'te')."""
    codigo_trampa = 'x = "bro" + "te"\n'
    violaciones = auditar_ast_pureza(codigo_trampa, nombre_archivo="trampa_cadena.py")
    assert any("brote" in v.lower() for v in violaciones), (
        "El linter no detecto la concatenacion de cadena partida 'bro' + 'te'."
    )


def test_negativo_trampa_nombre_variable_dominio():
    """Verifica que el linter detecta nombres de variables o atributos acoplados al dominio."""
    codigo_trampa = "espora_activa = 1\nmonolito_local = True\n"
    violaciones = auditar_ast_pureza(codigo_trampa, nombre_archivo="trampa_variable.py")
    assert any("espora" in v.lower() for v in violaciones)
    assert any("monolito" in v.lower() for v in violaciones)


def test_negativo_trampa_constante_numerica_mundo():
    """Verifica que el linter detecta constantes numericas calibradas para un mundo (ej. 1320 ELO, 315 celdas)."""
    codigo_trampa = "LIMITE_MUNDO = 1320\nCELDAS_GRID = 315\n"
    violaciones = auditar_ast_pureza(codigo_trampa, nombre_archivo="trampa_constante.py")
    assert len(violaciones) >= 2


def test_negativo_trampa_bytes_encoding():
    """Verifica que el linter detecta literales de bytes ofuscados (ej. b'\\x63\\x72\\x61\\x66\\x74\\x65\\x72' = 'crafter')."""
    codigo_trampa = 'x = b"\\x63\\x72\\x61\\x66\\x74\\x65\\x72"\n'
    violaciones = auditar_ast_pureza(codigo_trampa, nombre_archivo="trampa_bytes.py")
    assert any("crafter" in v.lower() for v in violaciones), (
        "El linter no detecto el literal de bytes ofuscado b'\\x63\\x72\\x61\\x66\\x74\\x65\\x72'."
    )


def test_negativo_trampa_getattr_dinamico():
    """Verifica que el linter detecta accesos dinamicos getattr con literales de dominio o cadenas partidas."""
    codigo_trampa = 'fn = getattr(obj, "cra" + "fter")\n'
    violaciones = auditar_ast_pureza(codigo_trampa, nombre_archivo="trampa_getattr.py")
    assert any("crafter" in v.lower() for v in violaciones), (
        "El linter no detecto el termino de dominio en getattr(obj, 'cra' + 'fter')."
    )

