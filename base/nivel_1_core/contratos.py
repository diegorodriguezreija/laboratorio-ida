from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Dict, List, Any, Optional, Tuple, Protocol, runtime_checkable
import numpy as np
import time
from nivel_1_core.vocabulario import V_Comando, V_Modalidad


class LatidoAgotadoException(Exception):
    """Guillotina Computacional disparada cuando el reloj supera frecuencia_max_ms o la Amplitud se agota."""
    pass


@dataclass
class Arquetipo:
    """Genoma fenotipico Big Five con marcadores epigeneticos transgeneracionales y cadena de ancestros."""
    nombre: str = "Explorador_Natal"
    id_individuo: str = "Gen1_001"
    id_padre: Optional[str] = None
    linaje: str = "Linaje_Alfa"
    generacion: int = 1
    ancestros: List[str] = field(default_factory=list)
    apertura: float = 0.65
    responsabilidad: float = 0.60
    extraversion: float = 0.55
    amabilidad: float = 0.60
    neuroticismo: float = 0.45
    umbral_miedo: float = 0.65
    tasa_olvido: float = 0.05
    vinculo_base: str = "NEUTRO"
    marcadores_epigeneticos: Dict[str, float] = field(default_factory=dict)

    def mutar(self, nuevo_id: str, perfil_afectivo: Optional[Dict[str, float]] = None) -> "Arquetipo":
        perf = perfil_afectivo or {}
        f_estres = perf.get("fraccion_estres", 0.0)
        f_hambre = perf.get("fraccion_hambre", 0.0)
        f_armonia = perf.get("fraccion_armonia", 0.0)

        # Reversion parcial (50%) de marcas previas + nuevo delta acotado a +-0.03
        d_neur = float(np.clip((f_estres + f_hambre) * 0.03 - f_armonia * 0.02, -0.03, 0.03))
        d_resp = float(np.clip(f_hambre * 0.03, -0.03, 0.03))
        d_aper = float(np.clip(f_armonia * 0.03 - f_estres * 0.02, -0.03, 0.03))
        d_mied = float(np.clip(f_estres * 0.02 - f_armonia * 0.02, -0.03, 0.03))

        nuevos_ancestros = list(self.ancestros)
        if self.id_individuo not in nuevos_ancestros:
            nuevos_ancestros.append(self.id_individuo)

        return Arquetipo(
            nombre=self.nombre,
            id_individuo=nuevo_id,
            id_padre=self.id_individuo,
            linaje=self.linaje,
            generacion=self.generacion + 1,
            ancestros=nuevos_ancestros,
            apertura=float(np.clip(0.5 * self.apertura + 0.5 * 0.60 + d_aper, 0.20, 0.80)),
            responsabilidad=float(np.clip(0.5 * self.responsabilidad + 0.5 * 0.60 + d_resp, 0.20, 0.80)),
            extraversion=float(np.clip(self.extraversion, 0.20, 0.80)),
            amabilidad=float(np.clip(self.amabilidad, 0.20, 0.80)),
            neuroticismo=float(np.clip(0.5 * self.neuroticismo + 0.5 * 0.45 + d_neur, 0.20, 0.80)),
            umbral_miedo=float(np.clip(0.5 * self.umbral_miedo + 0.5 * 0.65 + d_mied, 0.20, 0.80)),
            tasa_olvido=self.tasa_olvido,
            vinculo_base=self.vinculo_base,
            marcadores_epigeneticos={
                "delta_neuroticismo": d_neur,
                "delta_responsabilidad": d_resp,
                "delta_apertura": d_aper,
                "delta_miedo": d_mied,
            },
        )


