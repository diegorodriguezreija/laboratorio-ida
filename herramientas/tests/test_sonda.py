"""
La sonda del paso 0 es de solo lectura: restaura todo lo que envuelve y no cambia la trayectoria.
"""

from nivel_1_core.gestor_onda import GestorOndaCore
from nivel_1_core.persistencia.memoria_tridimensional import DimensionActiva
from nivel_1_core.persistencia.motor_sqlite_wal import MotorSQLiteWAL
from nivel_2_sistemas.ciclo_sueno_rem import GestorCicloSuenoREM
from nivel_2_sistemas.sistema_base import SistemaCognitivoTriunico
from herramientas.analisis_paso0 import sonda

ENVUELTOS = [
    (SistemaCognitivoTriunico, "_ejecutar_tres_barridos"),
    (GestorOndaCore, "ejecutar_latido"),
    (DimensionActiva, "consolidar_pieza"),
    (DimensionActiva, "obtener_pieza"),
    (MotorSQLiteWAL, "sincronizar_desde_activa"),
    (GestorCicloSuenoREM, "procesar_sueno_rem"),
]


def test_restaura_los_metodos_al_salir():
    antes = [cls.__dict__[n] for cls, n in ENVUELTOS]
    with sonda.sondeando(sonda._Estado()):
        assert [cls.__dict__[n] for cls, n in ENVUELTOS] != antes
    assert [cls.__dict__[n] for cls, n in ENVUELTOS] == antes


def test_misma_trayectoria_con_y_sin_sonda():
    r = sonda.episodio("ejemplo_minimo", {"latidos": 30})  # se detiene si la trayectoria cambia
    assert len(r["filas"]) == 30
    fila = r["filas"][0]
    assert {"ms", "amp_usada", "amp_max", "componentes", "max_arousal_ev"} <= set(fila)
    assert sum(c["amplitud"] for c in fila["componentes"]) <= fila["amp_usada"]

