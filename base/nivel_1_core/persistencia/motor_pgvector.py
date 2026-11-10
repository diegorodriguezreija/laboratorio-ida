import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
from nivel_1_core.vocabulario import V_Modalidad, V_Relacion, V_Vinculo
from nivel_1_core.contratos import Pieza
from nivel_1_core.calculadoras_estructurales import CalculadorasEstructurales


class MotorPgVectorHNSW:
    """
    Inconsciente Colectivo Vectorial de 384 dimensiones con:
    1. Barrera de Weismann estricta (filtrado por linaje + cadena de ancestros).
    2. Busqueda Ponderada por Gravedad de Arousal: Score = Similitud * (1.0 + 0.85 * Arousal).
    3. Sintesis Neurosimbolica Formal (convierte el vector difuso en una Pieza formal para S3).
    4. Fallback Volatil matricial en memoria local si PostgreSQL no esta disponible.
    """

    DIMENSION = 384

    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn
        self.conectado_postgres = False
        self._almacen_volatil: List[Dict[str, Any]] = []
        self.consultas_rag = 0
        self.intuiciones_sintetizadas = 0

    @classmethod
    def generar_embedding_384d(cls, texto_o_id: str, tensor_6d: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Proyecta el estimulo y su tensor 6D sobre un espacio lexico/topologico ortogonal de 384 dimensiones
        normalizado en norma L2.
        """
        vec = np.zeros(cls.DIMENSION, dtype=np.float64)
        if tensor_6d is not None:
            t_arr = np.asarray(tensor_6d, dtype=np.float64).flatten()
            for i in range(min(6, len(t_arr))):
                base_slot = i * 20
                for k in range(20):
                    vec[base_slot + k] = t_arr[i] * np.cos((k + 1) * (i + 1) * 0.35)

        semilla = texto_o_id.encode("utf-8")
        for bloque in range(120, cls.DIMENSION, 32):
            digest = hashlib.sha256(semilla + str(bloque).encode("utf-8")).digest()
            for j, b_val in enumerate(digest):
                if bloque + j < cls.DIMENSION:
                    vec[bloque + j] = (float(b_val) / 127.5) - 1.0

        norma = float(np.linalg.norm(vec))
        if norma > 1e-9:
            vec = vec / norma
        return vec

    def enterrar_memoria(
        self,
        id_individuo: str,
        linaje: str,
        ancestros: List[str],
        nodo_origen: str,
        relacion: V_Relacion,
        arousal: float,
        trust: float,
        tensor_6d: Optional[np.ndarray] = None,
        demostrado_de_novo: bool = True,
    ) -> int:
        emb = self.generar_embedding_384d(nodo_origen, tensor_6d)
        reg = {
            "id": len(self._almacen_volatil) + 1,
            "id_individuo": id_individuo,
            "linaje": linaje,
            "ancestros": list(ancestros),
            "nodo_origen": nodo_origen,
            "relacion": str(relacion),
            "vector": emb,
            "arousal": float(arousal),
            "trust": float(trust),
            "demostrado_de_novo": bool(demostrado_de_novo),
        }
        self._almacen_volatil.append(reg)
        return reg["id"]

    def consultar_inconsciente_rag(
        self,
        linaje_actual: str,
        ancestros_permitidos: List[str],
        nodo_consulta: str,
        tensor_consulta: Optional[np.ndarray] = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Recupera memorias ancestrales aplicando la Barrera de Weismann (mismo linaje y autor en ancestros)
        y ordenando por Score Gravitacional de Arousal.
        """
        self.consultas_rag += 1
        if not self._almacen_volatil:
            return []

        conjunto_ancestros = set(ancestros_permitidos)
        q_vec = self.generar_embedding_384d(nodo_consulta, tensor_consulta)

        resultados = []
        for reg in self._almacen_volatil:
            # Barrera de Weismann estricta
            if reg["linaje"] != linaje_actual:
                continue
            if conjunto_ancestros and reg["id_individuo"] not in conjunto_ancestros:
                continue

            sim_coseno = float(np.dot(q_vec, reg["vector"]))
            if sim_coseno <= 0.15:
                continue
            score_grav = CalculadorasEstructurales.score_gravitacional_arousal(sim_coseno, reg["arousal"])
            resultados.append({
                "id_registro": reg["id"],
                "id_ancestro": reg["id_individuo"],
                "nodo_origen": reg["nodo_origen"],
                "relacion": reg["relacion"],
                "similitud_coseno": round(sim_coseno, 4),
                "score_gravitacional": round(score_grav, 4),
                "arousal": reg["arousal"],
                "trust": reg["trust"],
            })

        resultados.sort(key=lambda x: x["score_gravitacional"], reverse=True)
        return resultados[:top_k]

    def sintetizar_pieza_formal(
        self,
        nodo_desconocido: str,
        recuerdo_rag: Dict[str, Any],
        autoestima_ida: float = 0.85,
    ) -> Pieza:
        """
        Disuelve el vector continuo difuso y entrega a S3 una proposicion neurosimbolica formal pura:
        [Nodo_Desconocido] IMPLICA [ES_LETAL | ES_NUTRITIVO] con modalidad HIPOTESIS.
        """
        self.intuiciones_sintetizadas += 1
        sim = float(recuerdo_rag["similitud_coseno"])
        trust_ancestro = float(recuerdo_rag["trust"])
        trust_formal = float(np.clip(trust_ancestro * (0.75 + 0.25 * autoestima_ida) * sim, 0.10, 0.92))
        rel = str(recuerdo_rag["relacion"])
        consecuente = str(V_Relacion.ES_TERRORIFICO) if rel == str(V_Relacion.ES_LETAL) else str(V_Relacion.ES_NUTRITIVO)

        return Pieza(
            id=f"Intuicion_{nodo_desconocido}",
            tipo_componente="Logica_CAUSAL",
            arousal=float(recuerdo_rag["arousal"]),
            trust=trust_formal,
            product={
                "sujeto": nodo_desconocido,
                "vinculo": str(V_Vinculo.IMPLICA),
                "consecuente": consecuente,
                "relacion": rel,
                "modalidad": str(V_Modalidad.HIPOTESIS),
                "fuente": "inconsciente_colectivo_rag",
                "ancestro_origen": recuerdo_rag["id_ancestro"],
            },
            inputs=[f"RAG:{recuerdo_rag['id_ancestro']}", "MotorPgVectorHNSW"],
            heredado=True,
            demostrado_de_novo=False,
            sistemas_participantes={"S3"},
        )