@dataclass
class Pieza:
    """El Atomo Neurosimbolico Universal de IdA v12.0."""
    id: str                                         # ID de la entidad, nodo topologico o concepto abstracto
    tipo_componente: str                            # Ej: "Imagen", "Concepto", "Sujeto", "Predicado_VALOR", "Proposicion_VERDAD", "Sentencia", "Logica_CAUSAL", "Impulso"
    arousal: float                                  # [0.0, 1.0] Saliencia / Urgencia somatica y atencional
    trust: float                                    # [0.0, 1.0] Certeza epistemica o confianza acumulada
    tensor_sensorial: Optional[np.ndarray] = None   # Vector 6D [0,1]^6 para piezas sensoriales/conceptuales
    product: Dict[str, Any] = field(default_factory=dict)  # Atributos formales (V_Dominio, V_Modalidad, V_Relacion, V_Vinculo, etc.)
    inputs: List[str] = field(default_factory=list)        # Trazabilidad causal obligatoria (IDs/clases antecedentes que justifican el porque)
    heredado: bool = False                          # True si proviene del acervo ancestral; False si es descubierto de novo
    demostrado_de_novo: bool = False                # Gameto fertil cuando Modalidad == DEMOSTRADO y heredado == False
    sistemas_participantes: set = field(default_factory=set)  # {"S1", "S2", "S3"} para calculo real de Phi
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self.arousal = float(np.clip(self.arousal, 0.0, 1.0))
        self.trust = float(np.clip(self.trust, 0.0, 1.0))
        if self.tensor_sensorial is not None:
            t_arr = np.clip(np.asarray(self.tensor_sensorial, dtype=np.float64), 0.0, 1.0)
            if t_arr.shape != (6,):
                t_arr = np.resize(t_arr, (6,))
            self.tensor_sensorial = t_arr
        modalidad = self.product.get("modalidad")
        if str(modalidad) in (str(V_Modalidad.DEMOSTRADO), str(V_Modalidad.DEMOSTRADO_DEDUCTIVO)) and not self.heredado and self.trust >= 0.85:
            self.demostrado_de_novo = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tipo_componente": self.tipo_componente,
            "arousal": round(self.arousal, 4),
            "trust": round(self.trust, 4),
            "tensor_sensorial": self.tensor_sensorial.tolist() if self.tensor_sensorial is not None else None,
            "product": {k: (str(v) if hasattr(v, "value") else v) for k, v in self.product.items()},
            "inputs": list(self.inputs),
            "heredado": self.heredado,
            "demostrado_de_novo": self.demostrado_de_novo,
            "sistemas_participantes": list(self.sistemas_participantes),
            "created": self.created,
            "updated": self.updated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pieza":
        t_sens = data.get("tensor_sensorial")
        return cls(
            id=data["id"],
            tipo_componente=data.get("tipo_componente", "Pieza"),
            arousal=float(data.get("arousal", 0.5)),
            trust=float(data.get("trust", 0.5)),
            tensor_sensorial=np.array(t_sens, dtype=np.float64) if t_sens is not None else None,
            product=dict(data.get("product", {})),
            inputs=list(data.get("inputs", [])),
            heredado=bool(data.get("heredado", False)),
            demostrado_de_novo=bool(data.get("demostrado_de_novo", False)),
            sistemas_participantes=set(data.get("sistemas_participantes", [])),
            created=float(data.get("created", time.time())),
            updated=float(data.get("updated", time.time())),
        )


class DimensionReactiva:
    """
    Gobierna el Cuarteto de la Experiencia en cada latido (100 ms):
    - ei (Estado Inicial): Read-only (MappingProxyType) congelado a partir del 'ef' del latido N-1.
    - ef (Estado Fisiologico): Registro universal de coste 0. Todo componente escribe aqui siempre.
    - ev (Eventos / Foco Atencional): Percepcion e interpretacion consciente. PAGA PEAJE DE AMPLITUD.
    - acc (Accion Latente): Canal comun competitivo de impulsos motores ('Impulso') y expresiones ('Expresion'). PAGA PEAJE DE AMPLITUD.
    """

    def __init__(self, ef_anterior: Optional[Dict[str, Dict[str, Pieza]]] = None):
        estado_previo = ef_anterior if ef_anterior is not None else {}
        self.ei: MappingProxyType = MappingProxyType({
            comp: MappingProxyType(dict(piezas)) for comp, piezas in estado_previo.items()
        })
        self.ev: Dict[str, Dict[str, Pieza]] = {}
        self.acc: Dict[str, Dict[str, Pieza]] = {}
        self.ef: Dict[str, Dict[str, Pieza]] = {}

    def registrar_ef_universal(self, nombre_componente: str, pieza: Pieza) -> None:
        """Garantia de Nivel 1: Todo estado generado se registra siempre en 'ef' a coste metabolico 0."""
        self.ef.setdefault(nombre_componente, {})[pieza.id] = pieza

    def proyectar_atencion_ev(self, nombre_componente: str, pieza: Pieza, onda_ref: "Onda", coste_amplitud: int = 1) -> None:
        """Proyecta la pieza al foco consciente 'ev' cobrando peaje de Amplitud."""
        self.registrar_ef_universal(nombre_componente, pieza)
        onda_ref.control_vital(coste_amplitud)
        self.ev.setdefault(nombre_componente, {})[pieza.id] = pieza

    def converger_impulso_acc(self, tipo_canal: str, pieza: Pieza, onda_ref: "Onda", coste_amplitud: int = 1) -> None:
        """
        Deposita o modula una tendencia motora en acc['Impulso'] o acc['Expresion'].
        Aqui convergen S1, S2 y S3 sin condicionales despoticos.
        """
        self.registrar_ef_universal(tipo_canal, pieza)
        onda_ref.control_vital(coste_amplitud)
        self.acc.setdefault(tipo_canal, {})[pieza.id] = pieza


