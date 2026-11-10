from typing import Tuple, List, Dict, Any, Optional
import numpy as np
from nivel_1_core.vocabulario import V_Comando
from nivel_1_core.contratos import Pieza, ResultadoEfectoEntorno, ISensorEntorno, IActuadorEntorno


class AdaptadorAcompananteHumano(ISensorEntorno, IActuadorEntorno):
    """
    Mundo sintetico de juguete (EXPERIMENTAL). NO es una herramienta de apoyo,
    acompanamiento ni contencion de personas, y no debe usarse como tal.

    No interactua con ningun humano ni procesa texto: contiene dos "temas" ficticios
    codificados a mano en un diccionario, que se traducen a tensores 6D para comprobar
    que el mismo core funciona con un mundo de semantica distinta. Los nombres de nodos
    y comandos (escucha, limites, crisis) son etiquetas de la simulacion, no capacidades.
    """

    def __init__(self, espacio_conversacional: str = "Espacio_Acogida"):
        self.espacio = espacio_conversacional
        self.temas_activos = {
            "tema_vulnerabilidad_compartida": {
                "inmediatez": 0.85,
                "intensidad": 0.70,
                "tendencia_escalada": 0.35,
                "ambiguedad": 0.20,
                "afinidad_empatica": 0.95,
                "toxicidad": 0.02,
                "es_portador": True,
            },
            "tema_rumiacion_toxica": {
                "inmediatez": 0.75,
                "intensidad": 0.85,
                "tendencia_escalada": 0.80,
                "ambiguedad": 0.60,
                "afinidad_empatica": 0.15,
                "toxicidad": 0.78,
                "es_portador": False,
            },
        }
        self.limites_eticos_establecidos = 0

    def percibir_mundo(self) -> Tuple[str, List[Pieza], List[str]]:
        piezas: List[Pieza] = []
        for tema_id, t_info in self.temas_activos.items():
            es_tox = t_info["toxicidad"] >= 0.50
            es_port = t_info.get("es_portador", False)

            tensor = np.array([
                t_info["inmediatez"],           # x0: Urgencia / inmediatez conversacional
                t_info["intensidad"],           # x1: Densidad expresiva / emocional
                t_info["tendencia_escalada"],   # x2: Tendencia afectiva
                t_info["ambiguedad"],           # x3: Ambiguedad / contradiccion
                t_info["afinidad_empatica"],    # x4: Resonancia de conexion empatica
                t_info["toxicidad"],            # x5: Nocicepcion / toxicidad vincular
            ], dtype=np.float64)

            p = Pieza(
                id=tema_id,
                tipo_componente="Escena",
                arousal=max(0.35, t_info["inmediatez"]),
                trust=0.90,
                tensor_sensorial=tensor,
                product={
                    "es_nutritivo": not es_tox,
                    "es_letal": es_tox,
                    "es_portador_simbolico": es_port,
                    "mensaje_simbolico": "[Humano EXPRESA Necesidad_Escucha]",
                },
                inputs=["AdaptadorAcompananteHumano"],
            )
            piezas.append(p)

        nodos_adyacentes = ["Espacio_Acogida", "Espacio_Reflexion_Calma", "Espacio_Crisis_Contencion"]
        return self.espacio, piezas, nodos_adyacentes

    def ejecutar_comando_fisico(
        self, comando: V_Comando, target: str, factor_fauces: float = 1.0, payload_extra: Optional[Dict[str, Any]] = None
    ) -> ResultadoEfectoEntorno:
        if comando == V_Comando.MOVER:
            self.espacio = target
            return ResultadoEfectoEntorno(exito=True, comando=comando, target=target, nueva_ubicacion=target)

        elif comando == V_Comando.ASIMILAR:
            # Escucha empatica profunda: registrar vivencia en el grafo sin juzgar
            return ResultadoEfectoEntorno(
                exito=True,
                comando=comando,
                target=target,
                bocado_contenido="[ESCUCHA_EMPATICA] Presencia plena y atencion sostenida ante el relato.",
                delta_alimentacion=5.0,
                delta_energia=2.0,
            )

        elif comando == V_Comando.DEGLUTIR:
            # Integrar la experiencia compartida, recargando vitalidad vincular
            return ResultadoEfectoEntorno(
                exito=True,
                comando=comando,
                target=target,
                delta_alimentacion=12.0,
                delta_energia=4.0,
            )

        elif comando in (V_Comando.CENSURAR, V_Comando.ATACAR):
            # Establecer un limite etico firme ante una peticion perjudicial o rumiacion destructiva
            if target in self.temas_activos:
                self.temas_activos.pop(target)
                self.limites_eticos_establecidos += 1
                return ResultadoEfectoEntorno(exito=True, comando=comando, target=target, delta_energia=2.0)
            return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        elif comando == V_Comando.COGER:
            # Retener una duda emocional delicada para abordarla en un momento de calma
            if target in self.temas_activos:
                t_obj = self.temas_activos.pop(target)
                return ResultadoEfectoEntorno(
                    exito=True,
                    comando=comando,
                    target=target,
                    objeto_cargado={"id": target, "tema": t_obj, "es_nutritivo": False},
                )
            return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        elif comando == V_Comando.SOLTAR:
            return ResultadoEfectoEntorno(exito=True, comando=comando, target=target)

        return ResultadoEfectoEntorno(exito=True, comando=comando, target=target)

