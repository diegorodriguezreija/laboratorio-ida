import pytest
import numpy as np
from nivel_1_core.vocabulario import V_Comando, V_Estado, V_Relacion
from nivel_1_core.contratos import Arquetipo, Pieza
from nivel_1_core.estado_somatico import EstadoSomatico
from nivel_1_core.tribunal_motor import TribunalMotor
from nivel_1_core.cosechador_termodinamico import CosechadorTermodinamico
from nivel_2_sistemas.plasticidad_td_hebbiana import MatrizHebbianaTresFactores


def test_chasis_somatico_localizado_y_ponderacion():
    soma = EstadoSomatico()
    assert soma.vitalidad == 100.0
    assert soma.factor_coste_cinetico() == 1.0
    assert soma.probabilidad_ruido_sensorial() == 0.0

    # Deterioro de locomocion al 50% duplica coste cinetico
    soma.integridad["locomocion"] = 50.0
    assert soma.factor_coste_cinetico() == 2.0
    # Vitalidad: 40 + 10 + 20 + 20 = 90
    assert soma.vitalidad == 90.0

    # Deterioro de sensores por debajo de 80 inyecta probabilidad de ruido
    soma.integridad["sensores"] = 40.0
    assert soma.probabilidad_ruido_sensorial() == 0.50

    # Sanacion tisular en vigilia calma (ali >= 65 y des >= 65: +1.5)
    soma.alimentacion = 80.0
    soma.descanso = 80.0
    soma.aplicar_metabolismo_latido(ciclo_actual=1)
    assert soma.integridad["locomocion"] == 51.5
    assert soma.integridad["sensores"] == 41.5


def test_disociacion_berridge_schultz_dopamina_opioides():
    soma = EstadoSomatico()
    cosechador = CosechadorTermodinamico()
    tribunal = TribunalMotor(cosechador)

    # Nivel basal de dopamina: 35.0
    assert soma.dopamina == 35.0
    umbral_base = tribunal.calcular_umbral_acecho(soma)

    # RPE positivo (delta = +20) eleva dopamina y abre Via Directa D1 (reduce umbral de acecho)
    soma.actualizar_dopamina_rpe(20.0)
    assert soma.dopamina > 35.0
    umbral_d1 = tribunal.calcular_umbral_acecho(soma)
    assert umbral_d1 < umbral_base

    # RPE negativo deprime dopamina y activa Via Indirecta D2 (eleva umbral de acecho)
    soma.actualizar_dopamina_rpe(-40.0)
    umbral_d2 = tribunal.calcular_umbral_acecho(soma)
    assert umbral_d2 > umbral_d1

    # Opioides (Liking / Saciedad): cuando placer >= 60 purga cortisol
    soma.cortisol = 0.85
    soma.inyectar_placer_opioide(65.0)
    assert soma.placer >= 60.0
    assert soma.cortisol <= 0.40  # Cortisol purgado


def test_aprendizaje_hebbiano_3_factores_en_tensor_6d():
    hebb = MatrizHebbianaTresFactores(tasa_aprendizaje=0.10)
    # Tensor representativo con alta nocicepcion (x5)
    tensor_nocivo = np.array([1.0, 0.4, 0.5, 0.6, 0.1, 0.95], dtype=np.float64)

    scores_prev = hebb.evaluar_tensor_6d(tensor_nocivo)
    # Tras intoxicacion visceral aguda (delta_dopamina_rpe = -35.0 sobre canal 1 letal)
    # la regla refuerza la columna de letalidad
    w1_prev = float(hebb.W[5, 1])
    hebb.actualizar_hebbiano_3_factores(tensor_nocivo, canal_post_idx=1, delta_dopamina_rpe=35.0)
    assert hebb.W[5, 1] > w1_prev


