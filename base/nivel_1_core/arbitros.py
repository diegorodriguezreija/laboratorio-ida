"""
Módulo de Árbitros Intercambiables de Acción (Nivel 1 Core)
============================================================
Define la interfaz abstracta `ArbitroBase` y sus implementaciones concretas
(A0 a A7) para contrastar formalmente el arbitraje biológico del Tribunal Motor
frente a heurísticas simples de decisión y órdenes fijos de capas.

Arquitectura agnóstica: 100% libre de términos de dominio o mundos externos.
"""

from abc import ABC, abstractmethod
import random
from typing import Any, Dict, List, Optional, Tuple

from nivel_1_core.contratos import Pieza
from nivel_1_core.cosechador_termodinamico import CosechadorTermodinamico
from nivel_1_core.estado_somatico import EstadoSomatico
from nivel_1_core.vocabulario import V_Comando


def identificar_sistema_origen(pieza: Pieza) -> str:
    """Extrae el sistema de origen cognitivo (S1, S2, S3) de una propuesta."""
    sis = str(pieza.product.get("origen_sistema", ""))
    if sis in ("S1", "S2", "S3"):
        return sis
    for sis_tag in ("S3", "S2", "S1"):
        if sis_tag in pieza.sistemas_participantes or sis_tag in pieza.id:
            return sis_tag
    return "S1"


class ArbitroBase(ABC):
    """
    Contrato abstracto para cualquier algoritmo de selección de impulsos motores.
    Recibe el diccionario de impulsos candidatos y el estado somático,
    y devuelve la propuesta ganadora junto con metadatos de auditoría.
    """

    id_arbitro: str = "BASE"
    nombre: str = "Arbitro Base"

    @abstractmethod
    def seleccionar(
        self,
        impulsos: Dict[str, Pieza],
        soma: EstadoSomatico,
        cosechador: Optional[CosechadorTermodinamico] = None,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Pieza], Dict[str, Any]]:
        """
        Selecciona una propuesta ganadora de entre los impulsos disponibles.

        Retorna:
            (pieza_ganadora, metadatos_decision)
        """
        pass


class A0_TribunalMotorDefault(ArbitroBase):
    """
    A0: Tribunal Motor Biológico Canónico.
    - Ponderación de Arousal-Trust modulada por estrés somático (cortisol).
    - Desesperación instintiva en inanición crítica (alimentación <= 15%).
    - Modulación por peso sináptico hebbiano.
    - Bifurcación termodinámica de Prigogine ante empates (|score1 - score2| <= 0.03).
    - Veto prefrontal ante trampas parasitarias o vetos morales probados.
    """

    id_arbitro = "A0"
    nombre = "Tribunal Motor Biológico Canónico"
    EPSILON_PRIGOGINE = 0.03

    def seleccionar(
        self,
        impulsos: Dict[str, Pieza],
        soma: EstadoSomatico,
        cosechador: Optional[CosechadorTermodinamico] = None,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Pieza], Dict[str, Any]]:
        if not impulsos:
            return None, {"motivo": "sin_impulsos", "score": 0.0}

        estres = float(max(0.0, min(1.0, soma.cortisol)))
        en_desesperacion = soma.alimentacion <= soma.UMBRAL_INANICION_CRITICA

        candidatos = []
        for p in impulsos.values():
            es_sacrificio = bool(p.product.get("sacrificio_consciente", False))
            es_veto = bool(p.product.get("trampa_parasitaria_evitada", False)) or bool(
                p.product.get("veto_moral", False)
            )

            arousal_ef = p.arousal
            if en_desesperacion and not es_sacrificio and not es_veto:
                arousal_crudo = float(p.product.get("arousal_s1_crudo", p.arousal))
                arousal_ef = max(arousal_ef, arousal_crudo)

            peso_sin = float(p.product.get("peso_sinaptico", 1.0))
            mod_sinaptico = float(max(0.80, min(1.25, 0.85 + 0.15 * peso_sin)))
            score = ((arousal_ef * estres) + (p.trust * (1.0 - estres))) * mod_sinaptico
            candidatos.append((score, arousal_ef, p))

        candidatos.sort(key=lambda x: x[0], reverse=True)
        mejor_score, _, ganador = candidatos[0]

        hubo_veto = mejor_score <= 0.0 or bool(
            ganador.product.get("veto_moral")
            or ganador.product.get("trampa_parasitaria_evitada")
        )
        if hubo_veto:
            return None, {"motivo": "veto_prefrontal", "score": mejor_score}

        hubo_bifurcacion = False
        if len(candidatos) >= 2 and cosechador is not None:
            seg_score, _, segundo = candidatos[1]
            if abs(mejor_score - seg_score) <= self.EPSILON_PRIGOGINE:
                cosechador.bifurcaciones_totales += 1
                if cosechador.cosechar_unidad_uniforme() >= 0.5:
                    ganador = segundo
                    mejor_score = seg_score
                    hubo_bifurcacion = True

        return ganador, {
            "score": round(mejor_score, 4),
            "estres_utilizado": round(estres, 4),
            "desesperacion_activa": en_desesperacion,
            "bifurcacion_prigogine": hubo_bifurcacion,
        }