@dataclass
class Episodio:
    """Arco narrativo multi-onda consolidado por Keyframing de Arousal o Sorpresa."""
    id_episodio: str
    ubicacion_principal: str
    ciclo_inicio: int
    ciclo_fin: int = 0
    balance_vital: float = 0.0
    resuelto: bool = False
    ondas_resumen: List[Dict[str, Any]] = field(default_factory=list)
    piezas_clave: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Onda:
    """Paquete cuantico temporal de 100 ms que transporta la DimensionReactiva a traves de S1 -> S2 -> S3."""
    ciclo: int
    amplitud_max: int = 100
    frecuencia_max_ms: float = 100.0
    ubicacion_actual: str = "NODO_ORIGEN"
    ef_anterior: Optional[Dict[str, Dict[str, Pieza]]] = None
    priors_talamocorticales: Dict[str, Any] = field(default_factory=dict)
    tiempo_inicio: float = field(default_factory=time.perf_counter)
    amplitud_consumida: int = 0
    guillotina_disparada: bool = False
    motivo_guillotina: str = ""
    metricas: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.reactiva = DimensionReactiva(self.ef_anterior)

    def ms_transcurridos(self) -> float:
        return (time.perf_counter() - self.tiempo_inicio) * 1000.0

    def ms_restantes(self) -> float:
        return max(0.0, self.frecuencia_max_ms - self.ms_transcurridos())

    def amplitud_restante(self) -> int:
        return max(0, self.amplitud_max - self.amplitud_consumida)

    def verificar_guillotina_frecuencia(self, contexto: str = "") -> None:
        if self.ms_restantes() <= 0.0:
            raise LatidoAgotadoException(
                f"GUILLOTINA DE FRECUENCIA [{contexto}]: superado limite de {self.frecuencia_max_ms:.2f} ms."
            )

    def control_vital(self, coste_amplitud: int = 1, contexto: str = "") -> None:
        """Factura el peaje metabolico de Amplitud y verifica la Guillotina de Frecuencia."""
        self.verificar_guillotina_frecuencia(contexto=contexto)
        if coste_amplitud > 0:
            if self.amplitud_consumida + coste_amplitud > self.amplitud_max:
                self.amplitud_consumida = self.amplitud_max
                raise LatidoAgotadoException(
                    f"GUILLOTINA DE AMPLITUD [{contexto}]: agotada capacidad {self.amplitud_max}."
                )
            self.amplitud_consumida += coste_amplitud


@dataclass
class ResultadoEfectoEntorno:
    """Consecuencia fisica devuelta por el mundo tras ejecutar un V_Comando."""
    exito: bool
    comando: V_Comando
    target: str
    nueva_ubicacion: Optional[str] = None
    delta_alimentacion: float = 0.0
    delta_energia: float = 0.0
    dano_subsistemas: Dict[str, float] = field(default_factory=dict)  # ej: {"core": -14.0, "fauces": -10.0}
    intoxicacion_aguda: bool = False
    bocado_contenido: Optional[str] = None
    recurso_agotado: bool = False
    objeto_cargado: Optional[Dict[str, Any]] = None
    verdad_verificada: Optional[Dict[str, Any]] = None  # ej: {"sujeto": id, "relacion": V_Relacion.ES_NUTRITIVO}


@runtime_checkable
class ISensorEntorno(Protocol):
    """Puerto de entrada inyectado desde Nivel 3 hacia el Core."""
    def percibir_mundo(self) -> Tuple[str, List[Pieza], List[str]]:
        """
        Retorna:
        - id_nodo_actual (str)
        - lista de Piezas de escena con su tensor_sensorial 6D en [0, 1]^6
        - lista de ids de nodos adyacentes alcanzables
        """
        ...


@runtime_checkable
class IActuadorEntorno(Protocol):
    """Puerto de salida inyectado desde Nivel 3 hacia el TribunalMotor del Core."""
    def ejecutar_comando_fisico(
        self, comando: V_Comando, target: str, factor_fauces: float = 1.0, payload_extra: Optional[Dict[str, Any]] = None
    ) -> ResultadoEfectoEntorno:
        """Materializa fisicamente un V_Comando en el mundo y devuelve las consecuencias somaticas."""
        ...
