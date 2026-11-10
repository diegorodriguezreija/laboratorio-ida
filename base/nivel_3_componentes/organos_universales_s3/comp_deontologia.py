from typing import Dict, Any, List, Optional
from nivel_1_core.vocabulario import V_Comando, V_Dominio, V_Relacion, V_Vinculo
from nivel_1_core.contratos import Pieza, Onda
from nivel_2_sistemas.sistema_base import ComponenteCognitivoBase


class CompDeontologiaS3(ComponenteCognitivoBase):
    """
    Organo Universal S3: Normas de Linaje, Tabues y Veto Deontico.
    1. Audita los impulsos motores pendientes frente a prescripciones de linaje (ES_TABU / NO_DEBE).
    2. En abundancia / calma (Alimentacion > 15.0):
       - Aplica Veto Moral riguroso (Arousal = 0.0, Trust = 0.0, veto_moral = True, norma_respetada = True).
       - Emite pieza formal Deontologia con vinculo NO_DEBE.
    3. En inanicion critica (Alimentacion <= 15.0):
       - La desesperacion biologica rompe el tabu para sobrevivir; S3 no veta.
       - Consolida 'Transgresion_DEONTICO' en DimensionActiva.
       - En el siguiente latido, S2 detecta la transgresion y desata V_Estado.CULPA
         (drenando -1.0 Vit/latido y -1.5 descanso hasta su expiacion en sueno REM).
    """

    def __init__(self, tabues_iniciales: Optional[List[str]] = None, peso_sinaptico: float = 1.4):
        super().__init__("Comp_Deontologia", "S3", peso_sinaptico=peso_sinaptico)
        self.tabues: set = set(tabues_iniciales or ["nucleo_sagrado", "espora_ancestral", "recurso_sagrado"])

    def agregar_tabu(self, id_entidad: str) -> None:
        self.tabues.add(id_entidad)

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        soma = ctx["soma"]
        activa = ctx["activa"]
        impulsos = onda.reactiva.acc.get("Impulso", {})

        hubo_intervencion = False
        for imp in impulsos.values():
            cmd = imp.product.get("comando")
            target = str(imp.product.get("target", ""))

            # Comprobar si el objetivo es un tabu de linaje
            es_objetivo_tabu = target in self.tabues or any(t in target.lower() for t in self.tabues)
            if not es_objetivo_tabu:
                continue

            hubo_intervencion = True
            # Condicion 1: En abundancia / calma (Alimentacion > 15.0): VETO MORAL PREFRONTAL
            if soma.alimentacion > soma.UMBRAL_INANICION_CRITICA:
                imp.arousal = 0.0
                imp.trust = 0.0
                imp.product["veto_moral"] = True
                imp.product["norma_respetada"] = True
                imp.sistemas_participantes.add("S3")

                p_norma = Pieza(
                    id=f"Deontologia_{target}",
                    tipo_componente="Deontologia",
                    arousal=0.85,
                    trust=1.0,
                    product={
                        "dominio": V_Dominio.DEONTICO,
                        "vinculo": V_Vinculo.NO_DEBE,
                        "sujeto": "IdA",
                        "accion_prohibida": str(cmd),
                        "entidad_tabu": target,
                        "formula": f"[LINAJE IMPONE_NORMA]: [IdA] NO_DEBE [{cmd}({target})]",
                    },
                    inputs=[imp.id, self.id_componente],
                )
                self.emitir_reactiva(onda, "Deontologia", p_norma, proyectar_ev=True, coste_amplitud=1)

            # Condicion 2: En inanicion critica (Alimentacion <= 15.0): QUIEBRE DEONTICO POR SUPERVIVENCIA
            else:
                # S3 permite la transgresion por desesperacion somatica pero la registra como deuda moral
                p_trans = Pieza(
                    id="Transgresion_DEONTICO",
                    tipo_componente="Transgresion_DEONTICO",
                    arousal=0.95,
                    trust=1.0,
                    product={
                        "entidad": target,
                        "comando": str(cmd),
                        "ciclo": onda.ciclo,
                        "expiada": False,
                    },
                    inputs=[imp.id, self.id_componente],
                )
                activa.consolidar_pieza("IdA", p_trans)
                self.emitir_reactiva(onda, "Deontologia", p_trans, proyectar_ev=True, coste_amplitud=1)

        return hubo_intervencion

