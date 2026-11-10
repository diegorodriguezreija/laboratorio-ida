from typing import Dict, Any
import numpy as np
from nivel_1_core.vocabulario import V_Comando, V_Dominio, V_Modalidad, V_Relacion, V_Vinculo
from nivel_1_core.contratos import Pieza, Onda
from nivel_2_sistemas.sistema_base import ComponenteCognitivoBase, SistemaCognitivoTriunico
from nivel_2_sistemas.plasticidad_td_hebbiana import MatrizHebbianaTresFactores


class CompImagenS1(ComponenteCognitivoBase):
    """
    Modulo Sentir de S1:
    1. Lee ei['Ejecucion'] y los deltas de ev['Interocepcion'] para computar Agencia Causal
       ("ejecute accion X en t-1 y mi cuerpo experimento este cambio en t").
    2. Evalua el peligro y la nutricion de cada entidad de ev['Escena'] mediante la matriz
       sinaptica Hebbiana W (6x4) aplicada al tensor sensorial 6D.
    3. Emite la pieza 'Imagen' (Gestalt del instante) y piezas 'Objeto' valoradas.
    """

    def __init__(self, matriz_hebbiana: MatrizHebbianaTresFactores):
        super().__init__("Comp_Imagen", "S1")
        self.hebb = matriz_hebbiana

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        activa = ctx["activa"]
        soma = ctx["soma"]

        # 1. Agencia Causal desde ei["Ejecucion"]
        ejec_prev = None
        if "Ejecucion" in onda.reactiva.ei and "Ejecucion" in onda.reactiva.ei["Ejecucion"]:
            ejec_prev = onda.reactiva.ei["Ejecucion"]["Ejecucion"]

        intero_ev = onda.reactiva.ev.get("Interocepcion", {})
        delta_ali = float(intero_ev.get("alimentacion", Pieza("ali", "I", 0, 1)).product.get("delta", 0.0))
        delta_vit = float(intero_ev.get("vitalidad", Pieza("vit", "I", 0, 1)).product.get("delta", 0.0))

        efecto_agencia = "NEUTRO"
        if ejec_prev is not None:
            cmd_prev = str(ejec_prev.product.get("comando", ""))
            target_prev = str(ejec_prev.product.get("target", ""))
            intox_prev = bool(ejec_prev.product.get("intoxicacion_aguda", False))

            if intox_prev or delta_vit <= -8.0:
                efecto_agencia = "DANO_VISCERAL_AGUDO"
                # Consolidacion empirica inmediata del trauma: [target] ES_LETAL (DEMOSTRADO)
                activa.verificar_hipotesis_empirica(
                    sujeto_id=target_prev,
                    balance_positivo=True,
                    id_episodio_evidencia=f"Agencia_{onda.ciclo}",
                    relacion_confirmada=V_Relacion.ES_LETAL,
                )
                activa.registrar_enlace_causal(
                    target_prev, str(V_Relacion.ES_LETAL), "Logica_CAUSAL", V_Vinculo.CAUSA, 0.98
                )
            elif cmd_prev == str(V_Comando.DEGLUTIR) and delta_ali > 0.0:
                efecto_agencia = "RECARGA_NUTRICIONAL"
                activa.verificar_hipotesis_empirica(
                    sujeto_id=target_prev,
                    balance_positivo=True,
                    id_episodio_evidencia=f"Agencia_{onda.ciclo}",
                    relacion_confirmada=V_Relacion.ES_NUTRITIVO,
                )

        # 2. Valoracion Hebbiana 6D de las entidades de Escena
        escena_dict = onda.reactiva.ev.get("Escena", {})
        foco_primario = None
        max_saliencia = -1.0

        for eid, p_esc in escena_dict.items():
            tensor = p_esc.tensor_sensorial if p_esc.tensor_sensorial is not None else np.zeros(6)
            scores = self.hebb.evaluar_tensor_6d(tensor)

            # Si hubo intoxicacion o recarga sobre este objeto en t-1, ajustar W hebbiana
            if ejec_prev is not None and str(ejec_prev.product.get("target", "")) == eid:
                if efecto_agencia == "DANO_VISCERAL_AGUDO":
                    self.hebb.actualizar_hebbiano_3_factores(tensor, canal_post_idx=1, delta_dopamina_rpe=-35.0)
                elif efecto_agencia == "RECARGA_NUTRICIONAL":
                    self.hebb.actualizar_hebbiano_3_factores(tensor, canal_post_idx=0, delta_dopamina_rpe=15.0)

            # Atenuacion por fatiga atencional (habituacion cognitiva)
            fatiga = activa.fatiga_atencional.get(eid, 0.0)
            arousal_obj = float(np.clip(max(scores["score_nutritivo"], scores["score_letal"], p_esc.arousal) - fatiga * 0.2, 0.10, 1.0))

            p_obj = Pieza(
                id=eid,
                tipo_componente="Objeto",
                arousal=arousal_obj,
                trust=p_esc.trust,
                tensor_sensorial=tensor,
                product={
                    **p_esc.product,
                    **scores,
                    "proximidad_letal": float(tensor[0] * tensor[5]),
                },
                inputs=[p_esc.id, self.id_componente],
            )
            self.emitir_reactiva(onda, "Objeto", p_obj, proyectar_ev=True, coste_amplitud=1)

            if arousal_obj > max_saliencia:
                max_saliencia = arousal_obj
                foco_primario = eid

        p_imagen = Pieza(
            id=f"Imagen_{onda.ciclo}",
            tipo_componente="Imagen",
            arousal=max(0.2, max_saliencia),
            trust=0.95,
            product={
                "ubicacion": onda.ubicacion_actual,
                "foco_primario": foco_primario,
                "efecto_agencia": efecto_agencia,
                "delta_alimentacion": delta_ali,
                "delta_vitalidad": delta_vit,
                "num_entidades": len(escena_dict),
            },
            inputs=["Escena", "Interocepcion", self.id_componente],
        )
        self.emitir_reactiva(onda, "Imagen", p_imagen, proyectar_ev=True, coste_amplitud=1)
        return True


