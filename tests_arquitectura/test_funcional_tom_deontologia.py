import asyncio
import pytest
from nivel_1_core.vocabulario import V_Comando, V_Dominio, V_Modalidad, V_Relacion, V_Estado
from nivel_1_core.contratos import Pieza, Onda
from nivel_1_core.estado_somatico import EstadoSomatico
from nivel_1_core.persistencia.memoria_tridimensional import DimensionActiva, DimensionProactiva
from nivel_2_sistemas.s2_limbico import CompGenerarEmocionS2
from nivel_3_componentes.organos_universales_s3.comp_deontologia import CompDeontologiaS3
from nivel_3_componentes.organos_universales_s3.comp_teoria_mente import CompTeoriaMenteS3


def test_veto_deontologico_y_quiebre_por_inanicion():
    deont = CompDeontologiaS3(tabues_iniciales=["recurso_sagrado"])
    soma = EstadoSomatico()
    activa = DimensionActiva()
    proactiva = DimensionProactiva()
    ctx = {"soma": soma, "activa": activa, "proactiva": proactiva}

    # 1. En calma (alimentacion > 15): Veto Moral estricto
    soma.alimentacion = 80.0
    onda1 = Onda(ciclo=1)
    p_imp1 = Pieza(
        id="imp_1",
        tipo_componente="Impulso",
        arousal=0.85,
        trust=0.90,
        product={"comando": V_Comando.DEGLUTIR, "target": "recurso_sagrado"},
    )
    onda1.reactiva.converger_impulso_acc("Impulso", p_imp1, onda1, coste_amplitud=0)

    asyncio.run(deont.procesar_reactiva(onda1, ctx))
    assert p_imp1.arousal == 0.0
    assert p_imp1.trust == 0.0
    assert p_imp1.product["veto_moral"] is True

    # 2. En inanicion critica (alimentacion <= 15): Quiebre por supervivencia
    soma.alimentacion = 10.0
    onda2 = Onda(ciclo=2)
    p_imp2 = Pieza(
        id="imp_2",
        tipo_componente="Impulso",
        arousal=0.95,
        trust=0.90,
        product={"comando": V_Comando.DEGLUTIR, "target": "recurso_sagrado"},
    )
    onda2.reactiva.converger_impulso_acc("Impulso", p_imp2, onda2, coste_amplitud=0)

    asyncio.run(deont.procesar_reactiva(onda2, ctx))
    # No se veta: el organismo lucha por no morir
    assert p_imp2.arousal == 0.95
    # Pero se consolida la transgresion moral en Memoria Activa
    trans = activa.obtener_pieza("IdA", "Transgresion_DEONTICO")
    assert trans is not None

    # 3. Al latido siguiente, S2 detecta la transgresion y desata CULPA
    comp_emo = CompGenerarEmocionS2()
    onda3 = Onda(ciclo=3)
    asyncio.run(comp_emo.procesar_reactiva(onda3, ctx))
    assert soma.estado_afectivo == V_Estado.CULPA
    assert soma.cortisol == 0.88


def test_teoria_de_la_mente_y_psicopatia_tactica():
    tom = CompTeoriaMenteS3()
    soma = EstadoSomatico()
    activa = DimensionActiva()
    proactiva = DimensionProactiva()
    ctx = {"soma": soma, "activa": activa, "proactiva": proactiva}

    # Sembrar en memoria activa que 'Abismo_Toxico' es ES_LETAL
    p_letal = Pieza("Abismo_Toxico", "Proposicion_VERDAD", 0.9, 0.95, product={"relacion": V_Relacion.ES_LETAL})
    activa.consolidar_pieza("Abismo_Toxico", p_letal)

    # El agente externo 'Parasito_X' emite una mentira intencional afirmando que Abismo_Toxico es ES_NUTRITIVO
    onda = Onda(ciclo=5)
    p_sent = Pieza(
        id="sent_parasito",
        tipo_componente="Sentencia",
        arousal=0.75,
        trust=0.70,
        product={
            "agente_emisor": "Parasito_X",
            "sujeto_interno": "Abismo_Toxico",
            "relacion_interna": str(V_Relacion.ES_NUTRITIVO),
        },
    )
    onda.reactiva.registrar_ef_universal("Sentencia", p_sent)
    onda.reactiva.ev.setdefault("Sentencia", {})[p_sent.id] = p_sent

    # Impulso tentativo hacia el cebo
    p_imp = Pieza(
        id="imp_hacia_trampa",
        tipo_componente="Impulso",
        arousal=0.65,
        trust=0.70,
        product={"comando": V_Comando.MOVER, "target": "Abismo_Toxico"},
    )
    onda.reactiva.converger_impulso_acc("Impulso", p_imp, onda, coste_amplitud=0)

    asyncio.run(tom.procesar_reactiva(onda, ctx))

    # ToM detecto el engaño:
    # 1. Parasito marcado como ES_PARASITARIO con Trust minimo
    p_soc = activa.obtener_pieza("Parasito_X", "Predicado_SOCIAL")
    assert p_soc is not None
    assert p_soc.product["relacion"] == V_Relacion.ES_PARASITARIO
    assert p_soc.trust <= 0.05

    # 2. Veto prefrontal sobre el cebo
    assert p_imp.arousal == 0.0
    assert p_imp.product["trampa_parasitaria_evitada"] is True

    # 3. Psicopatia Tactica: Secreto senuelo letal en acc['Expresion']
    assert "Expresion" in onda.reactiva.acc
    senuelos = onda.reactiva.acc["Expresion"]
    assert any(p.product.get("es_senuelo_tactico") for p in senuelos.values())

