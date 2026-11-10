from typing import Dict, Any, List, Optional
from nivel_1_core.vocabulario import V_Comando, V_Dominio, V_Modalidad, V_Relacion, V_Vinculo, V_Estado
from nivel_1_core.contratos import Pieza, Onda
from nivel_2_sistemas.sistema_base import ComponenteCognitivoBase, SistemaCognitivoTriunico


class CompComunicacionS3(ComponenteCognitivoBase):
    """
    Modulo Sentir de S3:
    Detecta portadores de informacion simbolica en la escena (mensajes, fuentes epistemicas,
    senales de otros agentes o bocados asimilados) y prepara su estructura para el analisis sintactico.
    """

    def __init__(self):
        super().__init__("Comp_Comunicacion", "S3")

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        objetos = onda.reactiva.ev.get("Objeto", {})
        for oid, p_obj in objetos.items():
            es_portador = bool(p_obj.product.get("es_portador_simbolico", False)) or (
                p_obj.product.get("mensaje_simbolico") is not None
            ) or bool(p_obj.product.get("es_fuente_epistemica", False))
            if es_portador:
                p_com = Pieza(
                    id=oid,
                    tipo_componente="Comunicacion",
                    arousal=max(0.55, p_obj.arousal),
                    trust=p_obj.trust,
                    product={
                        "portador": oid,
                        "emisor": p_obj.product.get("emisor", "Ancestro"),
                        "sujeto_referido": p_obj.product.get("sujeto_referido", oid),
                        "relacion_expresada": p_obj.product.get("relacion_expresada", str(V_Relacion.ES_SEGURO)),
                        "es_fuente_epistemica": bool(p_obj.product.get("es_fuente_epistemica", False)),
                        "firma_autor": p_obj.product.get("firma_autor"),
                    },
                    inputs=[oid, self.id_componente],
                )
                self.emitir_reactiva(onda, "Comunicacion", p_com, proyectar_ev=True, coste_amplitud=1)
        return True


