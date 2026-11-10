from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import numpy as np
from nivel_1_core.vocabulario import V_Estado, V_Comando
from nivel_1_core.contratos import Pieza, ResultadoEfectoEntorno


@dataclass
class EstadoSomatico:
    """
    Chasis Somatico Localizado Cuatripartito y Tridimensionalidad Metabolica (Rescate v11.7).
    Separa el Wanting (Dopamina RPE) del Liking (Opioides/Placer) segun Berridge-Schultz.
    """
    integridad: Dict[str, float] = field(default_factory=lambda: {
        "core": 100.0,
        "locomocion": 100.0,
        "fauces": 100.0,
        "sensores": 100.0,
    })
    alimentacion: float = 85.0
    energia: float = 90.0
    descanso: float = 95.0
    dopamina: float = 35.0          # [0.0, 100.0] Basal 35.0 (Wanting / RPE)
    placer: float = 20.0            # [0.0, 100.0] Opioides endogenos (Liking / Saciedad)
    cortisol: float = 0.05          # [0.0, 1.0] Nivel de estres somatico
    autoestima_cognitiva: float = 0.85  # [0.20, 1.00]
    edad_biologica: float = 0.0     # [0.0, 1.0]
    ciclos_inanicion: int = 0
    ciclos_panico: int = 0
    estado_afectivo: V_Estado = V_Estado.CALMA
    objeto_cargado: Optional[Dict[str, Any]] = None
    bocado_reciente: Optional[str] = None
    historial_nodos: List[str] = field(default_factory=list)

    # Constantes fisiologicas canonicas
    UMBRAL_INANICION_CRITICA: float = 15.0
    UMBRAL_HAMBRE_MODERADA: float = 45.0
    UMBRAL_PANICO_ESTRES: float = 0.80
    DOPAMINA_BASAL: float = 35.0
    TASA_RETORNO_DOPAMINA: float = 0.18
    UMBRAL_SACIEDAD_OPIOIDE: float = 60.0
    COSTE_DESPLAZAMIENTO_BASAL: float = 3.0
    COSTE_FALLO_SOMATICO: float = 1.0

    @property
    def vitalidad(self) -> float:
        """Vitalidad ponderada: 40% core, 20% locomocion, 20% fauces, 20% sensores."""
        return float(
            0.40 * self.integridad["core"]
            + 0.20 * self.integridad["locomocion"]
            + 0.20 * self.integridad["fauces"]
            + 0.20 * self.integridad["sensores"]
        )

    @vitalidad.setter
    def vitalidad(self, nuevo_valor: float) -> None:
        actual = self.vitalidad
        objetivo = float(np.clip(nuevo_valor, 0.0, 100.0))
        if actual <= 0.0:
            for k in self.integridad:
                self.integridad[k] = objetivo
        else:
            ratio = objetivo / actual
            for k in self.integridad:
                self.integridad[k] = float(np.clip(self.integridad[k] * ratio, 0.0, 100.0))

    @property
    def esta_vivo(self) -> bool:
        return self.integridad["core"] > 0.0 and self.vitalidad > 0.0

    def factor_coste_cinetico(self) -> float:
        """Deterioro de locomocion multiplica el coste de ACC_MOVER (cojera fisica)."""
        return 1.0 + (100.0 - self.integridad["locomocion"]) / 50.0

    def probabilidad_ruido_sensorial(self) -> float:
        """Deterioro de sensores (< 80) inyecta ruido perceptual."""
        if self.integridad["sensores"] >= 80.0:
            return 0.0
        return float((80.0 - self.integridad["sensores"]) / 80.0)

    def factor_ingesta_fauces(self) -> float:
        """Deterioro de fauces reduce la tasa de ingesta por bocado en ACC_DEGLUTIR."""
        return float(max(0.2, self.integridad["fauces"] / 100.0))

    def actualizar_dopamina_rpe(self, delta_rpe: float) -> float:
        """
        Actualiza la dopamina estriatal con el Error de Prediccion de Recompensa (delta = R - E[R])
        y aplica decaimiento exponencial hacia el nivel tonico basal (35.0) con tasa 0.18.
        """
        self.dopamina = float(np.clip(
            self.dopamina + delta_rpe - self.TASA_RETORNO_DOPAMINA * (self.dopamina - self.DOPAMINA_BASAL),
            0.0,
            100.0,
        ))
        return self.dopamina

    def inyectar_placer_opioide(self, delta_placer: float) -> None:
        """
        Incrementa opioides endogenos (Liking). Cuando placer >= 60.0 induce relajacion
        parasimpatica y purga cortisol sin acelerar ciegamente el motor.
        """
        self.placer = float(np.clip(self.placer + delta_placer, 0.0, 100.0))
        if self.placer >= self.UMBRAL_SACIEDAD_OPIOIDE:
            self.cortisol = float(max(0.05, self.cortisol * 0.45))
            self.ciclos_inanicion = max(0, self.ciclos_inanicion - 2)

    def aplicar_metabolismo_latido(self, ciclo_actual: int, max_latidos: int = 500) -> None:
        """Ejecuta el desgaste metabolico circadiano, lastre de carga, toxina de culpa y sanacion tisular."""
        es_dormido = self.estado_afectivo == V_Estado.DORMIDO

        if es_dormido:
            self.energia = float(min(100.0, self.energia + 15.0))
            self.descanso = float(min(100.0, self.descanso + 25.0))
            # Cicatrizacion tisular profunda en Sueno REM (+2.5 a cada subsistema si alimentacion >= 25)
            if self.alimentacion >= 25.0:
                for k in self.integridad:
                    self.integridad[k] = float(min(100.0, self.integridad[k] + 2.5))
        else:
            # Desgaste basal en vigilia
            desgaste_ali = 0.8 + (0.5 if self.objeto_cargado is not None else 0.0)
            self.alimentacion = float(max(0.0, self.alimentacion - desgaste_ali))
            self.descanso = float(max(0.0, self.descanso - 0.36))
            if self.alimentacion > 20.0:
                self.energia = float(min(100.0, self.energia + 0.6))
            else:
                self.energia = float(max(0.0, self.energia - 1.2))

            # Sanacion tisular reversible en Vigilia Calma (alimentacion >= 65 y descanso >= 65: +1.5)
            if self.alimentacion >= 65.0 and self.descanso >= 65.0:
                for k in self.integridad:
                    self.integridad[k] = float(min(100.0, self.integridad[k] + 1.5))

        # Control de inanicion y cortisol
        if self.alimentacion <= self.UMBRAL_INANICION_CRITICA:
            self.ciclos_inanicion += 1
            self.cortisol = float(min(1.0, self.cortisol + 0.08))
            if self.alimentacion <= 0.0:
                self.integridad["core"] = float(max(0.0, self.integridad["core"] - 2.0))
        else:
            self.ciclos_inanicion = 0
            self.cortisol = float(max(0.05, self.cortisol - 0.03))

        # Toxina psicosomatica de la CULPA (-1.0 Vit/latido, -1.5 descanso, autoestima a 0.20)
        if self.estado_afectivo == V_Estado.CULPA:
            for k in self.integridad:
                self.integridad[k] = float(max(0.0, self.integridad[k] - 1.0))
            self.descanso = float(max(0.0, self.descanso - 1.5))
            self.autoestima_cognitiva = 0.20

        # Decaimiento natural del placer opioide y retorno tonico de dopamina
        self.placer = float(max(0.0, self.placer - 1.2))
        self.actualizar_dopamina_rpe(0.0)

        # Edad biologica no lineal
        self.edad_biologica = float(np.clip(
            (ciclo_actual / max(1, max_latidos))
            + (self.ciclos_inanicion * 0.003)
            + ((100.0 - self.vitalidad) * 0.002),
            0.0,
            1.0,
        ))

    def aplicar_consecuencia_fisica(self, res: ResultadoEfectoEntorno) -> None:
        """Aplica al chasis las consecuencias devueltas por el IActuadorEntorno."""
        self.bocado_reciente = None
        if not res.exito:
            self.energia = float(max(0.0, self.energia - self.COSTE_FALLO_SOMATICO))
            return

        if res.comando == V_Comando.MOVER and res.nueva_ubicacion:
            coste_mov = self.COSTE_DESPLAZAMIENTO_BASAL * self.factor_coste_cinetico()
            self.energia = float(max(0.0, self.energia - coste_mov * 0.35))
            self.historial_nodos.append(res.nueva_ubicacion)
            if len(self.historial_nodos) > 10:
                self.historial_nodos = self.historial_nodos[-10:]

        self.alimentacion = float(np.clip(self.alimentacion + res.delta_alimentacion, 0.0, 100.0))
        self.energia = float(np.clip(self.energia + res.delta_energia, 0.0, 100.0))

        for sub, delta in res.dano_subsistemas.items():
            if sub in self.integridad:
                self.integridad[sub] = float(np.clip(self.integridad[sub] + delta, 0.0, 100.0))

        # Intoxicacion visceral aguda por agente nocivo (-14 core, -10 fauces, -8 ali, placer=0, dopamina -35)
        if res.intoxicacion_aguda:
            self.integridad["core"] = float(max(0.0, self.integridad["core"] - 14.0))
            self.integridad["fauces"] = float(max(0.0, self.integridad["fauces"] - 10.0))
            self.alimentacion = float(max(0.0, self.alimentacion - 8.0))
            self.placer = 0.0
            self.actualizar_dopamina_rpe(-35.0)
            self.cortisol = float(min(1.0, self.cortisol + 0.35))
        elif res.comando == V_Comando.DEGLUTIR and res.delta_alimentacion > 0:
            bono_opioide = 6.0 + (14.0 if res.recurso_agotado else 0.0)
            self.inyectar_placer_opioide(bono_opioide)
            self.actualizar_dopamina_rpe(12.0)

        if res.bocado_contenido:
            self.bocado_reciente = res.bocado_contenido

        if res.comando == V_Comando.COGER and res.objeto_cargado is not None:
            self.objeto_cargado = res.objeto_cargado
        elif res.comando == V_Comando.SOLTAR:
            self.objeto_cargado = None

    def emitir_piezas_interoceptivas(
        self, ef_previo_intero: Dict[str, Pieza], jitter_termico: float = 0.0
    ) -> Dict[str, Pieza]:
        """Genera las Piezas interoceptivas con sus deltas respecto al latido t-1."""
        constantes = {
            "vitalidad": self.vitalidad,
            "energia": self.energia,
            "alimentacion": self.alimentacion,
            "descanso": self.descanso,
            "dopamina": self.dopamina,
            "placer": self.placer,
        }
        piezas: Dict[str, Pieza] = {}
        for nombre, val in constantes.items():
            prev_val = val
            if nombre in ef_previo_intero:
                prev_val = float(ef_previo_intero[nombre].product.get("valor", val))
            delta = val - prev_val
            arousal_base = max(0.0, min(1.0, (100.0 - val) / 100.0 + jitter_termico))
            piezas[nombre] = Pieza(
                id=nombre,
                tipo_componente="Interocepcion",
                arousal=arousal_base,
                trust=1.0,
                product={
                    "valor": round(val, 3),
                    "delta": round(delta, 3),
                    "inanicion_critica": self.alimentacion <= self.UMBRAL_INANICION_CRITICA,
                    "integridad": dict(self.integridad),
                    "edad_biologica": round(self.edad_biologica, 4),
                    "autoestima": round(self.autoestima_cognitiva, 4),
                    "estres": round(self.cortisol, 4),
                },
                inputs=["EstadoSomatico"],
            )
        if self.objeto_cargado is not None:
            piezas["carga_fisica"] = Pieza(
                id="carga_fisica",
                tipo_componente="Interocepcion",
                arousal=0.35,
                trust=1.0,
                product={"objeto_cargado": dict(self.objeto_cargado), "lastre_metabolico": -0.5},
                inputs=["EstadoSomatico"],
            )
        if self.bocado_reciente is not None:
            piezas["bocado_digestivo"] = Pieza(
                id="bocado_digestivo",
                tipo_componente="Ingestion",
                arousal=0.65,
                trust=0.90,
                product={"contenido": self.bocado_reciente},
                inputs=["EstadoSomatico"],
            )
        return piezas

