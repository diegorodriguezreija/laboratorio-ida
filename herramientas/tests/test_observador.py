"""
Pasos 2 y 3 de la v14: el observador no cambia la trayectoria y sus piezas cumplen las reglas del plan.
"""

import asyncio

import numpy as np
import pytest

from nivel_1_core.calculadoras_estructurales import CalculadorasEstructurales
from nivel_1_core.gestor_onda import GestorOndaCore
from nivel_2_sistemas.sistema_base import SistemaCognitivoTriunico
from herramientas import parametros as P
from herramientas.analisis_paso0.episodios import EPISODIOS
from herramientas.observador.almacen import Almacen, Registro, relevancia
from herramientas.observador.episodios import Segmentador
from herramientas.observador.observador import ObservadorV14, observando
from herramientas.observador.proactiva import Proactiva

CASOS = [
    pytest.param("ejemplo_minimo", {"latidos": 60}, id="ejemplo_minimo"),
    pytest.param("bosque", {"latidos": 40}, id="bosque"),
    pytest.param("crafter", {"latidos": 150, "semilla": 7}, id="crafter_semilla_7"),
]


@pytest.mark.parametrize("mundo,opciones", CASOS)
def test_misma_trayectoria_con_observador_encendido(mundo, opciones):
    sin = asyncio.run(EPISODIOS[mundo](aislar_ruido=True, **opciones))
    flags, ajustes = P.parametros(mundo, P.RUTA_OBSERVACION), P.ajustes(mundo, P.RUTA_OBSERVACION)
    assert flags["observar_activa"] and flags["observar_proactiva"]
    obs = ObservadorV14(mundo, flags, ajustes)
    with observando(obs):
        con = asyncio.run(EPISODIOS[mundo](aislar_ruido=True, **opciones))
    res = obs.cerrar()
    assert con["decisiones"] == sin["decisiones"]
    assert res["latidos"] == len(sin["decisiones"])
    assert res["proactiva"]["pendientes_al_final"] == 0


def test_observando_restaura_los_metodos():
    antes = (GestorOndaCore.__dict__["ejecutar_latido"], SistemaCognitivoTriunico.__dict__["_ejecutar_tres_barridos"])
    obs = ObservadorV14("ejemplo_minimo", P.parametros("ejemplo_minimo"), P.ajustes("ejemplo_minimo"))
    with observando(obs):
        pass
    assert (GestorOndaCore.__dict__["ejecutar_latido"], SistemaCognitivoTriunico.__dict__["_ejecutar_tres_barridos"]) == antes


def test_con_los_flags_por_defecto_no_hace_nada():
    obs = ObservadorV14("crafter", P.parametros("crafter"), P.ajustes("crafter"))
    assert not obs.activo
    assert obs.cerrar() == {"activo": False}


def test_relevancia_es_la_formula_del_nucleo():
    cos = np.array([0.1, 0.5, 0.9, 1.0])
    aro = np.array([0.0, 0.3, 0.8, 1.4])
    esperado = [CalculadorasEstructurales.score_gravitacional_arousal(c, a) for c, a in zip(cos, aro)]
    assert np.allclose(relevancia(cos, aro), esperado)


def _reg(clase, id_, latido, protegido=False, rasgos=(1, 0, 0)):
    return Registro(clase=clase, id=id_, latido=latido, arousal=0.5, confianza=0.5, rasgos=np.array(rasgos, float),
                    sistema="S1", componente="c", episodio=None, protegido=protegido)