def test_mapa_cognitivo_alocentrico_hipocampal():
    from nivel_1_core.persistencia.memoria_tridimensional import DimensionActiva

    activa = DimensionActiva(id_linaje="Test_Linaje")

    # 1. Registro de hito estacionario (ej. estación de trabajo fija, permanencia 1.0)
    activa.registrar_hito_alocentrico(
        ubicacion="nodo_25_30",
        categoria="estacion_trabajo",
        tipo_entidad="mesa",
        ciclo=10,
        permanencia=1.0,
        propiedades={"x": 25, "y": 30},
    )

    # 2. Registro de hito semi-permanente (ej. charca de agua, permanencia 0.8)
    activa.registrar_hito_alocentrico(
        ubicacion="nodo_10_10",
        categoria="fuente_recurso",
        tipo_entidad="agua",
        ciclo=10,
        permanencia=0.8,
        propiedades={"x": 10, "y": 10},
    )

    # Consulta por tipo y categoría
    mesas = activa.consultar_hitos_alocentricos(categoria="estacion_trabajo", tipo_entidad="mesa")
    assert len(mesas) == 1
    assert mesas[0]["ubicacion"] == "nodo_25_30"
    assert mesas[0]["propiedades"]["x"] == 25

    aguas = activa.consultar_hitos_alocentricos(categoria="fuente_recurso")
    assert len(aguas) == 1
    assert aguas[0]["tipo_entidad"] == "agua"

    # 3. Decaimiento temporal pasivo: la mesa (permanencia=1.0) no decae; el agua sí
    activa.aplicar_decaimiento_alocentrico(ciclo_actual=600, tasa_decaimiento_por_ciclo=0.001)
    mesas_post = activa.consultar_hitos_alocentricos(categoria="estacion_trabajo")
    assert len(mesas_post) == 1
    assert mesas_post[0]["permanencia"] == 1.0

    # 4. Falsación / remoción de hito
    activa.remover_hito_alocentrico("nodo_25_30")
    assert len(activa.consultar_hitos_alocentricos(categoria="estacion_trabajo")) == 0


def test_plasticidad_td_lambda_y_telemetria_arbitraje_tribunal():
    from nivel_1_core.contratos import Onda, IActuadorEntorno, ResultadoEfectoEntorno
    from nivel_2_sistemas.s1_reactivo import crear_sistema_s1
    from nivel_2_sistemas.plasticidad_td_hebbiana import MatrizHebbianaTresFactores

    s1 = crear_sistema_s1(MatrizHebbianaTresFactores())
    comp_imp = s1.estaciones["REACCIONAR"][0]
    peso_inicial = comp_imp.peso_sinaptico

    # Refuerzo positivo en MotorTDLambda incrementa peso sinaptico del componente activado
    delta_td = s1.actualizar_plasticidad_td(recompensa=0.80, ids_activados={comp_imp.id_componente})
    assert delta_td > 0.0
    assert comp_imp.peso_sinaptico > peso_inicial

    # Verificar telemetria de arbitraje por capa en TribunalMotor
    class ActuadorDummy(IActuadorEntorno):
        def ejecutar_comando_fisico(self, comando, target, factor_fauces=1.0, payload_extra=None):
            return ResultadoEfectoEntorno(exito=True, comando=comando, target=target)

    soma = EstadoSomatico()
    soma.cortisol = 0.05  # En calma domina el Trust de S3 frente al Arousal bruto de S1
    tribunal = TribunalMotor(CosechadorTermodinamico())
    onda = Onda(ciclo=1)

    p_s1 = Pieza(
        "Imp_S1", "Impulso", arousal=0.92, trust=0.45,
        product={"comando": V_Comando.MOVER, "target": "Norte", "origen_sistema": "S1", "id_componente": "Comp_S1"},
        sistemas_participantes={"S1"},
    )
    p_s3 = Pieza(
        "Imp_S3", "Impulso", arousal=0.75, trust=0.98,
        product={"comando": V_Comando.MOVER, "target": "Sur", "origen_sistema": "S3", "id_componente": "Comp_S3"},
        sistemas_participantes={"S3"},
    )
    onda.reactiva.converger_impulso_acc("Impulso", p_s1, onda, coste_amplitud=0)
    onda.reactiva.converger_impulso_acc("Impulso", p_s3, onda, coste_amplitud=0)

    tribunal.arbitrar_y_ejecutar(onda, soma, ActuadorDummy())
    assert onda.metricas["sistema_ganador"] == "S3"
    assert onda.metricas["tribunal_altero_arousal_puro"] is True
    assert onda.metricas["impulsos_por_sistema"] == {"S1": 1, "S2": 0, "S3": 1}


