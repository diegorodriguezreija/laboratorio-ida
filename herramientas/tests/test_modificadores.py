"""
Modificadores de E2-E4: apagados no envuelven nada; con valores originales no cambian la trayectoria;
la curiosidad nunca supera a S1 y calla con peligro o hambre.
"""

import asyncio

import pytest

from nivel_1_core.contratos import Onda, Pieza
from nivel_1_core.estado_somatico import EstadoSomatico
from nivel_1_core.gestor_onda import GestorOndaCore
from nivel_1_core.persistencia.memoria_tridimensional import DimensionActiva
from nivel_1_core.vocabulario import V_Comando
from herramientas import parametros as P
from herramientas.analisis_paso0.episodios import EPISODIOS
from herramientas.modificadores import CompCuriosidadIntrinseca, modificando, puntuacion_a0


def test_apagados_no_envuelven_nada():
    antes = GestorOndaCore.__dict__["ejecutar_latido"]
    with modificando(P.parametros("crafter"), P.ajustes("crafter")):
        assert GestorOndaCore.__dict__["ejecutar_latido"] is antes


def test_calibracion_con_valores_originales_no_cambia_la_trayectoria():
    sin = asyncio.run(EPISODIOS["crafter"](aislar_ruido=True, latidos=120, semilla=7))
    flags = dict(P.parametros("crafter"), calibracion_cuerpo_crafter=True)
    with modificando(flags, P.ajustes("crafter")):  # factores 1,0 y alcance sin lÃ­mite
        con = asyncio.run(EPISODIOS["crafter"](aislar_ruido=True, latidos=120, semilla=7))
    assert con["decisiones"] == sin["decisiones"]
    assert GestorOndaCore.__dict__["ejecutar_latido"] is not None


def _onda(peligro, impulsos_s1):
    onda = Onda(ciclo=1, amplitud_max=100)
    onda.reactiva.ev["Supervivencia"] = {"Alarma_Supervivencia": Pieza(
        "Alarma_Supervivencia", "Supervivencia", 0.5, 0.9, product={"nivel_peligro": peligro})}
    onda.reactiva.ev["Propiocepcion"] = {"p": Pieza("p", "Propiocepcion", 0.2, 1.0,
                                                    product={"nodos_adyacentes": ["a", "b"]})}
    for i, (ar, tr) in enumerate(impulsos_s1):
        onda.reactiva.acc.setdefault("Impulso", {})[f"s1_{i}"] = Pieza(
            f"s1_{i}", "Impulso", ar, tr, product={"comando": V_Comando.MOVER, "target": "a", "origen_sistema": "S1"})
    return onda


def _ctx(alimentacion=80.0):
    soma = EstadoSomatico()
    soma.alimentacion = alimentacion
    activa = DimensionActiva()
    activa.registrar_transicion_topologica("x", "a")  # Â«aÂ» ya visitado: lo nuevo es Â«bÂ»
    return {"soma": soma, "activa": activa}


AJ = dict(P.AJUSTES_BASE["curiosidad"], peso=0.9)


def test_curiosidad_nunca_supera_a_s1():
    comp = CompCuriosidadIntrinseca(AJ)
    onda = _onda(0.0, [(0.40, 0.40), (0.95, 0.90)])
    assert asyncio.run(comp.procesar_reactiva(onda, _ctx()))
    imp = onda.reactiva.acc["Impulso"]["impulso_curiosidad_b"]
    estres = _ctx()["soma"].cortisol
    s1 = min(puntuacion_a0(p, estres) for k, p in onda.reactiva.acc["Impulso"].items() if k.startswith("s1_"))
    assert puntuacion_a0(imp, estres) <= s1 - AJ["margen_s1"] + 1e-9
    assert imp.product["target"] == "b"


@pytest.mark.parametrize("peligro,alimentacion", [(0.9, 80.0), (0.0, 30.0)], ids=["peligro", "hambre"])
def test_curiosidad_calla_con_peligro_o_hambre(peligro, alimentacion):
    comp = CompCuriosidadIntrinseca(AJ)
    onda = _onda(peligro, [])
    assert not asyncio.run(comp.procesar_reactiva(onda, _ctx(alimentacion)))
    assert "Impulso" not in onda.reactiva.acc

