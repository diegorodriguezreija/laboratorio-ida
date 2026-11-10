from typing import Dict, Any
import numpy as np
from nivel_1_core.vocabulario import V_Comando, V_Dominio, V_Modalidad, V_Relacion, V_Estado
from nivel_1_core.contratos import Pieza, Onda
from nivel_2_sistemas.sistema_base import ComponenteCognitivoBase, SistemaCognitivoTriunico


class CompConceptoSujetoS2(ComponenteCognitivoBase):
    """
    Modulo Sentir de S2:
    Abstrae las entidades concretas percibidas en clases ontologicas universales
    (concepto_nutriente, concepto_amenaza, concepto_armonico, concepto_disonante,
     concepto_misterio, concepto_agente) segun la firma de su tensor 6D,
    y tipifica el Sujeto de la oracion mental (incluyendo al propio 'IdA').
    """

    def __init__(self):
        super().__init__("Comp_Concepto", "S2")

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        objetos = onda.reactiva.ev.get("Objeto", {})
        for oid, p_obj in objetos.items():
            t = p_obj.tensor_sensorial if p_obj.tensor_sensorial is not None else np.zeros(6)
            sc_nut = float(p_obj.product.get("score_nutritivo", t[4]))
            sc_let = float(p_obj.product.get("score_letal", t[5]))
            sc_arm = float(p_obj.product.get("score_armonico", 0.0))
            sc_epi = float(p_obj.product.get("score_epistemico", t[3]))

            if p_obj.product.get("emisor") is not None:
                concepto = "concepto_agente"
            elif sc_let >= 0.60:
                concepto = "concepto_amenaza"
            elif sc_epi >= 0.65 and sc_nut >= 0.40:
                concepto = "concepto_misterio"
            elif sc_nut >= 0.55:
                concepto = "concepto_nutriente"
            elif sc_arm >= 0.50:
                concepto = "concepto_armonico"
            else:
                concepto = "concepto_disonante"

            p_conc = Pieza(
                id=oid,
                tipo_componente="Concepto",
                arousal=p_obj.arousal,
                trust=p_obj.trust,
                tensor_sensorial=t,
                product={"concepto": concepto, "sujeto": oid, **p_obj.product},
                inputs=[oid, self.id_componente],
            )
            self.emitir_reactiva(onda, "Concepto", p_conc, proyectar_ev=True, coste_amplitud=1)

            p_suj = Pieza(
                id=oid,
                tipo_componente="Sujeto",
                arousal=p_obj.arousal,
                trust=p_obj.trust,
                tensor_sensorial=t,
                product={"sujeto": oid, "clase_ontologica": concepto},
                inputs=[oid, "Comp_Sujeto"],
            )
            self.emitir_reactiva(onda, "Sujeto", p_suj, proyectar_ev=True, coste_amplitud=0)

        # Autoconciencia basal: Sujeto 'IdA'
        p_yo = Pieza(
            id="IdA",
            tipo_componente="Sujeto",
            arousal=0.3,
            trust=1.0,
            product={"sujeto": "IdA", "clase_ontologica": "concepto_yo"},
            inputs=["Interocepcion", "Comp_Sujeto"],
        )
        self.emitir_reactiva(onda, "Sujeto", p_yo, proyectar_ev=True, coste_amplitud=0)
        return True


