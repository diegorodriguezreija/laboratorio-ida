import pytest
from nivel_1_core.vocabulario import V_Comando
from nivel_1_core.contratos import Pieza, Onda, IActuadorEntorno, ResultadoEfectoEntorno
from nivel_1_core.estado_somatico import EstadoSomatico
from nivel_1_core.cosechador_termodinamico import CosechadorTermodinamico
from nivel_1_core.arbitros import (
    ArbitroBase,
    A0_TribunalMotorDefault,
    A1_MayorArousal,
    A2_PrioridadFijaS1,
    A3_PrioridadFijaS3,
    A4_AleatorioPonderado,
    A5_SoloS1,
    A6_SoloS3,
    A7_MayorProducto,
    crear_arbitro,
)
from nivel_1_core.tribunal_motor import TribunalMotor


class MockActuador(IActuadorEntorno):
    def __init__(self):
        self.ultimas_acciones = []

    def ejecutar_comando_fisico(
        self, comando: V_Comando, target: str, factor_fauces: float = 1.0, payload_extra: dict = None
    ) -> ResultadoEfectoEntorno:
        self.ultimas_acciones.append((comando, target))
        return ResultadoEfectoEntorno(
            exito=True,
            comando=comando,
            target=target,
            delta_alimentacion=5.0,
            delta_energia=-1.0,
        )


def _crear_impulso(id_p: str, origen: str, arousal: float, trust: float, cmd: V_Comando) -> Pieza:
    return Pieza(
        id=id_p,
        tipo_componente="Impulso",
        arousal=arousal,
        trust=trust,
        product={"comando": cmd, "target": "pos_test", "origen_sistema": origen},
        sistemas_participantes=[origen],
    )


def test_reglas_seleccion_arbitros():
    soma = EstadoSomatico()
    soma.cortisol = 0.20  # Bajo estrés -> domina el trust en A0

    p_s1 = _crear_impulso("Imp_S1", "S1", arousal=0.90, trust=0.30, cmd=V_Comando.ATACAR)
    p_s2 = _crear_impulso("Imp_S2", "S2", arousal=0.60, trust=0.70, cmd=V_Comando.ACECHAR)
    p_s3 = _crear_impulso("Imp_S3", "S3", arousal=0.40, trust=0.95, cmd=V_Comando.COGER)

    impulsos = {"S1": p_s1, "S2": p_s2, "S3": p_s3}

    # A1: Mayor Arousal -> debe ganar p_s1 (0.90)
    a1 = A1_MayorArousal()
    ganador_a1, _ = a1.seleccionar(impulsos, soma)
    assert ganador_a1.id == "Imp_S1"

    # A2: Prioridad Fija S1 -> debe ganar p_s1
    a2 = A2_PrioridadFijaS1()
    ganador_a2, _ = a2.seleccionar(impulsos, soma)
    assert ganador_a2.id == "Imp_S1"

    # A3: Prioridad Fija S3 -> debe ganar p_s3
    a3 = A3_PrioridadFijaS3()
    ganador_a3, _ = a3.seleccionar(impulsos, soma)
    assert ganador_a3.id == "Imp_S3"

    # A5: Solo S1 -> debe ganar p_s1
    a5 = A5_SoloS1()
    ganador_a5, _ = a5.seleccionar(impulsos, soma)
    assert ganador_a5.id == "Imp_S1"

    # A6: Solo S3 -> debe ganar p_s3
    a6 = A6_SoloS3()
    ganador_a6, _ = a6.seleccionar(impulsos, soma)
    assert ganador_a6.id == "Imp_S3"

    # A7: Mayor Producto -> p_s1=0.27, p_s2=0.42, p_s3=0.38 -> gana p_s2 (0.42)
    a7 = A7_MayorProducto()
    ganador_a7, _ = a7.seleccionar(impulsos, soma)
    assert ganador_a7.id == "Imp_S2"


