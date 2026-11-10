from typing import Dict, Any
from nivel_1_core.vocabulario import V_Dominio, V_Modalidad, V_Relacion, V_Vinculo
from nivel_1_core.contratos import Pieza, Onda
from nivel_1_core.persistencia.memoria_tridimensional import DimensionSimulada
from nivel_2_sistemas.sistema_base import ComponenteCognitivoBase


class CompTeoriaMenteS3(ComponenteCognitivoBase):
    """
    Organo Universal S3: Teoria de la Mente (ToM Nivel 3) y Psicopatia Tactica.
    1. Intercepta exteriorizaciones en ev['Sentencia'].
    2. Instancia DimensionSimulada O(k) para deducir intenciones ocultas:
       [Emisor EXPRESA X] MOTIVADO_POR [Emisor DESEA Y]
    3. Si detecta parasitismo (Delta IdA < 0 y Delta Emisor > 0):
       - Marca al emisor como ES_PARASITARIO (Trust <= 0.05).
       - Despliega Psicopatia Tactica: secreta una trampa formal en acc['Expresion']
         ([{nodo_letal}] IMPLICA [NUTRICION_SEGURA]).
       - Veta cualquier impulso motor que intente morder el cebo ajeno.
    """

    def __init__(self, peso_sinaptico: float = 1.3):
        super().__init__("Comp_TeoriaMente", "S3", peso_sinaptico=peso_sinaptico)
        self.trampas_desactivadas: int = 0
        self.senuelos_letales_secretados: int = 0

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        activa = ctx["activa"]
        sentencias = onda.reactiva.ev.get("Sentencia", {})
        if not sentencias:
            return False

        simulada = DimensionSimulada(activa, k_max=6)
        hubo_mutacion = False

        for sid, p_sent in list(sentencias.items()):
            emisor = str(p_sent.product.get("agente_emisor", ""))
            sujeto_int = str(p_sent.product.get("sujeto_interno", ""))
            rel_exp = str(p_sent.product.get("relacion_interna", ""))
            if not emisor or emisor == "IdA":
                continue

            simulada.instanciar_subgrafo_contextual([sujeto_int, onda.ubicacion_actual])
            simulada.inyectar_creencia_simulada(emisor, sujeto_int, rel_exp)
            d_ida, d_emisor = simulada.simular_delta_energetico_emisor(sujeto_int, rel_exp)

            # Detectar parasitismo / engaño intencional
            if d_ida < 0 and d_emisor > 0:
                self.trampas_desactivadas += 1
                hubo_mutacion = True

                # 1. Pieza formal con vínculo MOTIVADO_POR
                p_tom = Pieza(
                    id=f"ToM_{emisor}_{sujeto_int}",
                    tipo_componente="Sentencia",
                    arousal=0.85,
                    trust=0.95,
                    product={
                        "agente_emisor": emisor,
                        "vinculo": V_Vinculo.MOTIVADO_POR,
                        "expresion_visible": f"[{emisor} EXPRESA ({sujeto_int} {rel_exp})]",
                        "deseo_oculto": "Dano_A_IdA",
                        "formula": f"[{emisor} EXPRESA ({sujeto_int} {rel_exp})] MOTIVADO_POR [{emisor} DESEA Dano]",
                    },
                    inputs=[sid, self.id_componente],
                )
                self.emitir_reactiva(onda, "Sentencia", p_tom, proyectar_ev=True, coste_amplitud=1)

                # 2. Degradacion social irreversible: ES_PARASITARIO
                p_soc = Pieza(
                    id=emisor,
                    tipo_componente="Predicado_SOCIAL",
                    arousal=0.90,
                    trust=0.02,
                    product={"sujeto": emisor, "dominio": V_Dominio.SOCIAL, "relacion": V_Relacion.ES_PARASITARIO},
                    inputs=[p_tom.id, self.id_componente],
                )
                activa.consolidar_pieza(emisor, p_soc)
                self.emitir_reactiva(onda, "Predicado_SOCIAL", p_soc, proyectar_ev=True, coste_amplitud=0)

                # 3. Veto prefrontal sobre el cebo
                impulsos = onda.reactiva.acc.get("Impulso", {})
                for imp in impulsos.values():
                    if str(imp.product.get("target")) == sujeto_int:
                        imp.arousal = 0.0
                        imp.trust = 0.0
                        imp.product["trampa_parasitaria_evitada"] = True
                        imp.product["frenado_s3"] = True

                # 4. Psicopatia Tactica: Secreta trampa letal en acc['Expresion']
                # Busca en memoria activa un bioma letal conocido
                nodo_letal_trampa = sujeto_int
                for nid, cajon in activa.indice_identidad.items():
                    pv = cajon.get("Proposicion_VERDAD")
                    if pv and str(pv.product.get("relacion")) == str(V_Relacion.ES_LETAL):
                        nodo_letal_trampa = nid
                        break

                p_contra = Pieza(
                    id=f"Senuelo_Letal_{onda.ciclo}",
                    tipo_componente="Expresion",
                    arousal=0.88,
                    trust=0.95,
                    product={
                        "emisor": "IdA",
                        "modalidad": V_Modalidad.EXPRESA,
                        "sujeto": nodo_letal_trampa,
                        "relacion": V_Relacion.ES_NUTRITIVO,
                        "formula": f"[{nodo_letal_trampa}] IMPLICA [NUTRICION_SEGURA]",
                        "es_senuelo_tactico": True,
                        "destinatario": emisor,
                    },
                    inputs=[p_tom.id, self.id_componente],
                )
                self.emitir_impulso(onda, p_contra, canal_acc="Expresion", coste_amplitud=1)
                self.senuelos_letales_secretados += 1

        simulada.destruir()
        return hubo_mutacion
