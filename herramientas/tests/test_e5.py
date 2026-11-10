"""
E5: registro del arbitraje y creencias sin cambiar la trayectoria; clases de candidato; carga falsa;
regla nueva de la curiosidad (gana solo frente a relleno y sin supervivencia de S1).
"""

import asyncio
import os
from types import SimpleNamespace

import pytest

from nivel_1_core.contratos import Onda, Pieza
from nivel_1_core.estado_somatico import EstadoSomatico
from nivel_1_core.persistencia.memoria_tridimensional import DimensionActiva
from nivel_1_core.vocabulario import V_Comando
from herramientas import parametros as P
from herramientas.analisis_paso0.episodios import EPISODIOS
from herramientas.arbitraje import clase, puntuacion
from herramientas.modificadores import CompCuriosidadIntrinseca, instalar_correccion_carga
from herramientas.observador.observador import ObservadorV14, observando


def test_registros_de_e5_no_cambian_la_trayectoria(tmp_path):
    sin = asyncio.run(EPISODIOS["crafter"](aislar_ruido=True, latidos=120, semilla=7))
    aj = dict(P.ajustes("crafter", P.RUTA_OBSERVACION), registrar_arbitraje=True, creencias=True)
    obs = ObservadorV14("crafter", P.parametros("crafter", P.RUTA_OBSERVACION), aj,
                        salida=str(tmp_path / "c.jsonl.gz"), partida="c")
    with observando(obs):
        con = asyncio.run(EPISODIOS["crafter"](aislar_ruido=True, latidos=120, semilla=7))
    obs.cerrar()
    assert con["decisiones"] == sin["decisiones"]
    assert os.path.exists(tmp_path / "c.creencias.md") and os.path.exists(tmp_path / "c.creencias.json")


def _imp(cmd, inputs, **prod):
    return Pieza("i", "Impulso", 0.7, 0.7, product={"comando": cmd, **prod}, inputs=inputs)


@pytest.mark.parametrize("pieza,esperada", [
    (_imp(V_Comando.ATACAR, ["zombi", "Comp_CrafterS1"]), "supervivencia"),
    (_imp(V_Comando.MOVER, ["Propiocepcion_x", "Comp_CrafterS1"], es_supervivencia_pag=True), "supervivencia"),
    (_imp(V_Comando.MOVER, ["Propiocepcion_x", "Comp_CrafterS1"]), "relleno"),
    (_imp(V_Comando.ESPERAR, ["Propiocepcion_x", "Comp_CrafterS1"]), "relleno"),
    (_imp(V_Comando.ESPERAR, ["Comp_CrafterS2"], dormir=True, target="DORMIR"), "proposito"),
    (_imp(V_Comando.MOVER, ["agua_3", "Comp_CrafterS1"]), "proposito"),
    (_imp(V_Comando.MOVER, ["Simulacion_Ruta", "Comp_PlanificacionMotora"], meta_teleologica="RUTA_FERTIL"), "proposito"),
], ids=["atacar", "huir", "moverse_sin_objetivo", "esperar", "dormir", "ir_al_agua", "ruta_con_meta"])
def test_clase_de_candidato(pieza, esperada):
    assert clase(pieza) == esperada


def test_correccion_de_la_carga_falsa():
    soma = EstadoSomatico()
    jugador = SimpleNamespace(inventory={"wood": 3, "stone": 2})
    core = SimpleNamespace(soma=soma, sensor=SimpleNamespace(env=SimpleNamespace(_player=jugador)))
    instalar_correccion_carga(core, ["iron", "diamond"])
    soma.objeto_cargado = {"salud": 9}  # lo que deja un COGER en Crafter
    soma.aplicar_metabolismo_latido(1)
    assert soma.objeto_cargado is None
    jugador.inventory["iron"] = 1
    soma.aplicar_metabolismo_latido(2)
    assert soma.objeto_cargado is not None


def _onda(impulsos):
    onda = Onda(ciclo=1, amplitud_max=100)
    onda.reactiva.ev["Supervivencia"] = {"Alarma_Supervivencia": Pieza(
        "Alarma_Supervivencia", "Supervivencia", 0.2, 0.9, product={"nivel_peligro": 0.0})}
    onda.reactiva.ev["Propiocepcion"] = {"p": Pieza("p", "Propiocepcion", 0.2, 1.0, product={"nodos_adyacentes": ["a", "b"]})}
    for i, p in enumerate(impulsos):
        p.id = f"s1_{i}"
        p.product["origen_sistema"] = "S1"
        onda.reactiva.acc.setdefault("Impulso", {})[p.id] = p
    return onda


def _ctx():
    soma = EstadoSomatico()
    soma.alimentacion = 80.0
    return {"soma": soma, "activa": DimensionActiva()}


AJ = dict(P.AJUSTES_BASE["curiosidad"], peso=0.3, regla="relleno")


def test_curiosidad_gana_al_relleno_sin_supervivencia():
    relleno = _imp(V_Comando.MOVER, ["Propiocepcion_x", "Comp_CrafterS1"])
    onda, ctx = _onda([relleno]), _ctx()
    assert asyncio.run(CompCuriosidadIntrinseca(AJ).procesar_reactiva(onda, ctx))
    cur = onda.reactiva.acc["Impulso"]["impulso_curiosidad_a"]
    assert puntuacion(cur, ctx["soma"]) > puntuacion(relleno, ctx["soma"])


def test_curiosidad_no_gana_a_la_supervivencia_ni_al_proposito():
    for imp in (_imp(V_Comando.ATACAR, ["zombi", "Comp_CrafterS1"]), _imp(V_Comando.MOVER, ["agua_3", "Comp_CrafterS1"])):
        onda, ctx = _onda([imp]), _ctx()
        asyncio.run(CompCuriosidadIntrinseca(AJ).procesar_reactiva(onda, ctx))
        cur = onda.reactiva.acc["Impulso"].get("impulso_curiosidad_a")
        assert cur is None or puntuacion(cur, ctx["soma"]) < puntuacion(imp, ctx["soma"]) - 0.04