def test_aislamiento_contrafactual_y_determinismo():
    """
    Verifica que la activación del registro contrafactual no modifica en absoluto
    la decisión física efectiva tomada por el Tribunal ni el estado del Cosechador.
    """
    p_s1 = _crear_impulso("Imp_S1", "S1", arousal=0.85, trust=0.40, cmd=V_Comando.MOVER)
    p_s3 = _crear_impulso("Imp_S3", "S3", arousal=0.50, trust=0.90, cmd=V_Comando.COGER)

    # 1. Ejecución SIN contrafactual
    cosechador1 = CosechadorTermodinamico()
    cosechador1.amplitud_basal = 0.0
    cosechador1.cosechar_unidad_uniforme = lambda: 0.5
    tribunal_sin_cf = TribunalMotor(cosechador1, registrar_contrafactual=False)
    actuador1 = MockActuador()
    soma1 = EstadoSomatico()
    onda1 = Onda(ciclo=1, amplitud_max=100)
    onda1.reactiva.converger_impulso_acc("Impulso", p_s1, onda1)
    onda1.reactiva.converger_impulso_acc("Impulso", p_s3, onda1)

    pieza_sin, res_sin = tribunal_sin_cf.arbitrar_y_ejecutar(onda1, soma1, actuador1)

    # 2. Ejecución CON contrafactual
    cosechador2 = CosechadorTermodinamico()
    cosechador2.amplitud_basal = 0.0
    cosechador2.cosechar_unidad_uniforme = lambda: 0.5
    tribunal_con_cf = TribunalMotor(cosechador2, registrar_contrafactual=True)
    actuador2 = MockActuador()
    soma2 = EstadoSomatico()
    onda2 = Onda(ciclo=1, amplitud_max=100)
    onda2.reactiva.converger_impulso_acc("Impulso", p_s1, onda2)
    onda2.reactiva.converger_impulso_acc("Impulso", p_s3, onda2)

    pieza_con, res_con = tribunal_con_cf.arbitrar_y_ejecutar(onda2, soma2, actuador2)

    # Verificación de identidad estricta
    assert pieza_sin.product["comando"] == pieza_con.product["comando"]
    assert pieza_sin.inputs == pieza_con.inputs
    assert actuador1.ultimas_acciones == actuador2.ultimas_acciones
    assert soma1.alimentacion == soma2.alimentacion

    # Comprobar que el contrafactual registró las 8 opciones
    cf_map = onda2.metricas.get("contrafactual", {})
    assert len(cf_map) == 8
    assert "A0" in cf_map and "A1" in cf_map and "A3" in cf_map


def test_modos_ablacion_nivel_a_vs_nivel_b():
    """
    Verifica que en Nivel a se evalúa el umbral de acecho D1/D2,
    mientras que en Nivel b el árbitro emite la acción directamente sin acecho.
    """
    cosechador = CosechadorTermodinamico()
    cosechador.amplitud_basal = 0.0
    cosechador.cosechar_unidad_uniforme = lambda: 0.5

    # Propuesta con bajo trust (0.20) para activar acecho en Nivel a
    p_baja_confianza = _crear_impulso("Imp_Cautela", "S3", arousal=0.70, trust=0.20, cmd=V_Comando.MOVER)

    # Nivel a: debe interceptar y emitir ACECHAR
    tribunal_a = TribunalMotor(cosechador, arbitro=A1_MayorArousal(), modo_ablacion="nivel_a")
    actuador_a = MockActuador()
    soma_a = EstadoSomatico()
    onda_a = Onda(ciclo=1, amplitud_max=100)
    onda_a.reactiva.converger_impulso_acc("Impulso", p_baja_confianza, onda_a)

    pieza_a, res_a = tribunal_a.arbitrar_y_ejecutar(onda_a, soma_a, actuador_a)
    assert pieza_a.product["comando"] == V_Comando.ACECHAR
    assert len(actuador_a.ultimas_acciones) == 0  # No ejecuta en entorno físico aún

    # Nivel b: debe emitir directamente el comando propuesto (MOVER) al actuador
    tribunal_b = TribunalMotor(cosechador, arbitro=A1_MayorArousal(), modo_ablacion="nivel_b")
    actuador_b = MockActuador()
    soma_b = EstadoSomatico()
    onda_b = Onda(ciclo=1, amplitud_max=100)
    onda_b.reactiva.converger_impulso_acc("Impulso", p_baja_confianza, onda_b)

    pieza_b, res_b = tribunal_b.arbitrar_y_ejecutar(onda_b, soma_b, actuador_b)
    assert pieza_b.product["comando"] == V_Comando.MOVER
    assert len(actuador_b.ultimas_acciones) == 1
    assert actuador_b.ultimas_acciones[0][0] == V_Comando.MOVER