class CompSupervivenciaS1(ComponenteCognitivoBase):
    """
    Modulo Interpretar de S1:
    Cruza la Imagen con las alarmas interoceptivas (alimentacion <= 15.0, caida brusca de vitalidad
    o proximidad x0 * x5 de una amenaza) y proyecta expectativas viscerales inmediatas.
    """

    def __init__(self):
        super().__init__("Comp_Supervivencia", "S1")

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        soma = ctx["soma"]
        objetos = onda.reactiva.ev.get("Objeto", {})

        amenaza_inminente = None
        max_peligro = 0.0
        mejor_nutriente = None
        max_nutricion = 0.0

        for oid, p_obj in objetos.items():
            peligro = max(float(p_obj.product.get("score_letal", 0.0)), float(p_obj.product.get("proximidad_letal", 0.0)))
            nutri = float(p_obj.product.get("score_nutritivo", 0.0))
            if peligro > max_peligro and peligro >= 0.55:
                max_peligro = peligro
                amenaza_inminente = oid
            if nutri > max_nutricion and peligro < 0.55:
                max_nutricion = nutri
                mejor_nutriente = oid

        inanicion = soma.alimentacion <= soma.UMBRAL_INANICION_CRITICA
        urgencia = max(max_peligro, 0.95 if inanicion else (100.0 - soma.alimentacion) / 100.0)

        p_sup = Pieza(
            id="Alarma_Supervivencia",
            tipo_componente="Supervivencia",
            arousal=float(np.clip(urgencia, 0.1, 1.0)),
            trust=0.90,
            product={
                "dominio": V_Dominio.SUPERVIVENCIA,
                "inanicion_critica": inanicion,
                "amenaza_inminente": amenaza_inminente,
                "nivel_peligro": round(max_peligro, 4),
                "mejor_nutriente": mejor_nutriente,
                "nivel_nutricion": round(max_nutricion, 4),
            },
            inputs=["Imagen", self.id_componente],
        )
        self.emitir_reactiva(onda, "Supervivencia", p_sup, proyectar_ev=True, coste_amplitud=1)
        return True


