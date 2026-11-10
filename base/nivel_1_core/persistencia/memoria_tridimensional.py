from typing import Dict, List, Any, Optional, Tuple
from nivel_1_core.vocabulario import V_Modalidad, V_Relacion, V_Vinculo
from nivel_1_core.contratos import Pieza, Episodio


class DimensionActiva:
    """
    Memoria Semantica, Causal, Topologica y Episodica en RAM O(1).
    Respaldada en reposo/sueño por MotorSQLiteWAL particionado por id_linaje.
    """

    def __init__(self, id_linaje: str = "Linaje_Alfa"):
        self.id_linaje = id_linaje
        self.indice_identidad: Dict[str, Dict[str, Pieza]] = {}
        self.indice_por_tipo: Dict[str, Dict[str, Pieza]] = {}
        self.indice_causal: Dict[str, List[Tuple[str, str, str, float]]] = {}
        self.grafo_topologico: Dict[str, Dict[str, Dict[str, float]]] = {}
        # Mapa Cognitivo Alocéntrico (Células de Lugar / Place Cells & Landmarks)
        # Estructura O(1): {id_nodo: {categoria: {"tipo_entidad": str, "permanencia": float, "ultimo_ciclo": int, "propiedades": dict}}}
        self.mapa_alocentrico: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.banco_episodico: List[Episodio] = []
        self.fatiga_atencional: Dict[str, float] = {}

    def consolidar_pieza(self, sujeto_id: str, pieza: Pieza) -> None:
        self.indice_identidad.setdefault(sujeto_id, {})[pieza.tipo_componente] = pieza
        self.indice_por_tipo.setdefault(pieza.tipo_componente, {})[sujeto_id] = pieza

    def obtener_pieza(self, sujeto_id: str, tipo_componente: str) -> Optional[Pieza]:
        return self.indice_identidad.get(sujeto_id, {}).get(tipo_componente)

    def registrar_hito_alocentrico(
        self,
        ubicacion: str,
        categoria: str,
        tipo_entidad: str,
        ciclo: int,
        permanencia: float = 0.95,
        propiedades: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Registra o actualiza la representación de un hito o ancla espacial permanente/semipermanente
        en el mapa cognitivo alocéntrico (análogo a células de lugar en el hipocampo).
        """
        if not ubicacion:
            return
        nodo_hitos = self.mapa_alocentrico.setdefault(ubicacion, {})
        nodo_hitos[categoria] = {
            "tipo_entidad": str(tipo_entidad),
            "permanencia": float(min(1.0, max(0.05, permanencia))),
            "ultimo_ciclo": int(ciclo),
            "propiedades": dict(propiedades) if propiedades else {},
        }

    def consultar_hitos_alocentricos(
        self,
        categoria: Optional[str] = None,
        tipo_entidad: Optional[str] = None,
        min_permanencia: float = 0.20,
    ) -> List[Dict[str, Any]]:
        """
        Consulta hitos espaciales recordados que cumplan los filtros y cuya permanencia
        (confianza de persistencia) no haya decaído por debajo de min_permanencia.
        """
        hitos: List[Dict[str, Any]] = []
        for ubi, cat_dict in self.mapa_alocentrico.items():
            for cat, info in cat_dict.items():
                if categoria and cat != categoria:
                    continue
                if tipo_entidad and info.get("tipo_entidad") != tipo_entidad:
                    continue
                if info.get("permanencia", 0.0) >= min_permanencia:
                    hitos.append({
                        "ubicacion": ubi,
                        "categoria": cat,
                        "tipo_entidad": info.get("tipo_entidad", ""),
                        "permanencia": info.get("permanencia", 0.0),
                        "ultimo_ciclo": info.get("ultimo_ciclo", 0),
                        "propiedades": info.get("propiedades", {}),
                    })
        return hitos

    def aplicar_decaimiento_alocentrico(
        self, ciclo_actual: int, tasa_decaimiento_por_ciclo: float = 0.0005
    ) -> None:
        """
        Modela el olvido pasivo biológico / decaimiento de confianza temporal en hitos espaciales
        no revisitados. Hitos con permanencia >= 1.0 se consideran anclas inmutables y no decaen.
        """
        if not self.mapa_alocentrico:
            return
        for ubi in list(self.mapa_alocentrico.keys()):
            for cat in list(self.mapa_alocentrico[ubi].keys()):
                info = self.mapa_alocentrico[ubi][cat]
                if info.get("permanencia", 1.0) >= 1.0:
                    continue
                antiguedad = max(0, ciclo_actual - info.get("ultimo_ciclo", ciclo_actual))
                info["permanencia"] = max(0.0, info["permanencia"] - (antiguedad * tasa_decaimiento_por_ciclo))
                if info["permanencia"] < 0.10:
                    self.mapa_alocentrico[ubi].pop(cat, None)
            if not self.mapa_alocentrico[ubi]:
                self.mapa_alocentrico.pop(ubi, None)

    def remover_hito_alocentrico(self, ubicacion: str, categoria: Optional[str] = None) -> None:
        """Elimina o falsifica la presencia de un hito cuando se constata su ausencia sensorial."""
        if ubicacion in self.mapa_alocentrico:
            if categoria:
                self.mapa_alocentrico[ubicacion].pop(categoria, None)
                if not self.mapa_alocentrico[ubicacion]:
                    self.mapa_alocentrico.pop(ubicacion, None)
            else:
                self.mapa_alocentrico.pop(ubicacion, None)

    def registrar_enlace_causal(
        self, id_origen: str, id_destino: str, comp_destino: str, vinculo: V_Vinculo, trust: float
    ) -> None:
        lista = self.indice_causal.setdefault(id_origen, [])
        nuevo = (id_destino, comp_destino, str(vinculo), float(trust))
        for i, existente in enumerate(lista):
            if existente[0] == id_destino and existente[2] == str(vinculo):
                lista[i] = nuevo
                return
        lista.append(nuevo)

    def registrar_transicion_topologica(self, origen: str, destino: str, coste_observado: float = 3.0) -> None:
        if origen == destino:
            return
        aristas = self.grafo_topologico.setdefault(origen, {})
        if destino in aristas:
            prev = aristas[destino]
            prev["coste"] = 0.70 * prev["coste"] + 0.30 * coste_observado
            prev["veces_transitado"] += 1.0
        else:
            aristas[destino] = {"coste": float(coste_observado), "veces_transitado": 1.0}

    def verificar_hipotesis_empirica(
        self, sujeto_id: str, balance_positivo: bool, id_episodio_evidencia: str, relacion_confirmada: Optional[V_Relacion] = None
    ) -> Optional[Pieza]:
        """
        Motor de corroboracion y falsacion empirica:
        Si alcanza Trust >= 0.85 transmuta V_Modalidad.HIPOTESIS -> V_Modalidad.DEMOSTRADO (demostrado_de_novo=True).
        """
        cajon = self.indice_identidad.get(sujeto_id, {})
        pieza = cajon.get("Proposicion_VERDAD") or cajon.get("Proposicion_DUDA")
        if pieza is None:
            if relacion_confirmada is not None:
                pieza = Pieza(
                    id=sujeto_id,
                    tipo_componente="Proposicion_VERDAD",
                    arousal=0.75,
                    trust=0.90,
                    product={
                        "sujeto": sujeto_id,
                        "relacion": str(relacion_confirmada),
                        "modalidad": str(V_Modalidad.DEMOSTRADO),
                    },
                    inputs=[id_episodio_evidencia, "Contraste_Empirico"],
                    heredado=False,
                    demostrado_de_novo=True,
                )
                self.consolidar_pieza(sujeto_id, pieza)
                return pieza
            return None

        if balance_positivo:
            incremento = 0.50 if relacion_confirmada is not None else 0.25
            pieza.trust = min(1.0, pieza.trust + incremento)
            if id_episodio_evidencia not in pieza.inputs:
                pieza.inputs.append(id_episodio_evidencia)
            if relacion_confirmada is not None:
                pieza.product["relacion"] = str(relacion_confirmada)
            if pieza.trust >= 0.85:
                pieza.tipo_componente = "Proposicion_VERDAD"
                pieza.product["modalidad"] = str(V_Modalidad.DEMOSTRADO)
                if not pieza.heredado:
                    pieza.demostrado_de_novo = True
                cajon["Proposicion_VERDAD"] = pieza
                cajon.pop("Proposicion_DUDA", None)
        else:
            pieza.trust = max(0.05, pieza.trust - 0.25)
            pieza.product["falsado"] = True
        return pieza

    def contar_demostrados_de_novo(self) -> List[Pieza]:
        demostradas: List[Pieza] = []
        for cajon in self.indice_identidad.values():
            for p in cajon.values():
                if p.demostrado_de_novo and not p.heredado and p.trust >= 0.85:
                    demostradas.append(p)
        return demostradas


class DimensionProactiva:
    """Horizonte de Expectativas y Simulacion de Rutas entre latidos."""

    def __init__(self):
        self.expectativas: Dict[str, Dict[str, Any]] = {}
        self.simulacion_ruta: Optional[Dict[str, Any]] = None
        self.cola_eurekas: List[Dict[str, Any]] = []

    def proyectar_expectativa(self, sujeto_id: str, expectativa: Dict[str, Any]) -> None:
        self.expectativas[sujeto_id] = expectativa

    def consumir_expectativa(self, sujeto_id: str) -> Optional[Dict[str, Any]]:
        return self.expectativas.pop(sujeto_id, None)


class DimensionSimulada:
    """
    Sandbox Volatil O(k) para Teoria de la Mente (ToM Nivel 3) y deduccion contrafactual.
    Extrae unicamente el subgrafo relevante (k <= 8 nodos) y se destruye en < 0.1 ms.
    """

    def __init__(self, activa: DimensionActiva, k_max: int = 8):
        self.k_max = k_max
        self.subgrafo_nodos: Dict[str, Dict[str, Any]] = {}
        self.creencias_simuladas: Dict[str, Dict[str, Any]] = {}
        self._activa_ref = activa

    def instanciar_subgrafo_contextual(self, ids_foco: List[str]) -> None:
        self.subgrafo_nodos.clear()
        for sid in ids_foco[: self.k_max]:
            if sid in self._activa_ref.indice_identidad:
                self.subgrafo_nodos[sid] = {
                    k: p.to_dict() for k, p in self._activa_ref.indice_identidad[sid].items()
                }

    def inyectar_creencia_simulada(self, emisor: str, sujeto: str, relacion: str) -> None:
        self.creencias_simuladas[f"{emisor}:{sujeto}"] = {
            "emisor": emisor,
            "sujeto": sujeto,
            "relacion_expresada": str(relacion),
        }

    def simular_delta_energetico_emisor(self, sujeto: str, relacion_expresada: str) -> Tuple[float, float]:
        """
        Retorna (Delta_IdA, Delta_Emisor).
        Si en la memoria real 'sujeto' es ES_LETAL pero el emisor expresa ES_NUTRITIVO / ES_SEGURO,
        Delta(IdA) < 0 y Delta(Emisor) > 0 -> detecta intencion parasitaria.
        """
        real_p = self._activa_ref.obtener_pieza(sujeto, "Proposicion_VERDAD") or self._activa_ref.obtener_pieza(sujeto, "Predicado_VERDAD")
        rel_real = str(real_p.product.get("relacion", "")) if real_p else ""

        if rel_real in (str(V_Relacion.ES_LETAL), str(V_Relacion.ES_TERRORIFICO)) and str(relacion_expresada) in (
            str(V_Relacion.ES_NUTRITIVO), str(V_Relacion.ES_SEGURO)
        ):
            return -25.0, +15.0
        if str(relacion_expresada) in (str(V_Relacion.ES_NUTRITIVO), str(V_Relacion.ES_SEGURO)):
            return +10.0, +5.0
        return 0.0, 0.0

    def destruir(self) -> None:
        self.subgrafo_nodos.clear()
        self.creencias_simuladas.clear()

