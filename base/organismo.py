"""
Constructor del organismo bioinspirado de IdA (base).
"""

from typing import Optional
from nivel_1_core.contratos import Arquetipo
from nivel_1_core.gestor_onda import GestorOndaCore
from nivel_1_core.persistencia.motor_sqlite_wal import MotorSQLiteWAL

from nivel_2_sistemas.plasticidad_td_hebbiana import MatrizHebbianaTresFactores
from nivel_2_sistemas.s1_reactivo import crear_sistema_s1
from nivel_2_sistemas.s2_limbico import crear_sistema_s2
from nivel_2_sistemas.s3_racional import crear_sistema_s3
from nivel_2_sistemas.ciclo_sueno_rem import GestorCicloSuenoREM
from nivel_2_sistemas.consciencia_talamo_dmn import (
    BucleTalamocortical,
    RedNeuronalPorDefecto,
)
from nivel_2_sistemas.autopoiesis_ast import CirujanoAST


def construir_organismo(
    sensor,
    actuador,
    arquetipo: Optional[Arquetipo] = None,
    db_sqlite_path: str = ":memory:",
    frecuencia_max_ms: float = 100.0,
    habilitar_autopoiesis: bool = False,
) -> GestorOndaCore:
    if arquetipo is None:
        arquetipo = Arquetipo(nombre="OrganismoBase", linaje="Base_IdA")

    matriz = MatrizHebbianaTresFactores()
    s1 = crear_sistema_s1(matriz_hebbiana=matriz)
    s2 = crear_sistema_s2()
    s3 = crear_sistema_s3()

    sqlite_wal = MotorSQLiteWAL(db_sqlite_path) if db_sqlite_path != ":memory:" else None
    cirujano = CirujanoAST() if habilitar_autopoiesis else None

    return GestorOndaCore(
        sensor=sensor,
        actuador=actuador,
        arquetipo=arquetipo,
        sistemas_cognitivos=[s1, s2, s3],
        bucle_talamocortical=BucleTalamocortical(),
        dmn=RedNeuronalPorDefecto(),
        gestor_sueno_rem=GestorCicloSuenoREM(),
        cirujano_ast=cirujano,
        sqlite_wal=sqlite_wal,
        frecuencia_max_ms=frecuencia_max_ms,
        amplitud_max=100,
    )
