"""
Parámetros de la v14 por mundo (`v14/parametros_mundo.json`).

Cada mundo declara los mismos flags. Todos están apagados por defecto: con estos valores la v14
es idéntica a la v13 (lo comprueba `v14/canario.py`). Cada mundo puede además ajustar, en
`ajustes`, los valores numéricos de los observadores (umbrales del Episodio, K, olvido, presupuesto
y tope de coste); lo que no ajusta toma el valor de `AJUSTES_BASE`. Los ajustes no encienden nada.

El esquema es cerrado: un flag o un ajuste desconocido, o un valor de otro tipo, es un error, para
que una errata no encienda nada en silencio.
"""

from __future__ import annotations

import copy
import json
import os
from typing import Any, Dict

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parametros_mundo.json")
RUTA_OBSERVACION = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parametros_observacion.json")
ESQUEMA = "ida.v14.parametros_mundo/4"

PERFILES_MEMORIA = ("apagada", "ligera", "completa")
SENALES_EPISODIO = ("soma", "mundo_crafter")

# flag -> (tipo, valor apagado)
FLAGS: Dict[str, Any] = {
    "paso1_claves_axiomas_heredados": (bool, False),
    "paso1_cuota_frecuencia": (bool, False),
    "paso1_alerta": (bool, False),
    "memoria_experiencia": (str, "apagada"),
    "observar_activa": (bool, False),
    "observar_proactiva": (bool, False),
    "indicadores_generales": (bool, False),
    "reglas_ancestrales": (bool, False),
    # Modificadores de E2-E4 (bloques A y B): apagados por defecto, medidos aparte
    "calibracion_cuerpo_crafter": (bool, False),
    "curiosidad_intrinseca": (bool, False),
    # Modificador de E5 (bloque E)
    "corregir_carga_falsa_crafter": (bool, False),
}

# Valores numéricos de los observadores (plan v14, secciones 4.3 a 4.5). Calibración inicial.
AJUSTES_BASE: Dict[str, Any] = {
    # De dónde salen las señales del Episodio y del balance: el soma o, en Crafter, el juego
    "senales_episodio": "soma",
    # Peligro que leen los observadores de Crafter: el de S1 ("s1", pasos 2 y 3) o el de las piezas
    # de peligro del juego que entrega el adaptador ("juego", preregistro E2-E4)
    "peligro_crafter": "s1",
    # E5: registro del arbitraje (bloque D) y conocimiento formal legible al morir (bloque G2), observadores
    "registrar_arbitraje": False,
    "creencias": False,
    # E5, bloque E: objetos del inventario del juego que cuentan como carga física
    "carga_pesados": ["iron", "diamond"],
    "episodio": {"abre_arousal": 0.65, "cierra_arousal": 0.55, "abre_dvit": 2.0, "abre_dali": 12.0,
                 "cierra_dvit": 0.5, "longitud_max": 6, "sorpresa_abre": True},
    # El Core guarda las K Piezas de mayor arousal de la Onda, sin las del cuerpo ni las motoras
    "k_piezas": 3,
    "clases_excluidas": ["Interocepcion", "Propiocepcion", "Ingestion", "Escena", "Impulso", "Ejecucion",
                         "Exteriorizacion", "Expresion"],
    # Mantenimiento (consolidar, indexar, olvidar): en REM, cada N latidos (0 = nunca) y al morir
    "mantenimiento_cada": 25,
    # Nunca se olvidan las proposiciones demostradas, lo heredado ni los episodios de balance extremo
    "olvido": {"horizonte_latidos": 150, "arousal_acumulado_min": 1.5, "balance_extremo": 10.0},
    # Presupuesto de memoria (virtual, en unidades de amplitud), en orden S1, S2, S3
    "memoria_presupuesto": {"fraccion_sobrante": 0.10, "restante_minimo_s2_s3": 0.50,
                            "coste_guardar": 1, "coste_recuperar": 1},
    # Proactiva: expectativas solo con más sobrante; caducan y tienen un tope de abiertas
    "proactiva": {"restante_minimo": 0.70, "horizonte_latidos": 12, "max_abiertas": 20,
                  "min_confirmaciones": 3, "ventana_falsacion": 5, "paso_sube": 0.10, "paso_baja": 0.20,
                  "confianza_demostrada": 0.80, "tolerancia_neutro": 0.25},
    # Bloque A: calibración del cuerpo simulado de Crafter (valores originales = sin efecto)
    "calibracion": {"factor_lastre_carga": 1.0, "factor_desgaste_basal": 1.0, "alcance_peligro": 99.0},
    # Bloque B: curiosidad intrínseca (un solo parámetro libre: el peso)
    "curiosidad": {"peso": 0.5, "peligro_max": 0.35, "alimentacion_min": 45.0, "amplitud_restante_min": 0.5,
                   "margen_s1": 0.05, "regla": "bajo_s1"},  # "bajo_s1" (E2-E4) o "relleno" (E5, bloque F)
    # Tope de coste por latido del observador: fracción de la latencia mediana medida y del plazo
    "tope_coste": {"fraccion_latencia": 0.05, "fraccion_plazo": 0.01, "absoluto_ms": 0.0},
}