def test_factoria_arbitros_y_excepciones():
    a0 = crear_arbitro("A0")
    assert isinstance(a0, A0_TribunalMotorDefault)
    a4 = crear_arbitro("a4", seed_propia=123)
    assert isinstance(a4, A4_AleatorioPonderado)
    with pytest.raises(ValueError):
        crear_arbitro("INEXISTENTE")


def test_identificar_sistema_origen_exhaustivo():
    from nivel_1_core.arbitros import identificar_sistema_origen

    # 1. Por product["origen_sistema"]
    p1 = Pieza(id="P1", tipo_componente="Impulso", arousal=0.5, trust=0.5, product={"origen_sistema": "S3"})
    assert identificar_sistema_origen(p1) == "S3"

    # 2. Por sistemas_participantes
    p2 = Pieza(id="P2", tipo_componente="Impulso", arousal=0.5, trust=0.5, product={}, sistemas_participantes={"S2"})
    assert identificar_sistema_origen(p2) == "S2"

    # 3. Por id
    p3 = Pieza(id="Impulso_S1_Evasion", tipo_componente="Impulso", arousal=0.5, trust=0.5, product={})
    assert identificar_sistema_origen(p3) == "S1"

    # 4. Fallback por defecto a S1 si no hay indicios
    p4 = Pieza(id="Impulso_Anonimo", tipo_componente="Impulso", arousal=0.5, trust=0.5, product={})
    assert identificar_sistema_origen(p4) == "S1"


def test_peso_sinaptico_rango_dinamico_y_clamping():
    a0 = A0_TribunalMotorDefault()
    soma = EstadoSomatico()
    soma.cortisol = 0.50

    # Peso normal (1.0) -> mod = 0.85 + 0.15 * 1.0 = 1.00
    p_norm = Pieza(id="p1", tipo_componente="Impulso", arousal=0.8, trust=0.8, product={"peso_sinaptico": 1.0})
    _, meta_norm = a0.seleccionar({"p1": p_norm}, soma)
    score_norm = meta_norm["score"]

    # Peso alto (5.0) -> mod = 0.85 + 0.15 * 5.0 = 1.60 -> clamped a 1.25 (+25%)
    p_alto = Pieza(id="p2", tipo_componente="Impulso", arousal=0.8, trust=0.8, product={"peso_sinaptico": 5.0})
    _, meta_alto = a0.seleccionar({"p2": p_alto}, soma)
    score_alto = meta_alto["score"]

    # Peso bajo (0.0) -> mod = 0.85 + 0.0 = 0.85
    p_bajo = Pieza(id="p3", tipo_componente="Impulso", arousal=0.8, trust=0.8, product={"peso_sinaptico": 0.0})
    _, meta_bajo = a0.seleccionar({"p3": p_bajo}, soma)
    score_bajo = meta_bajo["score"]

    # Peso fuertemente deprimido (-2.0) -> mod = 0.85 - 0.30 = 0.55 -> clamped a 0.80 (-20%)
    p_dep = Pieza(id="p4", tipo_componente="Impulso", arousal=0.8, trust=0.8, product={"peso_sinaptico": -2.0})
    _, meta_dep = a0.seleccionar({"p4": p_dep}, soma)
    score_dep = meta_dep["score"]

    assert score_alto == pytest.approx(score_norm * 1.25, abs=1e-4)
    assert score_bajo == pytest.approx(score_norm * 0.85, abs=1e-4)
    assert score_dep == pytest.approx(score_norm * 0.80, abs=1e-4)