class A1_MayorArousal(ArbitroBase):
    """
    A1: Heurística Reactiva Pura.
    Gana la propuesta con mayor arousal numérico. Desempata por trust.
    Ignora cortisol, estrés y pesos sinápticos.
    """

    id_arbitro = "A1"
    nombre = "Mayor Arousal Crudo"

    def seleccionar(
        self,
        impulsos: Dict[str, Pieza],
        soma: EstadoSomatico,
        cosechador: Optional[CosechadorTermodinamico] = None,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Pieza], Dict[str, Any]]:
        if not impulsos:
            return None, {"motivo": "sin_impulsos"}
        ganador = max(impulsos.values(), key=lambda p: (p.arousal, p.trust))
        return ganador, {"arousal": ganador.arousal, "trust": ganador.trust}


class A2_PrioridadFijaS1(ArbitroBase):
    """
    A2: Jerarquía Reactiva Rígida.
    Prioridad estricta S1 > S2 > S3.
    Dentro de la misma capa prioritaria, desempata por mayor arousal.
    """

    id_arbitro = "A2"
    nombre = "Prioridad Fija S1 > S2 > S3"

    def seleccionar(
        self,
        impulsos: Dict[str, Pieza],
        soma: EstadoSomatico,
        cosechador: Optional[CosechadorTermodinamico] = None,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Pieza], Dict[str, Any]]:
        if not impulsos:
            return None, {"motivo": "sin_impulsos"}

        por_sistema: Dict[str, List[Pieza]] = {"S1": [], "S2": [], "S3": []}
        for p in impulsos.values():
            sis = identificar_sistema_origen(p)
            por_sistema[sis].append(p)

        for sis in ("S1", "S2", "S3"):
            if por_sistema[sis]:
                ganador = max(por_sistema[sis], key=lambda p: (p.arousal, p.trust))
                return ganador, {"capa_ganadora": sis, "arousal": ganador.arousal}

        ganador_fallback = max(impulsos.values(), key=lambda p: p.arousal)
        return ganador_fallback, {"capa_ganadora": "fallback"}


class A3_PrioridadFijaS3(ArbitroBase):
    """
    A3: Jerarquía Deliberativa Rígida.
    Prioridad estricta S3 > S2 > S1.
    Dentro de la misma capa, desempata por mayor trust y luego arousal.
    """

    id_arbitro = "A3"
    nombre = "Prioridad Fija S3 > S2 > S1"

    def seleccionar(
        self,
        impulsos: Dict[str, Pieza],
        soma: EstadoSomatico,
        cosechador: Optional[CosechadorTermodinamico] = None,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Pieza], Dict[str, Any]]:
        if not impulsos:
            return None, {"motivo": "sin_impulsos"}

        por_sistema: Dict[str, List[Pieza]] = {"S1": [], "S2": [], "S3": []}
        for p in impulsos.values():
            sis = identificar_sistema_origen(p)
            por_sistema[sis].append(p)

        for sis in ("S3", "S2", "S1"):
            if por_sistema[sis]:
                ganador = max(por_sistema[sis], key=lambda p: (p.trust, p.arousal))
                return ganador, {"capa_ganadora": sis, "trust": ganador.trust}

        ganador_fallback = max(impulsos.values(), key=lambda p: p.trust)
        return ganador_fallback, {"capa_ganadora": "fallback"}