class CompPredicadoProposicionS2(ComponenteCognitivoBase):
    """
    Modulo Interpretar de S2:
    1. Comp_Predicado: Asigna propiedades relacionales (V_Relacion) al Sujeto en los dominios VALOR y SOCIAL,
       aplicando el sesgo genetico del Arquetipo (Big Five).
    2. Comp_Proposicion: Une Sujeto + Predicado dotandolo de modalidad epistemica/afectiva
       (SIENTE, CREE, HIPOTESIS, DEMOSTRADO). Si hay conflicto de evidencia o falta de contrastacion
       sobre una entidad ambigua, emite formalmente una Proposicion_DUDA:
       [Especie/Entidad] MODALIDAD: HIPOTESIS => ¿ES_NUTRITIVO v ES_LETAL?
    """

    def __init__(self):
        super().__init__("Comp_Predicado_Proposicion", "S2")

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        arq = ctx["arquetipo"]
        activa = ctx["activa"]
        conceptos = onda.reactiva.ev.get("Concepto", {})

        for cid, p_conc in conceptos.items():
            clase = str(p_conc.product.get("concepto", ""))
            t = p_conc.tensor_sensorial if p_conc.tensor_sensorial is not None else np.zeros(6)

            # Evaluar en dominio VALOR con sesgo Big Five del Arquetipo
            valencia_estetica = (t[4] * arq.apertura) - (t[5] * arq.neuroticismo)
            if valencia_estetica >= 0.25:
                rel_valor = V_Relacion.ES_AGRADABLE if clase != "concepto_armonico" else V_Relacion.ES_ARMONICO
            elif valencia_estetica <= -0.20:
                rel_valor = V_Relacion.ES_TERRORIFICO if t[5] > 0.7 else V_Relacion.ES_REPULSIVO
            else:
                rel_valor = V_Relacion.ES_DISONANTE

            p_pred_val = Pieza(
                id=cid,
                tipo_componente="Predicado_VALOR",
                arousal=p_conc.arousal,
                trust=p_conc.trust,
                product={"sujeto": cid, "dominio": V_Dominio.VALOR, "relacion": rel_valor},
                inputs=[cid, "Comp_Predicado"],
            )
            self.emitir_reactiva(onda, "Predicado_VALOR", p_pred_val, proyectar_ev=True, coste_amplitud=1)

            # Evaluar en dominio SOCIAL si tiene emisor
            emisor = p_conc.product.get("emisor")
            if emisor is not None:
                prev_soc = activa.obtener_pieza(str(emisor), "Predicado_SOCIAL")
                rel_soc = V_Relacion(str(prev_soc.product["relacion"])) if prev_soc else V_Relacion.ES_DESCONOCIDO
                p_pred_soc = Pieza(
                    id=str(emisor),
                    tipo_componente="Predicado_SOCIAL",
                    arousal=p_conc.arousal,
                    trust=prev_soc.trust if prev_soc else 0.50,
                    product={"sujeto": str(emisor), "dominio": V_Dominio.SOCIAL, "relacion": rel_soc},
                    inputs=[cid, "Comp_Predicado"],
                )
                self.emitir_reactiva(onda, "Predicado_SOCIAL", p_pred_soc, proyectar_ev=True, coste_amplitud=0)

            # Construccion de Proposicion o Proposicion_DUDA
            mem_verdad = activa.obtener_pieza(cid, "Proposicion_VERDAD")
            mem_duda = activa.obtener_pieza(cid, "Proposicion_DUDA")
            es_entidad_desconocida = (
                bool(p_conc.product.get("requiere_verificacion_epistemica", False))
                or (clase == "concepto_misterio")
            ) and mem_verdad is None

            if mem_verdad is not None and str(mem_verdad.product.get("modalidad")) in (
                str(V_Modalidad.DEMOSTRADO),
                str(V_Modalidad.DEMOSTRADO_DEDUCTIVO),
            ):
                self.emitir_reactiva(onda, "Proposicion_VERDAD", mem_verdad, proyectar_ev=True, coste_amplitud=0)
            elif es_entidad_desconocida:
                p_duda = Pieza(
                    id=cid,
                    tipo_componente="Proposicion_DUDA",
                    arousal=max(0.65, p_conc.arousal),
                    trust=mem_duda.trust if mem_duda is not None else 0.40,
                    product={
                        "sujeto": cid,
                        "dominio": V_Dominio.VERDAD,
                        "modalidad": V_Modalidad.HIPOTESIS,
                        "duda_alternativas": [str(V_Relacion.ES_NUTRITIVO), str(V_Relacion.ES_LETAL)],
                        "formula": f"[{cid}] MODALIDAD: HIPOTESIS => ¿ES_NUTRITIVO v ES_LETAL?",
                    },
                    inputs=[cid, "Comp_Proposicion"],
                )
                self.emitir_reactiva(onda, "Proposicion_DUDA", p_duda, proyectar_ev=True, coste_amplitud=1)
                activa.consolidar_pieza(cid, p_duda)
            else:
                rel_verdad = V_Relacion.ES_LETAL if clase == "concepto_amenaza" else (
                    V_Relacion.ES_NUTRITIVO if clase == "concepto_nutriente" else rel_valor
                )
                p_prop = Pieza(
                    id=cid,
                    tipo_componente="Proposicion_VALOR",
                    arousal=p_conc.arousal,
                    trust=p_conc.trust,
                    product={
                        "sujeto": cid,
                        "dominio": V_Dominio.VALOR,
                        "modalidad": V_Modalidad.SIENTE,
                        "relacion": rel_valor,
                        "relacion_inferida": rel_verdad,
                    },
                    inputs=[cid, "Comp_Proposicion"],
                )
                self.emitir_reactiva(onda, "Proposicion_VALOR", p_prop, proyectar_ev=True, coste_amplitud=0)

        return True


