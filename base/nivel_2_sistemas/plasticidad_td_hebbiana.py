from typing import Dict, List
import numpy as np


class MatrizHebbianaTresFactores:
    """
    Aprendizaje Hebbiano de 3 Factores (Pre-sinaptico * Post-sinaptico * Dopamina_RPE)
    sobre el Tensor Sensorial 6D [x0..x5] hacia 4 canales de valoracion ontologica:
    - Columna 0: Nutricion (ES_NUTRITIVO)
    - Columna 1: Letalidad / Peligro (ES_LETAL)
    - Columna 2: Armonia / Estetica (ES_ARMONICO)
    - Columna 3: Misterio / Epistemologia (HIPOTESIS / VERIFICACION)
    """

    def __init__(self, tasa_aprendizaje: float = 0.06):
        self.lr = tasa_aprendizaje
        # Pesos iniciales W (6x4) biologicamente sintonizados pero 100% plasticos
        self.W = np.array(
            [
                [0.25, 0.15, 0.10, 0.15],  # x0: Proximidad / Inminencia
                [0.20, 0.08, 0.15, 0.25],  # x1: Magnitud / Densidad
                [0.10, 0.12, 0.05, 0.10],  # x2: Gradiente / Cinematica
                [0.05, 0.08, 0.10, 0.65],  # x3: Entropia / Complejidad
                [0.85, 0.01, 0.45, 0.20],  # x4: Afinidad Nutricional
                [0.02, 0.92, 0.02, 0.15],  # x5: Nocicepcion / Toxicidad
            ],
            dtype=np.float64,
        )

    def evaluar_tensor_6d(self, tensor_6d: np.ndarray) -> Dict[str, float]:
        x = np.clip(np.asarray(tensor_6d, dtype=np.float64).flatten()[:6], 0.0, 1.0)
        y = np.clip(x @ self.W, 0.0, 1.0)
        return {
            "score_nutritivo": float(y[0]),
            "score_letal": float(y[1]),
            "score_armonico": float(y[2]),
            "score_epistemico": float(y[3]),
        }

    def actualizar_hebbiano_3_factores(
        self, tensor_pre_6d: np.ndarray, canal_post_idx: int, delta_dopamina_rpe: float
    ) -> None:
        """
        Regla de 3 factores: Delta_W_ij = lr * Pre_i * Post_j * tanh(delta_RPE / 25.0)
        Si delta_RPE < 0 (intoxicacion visceral), refuerza la columna de letalidad (idx=1) y deprime nutricion (idx=0).
        """
        x_pre = np.clip(np.asarray(tensor_pre_6d, dtype=np.float64).flatten()[:6], 0.0, 1.0)
        mod_rpe = float(np.tanh(delta_dopamina_rpe / 25.0))
        post_vec = np.zeros(4, dtype=np.float64)
        post_vec[canal_post_idx] = 1.0

        delta_w = self.lr * np.outer(x_pre, post_vec) * mod_rpe
        self.W = np.clip(self.W + delta_w, 0.01, 1.50)


class MotorTDLambda:
    """Aprendizaje por Diferencias Temporales TD(lambda) con trazas de elegibilidad sobre pesos sinapticos."""

    def __init__(self, alpha: float = 0.08, gamma: float = 0.90, lam: float = 0.70):
        self.alpha = alpha
        self.gamma = gamma
        self.lam = lam
        self.valor_estado: float = 0.0
        self.trazas: Dict[str, float] = {}

    def actualizar_pesos_componentes(
        self, recompensa: float, componentes: List, ids_activados: set
    ) -> float:
        delta_td = recompensa + self.gamma * self.valor_estado - self.valor_estado
        self.valor_estado += 0.10 * delta_td
        for comp in componentes:
            e_prev = self.trazas.get(comp.id_componente, 0.0)
            act = 1.0 if comp.id_componente in ids_activados else 0.0
            e_nueva = self.gamma * self.lam * e_prev + act
            self.trazas[comp.id_componente] = e_nueva
            comp.peso_sinaptico = float(np.clip(comp.peso_sinaptico + self.alpha * delta_td * e_nueva, 0.1, 5.0))
        return float(delta_td)