class CompSentenciaLogicaS3(ComponenteCognitivoBase):
    """
    Modulo Interpretar de S3:
    1. Comp_Sentencia: Construye estructuras intencionales de segundo orden (recursivas):
       Sentencia = [Agente_Emisor] + V_Modalidad(CREE | DESEA | EXPRESA | ASUME_ROL) + [Proposicion | Sentencia]
    2. Comp_Logica: Construye y recorre el grafo de inferencia causal (Logica_CAUSAL) mediante
       V_Vinculo (CAUSA, IMPLICA, CONTRADICE, ES_ANALOGO_A).
    3. Resolucion Silogistica Deductiva: Si en DimensionActiva existen dos verdades demostradas
       ([A ES_ANALOGO_A B] y [B IMPLICA ES_LETAL]), deduce formalmente [A IMPLICA ES_LETAL]
       con modalidad DEMOSTRADO_DEDUCTIVO sin requerir dano fisico previo.
    """

    def __init__(self):
        super().__init__("Comp_Sentencia_Logica", "S3")

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        activa = ctx["activa"]
        arq = ctx["arquetipo"]
        comunicaciones = onda.reactiva.ev.get("Comunicacion", {})

        for cid, p_com in comunicaciones.items():
            emisor = str(p_com.product.get("emisor", "Ancestro"))
            sujeto_ref = str(p_com.product.get("sujeto_referido", cid))
            rel_exp = str(p_com.product.get("relacion_expresada", V_Relacion.ES_SEGURO))
            firma = p_com.product.get("firma_autor")

            # Reconocimiento criptografico de senuelos tacticos propios o de ancestros directos
            if firma is not None and (firma == arq.id_individuo or firma in arq.ancestros):
                if p_com.product.get("es_senuelo_tactico", False):
                    continue

            formula_sentencia = f"[{emisor} EXPRESA ([{sujeto_ref}] {rel_exp})]"
            p_sent = Pieza(
                id=f"Sentencia_{cid}",
                tipo_componente="Sentencia",
                arousal=p_com.arousal,
                trust=p_com.trust,
                product={
                    "agente_emisor": emisor,
                    "modalidad": V_Modalidad.EXPRESA,
                    "sujeto_interno": sujeto_ref,
                    "relacion_interna": rel_exp,
                    "formula": formula_sentencia,
                },
                inputs=[cid, "Comp_Sentencia"],
            )
            self.emitir_reactiva(onda, "Sentencia", p_sent, proyectar_ev=True, coste_amplitud=1)

            # Si hay Amplitud disponible (>= 2), formalizar regla Logica_CAUSAL vicaria
            if onda.amplitud_restante() >= 2:
                efecto = "EVASION_PRIORITARIA" if rel_exp in (str(V_Relacion.ES_LETAL), str(V_Relacion.ES_TERRORIFICO)) else "RUTA_FERTIL"
                p_log = Pieza(
                    id=f"Logica_{sujeto_ref}",
                    tipo_componente="Logica_CAUSAL",
                    arousal=p_com.arousal,
                    trust=p_com.trust,
                    product={
                        "sujeto": sujeto_ref,
                        "vinculo": V_Vinculo.IMPLICA,
                        "consecuente": rel_exp,
                        "efecto_conductual": efecto,
                        "fuente": "vicaria",
                        "emisor": emisor,
                        "modalidad": V_Modalidad.HIPOTESIS,
                    },
                    inputs=[p_sent.id, "Comp_Logica"],
                    heredado=True,
                )
                self.emitir_reactiva(onda, "Logica", p_log, proyectar_ev=True, coste_amplitud=2)
                activa.consolidar_pieza(sujeto_ref, p_log)
                activa.registrar_enlace_causal(sujeto_ref, rel_exp, "Logica_CAUSAL", V_Vinculo.IMPLICA, p_com.trust)

        # Resolucion Silogistica Deductiva sobre DimensionActiva:
        # Si [A ES_ANALOGO_A B] y [B IMPLICA ES_LETAL (DEMOSTRADO)] => [A IMPLICA ES_LETAL (DEMOSTRADO_DEDUCTIVO)]
        for suj_a, enlaces_a in list(activa.indice_causal.items()):
            for dest_b, _, vinc_ab, trust_ab in enlaces_a:
                if vinc_ab == str(V_Vinculo.ES_ANALOGO_A) and trust_ab >= 0.75:
                    for dest_c, _, vinc_bc, trust_bc in activa.indice_causal.get(dest_b, []):
                        if vinc_bc in (str(V_Vinculo.IMPLICA), str(V_Vinculo.CAUSA)) and trust_bc >= 0.85:
                            existente = activa.obtener_pieza(suj_a, "Proposicion_VERDAD")
                            if existente is None or str(existente.product.get("modalidad")) == str(V_Modalidad.HIPOTESIS):
                                p_ded = Pieza(
                                    id=suj_a,
                                    tipo_componente="Proposicion_VERDAD",
                                    arousal=0.75,
                                    trust=min(1.0, trust_ab * trust_bc),
                                    product={
                                        "sujeto": suj_a,
                                        "dominio": V_Dominio.VERDAD,
                                        "relacion": dest_c,
                                        "vinculo": V_Vinculo.IMPLICA,
                                        "modalidad": V_Modalidad.DEMOSTRADO_DEDUCTIVO,
                                        "formula": f"[{suj_a} IMPLICA {dest_c}] (DEMOSTRADO_DEDUCTIVO via {dest_b})",
                                    },
                                    inputs=[f"Analogia:{suj_a}~{dest_b}", f"Causal:{dest_b}->{dest_c}", "Comp_Logica"],
                                    heredado=False,
                                    demostrado_de_novo=True,
                                )
                                activa.consolidar_pieza(suj_a, p_ded)
                                self.emitir_reactiva(onda, "Logica", p_ded, proyectar_ev=True, coste_amplitud=1)

        return True


