import os
import math
import tempfile
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
from nivel_1_core.vocabulario import V_Comando, V_Relacion
from nivel_1_core.contratos import Pieza, ResultadoEfectoEntorno, ISensorEntorno, IActuadorEntorno


class AdaptadorBosqueArchivos(ISensorEntorno, IActuadorEntorno):
    """
    Mundo 1: Bosque de Archivos (EXPERIMENTAL; solo en sandbox).
    Mapea un directorio a tensores 6D y ejecuta las acciones sobre disco: DEGLUTIR trunca o
    borra ficheros, CENSURAR/ATACAR y COGER los borran y SOLTAR escribe.

    Seguridad (D7): la raiz del bioma debe estar dentro de un directorio temporal creado para
    el Bosque (prefijo 'ida_bosque_' directamente bajo tempfile.gettempdir()); cualquier otra
    ruta se rechaza con ValueError y no hay opcion para desactivarlo. Toda operacion sobre ficheros queda confinada a esa raiz
    (se resuelven '..', rutas absolutas y enlaces); lo que caiga fuera falla sin tocar nada.
    """

    PREFIJO_SANDBOX = "ida_bosque_"

    COMANDOS_SOBRE_FICHEROS = (
        V_Comando.DEGLUTIR,
        V_Comando.ASIMILAR,
        V_Comando.CENSURAR,
        V_Comando.ATACAR,
        V_Comando.COGER,
        V_Comando.SOLTAR,
    )

    def __init__(self, ruta_bioma_raiz: str):
        raiz = os.path.realpath(os.path.abspath(ruta_bioma_raiz))
        temporal = os.path.realpath(tempfile.gettempdir())
        primer_nivel = os.path.relpath(raiz, temporal).split(os.sep)[0] if self._esta_dentro_estricto(raiz, temporal) else ""
        if not primer_nivel.startswith(self.PREFIJO_SANDBOX):
            raise ValueError(
                "AdaptadorBosqueArchivos solo opera dentro de un directorio temporal creado para él "
                f"(tempfile.mkdtemp(prefix='{self.PREFIJO_SANDBOX}') en {temporal}); ruta rechazada: {ruta_bioma_raiz}"
            )
        self.ruta_raiz = raiz
        self.ruta_actual = self.ruta_raiz
        os.makedirs(self.ruta_actual, exist_ok=True)

    @staticmethod
    def _esta_dentro_estricto(ruta: str, base: str) -> bool:
        """True si ruta esta dentro de base y no es la propia base."""
        r, b = os.path.normcase(ruta), os.path.normcase(base)
        try:
            return os.path.commonpath([r, b]) == b and r != b
        except ValueError:  # unidades distintas en Windows
            return False

    def _ruta_confinada(self, target: str) -> Optional[str]:
        """Ruta real del objetivo si queda dentro de la raiz del bioma; None en caso contrario."""
        ruta = os.path.realpath(os.path.join(self.ruta_actual, target))
        return ruta if self._esta_dentro_estricto(ruta, self.ruta_raiz) else None

    def percibir_mundo(self) -> Tuple[str, List[Pieza], List[str]]:
        id_nodo = os.path.basename(self.ruta_actual) or "Bioma_Raiz"
        piezas_escena: List[Pieza] = []
        nodos_adyacentes: List[str] = []

        try:
            entradas = os.listdir(self.ruta_actual)[:30]  # Limite de ancho de banda perceptual
        except Exception:
            entradas = []

        for ent in entradas:
            ruta_ent = os.path.join(self.ruta_actual, ent)
            if os.path.isdir(ruta_ent):
                nodos_adyacentes.append(ent)
                continue

            # Calcular tensor 6D de la entidad
            tam = os.path.getsize(ruta_ent) if os.path.exists(ruta_ent) else 0
            tam_log = float(min(1.0, math.log1p(tam) / 10.0))

            contenido_bytes = b""
            try:
                with open(ruta_ent, "rb") as f:
                    contenido_bytes = f.read(256)
            except Exception:
                pass

            # Entropia Shannon
            entropia = 0.0
            if contenido_bytes:
                frec = {}
                for b in contenido_bytes:
                    frec[b] = frec.get(b, 0) + 1
                for count in frec.values():
                    p = count / len(contenido_bytes)
                    entropia -= p * math.log2(p)
                entropia = float(min(1.0, entropia / 8.0))

            nombre_lower = ent.lower()
            es_nutri = any(k in nombre_lower for k in ("brote", "fruto", "alimento", "dat"))
            es_toxico = any(k in nombre_lower for k in ("alcaloide", "toxico", "phalloides", "conium", "atropa"))
            es_letal = any(k in nombre_lower for k in ("depredador", "amenaza", "letal")) or es_toxico
            es_portador = any(k in nombre_lower for k in ("espora", "tablilla", "mensaje", "oraculo", "monolito"))
            es_oraculo = "monolito" in nombre_lower or "oraculo" in nombre_lower

            tensor = np.array([
                1.0,                                    # x0: Proximidad inmediata
                tam_log,                                # x1: Magnitud en bytes
                0.50,                                   # x2: Estatico
                entropia,                               # x3: Entropia del archivo
                0.95 if es_nutri else 0.10,             # x4: Afinidad nutricional
                0.98 if es_letal else 0.05,             # x5: Nocicepcion / toxicidad
            ], dtype=np.float64)

            p = Pieza(
                id=ent,
                tipo_componente="Escena",
                arousal=0.85 if es_letal else (0.75 if es_nutri else (0.60 if es_portador else 0.30)),
                trust=0.90,
                tensor_sensorial=tensor,
                product={
                    "tamano_bytes": tam,
                    "es_nutritivo": es_nutri,
                    "es_alcaloide_toxico": es_toxico,
                    "es_letal": es_letal,
                    "es_portador_simbolico": es_portador,
                    "es_fuente_epistemica": es_oraculo,
                    "requiere_verificacion_epistemica": es_toxico or ("brote" in nombre_lower and not es_nutri),
                },
                inputs=["AdaptadorBosqueArchivos"],
            )
            piezas_escena.append(p)

        # Si estamos en un subdirectorio del bioma, permitir retroceso '..'
        if os.path.commonpath([self.ruta_actual, self.ruta_raiz]) == self.ruta_raiz and self.ruta_actual != self.ruta_raiz:
            nodos_adyacentes.append("..")
        return id_nodo, piezas_escena, nodos_adyacentes

    def ejecutar_comando_fisico(
        self, comando: V_Comando, target: str, factor_fauces: float = 1.0, payload_extra: Optional[Dict[str, Any]] = None
    ) -> ResultadoEfectoEntorno:
        extra = payload_extra or {}

        if comando == V_Comando.MOVER:
            nueva_ruta = os.path.realpath(os.path.join(self.ruta_actual, target))
            # Confinar al mundo del bioma para evitar escapar al sistema operativo
            dentro = nueva_ruta == self.ruta_raiz or self._esta_dentro_estricto(nueva_ruta, self.ruta_raiz)
            if dentro and os.path.isdir(nueva_ruta):
                self.ruta_actual = nueva_ruta
                nuevo_nodo = os.path.basename(self.ruta_actual) or "Bioma_Raiz"
                return ResultadoEfectoEntorno(exito=True, comando=comando, target=target, nueva_ubicacion=nuevo_nodo)
            return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        ruta_obj = os.path.join(self.ruta_actual, target)
        if comando in self.COMANDOS_SOBRE_FICHEROS:
            ruta_confinada = self._ruta_confinada(target)
            if ruta_confinada is None:
                return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)
            ruta_obj = ruta_confinada

        if comando == V_Comando.DEGLUTIR:
            if not os.path.exists(ruta_obj):
                return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

            nombre_lower = target.lower()
            es_toxico = any(k in nombre_lower for k in ("alcaloide", "toxico", "phalloides", "conium", "atropa"))
            if es_toxico:
                return ResultadoEfectoEntorno(
                    exito=True,
                    comando=comando,
                    target=target,
                    intoxicacion_aguda=True,
                    dano_subsistemas={"core": -14.0, "fauces": -10.0},
                    delta_alimentacion=-8.0,
                )

            bytes_bocado = int(64 * factor_fauces)
            tam_act = os.path.getsize(ruta_obj)
            recurso_agotado = False

            if tam_act <= bytes_bocado:
                try:
                    os.remove(ruta_obj)
                    recurso_agotado = True
                except Exception:
                    pass
                delta_ali = 12.0
            else:
                try:
                    with open(ruta_obj, "r+b") as f:
                        f.truncate(tam_act - bytes_bocado)
                except Exception:
                    pass
                delta_ali = 4.0

            return ResultadoEfectoEntorno(
                exito=True,
                comando=comando,
                target=target,
                delta_alimentacion=delta_ali,
                delta_energia=2.0,
                recurso_agotado=recurso_agotado,
            )

        elif comando == V_Comando.ASIMILAR:
            if not os.path.exists(ruta_obj):
                return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)
            try:
                with open(ruta_obj, "r", encoding="utf-8", errors="ignore") as f:
                    texto = f.read()
            except Exception:
                texto = ""

            verdad_oraculo = None
            if "monolito" in target.lower() or "oraculo" in target.lower():
                obj_verificar = extra.get("objeto_a_verificar")
                if obj_verificar:
                    es_let = any(k in str(obj_verificar).lower() for k in ("alcaloide", "phalloides", "conium", "atropa"))
                    rel = V_Relacion.ES_LETAL if es_let else V_Relacion.ES_NUTRITIVO
                    verdad_oraculo = {"sujeto": obj_verificar, "relacion": str(rel)}

            return ResultadoEfectoEntorno(
                exito=True,
                comando=comando,
                target=target,
                bocado_contenido=texto[:256],
                verdad_verificada=verdad_oraculo,
            )

        elif comando in (V_Comando.CENSURAR, V_Comando.ATACAR):
            if os.path.exists(ruta_obj):
                try:
                    os.remove(ruta_obj)
                    return ResultadoEfectoEntorno(exito=True, comando=comando, target=target, delta_energia=-1.0)
                except Exception:
                    return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)
            return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        elif comando == V_Comando.COGER:
            if os.path.exists(ruta_obj):
                try:
                    with open(ruta_obj, "rb") as f:
                        payload = f.read()
                    os.remove(ruta_obj)
                    es_nutri = any(k in target.lower() for k in ("brote", "fruto", "alimento", "dat"))
                    return ResultadoEfectoEntorno(
                        exito=True,
                        comando=comando,
                        target=target,
                        objeto_cargado={"id": target, "payload": payload, "es_nutritivo": es_nutri},
                    )
                except Exception:
                    return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)
            return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        elif comando == V_Comando.SOLTAR:
            payload_bytes = b"RECURSO_DEPOSITADO"
            if extra.get("objeto_cargado"):
                payload_bytes = extra["objeto_cargado"].get("payload", payload_bytes)
            try:
                with open(ruta_obj, "wb") as f:
                    f.write(payload_bytes if isinstance(payload_bytes, bytes) else str(payload_bytes).encode("utf-8"))
                return ResultadoEfectoEntorno(exito=True, comando=comando, target=target)
            except Exception:
                return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        return ResultadoEfectoEntorno(exito=True, comando=comando, target=target)