class A4_AleatorioPonderado(ArbitroBase):
    """
    A4: Muestreo Estocástico Proporcional al Arousal.
    Utiliza un generador pseudoaleatorio propio con semilla dedicada
    para garantizar reproducibilidad estricta y aislarse del RNG del kernel y del core.
    """

    id_arbitro = "A4"
    nombre = "Muestreo Aleatorio Ponderado por Arousal"

    def __init__(self, seed_propia: int = 42):
        self.rng = random.Random(seed_propia)

    def resembrar(self, seed: int) -> None:
        self.rng.seed(seed)

    def seleccionar(
        self,
        impulsos: Dict[str, Pieza],
        soma: EstadoSomatico,
        cosechador: Optional[CosechadorTermodinamico] = None,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Pieza], Dict[str, Any]]:
        if not impulsos:
            return None, {"motivo": "sin_impulsos"}

        candidatos = list(impulsos.values())
        pesos = [max(0.01, float(p.arousal)) for p in candidatos]
        total_p = sum(pesos)
        pesos_norm = [w / total_p for w in pesos]

        ganador = self.rng.choices(candidatos, weights=pesos_norm, k=1)[0]
        return ganador, {"arousal": ganador.arousal, "metodo": "estocastico_propio"}


class A5_SoloS1(ArbitroBase):
    """
    A5: Ablación de Capas Superiores (Solo S1 Reactivo).
    Descarta de forma absoluta cualquier propuesta de S2 y S3.
    Si no hay impulsos de S1, no emite acción (espera).
    """

    id_arbitro = "A5"
    nombre = "Solo S1 Reactivo"

    def seleccionar(
        self,
        impulsos: Dict[str, Pieza],
        soma: EstadoSomatico,
        cosechador: Optional[CosechadorTermodinamico] = None,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Pieza], Dict[str, Any]]:
        if not impulsos:
            return None, {"motivo": "sin_impulsos"}

        cands_s1 = [p for p in impulsos.values() if identificar_sistema_origen(p) == "S1"]
        if not cands_s1:
            return None, {"motivo": "sin_propuestas_s1"}

        ganador = max(cands_s1, key=lambda p: (p.arousal, p.trust))
        return ganador, {"capa_ganadora": "S1", "arousal": ganador.arousal}


class A6_SoloS3(ArbitroBase):
    """
    A6: Ablación de Capas Inferiores (Solo S3 Deliberativo).
    Descarta cualquier propuesta reactiva de S1 y límbica de S2.
    Si no hay impulsos de S3, no emite acción (espera).
    """

    id_arbitro = "A6"
    nombre = "Solo S3 Deliberativo"

    def seleccionar(
        self,
        impulsos: Dict[str, Pieza],
        soma: EstadoSomatico,
        cosechador: Optional[CosechadorTermodinamico] = None,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Pieza], Dict[str, Any]]:
        if not impulsos:
            return None, {"motivo": "sin_impulsos"}

        cands_s3 = [p for p in impulsos.values() if identificar_sistema_origen(p) == "S3"]
        if not cands_s3:
            return None, {"motivo": "sin_propuestas_s3"}

        ganador = max(cands_s3, key=lambda p: (p.trust, p.arousal))
        return ganador, {"capa_ganadora": "S3", "trust": ganador.trust}


class A7_MayorProducto(ArbitroBase):
    """
    A7: Multiplicación Estática Arousal x Trust.
    Evalúa la congruencia estática sin considerar el cortisol ni el estrés somático.
    """

    id_arbitro = "A7"
    nombre = "Mayor Producto Arousal x Trust (Sin Soma)"

    def seleccionar(
        self,
        impulsos: Dict[str, Pieza],
        soma: EstadoSomatico,
        cosechador: Optional[CosechadorTermodinamico] = None,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Pieza], Dict[str, Any]]:
        if not impulsos:
            return None, {"motivo": "sin_impulsos"}

        ganador = max(
            impulsos.values(),
            key=lambda p: (float(p.arousal) * float(p.trust), p.arousal),
        )
        prod = round(float(ganador.arousal) * float(ganador.trust), 4)
        return ganador, {"producto": prod}


REGISTRO_ARBITROS: Dict[str, type] = {
    "A0": A0_TribunalMotorDefault,
    "A1": A1_MayorArousal,
    "A2": A2_PrioridadFijaS1,
    "A3": A3_PrioridadFijaS3,
    "A4": A4_AleatorioPonderado,
    "A5": A5_SoloS1,
    "A6": A6_SoloS3,
    "A7": A7_MayorProducto,
}


def crear_arbitro(arbitro_id: str, **kwargs) -> ArbitroBase:
    """Factoría universal de árbitros para experimentos de ablación."""
    aid = arbitro_id.upper()
    if aid not in REGISTRO_ARBITROS:
        raise ValueError(
            f"Árbitro '{arbitro_id}' desconocido. Disponibles: {list(REGISTRO_ARBITROS.keys())}"
        )
    cls = REGISTRO_ARBITROS[aid]
    return cls(**kwargs)