class CompMapaCognitivoMetacognicionS3(ComponenteCognitivoBase):
    """
    Modulo Interpretar de S3:
    1. Contrasta las expectativas de DimensionProactiva (t-1) contra la realidad percibida en t.
    2. Calcula el Error de Prediccion de Recompensa (delta_RPE = R - E[R]) que alimenta la Dopamina estriatal.
       Si falla negativamente, emite 'Sorpresa' y deprime la dopamina (activando freno D2).
    3. Distingue entre Extincion Empirica de Trauma Cultural ([EMPIRISMO] CONTRADICE [TERROR_VICARIO],
       erosionando un 50% el trust del rumor cuando no hay peligro) y Nicho Pacificado (cuando el peligro
       fue abatido con ACC_ATACAR, conservando intacto el trust del ancestro).
    4. Comp_Metacognicion: actualiza la media movil de Autoestima_Cognitiva en [0.20, 1.00] evaluando
       unicamente las predicciones propias (nunca penaliza por comprobar que un rumor ajeno era falso)
       y emite [IdA CREE (IdA ES_FIABLE | ES_FALIBLE)].
    """

    def __init__(self):
        super().__init__("Comp_MapaCognitivo_Metacognicion", "S3")

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        soma = ctx["soma"]
        activa = ctx["activa"]
        proactiva = ctx["proactiva"]
        nodo = onda.ubicacion_actual

        # Verificar si en el latido anterior se asimilo verdad empirica verificada (Catarsis Epistemica)
        ejec_prev = onda.reactiva.ei.get("Ejecucion", {}).get("Ejecucion") if "Ejecucion" in onda.reactiva.ei else None
        if ejec_prev is not None and ejec_prev.product.get("verdad_verificada") is not None:
            vor = ejec_prev.product["verdad_verificada"]
            suj_v = str(vor["sujeto"])
            rel_v = V_Relacion(str(vor["relacion"]))
            activa.verificar_hipotesis_empirica(
                sujeto_id=suj_v,
                balance_positivo=True,
                id_episodio_evidencia=f"Evidencia_{onda.ciclo}",
                relacion_confirmada=rel_v,
            )
            # Catarsis Epistemica: +40.0 placer opioide y +25.0 dopamina RPE
            soma.inyectar_placer_opioide(40.0)
            soma.actualizar_dopamina_rpe(25.0)
            soma.autoestima_cognitiva = float(min(1.0, soma.autoestima_cognitiva + 0.08))

        # Contrastar regla vicaria sobre el nodo actual (Extincion Empirica vs Nicho Pacificado)
        regla_nodo = activa.obtener_pieza(nodo, "Logica_CAUSAL")
        sup = onda.reactiva.ev.get("Supervivencia", {}).get("Alarma_Supervivencia")
        hay_peligro_real = bool(sup and sup.product.get("amenaza_inminente") is not None)
        fue_abatido = bool(ejec_prev and str(ejec_prev.product.get("comando")) == str(V_Comando.ATACAR) and ejec_prev.product.get("exito"))

        if regla_nodo is not None and regla_nodo.product.get("fuente") == "vicaria":
            consecuente = str(regla_nodo.product.get("consecuente", ""))
            if consecuente in (str(V_Relacion.ES_LETAL), str(V_Relacion.ES_TERRORIFICO)):
                if fue_abatido:
                    regla_nodo.product["estado_nicho"] = "NICHO_PACIFICADO"
                    regla_nodo.product["confirmado_empiricamente"] = True
                elif not hay_peligro_real:
                    # Extincion empirica de trauma cultural: [EMPIRISMO] CONTRADICE [TERROR_VICARIO]
                    regla_nodo.trust *= 0.50
                    p_contra = Pieza(
                        id=f"Extincion_{nodo}",
                        tipo_componente="Logica_CAUSAL",
                        arousal=0.45,
                        trust=0.90,
                        product={
                            "sujeto": "EMPIRISMO",
                            "vinculo": V_Vinculo.CONTRADICE,
                            "consecuente": "TERROR_VICARIO",
                            "nodo": nodo,
                        },
                        inputs=[regla_nodo.id, "Comp_MapaCognitivo"],
                    )
                    self.emitir_reactiva(onda, "Logica", p_contra, proyectar_ev=True, coste_amplitud=1)
                    if regla_nodo.trust <= 0.25:
                        activa.indice_identidad.get(nodo, {}).pop("Logica_CAUSAL", None)

        # Contrastar expectativas de DimensionProactiva (Error de Prediccion RPE)
        exp = proactiva.consumir_expectativa(nodo)
        if exp is not None:
            es_propia = bool(exp.get("es_propia", True))
            recompensa_esperada = float(exp.get("recompensa_esperada", 5.0))
            recompensa_real = -15.0 if hay_peligro_real else float(onda.reactiva.ev.get("Imagen", {}).get(f"Imagen_{onda.ciclo}", Pieza("i", "I", 0, 1)).product.get("delta_alimentacion", 5.0))
            delta_rpe = recompensa_real - recompensa_esperada
            soma.actualizar_dopamina_rpe(delta_rpe)

            if delta_rpe < -5.0:
                p_sorpresa = Pieza(
                    id=f"Sorpresa_{onda.ciclo}",
                    tipo_componente="Sorpresa",
                    arousal=0.88,
                    trust=0.95,
                    product={"delta_rpe": round(delta_rpe, 3), "es_error_propio": es_propia, "nodo": nodo},
                    inputs=["Expectativa", "Comp_MapaCognitivo"],
                )
                self.emitir_reactiva(onda, "Sorpresa", p_sorpresa, proyectar_ev=True, coste_amplitud=1)
                if es_propia:
                    soma.autoestima_cognitiva = float(max(0.20, 0.85 * soma.autoestima_cognitiva + 0.15 * 0.25))
            else:
                if es_propia:
                    soma.autoestima_cognitiva = float(min(1.00, 0.90 * soma.autoestima_cognitiva + 0.10 * 0.95))

        # Comp_Metacognicion: consolidar Autoestima_Cognitiva y emitir sentencia reflexiva
        p_auto = Pieza(
            id="Autoestima_Cognitiva",
            tipo_componente="Autoestima_Cognitiva",
            arousal=0.25,
            trust=1.0,
            product={"valor": round(soma.autoestima_cognitiva, 4)},
            inputs=["Comp_Metacognicion"],
        )
        activa.consolidar_pieza("IdA", p_auto)

        if soma.autoestima_cognitiva < 0.50:
            rel_meta = V_Relacion.ES_FALIBLE
        elif soma.autoestima_cognitiva >= 0.85:
            rel_meta = V_Relacion.ES_FIABLE
        else:
            rel_meta = None

        if rel_meta is not None:
            p_sent_meta = Pieza(
                id="Sentencia_Metacognitiva",
                tipo_componente="Sentencia",
                arousal=0.35,
                trust=soma.autoestima_cognitiva,
                product={
                    "agente_emisor": "IdA",
                    "modalidad": V_Modalidad.CREE,
                    "sujeto_interno": "IdA",
                    "relacion_interna": rel_meta,
                    "formula": f"[IdA CREE (IdA {rel_meta})]",
                },
                inputs=["Autoestima_Cognitiva", "Comp_Metacognicion"],
            )
            self.emitir_reactiva(onda, "Sentencia", p_sent_meta, proyectar_ev=False, coste_amplitud=0)

        return True


