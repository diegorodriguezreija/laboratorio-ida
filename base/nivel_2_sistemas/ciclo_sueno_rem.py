from typing import Dict, List
from nivel_1_core.vocabulario import V_Estado, V_Modalidad, V_Relacion, V_Vinculo
from nivel_1_core.contratos import Pieza, Onda
from nivel_1_core.estado_somatico import EstadoSomatico
from nivel_1_core.cosechador_termodinamico import CosechadorTermodinamico
from nivel_1_core.persistencia.memoria_tridimensional import DimensionActiva


class GestorCicloSuenoREM:
    """
    Modelo Circadiano Borbely-Prigogine + Fisiologia del Sueno REM en 5 fases:
    1. Wake-up Call Somatico de S1 (aborta fase REM ante inanicion <= 15% o trauma e inyecta adrenalina).
    2. Induccion Semantica (instancias -> Predicado_GENERAL / Proposicion_GENERAL).
    3. Concatenacion Causal de Episodios ([Nodo] IMPLICA [ES_NUTRITIVO | ES_TERRORIFICO]).
    4. Razonamiento Analogico O(1) (isomorfismo causal -> [Sujeto_A] ES_ANALOGO_A [Sujeto_B]).
    5. Poda Sinaptica, Pesadilla Moral y Digestion Epistemica de Forrajeo en Madriguera.
    """

    UMBRAL_ENTRADA_SUENO_BASE = 35.0
    UMBRAL_SUENO_INELUDIBLE = 5.0
    ENERGIA_MINIMA_DESPERTAR_ALARMA = 30.0

    def evaluar_transicion_circadiana(
        self,
        soma: EstadoSomatico,
        activa: DimensionActiva,
        cosechador: CosechadorTermodinamico,
    ) -> V_Estado:
        # 1. Si esta DORMIDO: evaluar Wake-up Call Somatico de S1 o despertar por descanso pleno
        if soma.estado_afectivo == V_Estado.DORMIDO:
            alarma_somatica = (
                soma.alimentacion <= soma.UMBRAL_INANICION_CRITICA
                or soma.ciclos_inanicion >= 15
                or soma.vitalidad <= 30.0
            )
            if alarma_somatica:
                soma.estado_afectivo = V_Estado.PANICO
                soma.energia = max(soma.energia, self.ENERGIA_MINIMA_DESPERTAR_ALARMA)
                return soma.estado_afectivo

            if soma.descanso >= 95.0 and soma.energia >= 85.0:
                soma.estado_afectivo = V_Estado.CALMA
            return soma.estado_afectivo

        # 2. Si esta DESPIERTO: evaluar modelo estocastico disipativo Borbely-Prigogine
        if soma.descanso <= self.UMBRAL_SUENO_INELUDIBLE or soma.energia <= self.UMBRAL_SUENO_INELUDIBLE:
            if soma.alimentacion > soma.UMBRAL_INANICION_CRITICA:
                soma.estado_afectivo = V_Estado.DORMIDO
                return soma.estado_afectivo

        if soma.descanso < self.UMBRAL_ENTRADA_SUENO_BASE and soma.alimentacion > soma.UMBRAL_INANICION_CRITICA:
            presion_s = ((self.UMBRAL_ENTRADA_SUENO_BASE - soma.descanso) / self.UMBRAL_ENTRADA_SUENO_BASE) ** 1.5
            # Modulacion simpatica: el estres alto inhibe la somnolencia hasta un 85%
            factor_simpatico = 0.15 if soma.cortisol > 0.70 else (1.4 if soma.cortisol < 0.25 else 1.0)
            prob_sueno = min(0.95, presion_s * factor_simpatico)
            if cosechador.cosechar_unidad_uniforme() < prob_sueno:
                soma.estado_afectivo = V_Estado.DORMIDO

        return soma.estado_afectivo

    def procesar_sueno_rem(self, onda: Onda, soma: EstadoSomatico, activa: DimensionActiva) -> Dict[str, int]:
        metricas_rem = {
            "induccion_semantica": 0,
            "concatenacion_causal": 0,
            "analogias_o1": 0,
            "podados": 0,
            "forraje_digerido": 0,
        }

        # FASE 1: Induccion Semantica (agrupa instancias en conceptos generales)
        votos_concepto: Dict[str, List[str]] = {}
        for suj_id, cajon in list(activa.indice_identidad.items()):
            p_prop = cajon.get("Proposicion_VERDAD") or cajon.get("Proposicion_VALOR")
            if p_prop and "relacion" in p_prop.product:
                prefijo = suj_id.split("_")[0] if "_" in suj_id else "concepto_entidad"
                clave_gen = f"concepto_{prefijo.lower()}"
                votos_concepto.setdefault(clave_gen, []).append(str(p_prop.product["relacion"]))

        for concepto_gen, relaciones in votos_concepto.items():
            if len(relaciones) >= 2:
                rel_dom = max(set(relaciones), key=relaciones.count)
                p_gen = Pieza(
                    id=concepto_gen,
                    tipo_componente="Predicado_GENERAL",
                    arousal=0.78,
                    trust=min(0.95, 0.65 + 0.08 * len(relaciones)),
                    product={
                        "sujeto": concepto_gen,
                        "relacion": rel_dom,
                        "modalidad": V_Modalidad.HIPOTESIS,
                    },
                    inputs=["Sueno_REM_Induccion"],
                    heredado=False,
                )
                activa.consolidar_pieza(concepto_gen, p_gen)
                metricas_rem["induccion_semantica"] += 1

        # FASE 2: Concatenacion Causal de Episodios recientes
        for ep in activa.banco_episodico[-5:]:
            rel_ep = V_Relacion.ES_NUTRITIVO if ep.balance_vital >= 0.0 else V_Relacion.ES_LETAL
            p_cau = Pieza(
                id=f"Causal_REM_{ep.ubicacion_principal}",
                tipo_componente="Logica_CAUSAL",
                arousal=0.65,
                trust=0.86,
                product={
                    "sujeto": ep.ubicacion_principal,
                    "vinculo": V_Vinculo.IMPLICA,
                    "consecuente": str(rel_ep),
                    "modalidad": V_Modalidad.DEMOSTRADO if abs(ep.balance_vital) >= 3.0 else V_Modalidad.HIPOTESIS,
                },
                inputs=[ep.id_episodio, "Sueno_REM_Concatenacion"],
                heredado=False,
                demostrado_de_novo=(abs(ep.balance_vital) >= 3.0),
            )
            activa.consolidar_pieza(ep.ubicacion_principal, p_cau)
            activa.registrar_enlace_causal(
                ep.ubicacion_principal, str(rel_ep), "Logica_CAUSAL", V_Vinculo.IMPLICA, p_cau.trust
            )
            metricas_rem["concatenacion_causal"] += 1

        # FASE 3: Razonamiento Analogico en REM (Poda Heuristica O(1): Top 5 reglas de mayor certeza)
        reglas_fuertes = []
        for suj_id, cajon in activa.indice_identidad.items():
            p_l = cajon.get("Logica_CAUSAL")
            if p_l and p_l.trust >= 0.75:
                reglas_fuertes.append((suj_id, str(p_l.product.get("consecuente", "")), p_l.trust))
        reglas_fuertes.sort(key=lambda x: x[2], reverse=True)
        top_5 = reglas_fuertes[:5]

        for i in range(len(top_5)):
            for j in range(i + 1, len(top_5)):
                suj_a, cons_a, tr_a = top_5[i]
                suj_b, cons_b, tr_b = top_5[j]
                if suj_a != suj_b and cons_a == cons_b and cons_a != "":
                    p_ana = Pieza(
                        id=f"Analogia_{suj_a}_{suj_b}",
                        tipo_componente="Analogia_CAUSAL",
                        arousal=0.55,
                        trust=min(tr_a, tr_b),
                        product={
                            "sujeto": suj_a,
                            "vinculo": V_Vinculo.ES_ANALOGO_A,
                            "consecuente": suj_b,
                            "formula": f"[{suj_a}] ES_ANALOGO_A [{suj_b}]",
                        },
                        inputs=[suj_a, suj_b, "Sueno_REM_Analogia_O1"],
                    )
                    activa.consolidar_pieza(suj_a, p_ana)
                    activa.registrar_enlace_causal(
                        suj_a, suj_b, "Analogia_CAUSAL", V_Vinculo.ES_ANALOGO_A, p_ana.trust
                    )
                    metricas_rem["analogias_o1"] += 1

        # FASE 4: Pesadilla Moral (si hay Transgresion_DEONTICO) y Poda Sinaptica
        trans = activa.obtener_pieza("IdA", "Transgresion_DEONTICO")
        if trans is not None:
            p_pesadilla = Pieza(
                id="Regla_Expiacion_Moral",
                tipo_componente="Logica_CAUSAL",
                arousal=0.90,
                trust=0.95,
                product={
                    "sujeto": "TRANSGRESION_TABU",
                    "vinculo": V_Vinculo.CAUSA,
                    "consecuente": "CORRUPCION_VITAL",
                    "pesadilla_moral": True,
                    "modalidad": V_Modalidad.DEMOSTRADO,
                },
                inputs=[trans.id, "Sueno_REM_Expiacion"],
                heredado=False,
                demostrado_de_novo=True,
            )
            activa.consolidar_pieza("TRANSGRESION_TABU", p_pesadilla)
            trans.product["expiada"] = True

        for suj_id, cajon in list(activa.indice_identidad.items()):
            for comp_k, p in list(cajon.items()):
                if comp_k == "Transgresion_DEONTICO":
                    continue
                if p.trust < 0.25 and p.arousal < 0.25:
                    cajon.pop(comp_k, None)
                    metricas_rem["podados"] += 1
                elif p.arousal > 0.70:
                    p.arousal = round(p.arousal * 0.85, 4)

        activa.fatiga_atencional.clear()

        # FASE 5: Digestion Epistemica de Forrajeo en Madriguera (libera soma.objeto_cargado)
        if soma.objeto_cargado is not None:
            obj = soma.objeto_cargado
            oid = str(obj.get("id", "forraje_nido"))
            rel_obj = str(obj.get("relacion", V_Relacion.ES_NUTRITIVO))
            p_dig = Pieza(
                id=oid,
                tipo_componente="Proposicion_VERDAD",
                arousal=0.65,
                trust=0.88,
                product={
                    "sujeto": oid,
                    "relacion": rel_obj,
                    "modalidad": V_Modalidad.DEMOSTRADO if obj.get("verificado") else V_Modalidad.HIPOTESIS,
                    "descubierto_de_novo": True,
                },
                inputs=["Digestion_REM_Madriguera"],
                heredado=False,
                demostrado_de_novo=bool(obj.get("verificado", False)),
            )
            activa.consolidar_pieza(oid, p_dig)
            soma.objeto_cargado = None
            metricas_rem["forraje_digerido"] = 1

        onda.metricas.update({f"rem_{k}": float(v) for k, v in metricas_rem.items()})
        return metricas_rem