class CompGenerarEmocionS2(ComponenteCognitivoBase):
    """
    Modulo Interpretar de S2:
    1. Via Rapida Amigdalina (Eco Limbico de LeDoux): si detecta senales de peligro letal en
       ev['Ingestion'] o una 'Transgresion_DEONTICO' en memoria activa, dispara instantaneamente
       V_Estado.MIEDO o V_Estado.CULPA sin esperar a S3.
    2. Conmutacion Serena a Senescencia: si edad_biologica >= 0.88 (y no hay inanicion critica),
       conmuta a V_Estado.SENESCENTE.
    3. Mutacion a Serenidad Trascendental (V_Estado.TRASCENDENTE) ante sacrificio consciente.
    """

    def __init__(self):
        super().__init__("Comp_GenerarEmocion", "S2")

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        soma = ctx["soma"]
        activa = ctx["activa"]

        # Verificar si hay sacrificio consciente en curso
        impulsos = onda.reactiva.acc.get("Impulso", {})
        if any(p.product.get("sacrificio_consciente") for p in impulsos.values()):
            soma.estado_afectivo = V_Estado.TRASCENDENTE
            soma.cortisol = 0.05
            p_emo = Pieza(
                id="Emocion_Actual",
                tipo_componente="Emocion",
                arousal=0.20,
                trust=1.0,
                product={"estado": V_Estado.TRASCENDENTE, "estres": 0.05, "eco_ledoux": False},
                inputs=[self.id_componente],
            )
            self.emitir_reactiva(onda, "Emocion", p_emo, proyectar_ev=True, coste_amplitud=0)
            return True

        # 1. Via Rapida de LeDoux: Transgresion Deontica -> CULPA
        transgresion = activa.obtener_pieza("IdA", "Transgresion_DEONTICO")
        if transgresion is not None and not transgresion.product.get("expiada", False):
            soma.estado_afectivo = V_Estado.CULPA
            soma.cortisol = 0.88
            p_emo = Pieza(
                id="Emocion_Actual",
                tipo_componente="Emocion",
                arousal=0.88,
                trust=0.95,
                product={"estado": V_Estado.CULPA, "estres": 0.88, "eco_ledoux": True},
                inputs=["Transgresion_DEONTICO", self.id_componente],
            )
            self.emitir_reactiva(onda, "Emocion", p_emo, proyectar_ev=True, coste_amplitud=1)
            return True

        # 2. Via Rapida de LeDoux: Eco Limbico en tracto de Ingestion
        ingestion = onda.reactiva.ev.get("Ingestion", {})
        for p_ing in ingestion.values():
            texto = str(p_ing.product.get("contenido", "")).upper()
            if any(tok in texto for tok in ("TERROR", "ES_LETAL", "ES_TERRORIFICO", "PELIGRO")):
                soma.estado_afectivo = V_Estado.MIEDO
                soma.cortisol = float(min(1.0, max(soma.cortisol, 0.82)))
                p_emo = Pieza(
                    id="Emocion_Actual",
                    tipo_componente="Emocion",
                    arousal=0.85,
                    trust=0.90,
                    product={"estado": V_Estado.MIEDO, "estres": soma.cortisol, "eco_ledoux": True},
                    inputs=[p_ing.id, self.id_componente],
                )
                self.emitir_reactiva(onda, "Emocion", p_emo, proyectar_ev=True, coste_amplitud=1)
                return True

        # 3. Senescencia serena si edad_biologica >= 0.88 y sin inanicion critica
        sup = onda.reactiva.ev.get("Supervivencia", {}).get("Alarma_Supervivencia")
        inanicion = bool(sup.product.get("inanicion_critica", False)) if sup else False
        peligro = float(sup.product.get("nivel_peligro", 0.0)) if sup else 0.0

        if soma.edad_biologica >= 0.88 and not inanicion:
            estado = V_Estado.SENESCENTE
            soma.cortisol = 0.25
        elif peligro >= 0.75 or inanicion:
            estado = V_Estado.PANICO if soma.cortisol >= 0.80 else V_Estado.MIEDO
        elif onda.reactiva.ev.get("Proposicion_DUDA"):
            estado = V_Estado.CURIOSIDAD
        else:
            estado = V_Estado.CALMA

        soma.estado_afectivo = estado
        p_emo = Pieza(
            id="Emocion_Actual",
            tipo_componente="Emocion",
            arousal=max(0.15, soma.cortisol),
            trust=0.90,
            product={"estado": estado, "estres": round(soma.cortisol, 4), "eco_ledoux": False},
            inputs=[self.id_componente],
        )
        self.emitir_reactiva(onda, "Emocion", p_emo, proyectar_ev=True, coste_amplitud=1)
        return True