class CompArgumentacionIdentidadS3(ComponenteCognitivoBase):
    """
    Modulo Interpretar de S3:
    1. Comp_Argumentacion: Reune premisas ante entidades con Proposicion_DUDA, consulta el
       Inconsciente Colectivo RAG (pgvector con Barrera de Weismann) y vuelca eurekas de la cola
       asincrona como cascada formal: Predicado -> Proposicion -> Sentencia -> Logica.
    2. Comp_IdentidadNarrativa: Sintetiza el Rol del Yo ([IdA ASUME_ROL Protector/Altruista/Explorador])
       con axioma [PRIORIZA (Valor_Superior) SOBRE (Homeostasis)].
    """

    def __init__(self):
        super().__init__("Comp_Argumentacion_Identidad", "S3")

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        activa = ctx["activa"]
        proactiva = ctx["proactiva"]
        pgvector = ctx["pgvector"]
        arq = ctx["arquetipo"]
        soma = ctx["soma"]

        # 1. Volcar Eurekas pendientes de la cola asincrona en cascada formal
        while proactiva.cola_eurekas:
            eureka = proactiva.cola_eurekas.pop(0)
            suj = str(eureka["sujeto"])
            rel = V_Relacion(str(eureka["relacion"]))
            trust_e = float(eureka.get("trust", 0.78))

            p_pred = Pieza(id=suj, tipo_componente="Predicado_VERDAD", arousal=0.65, trust=trust_e, product={"sujeto": suj, "relacion": rel, "dominio": V_Dominio.VERDAD}, inputs=["Eureka_Asincrono"])
            p_prop = Pieza(id=suj, tipo_componente="Proposicion_VERDAD", arousal=0.65, trust=trust_e, product={"sujeto": suj, "relacion": rel, "modalidad": V_Modalidad.HIPOTESIS}, inputs=[p_pred.id])
            p_sent = Pieza(id=f"Sent_Eureka_{suj}", tipo_componente="Sentencia", arousal=0.65, trust=trust_e, product={"agente_emisor": "IdA", "modalidad": V_Modalidad.CREE, "sujeto_interno": suj, "relacion_interna": rel, "formula": f"[IdA CREE ([{suj}] {rel})]"}, inputs=[p_prop.id])
            p_log = Pieza(id=f"Log_Eureka_{suj}", tipo_componente="Logica_CAUSAL", arousal=0.65, trust=trust_e, product={"sujeto": suj, "vinculo": V_Vinculo.IMPLICA, "consecuente": str(rel), "modalidad": V_Modalidad.HIPOTESIS}, inputs=[p_sent.id])

            self.emitir_reactiva(onda, "Predicado_VERDAD", p_pred, proyectar_ev=True, coste_amplitud=1)
            self.emitir_reactiva(onda, "Proposicion_VERDAD", p_prop, proyectar_ev=True, coste_amplitud=0)
            self.emitir_reactiva(onda, "Sentencia", p_sent, proyectar_ev=True, coste_amplitud=0)
            self.emitir_reactiva(onda, "Logica", p_log, proyectar_ev=True, coste_amplitud=0)
            activa.consolidar_pieza(suj, p_prop)

        # 2. Consultar RAG Filogenetico ante Proposicion_DUDA
        dudas = onda.reactiva.ev.get("Proposicion_DUDA", {})
        for did, p_duda in dudas.items():
            recuerdos = pgvector.consultar_inconsciente_rag(
                linaje_actual=arq.linaje,
                ancestros_permitidos=arq.ancestros,
                nodo_consulta=did,
                tensor_consulta=p_duda.tensor_sensorial,
                top_k=1,
            )
            if recuerdos:
                p_intuicion = pgvector.sintetizar_pieza_formal(did, recuerdos[0], soma.autoestima_cognitiva)
                self.emitir_reactiva(onda, "Logica", p_intuicion, proyectar_ev=True, coste_amplitud=1)
                activa.consolidar_pieza(did, p_intuicion)

        # 3. Comp_IdentidadNarrativa: Consolidar el Rol del Yo
        rol = "Protector" if arq.responsabilidad >= 0.65 else ("Altruista" if arq.amabilidad >= 0.70 else "Explorador")
        en_zona_segura = bool(
            onda.reactiva.ev.get("Propiocepcion", {})
            .get(f"Propiocepcion_{onda.ubicacion_actual}", Pieza("p", "P", 0, 1))
            .product.get("es_zona_segura", False)
        )
        valor_sup = "Proteger_Entorno" if rol == "Protector" else ("Preservar_Legado" if rol == "Altruista" else "Verdad_Epistemica")

        p_ident = Pieza(
            id="Identidad_Narrativa",
            tipo_componente="Identidad_Narrativa",
            arousal=0.40,
            trust=1.0,
            product={
                "sujeto": "IdA",
                "modalidad": V_Modalidad.ASUME_ROL,
                "rol": rol,
                "en_zona_segura": en_zona_segura,
                "axioma": f"[PRIORIZA ({valor_sup}) SOBRE (Homeostasis)]",
                "vinculo": V_Vinculo.PRIORIZA,
            },
            inputs=["Arquetipo", "Comp_IdentidadNarrativa"],
        )
        activa.consolidar_pieza("IdA", p_ident)
        return True