MUNDOS = ("crafter", "ejemplo_minimo", "bosque", "ajedrez", "snake")


class ErrorParametros(ValueError):
    pass


def _validar_ajustes(mundo: str, ajustes: Dict[str, Any], base: Dict[str, Any], ruta: str = "") -> None:
    for clave, valor in ajustes.items():
        donde = f"{mundo}.ajustes.{ruta}{clave}"
        if clave not in base:
            raise ErrorParametros(f"{donde}: ajuste desconocido")
        esperado = base[clave]
        if isinstance(esperado, dict):
            if not isinstance(valor, dict):
                raise ErrorParametros(f"{donde}: se esperaba un objeto")
            _validar_ajustes(mundo, valor, esperado, f"{ruta}{clave}.")
        elif isinstance(esperado, bool) or isinstance(valor, bool):
            if type(valor) is not type(esperado):
                raise ErrorParametros(f"{donde}: tipo {type(valor).__name__}, se esperaba {type(esperado).__name__}")
        elif isinstance(esperado, (int, float)):
            if not isinstance(valor, (int, float)):
                raise ErrorParametros(f"{donde}: se esperaba un número")
        elif type(valor) is not type(esperado):
            raise ErrorParametros(f"{donde}: tipo {type(valor).__name__}, se esperaba {type(esperado).__name__}")
    if ruta == "" and ajustes.get("senales_episodio", "soma") not in SENALES_EPISODIO:
        raise ErrorParametros(f"{mundo}.ajustes.senales_episodio: no es uno de {SENALES_EPISODIO}")
    if ruta == "" and ajustes.get("curiosidad", {}).get("regla", "bajo_s1") not in ("bajo_s1", "relleno"):
        raise ErrorParametros(f"{mundo}.ajustes.curiosidad.regla: no es 'bajo_s1' ni 'relleno'")
    if ruta == "" and ajustes.get("peligro_crafter", "s1") not in ("s1", "juego"):
        raise ErrorParametros(f"{mundo}.ajustes.peligro_crafter: no es 's1' ni 'juego'")


def _mezclar(base: Dict[str, Any], encima: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in encima.items():
        out[k] = _mezclar(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def cargar(ruta: str = RUTA) -> Dict[str, Dict[str, Any]]:
    """Lee y valida el fichero. Devuelve {mundo: {flag: valor}} (solo los flags)."""
    return {m: d["flags"] for m, d in _cargar_completo(ruta).items()}


def _cargar_completo(ruta: str) -> Dict[str, Dict[str, Any]]:
    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)
    if datos.get("esquema") != ESQUEMA:
        raise ErrorParametros(f"esquema inesperado: {datos.get('esquema')!r} (se esperaba {ESQUEMA!r})")
    mundos = datos.get("mundos")
    if not isinstance(mundos, dict) or set(mundos) != set(MUNDOS):
        raise ErrorParametros(f"los mundos deben ser exactamente {MUNDOS}")
    out = {}
    for mundo, decl in mundos.items():
        if not isinstance(decl, dict) or set(decl) - {"flags", "ajustes"} or "flags" not in decl:
            raise ErrorParametros(f"{mundo}: debe tener 'flags' y, opcionalmente, 'ajustes'")
        flags = decl["flags"]
        if set(flags) != set(FLAGS):
            sobran = sorted(set(flags) - set(FLAGS))
            faltan = sorted(set(FLAGS) - set(flags))
            raise ErrorParametros(f"{mundo}: flags desconocidos {sobran} o ausentes {faltan}")
        for flag, valor in flags.items():
            tipo, _ = FLAGS[flag]
            if type(valor) is not tipo:
                raise ErrorParametros(f"{mundo}.{flag}: tipo {type(valor).__name__}, se esperaba {tipo.__name__}")
            if flag == "memoria_experiencia" and valor not in PERFILES_MEMORIA:
                raise ErrorParametros(f"{mundo}.{flag}: {valor!r} no es uno de {PERFILES_MEMORIA}")
        ajustes = decl.get("ajustes", {})
        _validar_ajustes(mundo, ajustes, AJUSTES_BASE)
        out[mundo] = {"flags": dict(flags), "ajustes": _mezclar(AJUSTES_BASE, ajustes)}
    return out


def parametros(mundo: str, ruta: str = RUTA) -> Dict[str, Any]:
    """Flags de un mundo."""
    return dict(cargar(ruta)[mundo])


def ajustes(mundo: str, ruta: str = RUTA) -> Dict[str, Any]:
    """Ajustes de un mundo, ya mezclados con AJUSTES_BASE."""
    return _cargar_completo(ruta)[mundo]["ajustes"]


def encendidos(ruta: str = RUTA) -> Dict[str, Dict[str, Any]]:
    """Flags que no están en su valor apagado, por mundo. Vacío si todo está apagado."""
    resultado: Dict[str, Dict[str, Any]] = {}
    for mundo, flags in cargar(ruta).items():
        distintos = {k: v for k, v in flags.items() if v != FLAGS[k][1]}
        if distintos:
            resultado[mundo] = distintos
    return resultado


def todos_apagados(ruta: str = RUTA) -> bool:
    return not encendidos(ruta)
