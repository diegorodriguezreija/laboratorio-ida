import asyncio
from typing import Dict, Any, Optional
from nivel_1_core.vocabulario import V_Relacion
from nivel_1_core.contratos import Onda
from nivel_2_sistemas.sistema_base import ComponenteCognitivoBase


class CompImaginacionLLMS3(ComponenteCognitivoBase):
    """
    Organo Universal S3:
    Razonamiento latente no bloqueante (asyncio) ante incertidumbre critica (Proposicion_DUDA).
    Ejecuta consulta a LLM oracular local (o fallback neurosimbolico rapido) y deposita
    el '¡Eureka!' en proactiva.cola_eurekas sin detener jamas el latido de 100 ms.
    """

    def __init__(self, latencia_simulada_ms: float = 15.0, peso_sinaptico: float = 1.2):
        super().__init__("Comp_Imaginacion_LLM", "S3", peso_sinaptico=peso_sinaptico)
        self.latencia_ms = latencia_simulada_ms
        self.eurekas_generados: int = 0
        self._tarea_activa: Optional[asyncio.Task] = None

    async def procesar_proactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        proactiva = ctx["proactiva"]
        dudas = onda.reactiva.ev.get("Proposicion_DUDA", {})
        if not dudas:
            return False

        # Si ya hay un eureka o tarea en vuelo, no saturar
        if self._tarea_activa is not None and not self._tarea_activa.done():
            return False

        target_duda = next(iter(dudas.values()))
        sujeto = target_duda.id

        async def _inferir_eureka():
            if self.latencia_ms > 0:
                await asyncio.sleep(self.latencia_ms / 1000.0)
            # Fallback deductivo/probabilistico de alta certidumbre
            tensor = target_duda.tensor_sensorial
            if tensor is not None and tensor[5] > 0.65:
                rel = V_Relacion.ES_LETAL
            else:
                rel = V_Relacion.ES_NUTRITIVO

            proactiva.cola_eurekas.append({
                "sujeto": sujeto,
                "relacion": rel,
                "trust": 0.88,
                "latido_origen": onda.ciclo,
            })
            self.eurekas_generados += 1

        self._tarea_activa = asyncio.create_task(_inferir_eureka())
        return True