class CompPlanificacionMotoraS3(ComponenteCognitivoBase):
    """
    Modulo Reaccionar de S3:
    Ejecuta Ensonacion Tactica Distribuida (BFS/A* acotado): en estado de CALMA y con Amplitud
    libre > 30, expande de 2 a 3 nodos por latido sobre DimensionActiva.grafo_topologico,
    guardando el estado parcial en DimensionProactiva (simulacion_ruta) para no violar los 100 ms.
    Ajusta la meta segun la teleologia activa: RUTA_FERTIL, FUENTE_EPISTEMICA o ZONA_SEGURA.
    """

    def __init__(self):
        super().__init__("Comp_PlanificacionMotora", "S3")

    async def procesar_proactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        soma = ctx["soma"]
        activa = ctx["activa"]
        proactiva = ctx["proactiva"]

        # Determinar meta teleologica activa
        porta_hipotesis = bool(soma.objeto_cargado and soma.objeto_cargado.get("modalidad") == str(V_Modalidad.HIPOTESIS))
        if porta_hipotesis:
            meta_tipo = "FUENTE_EPISTEMICA"
        elif soma.objeto_cargado is not None or soma.estado_afectivo == V_Estado.SENESCENTE:
            meta_tipo = "ZONA_SEGURA"
        else:
            meta_tipo = "RUTA_FERTIL"

        # En CALMA y con Amplitud libre > 30, expandir hasta 3 nodos en BFS sobre grafo_topologico
        if soma.cortisol <= 0.45 and onda.amplitud_restante() > 30 and activa.grafo_topologico:
            sim = proactiva.simulacion_ruta
            if sim is None or sim.get("origen") != onda.ubicacion_actual or sim.get("meta_tipo") != meta_tipo:
                sim = {
                    "origen": onda.ubicacion_actual,
                    "meta_tipo": meta_tipo,
                    "cola": [[onda.ubicacion_actual]],
                    "visitados": [onda.ubicacion_actual],
                    "ruta_hallada": None,
                }
                proactiva.simulacion_ruta = sim

            nodos_expandidos = 0
            while sim["cola"] and nodos_expandidos < 3 and sim["ruta_hallada"] is None:
                camino = sim["cola"].pop(0)
                actual = camino[-1]
                nodos_expandidos += 1

                for vecino in activa.grafo_topologico.get(actual, {}):
                    if vecino in sim["visitados"]:
                        continue
                    sim["visitados"].append(vecino)
                    nuevo_camino = camino + [vecino]

                    p_vec = activa.obtener_pieza(vecino, "Proposicion_VERDAD") or activa.obtener_pieza(vecino, "Logica_CAUSAL")
                    rel_vec = str(p_vec.product.get("relacion") or p_vec.product.get("consecuente", "")) if p_vec else ""
                    es_fuente_ep = bool(p_vec and p_vec.product.get("es_fuente_epistemica", False))

                    es_meta = (
                        (meta_tipo == "FUENTE_EPISTEMICA" and es_fuente_ep)
                        or (meta_tipo == "ZONA_SEGURA" and rel_vec == str(V_Relacion.ES_SEGURO))
                        or (meta_tipo == "RUTA_FERTIL" and rel_vec == str(V_Relacion.ES_NUTRITIVO))
                    )
                    if es_meta:
                        sim["ruta_hallada"] = nuevo_camino
                        break
                    sim["cola"].append(nuevo_camino)

            if sim.get("ruta_hallada") and len(sim["ruta_hallada"]) >= 2:
                sig_paso = sim["ruta_hallada"][1]
                p_plan = Pieza(
                    id=f"impulso_ruta_{sig_paso}",
                    tipo_componente="Impulso",
                    arousal=0.72,
                    trust=0.88 * soma.autoestima_cognitiva,
                    product={
                        "comando": V_Comando.MOVER,
                        "target": sig_paso,
                        "meta_teleologica": meta_tipo,
                        "ruta_completa": list(sim["ruta_hallada"]),
                    },
                    inputs=["Simulacion_Ruta", self.id_componente],
                )
                self.emitir_impulso(onda, p_plan, coste_amplitud=1)
                return True

        return False