def test_ablacion_td_lambda_alpha_cero_determinista():
    """
    Verifica que con tasa_aprendizaje alpha = 0.0 en MotorTDLambda, los pesos sinapticos
    permanecen invariantes y el arbitraje del TribunalMotor reproduce identicamente la referencia.
    """
    from nivel_1_core.contratos import Onda, IActuadorEntorno, ResultadoEfectoEntorno
    from nivel_2_sistemas.s1_reactivo import crear_sistema_s1
    from nivel_2_sistemas.plasticidad_td_hebbiana import MatrizHebbianaTresFactores, MotorTDLambda

    class ActuadorDummy(IActuadorEntorno):
        def ejecutar_comando_fisico(self, comando, target, factor_fauces=1.0, payload_extra=None):
            return ResultadoEfectoEntorno(exito=True, comando=comando, target=target)

    s1_alpha0 = crear_sistema_s1(MatrizHebbianaTresFactores())
    s1_alpha0.motor_td = MotorTDLambda(alpha=0.0, gamma=0.92, lam=0.80)
    comp = s1_alpha0.estaciones["REACCIONAR"][0]
    peso_ref = comp.peso_sinaptico

    for r in (0.9, -0.8, 0.5, 1.0):
        s1_alpha0.actualizar_plasticidad_td(recompensa=r, ids_activados={comp.id_componente})
        assert comp.peso_sinaptico == peso_ref

    # Con la misma semilla y alpha=0, la secuencia de decisiones del Tribunal es 100% identica a la referencia
    acciones_ref = []
    acciones_alpha0 = []
    for modo in ("ref", "alpha0"):
        soma = EstadoSomatico()
        soma.cortisol = 0.25
        tribunal = TribunalMotor(CosechadorTermodinamico())
        for ciclo in range(1, 6):
            onda = Onda(ciclo=ciclo)
            p1 = Pieza(
                "i1", "Impulso", arousal=0.80, trust=0.70,
                product={"comando": V_Comando.MOVER, "target": "Nodo_A", "peso_sinaptico": peso_ref if modo == "ref" else comp.peso_sinaptico},
            )
            p2 = Pieza(
                "i2", "Impulso", arousal=0.75, trust=0.85,
                product={"comando": V_Comando.MOVER, "target": "Nodo_B", "peso_sinaptico": 1.0},
            )
            onda.reactiva.converger_impulso_acc("Impulso", p1, onda, coste_amplitud=0)
            onda.reactiva.converger_impulso_acc("Impulso", p2, onda, coste_amplitud=0)
            ejec, _ = tribunal.arbitrar_y_ejecutar(onda, soma, ActuadorDummy())
            (acciones_ref if modo == "ref" else acciones_alpha0).append(ejec.product["target"])

    assert acciones_alpha0 == acciones_ref


