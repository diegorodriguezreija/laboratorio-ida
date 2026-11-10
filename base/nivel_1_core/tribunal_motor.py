from typing import Any, Dict, Optional, Tuple
from nivel_1_core.vocabulario import V_Comando
from nivel_1_core.contratos import Pieza, Onda, IActuadorEntorno, ResultadoEfectoEntorno
from nivel_1_core.estado_somatico import EstadoSomatico
from nivel_1_core.cosechador_termodinamico import CosechadorTermodinamico
from nivel_1_core.arbitros import (
    ArbitroBase,
    A0_TribunalMotorDefault,
    crear_arbitro,
    identificar_sistema_origen,
)


class TribunalMotor:
    """
    Ganglio Basal Biologicamente Verosimil (Nivel 1).
    Orquesta el arbitraje de impulsos y la transduccion sensoriomotora:
    1. Delega la regla de seleccion en un ArbitroBase inyectado (A0..A7).
    2. Soporta dos modos de ablacion:
       - "nivel_a" (suave): conserva umbral de acecho D1/D2, desesperacion y colapso.
       - "nivel_b" (estricta / directa): el arbitro simple emite la accion directamente.
    3. Registro contrafactual pasivo de alternativas A0..A7 (aislado del RNG principal).
    4. Aplicacion de consecuencias fisicas sobre el chasis somatico.
    """

    EPSILON_BIFURCACION_PRIGOGINE = 0.03

    def __init__(
        self,
        cosechador: CosechadorTermodinamico,
        arbitro: Optional[ArbitroBase] = None,
        modo_ablacion: str = "nivel_a",
        registrar_contrafactual: bool = True,
    ):
        self.cosechador = cosechador
        self.arbitro = arbitro if arbitro is not None else A0_TribunalMotorDefault()
        self.modo_ablacion = modo_ablacion.lower()
        if self.modo_ablacion not in ("nivel_a", "nivel_b"):
            raise ValueError(
                f"Modo de ablación '{modo_ablacion}' inválido. Debe ser 'nivel_a' o 'nivel_b'."
            )
        self.registrar_contrafactual = registrar_contrafactual
        self.memoria_acecho: Dict[str, float] = {}
        self.intentos_huida_fallidos: int = 0

        # Pool de árbitros contrafactuales pasivos (aislados, A4 con su propio RNG)
        if self.registrar_contrafactual:
            self._pool_contrafactual = {
                aid: crear_arbitro(aid, seed_propia=1000 + i) if aid == "A4" else crear_arbitro(aid)
                for i, aid in enumerate(("A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7"))
            }
        else:
            self._pool_contrafactual = {}

    def calcular_umbral_acecho(self, soma: EstadoSomatico) -> float:
        """
        Ecuacion estriatal Berridge-Schultz:
        Theta_acecho = 0.75 + 0.15 * (1.0 - Autoestima) - 0.12 * ((dopamina - 35.0) / 65.0)
        """
        theta = (
            0.75
            + 0.15 * (1.0 - soma.autoestima_cognitiva)
            - 0.12 * ((soma.dopamina - 35.0) / 65.0)
        )
        return float(max(0.25, min(0.95, theta)))

    def _evaluar_registro_contrafactual(
        self,
        impulsos_dict: Dict[str, Pieza],
        soma: EstadoSomatico,
        onda: Onda,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evalúa pasivamente qué decisión habría tomado cada uno de los árbitros alternativos
        (A0 a A7) ante el mismo conjunto de candidatos y estado somático.
        Totalmente libre de efectos secundarios sobre el actuador o el RNG principal.
        """
        contrafactuales: Dict[str, Dict[str, Any]] = {}
        for aid, arb in self._pool_contrafactual.items():
            p_cf, meta_cf = arb.seleccionar(
                impulsos_dict, soma, cosechador=None, contexto={"onda": onda}
            )
            if p_cf is not None:
                contrafactuales[aid] = {
                    "pieza_id": p_cf.id,
                    "comando": str(p_cf.product.get("comando", V_Comando.ESPERAR)),
                    "target": str(p_cf.product.get("target", onda.ubicacion_actual)),
                    "origen": identificar_sistema_origen(p_cf),
                    "arousal": p_cf.arousal,
                    "trust": p_cf.trust,
                }
            else:
                contrafactuales[aid] = {
                    "pieza_id": "VETO/NINGUNO",
                    "comando": str(V_Comando.ESPERAR),
                    "target": onda.ubicacion_actual,
                    "origen": "ESPERA",
                    "arousal": 0.0,
                    "trust": 0.0,
                }
        return contrafactuales

    def arbitrar_y_ejecutar(
        self, onda: Onda, soma: EstadoSomatico, actuador: IActuadorEntorno
    ) -> Tuple[Pieza, Optional[ResultadoEfectoEntorno]]:
        impulsos_dict = onda.reactiva.acc.get("Impulso", {})
        conteo_sistemas: Dict[str, int] = {"S1": 0, "S2": 0, "S3": 0}

        for p in impulsos_dict.values():
            sis = identificar_sistema_origen(p)
            conteo_sistemas[sis] += 1

        onda.metricas["impulsos_por_sistema"] = conteo_sistemas

        # Registro contrafactual pasivo (si está habilitado)
        if self.registrar_contrafactual and self._pool_contrafactual:
            cf_map = self._evaluar_registro_contrafactual(impulsos_dict, soma, onda)
            onda.metricas["contrafactual"] = cf_map
            # Evaluar si hay desacuerdo entre A0 y los árbitros simples
            cmd_a0 = cf_map.get("A0", {}).get("comando")
            desacuerdos = [aid for aid, d in cf_map.items() if d.get("comando") != cmd_a0]
            onda.metricas["desacuerdos_contrafactuales"] = desacuerdos
            onda.metricas["estres_latido"] = round(float(soma.cortisol), 4)
            onda.metricas["alimentacion_latido"] = round(float(soma.alimentacion), 2)

        if not impulsos_dict:
            onda.metricas["sistema_ganador"] = "ESPERA"
            onda.metricas["componente_ganador"] = "TribunalMotor"
            onda.metricas["tribunal_altero_arousal_puro"] = False
            pieza_espera = Pieza(
                id="Ejecucion",
                tipo_componente="Ejecucion",
                arousal=0.1,
                trust=1.0,
                product={"comando": V_Comando.ESPERAR, "target": onda.ubicacion_actual, "exito": True},
                inputs=["TribunalMotor"],
            )
            onda.reactiva.registrar_ef_universal("Ejecucion", pieza_espera)
            return pieza_espera, None

        # 1. Delegar selección en el árbitro configurado
        ganador, meta_arbitro = self.arbitro.seleccionar(
            impulsos_dict, soma, self.cosechador, {"onda": onda}
        )

        ganador_arousal_puro = max(impulsos_dict.values(), key=lambda x: x.arousal)

        # Si el árbitro devolvió None (por veto prefrontal o falta de candidatos en capa A5/A6)
        if ganador is None:
            motivo = meta_arbitro.get("motivo", "sin_candidato_valido")
            onda.metricas["sistema_ganador"] = "S3" if "veto" in motivo else "ESPERA"
            onda.metricas["componente_ganador"] = "Veto_Prefrontal" if "veto" in motivo else "Inhibicion"
            onda.metricas["tribunal_altero_arousal_puro"] = True
            pieza_veto = Pieza(
                id="Ejecucion",
                tipo_componente="Ejecucion",
                arousal=0.1,
                trust=1.0,
                product={
                    "comando": V_Comando.ESPERAR,
                    "target": onda.ubicacion_actual,
                    "veto_prefrontal": ("veto" in motivo),
                    "motivo_inhibicion": motivo,
                    "exito": True,
                },
                inputs=["TribunalMotor"],
            )
            onda.reactiva.registrar_ef_universal("Ejecucion", pieza_veto)
            return pieza_veto, None

        sistema_ganador = identificar_sistema_origen(ganador)
        onda.metricas["sistema_ganador"] = sistema_ganador
        onda.metricas["componente_ganador"] = str(ganador.product.get("id_componente", ganador.id))
        onda.metricas["tribunal_altero_arousal_puro"] = bool(ganador.id != ganador_arousal_puro.id)

        cmd_propuesto = V_Comando(str(ganador.product.get("comando", V_Comando.ESPERAR)))
        target = str(ganador.product.get("target", onda.ubicacion_actual))
        clave_acecho = f"{cmd_propuesto}:{target}"

        # -----------------------------------------------------------------
        # MODO DE ABLACIÓN B (EMISIÓN DIRECTA / ÁRBITRO ESTRICTO)
        # Suprime umbral de acecho D1/D2, desesperación y colapso tónico.
        # -----------------------------------------------------------------
        if self.modo_ablacion == "nivel_b":
            resultado = actuador.ejecutar_comando_fisico(
                comando=cmd_propuesto,
                target=target,
                factor_fauces=soma.factor_ingesta_fauces(),
                payload_extra=ganador.product,
            )
            soma.aplicar_consecuencia_fisica(resultado)
            pieza_ejec = Pieza(
                id="Ejecucion",
                tipo_componente="Ejecucion",
                arousal=ganador.arousal,
                trust=ganador.trust,
                product={
                    "comando": cmd_propuesto,
                    "target": target,
                    "exito": resultado.exito,
                    "delta_alimentacion": resultado.delta_alimentacion,
                    "intoxicacion_aguda": resultado.intoxicacion_aguda,
                    "verdad_verificada": resultado.verdad_verificada,
                    "sacrificio_consciente": bool(ganador.product.get("sacrificio_consciente", False)),
                    "modo_ablacion": "nivel_b",
                },
                inputs=[ganador.id, "TribunalMotor"],
            )
            onda.reactiva.registrar_ef_universal("Ejecucion", pieza_ejec)
            return pieza_ejec, resultado

        # -----------------------------------------------------------------
        # MODO DE ABLACIÓN A (CANÓNICO / MAQUINARIA SOMÁTICA PERIFÉRICA ACTIVA)
        # Evalúa umbral de acecho D1/D2 y colapso por pánico.
        # -----------------------------------------------------------------
        en_desesperacion = soma.alimentacion <= soma.UMBRAL_INANICION_CRITICA
        umbral_acecho = self.calcular_umbral_acecho(soma)
        trust_acumulado = self.memoria_acecho.get(clave_acecho, 0.0) + ganador.trust

        if (
            not en_desesperacion
            and cmd_propuesto not in (V_Comando.ESPERAR, V_Comando.SOLTAR)
            and trust_acumulado < umbral_acecho
        ):
            self.memoria_acecho[clave_acecho] = trust_acumulado
            pieza_acecho = Pieza(
                id="Ejecucion",
                tipo_componente="Ejecucion",
                arousal=ganador.arousal,
                trust=min(1.0, trust_acumulado),
                product={
                    "comando": V_Comando.ACECHAR,
                    "comando_latente": cmd_propuesto,
                    "target": target,
                    "umbral_acecho": round(umbral_acecho, 4),
                    "exito": True,
                    "modo_ablacion": "nivel_a",
                },
                inputs=[ganador.id, "TribunalMotor"],
            )
            onda.reactiva.registrar_ef_universal("Ejecucion", pieza_acecho)
            return pieza_acecho, None

        # Superado el umbral de acecho o en desesperacion: ejecutar comando fisico
        self.memoria_acecho.pop(clave_acecho, None)
        resultado = actuador.ejecutar_comando_fisico(
            comando=cmd_propuesto,
            target=target,
            factor_fauces=soma.factor_ingesta_fauces(),
            payload_extra=ganador.product,
        )

        estres = float(max(0.0, min(1.0, soma.cortisol)))
        if cmd_propuesto == V_Comando.MOVER and not resultado.exito and estres > soma.UMBRAL_PANICO_ESTRES:
            self.intentos_huida_fallidos += 1
            if self.intentos_huida_fallidos >= 2:
                cmd_propuesto = V_Comando.COLAPSO
        else:
            self.intentos_huida_fallidos = 0

        soma.aplicar_consecuencia_fisica(resultado)

        pieza_ejec = Pieza(
            id="Ejecucion",
            tipo_componente="Ejecucion",
            arousal=ganador.arousal,
            trust=ganador.trust,
            product={
                "comando": cmd_propuesto,
                "target": target,
                "exito": resultado.exito,
                "delta_alimentacion": resultado.delta_alimentacion,
                "intoxicacion_aguda": resultado.intoxicacion_aguda,
                "verdad_verificada": resultado.verdad_verificada,
                "sacrificio_consciente": bool(ganador.product.get("sacrificio_consciente", False)),
                "modo_ablacion": "nivel_a",
            },
            inputs=[ganador.id, "TribunalMotor"],
        )
        onda.reactiva.registrar_ef_universal("Ejecucion", pieza_ejec)
        return pieza_ejec, resultado