class CompImpulsoS3(ComponenteCognitivoBase):
    """
    Modulo Reaccionar de S3:
    1. Inhibicion Prefrontal (Veto) y Prudencia Epistemica: atenua drasticamente (arousal *= 0.15,
       frenado_s3 = True) cualquier impulso de S1 que intente ACC_DEGLUTIR una entidad cuya proposicion
       este en HIPOTESIS (no demostrada) o sea un senuelo parasitario, incluso con manos ocupadas.
    2. Gratificacion Diferida y Heuristica de Swap de la Mochila: si alimentacion > 45.0 y no esta
       en zona segura, transmuta ACC_DEGLUTIR en ACC_COGER. Si ya porta un objeto estetico/epistemico y
       el hambre aprieta (alimentacion <= 45.0), emite ACC_SOLTAR con swap_pendiente.
    3. Lucidez de Agonia: si S1 lleva >= 3 latidos en panico sin nutrirse, S3 rescata el nodo mas seguro
       de la memoria semantica y emite un ultimo flash direccional (Trust = 0.20).
    4. Comp_SecrecionDialectica: en estado SENESCENTE, emite en acc['Expresion'] la regla causal mas
       consolidada ([IdA] EXPRESA [Logica_Causal]).
    """

    def __init__(self):
        super().__init__("Comp_ImpulsoS3", "S3")

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        soma = ctx["soma"]
        activa = ctx["activa"]
        proactiva = ctx["proactiva"]
        impulsos = onda.reactiva.acc.get("Impulso", {})
        dudas = onda.reactiva.ev.get("Proposicion_DUDA", {})
        comunicaciones = onda.reactiva.ev.get("Comunicacion", {})

        en_zona_segura = bool(
            onda.reactiva.ev.get("Propiocepcion", {})
            .get(f"Propiocepcion_{onda.ubicacion_actual}", Pieza("p", "P", 0, 1))
            .product.get("es_zona_segura", False)
        )

        # Si hay una Fuente Epistemica visible y existe una entidad en HIPOTESIS/DUDA por verificar, emitir ACC_ASIMILAR
        obj_a_verificar = (
            soma.objeto_cargado.get("id")
            if soma.objeto_cargado
            else (next(iter(dudas.keys())) if dudas else None)
        )
        if obj_a_verificar is not None:
            for cid, p_com in comunicaciones.items():
                if p_com.product.get("es_fuente_epistemica"):
                    p_asim = Pieza(
                        id=f"impulso_asimilar_{cid}",
                        tipo_componente="Impulso",
                        arousal=0.88,
                        trust=0.95,
                        product={
                            "comando": V_Comando.ASIMILAR,
                            "target": cid,
                            "objeto_a_verificar": obj_a_verificar,
                        },
                        inputs=[cid, self.id_componente],
                    )
                    self.emitir_impulso(onda, p_asim, coste_amplitud=1)
                    activa.fatiga_atencional[cid] = activa.fatiga_atencional.get(cid, 0.0) + 3.0

        # Evaluar y modular los impulsos de S1/S2 en el canal comun acc['Impulso']
        for imp in list(impulsos.values()):
            cmd = imp.product.get("comando")
            target = str(imp.product.get("target", ""))

            if cmd == V_Comando.DEGLUTIR:
                # 1. Prudencia Epistemica Prefrontal (incluso con manos ocupadas)
                es_duda = target in dudas or (activa.obtener_pieza(target, "Proposicion_DUDA") is not None)
                mem_verdad = activa.obtener_pieza(target, "Proposicion_VERDAD")
                es_demostrado_nutritivo = bool(
                    mem_verdad
                    and str(mem_verdad.product.get("relacion")) == str(V_Relacion.ES_NUTRITIVO)
                    and str(mem_verdad.product.get("modalidad")) in (str(V_Modalidad.DEMOSTRADO), str(V_Modalidad.DEMOSTRADO_DEDUCTIVO))
                )

                if es_duda and not es_demostrado_nutritivo:
                    imp.arousal *= 0.15
                    imp.product["frenado_s3"] = True
                    imp.sistemas_participantes.add("S3")
                    # Si tiene manos libres y alimentacion > 25, recoger para verificar epistemicamente
                    if soma.objeto_cargado is None and soma.alimentacion > 25.0:
                        imp.product["comando"] = V_Comando.COGER
                        imp.product["modalidad"] = str(V_Modalidad.HIPOTESIS)
                        imp.arousal = 0.78
                        imp.trust = 0.88
                    continue

                # 2. Gratificacion Diferida hacia zona segura cuando alimentacion > 45.0 y existe grafo topologico navegable
                if (
                    soma.alimentacion > soma.UMBRAL_HAMBRE_MODERADA
                    and not en_zona_segura
                    and soma.objeto_cargado is None
                    and bool(activa.grafo_topologico)
                ):
                    imp.product["comando"] = V_Comando.COGER
                    imp.product["gratificacion_diferida"] = True
                    imp.product["es_nutritivo"] = True
                    imp.trust = max(imp.trust, 0.85 * soma.autoestima_cognitiva)
                    imp.sistemas_participantes.add("S3")

                # 3. Heuristica de Swap de la Mochila cuando alimentacion <= 45.0 y porta objeto no nutritivo
                elif (
                    soma.alimentacion <= soma.UMBRAL_HAMBRE_MODERADA
                    and soma.objeto_cargado is not None
                    and not soma.objeto_cargado.get("es_nutritivo", False)
                ):
                    p_swap = Pieza(
                        id="impulso_swap_mochila",
                        tipo_componente="Impulso",
                        arousal=0.89,
                        trust=0.92,
                        product={
                            "comando": V_Comando.SOLTAR,
                            "target": str(soma.objeto_cargado.get("id", "carga")),
                            "swap_pendiente": target,
                        },
                        inputs=[imp.id, self.id_componente],
                    )
                    self.emitir_impulso(onda, p_swap, coste_amplitud=1)

        # Si llega a zona segura con carga nutritiva, depositar (ACC_SOLTAR)
        if en_zona_segura and soma.objeto_cargado is not None:
            p_dep = Pieza(
                id="impulso_depositar_nicho",
                tipo_componente="Impulso",
                arousal=0.85,
                trust=0.95,
                product={
                    "comando": V_Comando.SOLTAR,
                    "target": str(soma.objeto_cargado.get("id", "carga")),
                    "deposito_nicho": True,
                },
                inputs=["Propiocepcion", self.id_componente],
            )
            self.emitir_impulso(onda, p_dep, coste_amplitud=1)

        # Lucidez de Agonia: si S1 lleva >= 3 latidos en panico y no hay sacrificio consciente
        id_narr = activa.obtener_pieza("IdA", "Identidad_Narrativa")
        en_sacrificio = bool(id_narr and id_narr.product.get("en_zona_segura") and id_narr.product.get("rol") in ("Protector", "Altruista") and soma.alimentacion <= soma.UMBRAL_INANICION_CRITICA)
        if soma.ciclos_panico >= 3 and not en_sacrificio and onda.amplitud_restante() >= 1:
            for suj_id, cajon in activa.indice_identidad.items():
                p_v = cajon.get("Proposicion_VERDAD")
                if p_v and str(p_v.product.get("relacion")) == str(V_Relacion.ES_NUTRITIVO):
                    p_flash = Pieza(
                        id=f"impulso_lucidez_agonia_{suj_id}",
                        tipo_componente="Impulso",
                        arousal=0.88,
                        trust=0.20,
                        product={
                            "comando": V_Comando.MOVER,
                            "target": suj_id,
                            "flash_supervivencia": True,
                        },
                        inputs=[p_v.id, "Comp_LucidezAgonia"],
                    )
                    self.emitir_impulso(onda, p_flash, coste_amplitud=1)
                    break

        # Secrecion Dialectica en estado SENESCENTE (cada 8 latidos)
        if soma.estado_afectivo == V_Estado.SENESCENTE and onda.ciclo % 8 == 0 and onda.amplitud_restante() >= 1:
            demostradas = activa.contar_demostrados_de_novo()
            if demostradas:
                mejor = max(demostradas, key=lambda p: p.trust * p.arousal)
                p_exp = Pieza(
                    id=f"Expresion_Simbolica_{onda.ciclo}",
                    tipo_componente="Expresion",
                    arousal=0.60,
                    trust=mejor.trust,
                    product={
                        "emisor": "IdA",
                        "modalidad": V_Modalidad.EXPRESA,
                        "sujeto": mejor.id,
                        "relacion": mejor.product.get("relacion", str(V_Relacion.ES_NUTRITIVO)),
                        "formula": f"[IdA] EXPRESA [{mejor.id} IMPLICA {mejor.product.get('relacion')}]",
                    },
                    inputs=[mejor.id, "Comp_SecrecionDialectica"],
                )
                self.emitir_impulso(onda, p_exp, canal_acc="Expresion", coste_amplitud=1)

        # Proyectar expectativa proactiva para el nodo destino del impulso de mayor arousal
        if impulsos:
            mejor_imp = max(impulsos.values(), key=lambda x: x.arousal)
            proactiva.proyectar_expectativa(
                str(mejor_imp.product.get("target", onda.ubicacion_actual)),
                {"es_propia": True, "recompensa_esperada": 6.0 if mejor_imp.product.get("comando") == V_Comando.DEGLUTIR else 1.0},
            )

        return True


def crear_sistema_s3(organos_nivel_3: Optional[List[ComponenteCognitivoBase]] = None) -> SistemaCognitivoTriunico:
    s3 = SistemaCognitivoTriunico("S3", cuota_frecuencia_ratio=0.45)
    s3.inyectar_componente("SENTIR", CompComunicacionS3())
    s3.inyectar_componente("INTERPRETAR", CompSentenciaLogicaS3())
    s3.inyectar_componente("INTERPRETAR", CompMapaCognitivoMetacognicionS3())
    s3.inyectar_componente("INTERPRETAR", CompArgumentacionIdentidadS3())
    if organos_nivel_3:
        for org in organos_nivel_3:
            s3.inyectar_componente("INTERPRETAR", org)
    s3.inyectar_componente("REACCIONAR", CompPlanificacionMotoraS3())
    s3.inyectar_componente("REACCIONAR", CompImpulsoS3())
    return s3