def test_calculo_crafter_score_canonico():
    """
    Fija mediante test el calculo del Crafter Score (Hafner, 2021) con una unica funcion:
    1. Sobre la matriz historica de 12 episodios: 3.797546% (sum_ln = 34.498299).
    2. Sobre la tabla de 50 generaciones publicada (11 logros): 3.751049% (sum_ln = 34.284039).
    3. Sobre el archivo linaje_evolutivo_crafter.json activo en disco.
    """
    import json
    import pathlib
    from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import (
        calcular_crafter_score_desde_tasas,
        calcular_crafter_score_poblacional,
    )

    historial_12g_canonico = [
        {"logros": ["collect_wood", "make_wood_pickaxe", "collect_sapling", "eat_cow", "defeat_zombie", "defeat_skeleton", "place_table", "collect_drink"]},
        {"logros": ["collect_wood", "collect_sapling", "defeat_zombie", "collect_drink"]},
        {"logros": ["place_table", "collect_wood", "collect_drink"]},
        {"logros": ["eat_cow", "defeat_zombie", "collect_drink"]},
        {"logros": ["defeat_zombie"]},
        {"logros": ["eat_cow", "defeat_zombie", "collect_drink"]},
        {"logros": ["eat_cow", "defeat_zombie", "collect_drink", "defeat_skeleton"]},
        {"logros": []},
        {"logros": ["collect_stone", "collect_wood", "make_wood_pickaxe", "eat_cow", "defeat_zombie", "defeat_skeleton", "place_table", "make_wood_sword"]},
        {"logros": ["defeat_skeleton"]},
        {"logros": ["defeat_zombie", "collect_drink"]},
        {"logros": ["collect_wood", "collect_sapling", "make_wood_pickaxe", "place_table", "make_wood_sword"]},
    ]
    res_12g = calcular_crafter_score_poblacional(historial_12g_canonico)
    assert res_12g["num_episodios"] == 12
    assert len(res_12g["logros_desbloqueados"]) == 10
    assert abs(res_12g["sum_ln"] - 34.498299) < 1e-5
    assert abs(res_12g["crafter_score"] - 3.797546) < 1e-5

    tasas_50g = {
        "collect_wood": 84.0,
        "defeat_zombie": 72.0,
        "eat_cow": 72.0,
        "collect_drink": 66.0,
        "place_table": 38.0,
        "make_wood_pickaxe": 32.0,
        "collect_sapling": 20.0,
        "defeat_skeleton": 8.0,
        "make_wood_sword": 6.0,
        "collect_stone": 4.0,
        "place_plant": 2.0,
    }
    score_50g, sum_ln_50g = calcular_crafter_score_desde_tasas(tasas_50g)
    assert abs(sum_ln_50g - 34.284039) < 1e-5
    assert abs(score_50g - 3.751049) < 1e-5

    # Fixture versionado (copia del linaje de ejemplo); los runners ya no escriben en el árbol.
    ruta_json = pathlib.Path(__file__).resolve().parent / "fixtures" / "linaje_evolutivo_crafter.json"
    assert ruta_json.exists(), f"Falta el fixture {ruta_json}"
    if ruta_json.exists():
        data = json.loads(ruta_json.read_text(encoding="utf-8"))
        res_actual = calcular_crafter_score_poblacional(data["historial_generaciones"])
        assert res_actual["num_episodios"] >= 1
        assert res_actual["crafter_score"] >= 3.75