class CompImpulsoExteriorizacionS2(ComponenteCognitivoBase):
    """
    Modulo Reaccionar de S2:
    1. Comp_ImpulsoS2: Modula los impulsos existentes en acc['Impulso'] anadiendo valencia estetica,
       atraccion ludica/coleccionista (ACC_COGER elementos armonicos cuando alimentacion > 60)
       y aversion por traumas pasados.
    2. Comp_Exteriorizacion: Registra en ef la expresion somatica del organismo a coste 0.
    """

    def __init__(self):
        super().__init__("Comp_ImpulsoS2", "S2")

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        soma = ctx["soma"]
        activa = ctx["activa"]
        impulsos = onda.reactiva.acc.get("Impulso", {})

        # Modular impulsos de S1 segun memoria afectiva y estetica
        for imp in impulsos.values():
            target = str(imp.product.get("target", ""))
            mem_verdad = activa.obtener_pieza(target, "Proposicion_VERDAD")
            if mem_verdad is not None:
                rel = str(mem_verdad.product.get("relacion", ""))
                if rel in (str(V_Relacion.ES_LETAL), str(V_Relacion.ES_TERRORIFICO)):
                    if imp.product.get("comando") == V_Comando.DEGLUTIR:
                        imp.arousal *= 0.10
                        imp.trust *= 0.20
                        imp.sistemas_participantes.add("S2")

        # Coleccionismo ludico/estetico en calma (alimentacion > 60 y manos libres)
        if soma.alimentacion > 60.0 and soma.objeto_cargado is None:
            pred_val = onda.reactiva.ev.get("Predicado_VALOR", {})
            for pid, p_val in pred_val.items():
                if p_val.product.get("relacion") == V_Relacion.ES_ARMONICO:
                    p_coger = Pieza(
                        id=f"impulso_coger_joya_{pid}",
                        tipo_componente="Impulso",
                        arousal=0.62,
                        trust=0.82,
                        product={
                            "comando": V_Comando.COGER,
                            "target": pid,
                            "coleccionismo_estetico": True,
                        },
                        inputs=[pid, self.id_componente],
                    )
                    self.emitir_impulso(onda, p_coger, coste_amplitud=1)

        # Exteriorizacion somatica en ef (coste 0)
        p_ext = Pieza(
            id="Exteriorizacion",
            tipo_componente="Exteriorizacion",
            arousal=soma.cortisol,
            trust=1.0,
            product={"estado_visible": str(soma.estado_afectivo), "placer": round(soma.placer, 2)},
            inputs=["Emocion_Actual", "Comp_Exteriorizacion"],
        )
        onda.reactiva.registrar_ef_universal("Exteriorizacion", p_ext)
        return True


def crear_sistema_s2() -> SistemaCognitivoTriunico:
    s2 = SistemaCognitivoTriunico("S2", cuota_frecuencia_ratio=0.30)
    s2.inyectar_componente("SENTIR", CompConceptoSujetoS2())
    s2.inyectar_componente("INTERPRETAR", CompPredicadoProposicionS2())
    s2.inyectar_componente("INTERPRETAR", CompGenerarEmocionS2())
    s2.inyectar_componente("REACCIONAR", CompImpulsoExteriorizacionS2())
    return s2
