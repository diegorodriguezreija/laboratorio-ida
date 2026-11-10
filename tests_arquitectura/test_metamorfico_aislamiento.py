"""
N7 – Prueba metamórfica del aislamiento de los niveles 1 y 2.

Si el core no depende del vocabulario del mundo, renombrar todos los identificadores que ve
(nodos y entidades) sin cambiar la dinámica no debe cambiar su conducta. Se ejecuta el mundo
de ejemplo mínimo con el ruido físico aislado y cuatro vocabularios, y se compara latido a
latido: comando, objetivo (traducido al vocabulario base), sistema ganador, vitalidad,
alimentación y posición.

Límite conocido: la memoria vectorial (MotorPgVectorHNSW) genera embeddings con SHA-256 del
identificador, pero hoy ningún módulo la alimenta (enterrar_memoria no se llama), así que esa
vía no se ejerce aquí. Si se conectara, esta prueba debería repetirse.
"""

import asyncio

import pytest

from nivel_3_componentes.mundos.mundo_ejemplo_minimo.ejemplo_minimo_runner import ejecutar

LATIDOS = 60
BASE = {"claro": "claro", "fruta": "fruta", "seta": "seta"}
VOCABULARIOS = {
    "opaco": {"claro": "n7q", "fruta": "x1", "seta": "z9"},
    "orden_alfabetico_invertido": {"claro": "zz_lugar", "fruta": "aa_obj", "seta": "bb_obj"},
    "nombres_largos": {"claro": "nodo_de_prueba_con_nombre_largo", "fruta": "recurso_alfa", "seta": "recurso_beta"},
}


def _normalizar(traza, vocabulario):
    filas = []
    for t in traza:
        objetivo = t["objetivo"]
        for canonico, nombre in vocabulario.items():
            if objetivo.startswith(nombre + "_"):
                objetivo = canonico + objetivo[len(nombre):]
        filas.append((t["comando"], objetivo, t["sistema"], t["vitalidad"], t["alimentacion"], t["posicion"]))
    return filas


@pytest.fixture(scope="module")
def referencia():
    return _normalizar(asyncio.run(ejecutar(LATIDOS, None, aislar_ruido=True)), BASE)


def test_ejecucion_con_ruido_aislado_es_reproducible(referencia):
    assert _normalizar(asyncio.run(ejecutar(LATIDOS, None, aislar_ruido=True)), BASE) == referencia


def test_referencia_no_trivial(referencia):
    comandos = {c for c, *_ in referencia}
    assert len(referencia) == LATIDOS
    assert {"ACC_MOVER", "ACC_DEGLUTIR"} <= comandos, "el ejemplo debe moverse y comer para que la prueba tenga contenido"


@pytest.mark.parametrize("nombre", sorted(VOCABULARIOS))
def test_renombrar_identificadores_no_cambia_la_conducta(referencia, nombre):
    vocab = VOCABULARIOS[nombre]
    assert _normalizar(asyncio.run(ejecutar(LATIDOS, vocab, aislar_ruido=True)), vocab) == referencia