def test_snake_s3_flood_fill_cuerpo_y_veto_area():
    """
    Verifica que CompEstrategiaSnakeS3 incluye todos los segmentos de cuerpo_coords[:-1]
    en el Flood Fill y veta el impulso de S1 cuando apunta a un bolsillo cerrado por el propio
    cuerpo con area_libre < longitud_serpiente (incluso teniendo salidas_futuras > 0 en el paso 1).
    """
    import asyncio
    from nivel_1_core.contratos import Onda
    from nivel_3_componentes.mundos.mundo_arcade_snake.componentes_snake import CompEstrategiaSnakeS3

    comp_s3 = CompEstrategiaSnakeS3()
    onda = Onda(ciclo=50, ubicacion_actual="nodo_5_5")

    # Construir un bolsillo cerrado hacia el ESTE (6,5) rodeado por el propio cuerpo de longitud 14
    # En (6,5) hay 3 casillas libres internas: (6,5), (7,5), (6,6), por lo que en el paso 1 tiene
    # 2 salidas inmediatas ((7,5) y (6,6)), pero el area total alcanzable es 3 < longitud_serpiente (14).
    bolsillo_muro = [
        (5, 5),  # cabeza
        (5, 4), (6, 4), (7, 4), (8, 4),
        (8, 5), (8, 6), (7, 6),
        (6, 7), (5, 7), (5, 6),
        (4, 6), (4, 7), (4, 8),  # cola
    ]
    p_prop = Pieza(
        "Propiocepcion_nodo_5_5", "Propiocepcion", 0.2, 1.0,
        product={
            "ubicacion": "nodo_5_5",
            "nodos_adyacentes": ["nodo_6_5", "nodo_4_5"],  # (6,5) bolsillo cerrado (area=3), (4,5) mar abierto
        },
    )
    # Alimento trampa dentro del bolsillo en (7,5) que atrae a S1
    p_alim = Pieza(
        "alimento_7_5", "Alimento", 0.9, 0.98,
        product={"x": 7, "y": 5, "target_nodo": "nodo_7_5", "relacion": V_Relacion.ES_NUTRITIVO},
    )
    p_est = Pieza(
        "estado_juego_snake", "Estado_Entorno", 0.3, 0.99,
        product={
            "estado_web": "playing",
            "score": 110,
            "longitud_serpiente": len(bolsillo_muro),
            "cuerpo_coords": bolsillo_muro,
        },
    )
    onda.reactiva.ev.setdefault("Propiocepcion", {})[p_prop.id] = p_prop
    onda.reactiva.ev.setdefault("Escena", {})[p_alim.id] = p_alim
    onda.reactiva.ev.setdefault("Escena", {})[p_est.id] = p_est

    # S1 emite impulso ciego hacia el alimento en nodo_6_5 (dentro del bolsillo de area 3)
    p_imp_s1 = Pieza(
        "Imp_S1_nodo_6_5", "Impulso", arousal=0.78, trust=0.82,
        product={"comando": V_Comando.MOVER, "target": "nodo_6_5", "origen_sistema": "S1"},
        sistemas_participantes={"S1"},
    )
    onda.reactiva.converger_impulso_acc("Impulso", p_imp_s1, onda, coste_amplitud=0)

    asyncio.run(comp_s3.procesar_reactiva(onda, {"activa": None, "arquetipo": None}))

    # S3 debe haber vetado a S1 (arousal=0.05, veto_s3_antienredo=True) y elegido nodo_4_5 (area abierta)
    assert p_imp_s1.product.get("veto_s3_antienredo") is True
    assert p_imp_s1.arousal == 0.05
    imp_s3 = onda.reactiva.acc["Impulso"].get("Imp_S3_Estrategico_nodo_4_5")
    assert imp_s3 is not None
    assert imp_s3.product["target"] == "nodo_4_5"
    assert imp_s3.product["area_asegurada"] >= len(bolsillo_muro)