def test_almacen_dos_velocidades_y_olvido():
    # recuperar cuenta como uso y suma arousal: Â«xÂ» acaba con 0,5 + 0,5 = 1,0 acumulado, por debajo de 2,0
    a = Almacen(olvido={"horizonte_latidos": 10, "arousal_acumulado_min": 2.0, "balance_extremo": 5.0})
    a.guardar(_reg("Objeto", "x", 1))
    assert a.recuperar("Objeto", np.array([1.0, 0, 0]), 2) is None  # en el bÃºfer: aÃºn no se recupera
    a.guardar(_reg("Objeto", "demostrada", 1, protegido=True))
    a.guardar_episodio({"id": "e1", "hasta": 1, "balance": 0.0, "signo": 0, "huella": [1, 0], "max_arousal": 0.5, "desde": 1})
    a.guardar_episodio({"id": "e2", "hasta": 1, "balance": 9.0, "signo": 1, "huella": [0, 1], "max_arousal": 0.5, "desde": 1})
    a.mantenimiento(1)
    assert a.recuperar("Objeto", np.array([1.0, 0, 0]), 2)["clase"] == "Objeto"
    a.mantenimiento(50)  # 48 latidos sin uso y poco arousal acumulado
    ids = {i for por in a.reactiva.values() for i in por}
    assert ids == {"demostrada"}  # lo demostrado no se olvida
    assert [e["id"] for e in a.episodios] == ["e2"]  # el de balance extremo, tampoco


def test_proactiva_no_acumula_expectativas():
    aj = dict(P.ajustes("crafter", P.RUTA_OBSERVACION)["proactiva"], horizonte_latidos=5, max_abiertas=3)
    pro = Proactiva(aj)
    for n in range(1, 40):
        pro.validar(n, vit=9.0, ali=10.0, cerrados=[])
        pro.anotar(n, "ACC_COGER", "tree", "t", None, 9.0, 10.0, puede_esperar=True)
        assert len(pro.pendientes) <= aj["horizonte_latidos"]
        assert pro.abiertas() <= aj["max_abiertas"]
    pro.validar(40, 9.0, 10.0, [], todas=True)
    assert len(pro.pendientes) == 0
    assert pro.creadas > 0 and pro.omitidas_por_tope > 0


def test_proactiva_demuestra_y_deja_de_demostrar():
    aj = dict(P.ajustes("crafter", P.RUTA_OBSERVACION)["proactiva"], horizonte_latidos=1, min_confirmaciones=3,
              ventana_falsacion=3, confianza_demostrada=0.6)
    pro = Proactiva(aj)
    n, ali = 0, 10.0
    for _ in range(12):  # la acciÃ³n siempre mejora la comida
        n += 1
        pro.validar(n, 9.0, ali, [])
        pro.anotar(n, "ACC_DEGLUTIR", "cow", "c", None, 9.0, ali, puede_esperar=True)
        ali += 1.0
    h = pro.hipotesis[("ACC_DEGLUTIR", "cow")]
    assert h.demostrada and h.falsaciones == 0
    for _ in range(3):  # ahora empeora: se falsa
        n += 1
        pro.validar(n, 9.0, ali, [])
        pro.anotar(n, "ACC_DEGLUTIR", "cow", "c", None, 9.0, ali, puede_esperar=True)
        ali -= 2.0
    pro.validar(n + 1, 9.0, ali, [], todas=True)
    assert not h.demostrada and h.falsaciones > 0


def test_segmentador_reglas():
    u = {"abre_arousal": 0.65, "cierra_arousal": 0.55, "abre_dvit": 2.0, "abre_dali": 12.0, "cierra_dvit": 0.5,
         "longitud_max": 6, "sorpresa_abre": True}
    seg = Segmentador(u, 0.25, "p")

    def s(n, ar, vit=100.0, ali=80.0, sorpresa=False, colapso=False):
        return {"n": n, "arousal_ep": ar, "vit": vit, "ali": ali, "sorpresa": sorpresa, "colapso": colapso,
                "ali_soma": ali, "vit_soma": vit, "peligro_externo": 0.0, "extra": [0.0] * 5,
                "comando": "ACC_MOVER", "sistema_ganador": "S1"}

    assert seg.paso(s(1, 0.2))["abre"] is None
    assert seg.paso(s(2, 0.9))["abre"] is not None
    assert seg.paso(s(3, 0.9, vit=97.0))["cierra"] is None
    ep = seg.paso(s(4, 0.1, vit=97.0))["cierra"]  # calma: cierra
    assert ep["cierre"] == "calma" and ep["balance"] == pytest.approx(-3.0) and ep["signo"] == -1
    seg.paso(s(5, 0.9))
    for n in range(6, 11):
        ep = seg.paso(s(n, 0.9))["cierra"]
    assert ep is not None and ep["cierre"] == "longitud" and ep["longitud"] == 6

