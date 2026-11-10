import os
import time
from typing import List
from nivel_1_core.contratos import Pieza


class CosechadorTermodinamico:
    """
    Extrae micro-jitter fisico de reloj de la CPU en nanosegundos emparejado mediante XOR
    con entropia cuantica/termica del kernel (os.urandom), rompiendo el determinismo de Prigogine.
    """

    def __init__(self, amplitud_basal: float = 0.015):
        self.amplitud_basal = amplitud_basal
        self._ultimo_ns = time.perf_counter_ns()
        self.bifurcaciones_totales: int = 0

    def cosechar_unidad_uniforme(self) -> float:
        """Retorna un escalar fisico real en [0.0, 1.0] desacoplado de random.seed."""
        t0 = time.perf_counter_ns()
        _ = (t0 ^ self._ultimo_ns) * 0x5DEECE66D
        t1 = time.perf_counter_ns()
        delta_ns = abs(t1 - t0) ^ (t1 & 0xFF)
        self._ultimo_ns = t1
        byte_kernel = os.urandom(2)
        semilla_fisica = ((byte_kernel[0] << 8) | byte_kernel[1]) ^ (delta_ns & 0xFFFF)
        return float((semilla_fisica & 0xFFFF) / 65535.0)

    def cosechar_jitter_bipolar(self, factor_escala: float = 1.0) -> float:
        """Retorna fluctuacion termica bipolar en [-amplitud, +amplitud]."""
        u = self.cosechar_unidad_uniforme()
        return float((u * 2.0 - 1.0) * self.amplitud_basal * factor_escala)

    def inyectar_ruido_sensorial(
        self, piezas_escena: List[Pieza], prob_ruido_sensores: float = 0.0, factor_escala: float = 1.0
    ) -> float:
        """Inyecta micro-fluctuacion termodinamica y deterioro de sensores (< 80) sobre los tensores 6D."""
        eta = self.cosechar_jitter_bipolar(factor_escala)
        for p in piezas_escena:
            p.arousal = float(max(0.0, min(1.0, p.arousal + eta)))
            if p.tensor_sensorial is not None and prob_ruido_sensores > 0.0:
                if self.cosechar_unidad_uniforme() < prob_ruido_sensores:
                    ruido_vec = (self.cosechar_unidad_uniforme() - 0.5) * 0.25
                    p.tensor_sensorial = (p.tensor_sensorial + ruido_vec).clip(0.0, 1.0)
        return eta