class CompImpulsoS1(ComponenteCognitivoBase):
    """
    Modulo Reaccionar de S1:
    1. Genera impulsos primarios de supervivencia en acc['Impulso'] (ACC_MOVER de huida, ACC_DEGLUTIR,
       ACC_ATACAR, o ACC_SOLTAR lastre en inanicion critica).
    2. Anti-Backtracking Instintivo: penaliza a 0 el arousal hacia los 2 ultimos nodos visitados
       en inanicion para evitar bucles oscilatorios A <-> B.
    3. Sacrificio Consciente (IoC Top-Down): si lee en DimensionActiva la pieza 'Identidad_Narrativa'
       con rol Protector/Altruista en una zona segura, suprime el panico y emite ACC_ESPERAR con sacrificio_consciente=True.
    """

    def __init__(self):
        super().__init__("Comp_ImpulsoS1", "S1")

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        soma = ctx["soma"]
        activa = ctx["activa"]
        sup = onda.reactiva.ev.get("Supervivencia", {}).get("Alarma_Supervivencia")
        if sup is None:
            return False

        propio = next(iter(onda.reactiva.ev.get("Propiocepcion", {}).values()), None)
        adyacentes = list(propio.product.get("nodos_adyacentes", [])) if propio else []
        historial = list(soma.historial_nodos)

        inanicion = bool(sup.product.get("inanicion_critica", False))
        amenaza = sup.product.get("amenaza_inminente")
        nutriente = sup.product.get("mejor_nutriente")

        # Verificar Sacrificio Consciente (Identidad_Narrativa en Memoria Activa)
        id_narrativa = activa.obtener_pieza("IdA", "Identidad_Narrativa")
        if inanicion and id_narrativa is not None:
            rol = str(id_narrativa.product.get("rol", ""))
            en_zona_segura = bool(id_narrativa.product.get("en_zona_segura", False))
            if rol in ("Protector", "Altruista") and en_zona_segura:
                p_sac = Pieza(
                    id="impulso_sacrificio_consciente",
                    tipo_componente="Impulso",
                    arousal=0.95,
                    trust=1.0,
                    product={
                        "comando": V_Comando.ESPERAR,
                        "target": onda.ubicacion_actual,
                        "sacrificio_consciente": True,
                        "arousal_s1_crudo": 0.95,
                    },
                    inputs=["Identidad_Narrativa", self.id_componente],
                )
                self.emitir_impulso(onda, p_sac, coste_amplitud=1)
                return True

        # En inanicion critica con carga no nutritiva: soltar lastre de emergencia
        if inanicion and soma.objeto_cargado is not None:
            es_comida_cargada = bool(soma.objeto_cargado.get("es_nutritivo", False))
            if not es_comida_cargada:
                p_soltar = Pieza(
                    id="impulso_soltar_lastre",
                    tipo_componente="Impulso",
                    arousal=0.96,
                    trust=0.95,
                    product={
                        "comando": V_Comando.SOLTAR,
                        "target": str(soma.objeto_cargado.get("id", "carga")),
                        "soltar_lastre_emergencia": True,
                        "arousal_s1_crudo": 0.96,
                    },
                    inputs=["Alarma_Supervivencia", self.id_componente],
                )
                self.emitir_impulso(onda, p_soltar, coste_amplitud=1)

        # Respuesta ante amenaza inminente (Fight-or-Flight): huir o atacar segun reserva somatica
        if amenaza is not None:
            soma.ciclos_panico += 1
            ar_atacar = 0.94 if (soma.vitalidad >= 60.0 and soma.energia >= 50.0) else 0.85
            p_atacar = Pieza(
                id=f"impulso_atacar_{amenaza}",
                tipo_componente="Impulso",
                arousal=ar_atacar,
                trust=0.86,
                product={
                    "comando": V_Comando.ATACAR,
                    "target": amenaza,
                    "arousal_s1_crudo": ar_atacar,
                },
                inputs=[amenaza, self.id_componente],
            )
            self.emitir_impulso(onda, p_atacar, coste_amplitud=1)
            if adyacentes:
                for dest in adyacentes:
                    p_huir = Pieza(
                        id=f"impulso_mover_{dest}",
                        tipo_componente="Impulso",
                        arousal=0.92,
                        trust=0.85,
                        product={
                            "comando": V_Comando.MOVER,
                            "target": dest,
                            "motivo": "evasion_amenaza",
                            "arousal_s1_crudo": 0.92,
                        },
                        inputs=[amenaza, self.id_componente],
                    )
                    self.emitir_impulso(onda, p_huir, coste_amplitud=1)
        else:
            soma.ciclos_panico = max(0, soma.ciclos_panico - 1)

        # Impulso apetitivo sobre nutriente visible
        if nutriente is not None:
            ar_nutri = 0.95 if inanicion else max(0.45, (100.0 - soma.alimentacion) / 100.0)
            p_deg = Pieza(
                id=f"impulso_nutriente_{nutriente}",
                tipo_componente="Impulso",
                arousal=ar_nutri,
                trust=0.80,
                product={
                    "comando": V_Comando.DEGLUTIR,
                    "target": nutriente,
                    "arousal_s1_crudo": ar_nutri,
                },
                inputs=[nutriente, self.id_componente],
            )
            self.emitir_impulso(onda, p_deg, coste_amplitud=1)

        # Exploracion espacial con Anti-Backtracking Instintivo en inanicion
        ultimos_dos = set(historial[-3:-1]) if len(historial) >= 3 else set()
        for dest in adyacentes:
            ar_mov = 0.75 if (inanicion and nutriente is None) else 0.35
            if inanicion and dest in ultimos_dos and len(adyacentes) > 1:
                ar_mov = 0.0  # Anti-Backtracking: penaliza a 0 volver a los 2 ultimos nodos visitados
            p_mov = Pieza(
                id=f"impulso_mover_{dest}",
                tipo_componente="Impulso",
                arousal=ar_mov,
                trust=0.75,
                product={
                    "comando": V_Comando.MOVER,
                    "target": dest,
                    "anti_backtracking_aplicado": (ar_mov == 0.0),
                    "arousal_s1_crudo": ar_mov,
                },
                inputs=["Alarma_Supervivencia", self.id_componente],
            )
            self.emitir_impulso(onda, p_mov, coste_amplitud=1)

        return True


def crear_sistema_s1(matriz_hebbiana: MatrizHebbianaTresFactores) -> SistemaCognitivoTriunico:
    s1 = SistemaCognitivoTriunico("S1", cuota_frecuencia_ratio=0.25)
    s1.inyectar_componente("SENTIR", CompImagenS1(matriz_hebbiana))
    s1.inyectar_componente("INTERPRETAR", CompSupervivenciaS1())
    s1.inyectar_componente("REACCIONAR", CompImpulsoS1())
    return s1