def test_mundo_acompanante_humano_e2e():
    """
    Verifica la ejecucion E2E del mundo sintetico Acompanante Humano sobre el mismo
    GestorOndaCore agnostico, neutralizando la rumiacion toxica y manteniendo vitalidad
    e integracion de onda.
    """
    import asyncio
    from nivel_1_core.contratos import Arquetipo
    from nivel_1_core.gestor_onda import GestorOndaCore
    from nivel_2_sistemas.plasticidad_td_hebbiana import MatrizHebbianaTresFactores
    from nivel_2_sistemas.s1_reactivo import crear_sistema_s1
    from nivel_2_sistemas.s2_limbico import crear_sistema_s2
    from nivel_2_sistemas.s3_racional import crear_sistema_s3
    from nivel_2_sistemas.consciencia_talamo_dmn import BucleTalamocortical, RedNeuronalPorDefecto
    from nivel_2_sistemas.ciclo_sueno_rem import GestorCicloSuenoREM
    from nivel_2_sistemas.autopoiesis_ast import CirujanoAST
    from nivel_3_componentes.mundos.mundo_acompanante_humano.adaptador_acompanante import AdaptadorAcompananteHumano

    async def _run_mundo(adaptador, nombre_arq):
        core = GestorOndaCore(
            sensor=adaptador,
            actuador=adaptador,
            arquetipo=Arquetipo(nombre=nombre_arq),
            sistemas_cognitivos=[
                crear_sistema_s1(MatrizHebbianaTresFactores()),
                crear_sistema_s2(),
                crear_sistema_s3(),
            ],
            bucle_talamocortical=BucleTalamocortical(),
            dmn=RedNeuronalPorDefecto(),
            gestor_sueno_rem=GestorCicloSuenoREM(),
            cirujano_ast=CirujanoAST(),
            frecuencia_max_ms=150.0,
            amplitud_max=150,
        )
        for _ in range(4):
            await core.ejecutar_latido()
        return core

    adaptador_acomp = AdaptadorAcompananteHumano()
    core_acomp = asyncio.run(_run_mundo(adaptador_acomp, "IdA_Empatia"))
    assert core_acomp.soma.vitalidad == 100.0
    assert adaptador_acomp.limites_eticos_establecidos >= 1


def test_experimento_heredabilidad_y_determinismo_crafter():
    """
    Verifica los resultados del experimento cientifico de determinismo (reproducibilidad en semilla)
    y heredabilidad en N=20 semillas no vistas (desplazamiento de la distribucion por seleccion y herencia).
    """
    import os
    import json

    ruta_json = os.path.join(
        os.path.dirname(__file__),
        "..",
        "archivo-v14",
        "resultados_historicos",
        "herencia_crafter",
        "experimento_heredabilidad_crafter.json",
    )
    assert os.path.exists(ruta_json), f"El archivo {ruta_json} debe existir."

    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Verificacion de determinismo estructural en la semilla record
    det = data["determinismo_misma_semilla"]
    assert det["es_100_por_100_determinista"] is True
    assert det["trayectoria_paso_a_paso_identica"] is True
    rep1 = det["replica_1"]
    rep2 = det["replica_2"]
    assert rep1["latidos"] == rep2["latidos"]
    assert rep1["fitness"]["global"] == rep2["fitness"]["global"]
    assert rep1["total_logros"] == rep2["total_logros"]

    # 2. Verificacion de ablacion en la misma semilla frente a linaje vacio
    control = det["control_linaje_vacio_misma_semilla"]
    assert rep1["total_logros"] > control["total_logros"]
    assert rep1["latidos"] > control["latidos"]

    # 3. Verificacion de heredabilidad en N=20 semillas nuevas
    hered = data["heredabilidad_20_semillas_nuevas"]
    assert hered["num_semillas"] == 20
    con_linaje = hered["con_linaje_record"]
    sin_linaje = hered["sin_linaje_vacio"]
    dif = hered["diferencial_pareado"]

    # Crafter Score poblacional con linaje superior al linaje vacio
    assert con_linaje["crafter_score_poblacional"] > sin_linaje["crafter_score_poblacional"]
    assert dif["delta_crafter_score_pct"] > 5.0
    assert dif["ratio_crafter_score"] >= 2.0

    # Media de logros por episodio superior con linaje
    assert con_linaje["logros_media"] > sin_linaje["logros_media"]
    assert dif["delta_logros_medio"] > 2.0

    # Dominancia en semillas pareadas
    assert con_linaje["fitness_media"] > sin_linaje["fitness_media"]


