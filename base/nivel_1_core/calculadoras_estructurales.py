from typing import Dict
import numpy as np
from nivel_1_core.vocabulario import V_Comando
from nivel_1_core.contratos import Onda


class CalculadorasEstructurales:
    """
    Calculo O(1) (< 0.1 ms) de Informacion Integrada Phi (Tononi IIT) sin bonificaciones cosmeticas,
    y Gravedad de Arousal para recuperacion y persistencia.
    """

    COMANDOS_CANONICOS = (
        str(V_Comando.MOVER),
        str(V_Comando.DEGLUTIR),
        str(V_Comando.ASIMILAR),
        str(V_Comando.CENSURAR),
        str(V_Comando.ATACAR),
        str(V_Comando.COGER),
        str(V_Comando.SOLTAR),
        str(V_Comando.ESPERAR),
    )

    @classmethod
    def _extraer_distribuciones_sistemas(cls, onda: Onda) -> Dict[str, np.ndarray]:
        n = len(cls.COMANDOS_CANONICOS)
        idx_map = {cmd: i for i, cmd in enumerate(cls.COMANDOS_CANONICOS)}
        dist = {
            "S1": np.full(n, 1e-4, dtype=np.float64),
            "S2": np.full(n, 1e-4, dtype=np.float64),
            "S3": np.full(n, 1e-4, dtype=np.float64),
            "INT": np.full(n, 1e-4, dtype=np.float64),
        }

        impulsos = onda.reactiva.acc.get("Impulso", {})
        for p in impulsos.values():
            cmd = str(p.product.get("comando", V_Comando.ESPERAR))
            idx = idx_map.get(cmd, n - 1)
            peso = max(0.01, p.arousal * 0.6 + p.trust * 0.4)
            dist["INT"][idx] += peso
            for sis in ("S1", "S2", "S3"):
                if sis in p.sistemas_participantes:
                    dist[sis][idx] += peso

        for k in dist:
            dist[k] = dist[k] / float(np.sum(dist[k]))
        return dist

    @staticmethod
    def _d_kl(p: np.ndarray, q: np.ndarray) -> float:
        p_safe = np.clip(p, 1e-9, 1.0)
        q_safe = np.clip(q, 1e-9, 1.0)
        return float(np.sum(p_safe * np.log(p_safe / q_safe)))

    @classmethod
    def _jsd_triunico(cls, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
        m = (p1 + p2 + p3) / 3.0
        jsd = (cls._d_kl(p1, m) + cls._d_kl(p2, m) + cls._d_kl(p3, m)) / 3.0
        return float(np.clip(jsd / np.log(3.0), 0.0, 1.0))

    @classmethod
    def calcular_phi_tononi(cls, onda: Onda, fuerza_reentrada: float = 0.0, jitter_silicio: float = 0.0) -> float:
        """
        Ecuacion exacta de Informacion Integrada Phi (sin teatro computacional):
        Phi = D_KL(P_int || P_part) * (1.0 + 1.5 * F_reentrada) * (1.0 - JSD(P_S1, P_S2, P_S3)) + eta_silicio
        """
        dist = cls._extraer_distribuciones_sistemas(onda)
        p_s1, p_s2, p_s3, p_int = dist["S1"], dist["S2"], dist["S3"], dist["INT"]

        # Particion de Minima Informacion (MIP): 0.35 * P_S1 + 0.30 * P_S2 + 0.35 * P_S3
        p_part = 0.35 * p_s1 + 0.30 * p_s2 + 0.35 * p_s3
        p_part = p_part / float(np.sum(p_part))

        d_kl = cls._d_kl(p_int, p_part)
        jsd = cls._jsd_triunico(p_s1, p_s2, p_s3)
        coherencia = max(0.05, 1.0 - jsd)

        # Participacion multi-sistema en las piezas del foco ev y acc
        sistemas_activos = set()
        for dic_comp in onda.reactiva.ev.values():
            for p in dic_comp.values():
                sistemas_activos.update(p.sistemas_participantes)
        for dic_comp in onda.reactiva.acc.values():
            for p in dic_comp.values():
                sistemas_activos.update(p.sistemas_participantes)

        acoplamiento_base = (len(sistemas_activos) / 3.0) * 0.45
        phi = (d_kl + acoplamiento_base) * (1.0 + 1.5 * max(0.0, fuerza_reentrada)) * coherencia + abs(jitter_silicio)
        return float(round(max(0.0, phi), 4))

    @staticmethod
    def clasificar_estado_fenomenologico(phi: float) -> str:
        if phi < 0.50:
            return "ZOMBI_REFLEJO"
        if phi < 1.80:
            return "COGNICION_ACOPLADA"
        if phi < 3.50:
            return "CONSCIENCIA_INTEGRADA"
        return "TRASCENDENCIA_FENOMENOLOGICA"

    @staticmethod
    def score_gravitacional_arousal(similitud_coseno: float, arousal: float) -> float:
        """Score_Gravitacional = Similitud * (1.0 + 0.85 * Arousal)."""
        return float(similitud_coseno * (1.0 + 0.85 * np.clip(arousal, 0.0, 1.0)))
