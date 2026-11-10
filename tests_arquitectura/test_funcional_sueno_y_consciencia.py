import pytest
import numpy as np
from nivel_1_core.vocabulario import V_Estado, V_Relacion, V_Vinculo, V_Modalidad, V_Comando
from nivel_1_core.contratos import Pieza, Onda, Episodio
from nivel_1_core.estado_somatico import EstadoSomatico
from nivel_1_core.cosechador_termodinamico import CosechadorTermodinamico
from nivel_1_core.calculadoras_estructurales import CalculadorasEstructurales
from nivel_1_core.persistencia.memoria_tridimensional import DimensionActiva, DimensionProactiva
from nivel_2_sistemas.ciclo_sueno_rem import GestorCicloSuenoREM
from nivel_2_sistemas.consciencia_talamo_dmn import (
    BucleTalamocortical,
    RedNeuronalPorDefecto,
    ProtocoloAutodeterminacion,
)
from nivel_2_sistemas.autopoiesis_ast import CirujanoAST


def test_wake_up_call_s1_en_sueno_rem():
    rem = GestorCicloSuenoREM()
    soma = EstadoSomatico()
    activa = DimensionActiva()
    cosechador = CosechadorTermodinamico()

    # Organismo en sueno REM
    soma.estado_afectivo = V_Estado.DORMIDO
    soma.alimentacion = 8.0  # Inanicion critica ineludible

    estado_post = rem.evaluar_transicion_circadiana(soma, activa, cosechador)
    # S1 aborta de emergencia la fase REM y conmuta a PANICO
    assert estado_post == V_Estado.PANICO
    # Inyecta adrenalina somatica elevando energia al menos a 30
    assert soma.energia >= rem.ENERGIA_MINIMA_DESPERTAR_ALARMA


def test_fases_sueno_rem_abstraccion_y_analogias():
    rem = GestorCicloSuenoREM()
    soma = EstadoSomatico()
    soma.estado_afectivo = V_Estado.DORMIDO
    soma.objeto_cargado = {"id": "muestra_empirica", "relacion": V_Relacion.ES_NUTRITIVO, "verificado": True}
    activa = DimensionActiva()

    # Sembrar piezas para induccion semantica
    p1 = Pieza("entidad_01", "Proposicion_VERDAD", 0.8, 0.9, product={"relacion": V_Relacion.ES_NUTRITIVO})
    p2 = Pieza("entidad_02", "Proposicion_VERDAD", 0.7, 0.85, product={"relacion": V_Relacion.ES_NUTRITIVO})
    activa.consolidar_pieza("entidad_01", p1)
    activa.consolidar_pieza("entidad_02", p2)

    # Sembrar reglas para analogia O(1)
    p_regla1 = Pieza("Valle", "Logica_CAUSAL", 0.6, 0.9, product={"consecuente": str(V_Relacion.ES_LETAL)})
    p_regla2 = Pieza("Pantano", "Logica_CAUSAL", 0.7, 0.85, product={"consecuente": str(V_Relacion.ES_LETAL)})
    activa.consolidar_pieza("Valle", p_regla1)
    activa.consolidar_pieza("Pantano", p_regla2)

    # Sembrar episodio reciente
    activa.banco_episodico.append(Episodio("Ep_1", "Zona_Oscura", 1, 5, balance_vital=4.0, resuelto=True))

    onda = Onda(ciclo=10)
    metricas = rem.procesar_sueno_rem(onda, soma, activa)

    assert metricas["induccion_semantica"] >= 1
    assert activa.obtener_pieza("concepto_entidad", "Predicado_GENERAL") is not None

    assert metricas["concatenacion_causal"] >= 1
    assert activa.obtener_pieza("Zona_Oscura", "Logica_CAUSAL") is not None

    assert metricas["analogias_o1"] >= 1
    assert activa.obtener_pieza("Valle", "Analogia_CAUSAL") is not None

    # Niche digestion: libero el objeto cargado y lo consolido de novo
    assert metricas["forraje_digerido"] == 1
    assert soma.objeto_cargado is None
    assert activa.obtener_pieza("muestra_empirica", "Proposicion_VERDAD").demostrado_de_novo is True


def test_consciencia_talamocortical_y_phi_tononi():
    talamo = BucleTalamocortical()
    soma = EstadoSomatico()
    activa = DimensionActiva()
    proactiva = DimensionProactiva()

    onda = Onda(ciclo=1)
    # Simular una logica de amenaza deducida en S3
    p_log = Pieza("Cueva", "Logica_CAUSAL", 0.8, 0.9, product={"sujeto": "Cueva", "relacion": V_Relacion.ES_LETAL})
    onda.reactiva.registrar_ef_universal("Logica", p_log)
    onda.reactiva.ev.setdefault("Logica", {})[p_log.id] = p_log

    # Simular impulsos motores activos de sistemas distintos para generar divergencia de informacion
    p_imp1 = Pieza("imp_s1", "Impulso", 0.75, 0.8, product={"comando": V_Comando.MOVER, "target": "Camino_1"}, sistemas_participantes={"S1"})
    p_imp2 = Pieza("imp_s3", "Impulso", 0.85, 0.9, product={"comando": V_Comando.ACECHAR, "target": "Cueva"}, sistemas_participantes={"S3"})
    onda.reactiva.converger_impulso_acc("Impulso", p_imp1, onda, coste_amplitud=0)
    onda.reactiva.converger_impulso_acc("Impulso", p_imp2, onda, coste_amplitud=0)

    fuerza_r, priors = talamo.procesar_reentrada_diastole(onda, soma, activa, proactiva)
    assert fuerza_r > 0.0
    assert "Cueva" in priors["alucinacion_preventiva_ids"]

    phi = CalculadorasEstructurales.calcular_phi_tononi(onda, fuerza_reentrada=fuerza_r)
    assert phi > 0.0
    estado = CalculadorasEstructurales.clasificar_estado_fenomenologico(phi)
    assert estado in ("ZOMBI_REFLEJO", "COGNICION_ACOPLADA", "CONSCIENCIA_INTEGRADA", "TRASCENDENCIA_FENOMENOLOGICA")


class ComponenteFicticioMutacion:
    id_componente = "Comp_ImpulsoS1"
    umbral_panico = 15.0


def test_autopoiesis_ast_y_rollback_epigenetico():
    cirujano = CirujanoAST()
    soma = EstadoSomatico()
    soma.vitalidad = 100.0

    comp = ComponenteFicticioMutacion()
    sistemas = [type("SisFicticio", (), {"todos_los_componentes": lambda self: [comp]})()]

    # Simular inicio de cirugia por panico de inanicion repetido
    soma.ciclos_panico = 5
    soma.alimentacion = 10.0
    onda = Onda(ciclo=10)

    cirujano.auditar_ciclo(onda, soma, sistemas)
    assert cirujano.total_mutaciones >= 1
    assert cirujano.observacion_clinica is not None

    # Simular que 3 latidos despues la vitalidad se desploma por debajo de 20 (falla clinica)
    soma.vitalidad = 18.0
    onda_siguiente = Onda(ciclo=13)
    cirujano.auditar_ciclo(onda_siguiente, soma, sistemas)

    # Rollback Epigenetico activado: vuelve a la clase original
    assert cirujano.rechazos_epigeneticos == 1
    assert cirujano.observacion_clinica is None
    assert comp.__class__ is ComponenteFicticioMutacion