def test_estudio_factorial_heredabilidad_crafter():
    """
    Verifica los resultados del diseño factorial 2x2 + controles (N=20 semillas nuevas 2000..2019):
    1. El efecto principal procede del arquetipo (beta_1 significativo, p < 0.001).
    2. La memoria epigenetica (axiomas) aislada no tiene efecto significativo (beta_2 p > 0.10).
    3. C1 vs C4 muestra superioridad estadistica en Wilcoxon y test de signos.
    4. C3 vs C4 no muestra diferencia estadistica significativa.
    """
    import os
    import json
    ruta_json = os.path.join(
        os.path.dirname(__file__),
        "..",
        "archivo-v14",
        "resultados_historicos",
        "herencia_crafter",
        "experimento_factorial_heredabilidad_crafter.json",
    )
    assert os.path.exists(ruta_json), f"El archivo {ruta_json} debe existir."

    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    conds = data["condiciones"]
    comp = data["comparativas_contra_control_vacio"]
    factorial = data["analisis_factorial_2x2"]

    # Crafter Score de Arquetipo Seleccionado (C1, C2) ~19.6 - 19.8%
    assert conds["C1_Record_Completo"]["crafter_score_poblacional"] > 19.0
    assert conds["C2_Solo_Arquetipo"]["crafter_score_poblacional"] > 19.0

    # Crafter Score de Fundador (C3, C4) ~6.1 - 6.7%
    assert conds["C4_Control_Vacio"]["crafter_score_poblacional"] < 7.0
    assert conds["C3_Solo_Axiomas"]["crafter_score_poblacional"] < 7.0

    # C1 vs C4 significativo
    assert comp["C1_Record_Completo"]["wilcoxon_p_value"] < 0.001
    assert comp["C1_Record_Completo"]["sign_test"]["victorias"] >= 18

    # C3 vs C4 NO significativo (axiomas sin arquetipo no bastan)
    assert comp["C3_Solo_Axiomas"]["wilcoxon_p_value"] > 0.10

    # Descomposicion Factorial MCO
    beta_arq = factorial["efecto_principal_arquetipo"]["beta"]
    p_arq = factorial["efecto_principal_arquetipo"]["p_value"]
    beta_ax = factorial["efecto_principal_axiomas"]["beta"]
    p_ax = factorial["efecto_principal_axiomas"]["p_value"]

    assert beta_arq >= 4.0
    assert p_arq < 0.001
    assert p_ax > 0.10









def test_crafter_score_episodio_usa_la_funcion_canonica():
    """
    N4: una sola función de Crafter Score. El score de un episodio se obtiene con la función
    canónica y coincide con la fórmula cerrada exp((k/22) ln 101) - 1 que usaba el código anterior.
    """
    import math
    from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import (
        ACHIEVEMENTS_22,
        calcular_crafter_score_episodio,
        calcular_crafter_score_desde_tasas,
    )

    for k in range(len(ACHIEVEMENTS_22) + 1):
        logros = ACHIEVEMENTS_22[:k]
        esperado = math.exp((k / 22) * math.log(101.0)) - 1.0
        assert abs(calcular_crafter_score_episodio(logros) - esperado) < 1e-9
        tasas = {a: (100.0 if a in logros else 0.0) for a in ACHIEVEMENTS_22}
        assert abs(calcular_crafter_score_desde_tasas(tasas)[0] - esperado) < 1e-9


def test_manipulacion_h2_fija_el_cortisol_aunque_el_core_lo_reescriba():
    """R1: con fijar_cortisol, las escrituras del core no alteran el valor que verá el Tribunal."""
    import pytest

    pytest.importorskip("crafter")
    from nivel_1_core.estado_somatico import EstadoSomatico
    from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import fijar_cortisol

    soma = EstadoSomatico()
    fijar_cortisol(soma, 0.90)
    soma.cortisol = 0.05
    soma.cortisol = float(max(0.05, soma.cortisol * 0.45))
    assert soma.cortisol == 0.90
    assert isinstance(soma, EstadoSomatico)
