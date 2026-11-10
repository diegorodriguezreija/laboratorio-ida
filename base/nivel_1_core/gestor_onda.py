from typing import List, Dict, Any, Optional
import time
from nivel_1_core.vocabulario import V_Comando, V_Estado
from nivel_1_core.contratos import (
    Pieza,
    Onda,
    Episodio,
    Arquetipo,
    ISensorEntorno,
    IActuadorEntorno,
    LatidoAgotadoException,
)
from nivel_1_core.estado_somatico import EstadoSomatico
from nivel_1_core.cosechador_termodinamico import CosechadorTermodinamico
from nivel_1_core.tribunal_motor import TribunalMotor
from nivel_1_core.calculadoras_estructurales import CalculadorasEstructurales
from nivel_1_core.persistencia.memoria_tridimensional import DimensionActiva, DimensionProactiva
from nivel_1_core.persistencia.motor_sqlite_wal import MotorSQLiteWAL
from nivel_1_core.persistencia.motor_pgvector import MotorPgVectorHNSW


class GestorOndaCore:
    """
    Orquestador del Latido en Dos Tiempos (Sistole Aferente + Diastole Recurrente),
    Reloj RTOS de la Guillotina (100 ms) y Juez de Persistencia / Keyframing Episodico.
    """

    def __init__(
        self,
        sensor: ISensorEntorno,
        actuador: IActuadorEntorno,
        arquetipo: Arquetipo,
        sistemas_cognitivos: List[Any],
        bucle_talamocortical: Any,
        dmn: Any,
        gestor_sueno_rem: Any,
        cirujano_ast: Any,
        sqlite_wal: Optional[MotorSQLiteWAL] = None,
        pgvector: Optional[MotorPgVectorHNSW] = None,
        frecuencia_max_ms: float = 100.0,
        amplitud_max: int = 100,
        tribunal: Optional[TribunalMotor] = None,
        arbitro: Optional[Any] = None,
        modo_ablacion: str = "nivel_a",
    ):
        self.sensor = sensor
        self.actuador = actuador
        self.arquetipo = arquetipo
        self.sistemas = sistemas_cognitivos  # [S1, S2, S3]
        self.talamo = bucle_talamocortical
        self.dmn = dmn
        self.sueno_rem = gestor_sueno_rem
        self.cirujano = cirujano_ast
        self.sqlite = sqlite_wal or MotorSQLiteWAL(":memory:")
        self.pgvector = pgvector or MotorPgVectorHNSW()
        self.frecuencia_max_ms = frecuencia_max_ms
        self.amplitud_max = amplitud_max

        self.soma = EstadoSomatico()
        self.cosechador = CosechadorTermodinamico()
        if tribunal is not None:
            self.tribunal = tribunal
        else:
            self.tribunal = TribunalMotor(
                self.cosechador, arbitro=arbitro, modo_ablacion=modo_ablacion
            )
        self.activa = DimensionActiva(id_linaje=arquetipo.linaje)
        self.proactiva = DimensionProactiva()

        self.ciclo_actual: int = 0
        self.ef_ultimo_latido: Optional[Dict[str, Dict[str, Pieza]]] = None
        self.priors_talamo_actuales: Dict[str, Any] = {}
        self._episodio_abierto: Optional[Episodio] = None
        self._vitalidad_inicio_ep: float = 100.0

    def _aplicar_priors_sensoriales_tiempo_1(self, piezas_escena: List[Pieza]) -> None:
        """Aplica en Tiempo 1 los priors proyectados por el Talamo en el Tiempo 2 del latido anterior."""
        if not self.priors_talamo_actuales:
            return
        amenazas_prev = set(self.priors_talamo_actuales.get("alucinacion_preventiva_ids", []))
        for p in piezas_escena:
            if p.id in amenazas_prev:
                p.arousal = float(min(1.0, p.arousal + 0.30))
                p.product["prior_alucinacion_preventiva"] = True

    async def ejecutar_latido(self, amplitud_override: Optional[int] = None, frecuencia_override_ms: Optional[float] = None) -> Onda:
        self.ciclo_actual += 1
        self.soma.aplicar_metabolismo_latido(self.ciclo_actual)
        self.activa.aplicar_decaimiento_alocentrico(self.ciclo_actual)

        # Evaluar transicion circadiana Borbely-Prigogine o Wake-up Call S1
        if self.sueno_rem is not None:
            self.sueno_rem.evaluar_transicion_circadiana(
                soma=self.soma,
                activa=self.activa,
                cosechador=self.cosechador,
            )

        en_sueno = self.soma.estado_afectivo == V_Estado.DORMIDO
        amp_latido = 20 if en_sueno else (amplitud_override if amplitud_override is not None else self.amplitud_max)
        freq_latido = frecuencia_override_ms if frecuencia_override_ms is not None else self.frecuencia_max_ms

        # =====================================================================
        # TIEMPO 1: SISTOLE AFERENTE (Bottom-Up: Sensores -> DMN -> S1 -> S2 -> S3)
        # =====================================================================
        nodo_actual, piezas_escena, nodos_adyacentes = self.sensor.percibir_mundo()
        if not self.soma.historial_nodos or self.soma.historial_nodos[-1] != nodo_actual:
            self.soma.historial_nodos.append(nodo_actual)

        # Escalado adaptativo del ruido termodinamico: mayor en panico/DMN, menor bajo control S3
        escala_ruido = 1.2 if self.soma.alimentacion <= self.soma.UMBRAL_INANICION_CRITICA else 0.35
        eta_silicio = self.cosechador.inyectar_ruido_sensorial(
            piezas_escena,
            prob_ruido_sensores=self.soma.probabilidad_ruido_sensorial(),
            factor_escala=escala_ruido,
        )
        self._aplicar_priors_sensoriales_tiempo_1(piezas_escena)

        onda = Onda(
            ciclo=self.ciclo_actual,
            amplitud_max=amp_latido,
            frecuencia_max_ms=freq_latido,
            ubicacion_actual=nodo_actual,
            ef_anterior=self.ef_ultimo_latido,
            priors_talamocorticales=dict(self.priors_talamo_actuales),
        )
        onda.metricas["jitter_silicio"] = eta_silicio

        # Emision Sensorial Dual (inmune_peaje=True: escribe en ef y en ev sin cobrar Amplitud)
        p_propio = Pieza(
            id=f"Propiocepcion_{nodo_actual}",
            tipo_componente="Propiocepcion",
            arousal=0.2,
            trust=1.0,
            product={
                "ubicacion": nodo_actual,
                "nodos_adyacentes": list(nodos_adyacentes),
                "objeto_cargado": self.soma.objeto_cargado,
                "historial_nodos": list(self.soma.historial_nodos),
            },
            inputs=["SensorPropiocepcion"],
        )
        onda.reactiva.registrar_ef_universal("Propiocepcion", p_propio)
        onda.reactiva.ev.setdefault("Propiocepcion", {})[p_propio.id] = p_propio

        ef_prev_intero = dict(onda.reactiva.ei.get("Interocepcion", {})) if "Interocepcion" in onda.reactiva.ei else {}
        piezas_intero = self.soma.emitir_piezas_interoceptivas(ef_prev_intero, jitter_termico=eta_silicio)
        for pid, p_int in piezas_intero.items():
            onda.reactiva.registrar_ef_universal(p_int.tipo_componente, p_int)
            onda.reactiva.ev.setdefault(p_int.tipo_componente, {})[pid] = p_int

        for p_esc in piezas_escena:
            onda.reactiva.registrar_ef_universal("Escena", p_esc)
            onda.reactiva.ev.setdefault("Escena", {})[p_esc.id] = p_esc

        # Si esta en Sueno REM, ejecuta las 4 fases oniricas con paralisis motora
        if en_sueno and self.sueno_rem is not None:
            self.sueno_rem.procesar_sueno_rem(onda, self.soma, self.activa)
            self.sqlite.sincronizar_desde_activa(self.activa)
            self.ef_ultimo_latido = onda.reactiva.ef
            return onda

        # Red Neuronal por Defecto (DMN): Desacople sensorial del 60% (arousal * 0.79) y rumiacion formal
        if self.dmn is not None:
            self.dmn.evaluar_y_rumiar(onda, self.soma, self.activa)

        # Canalizacion secuencial por la Mente Triunica: S1 -> S2 -> S3 bajo Guillotina
        contexto_cognitivo = {
            "soma": self.soma,
            "arquetipo": self.arquetipo,
            "activa": self.activa,
            "proactiva": self.proactiva,
            "pgvector": self.pgvector,
            "cosechador": self.cosechador,
        }
        try:
            for sistema in self.sistemas:
                onda.verificar_guillotina_frecuencia(contexto=f"Pre-{sistema.nombre}")
                await sistema.procesar_onda(onda, contexto_cognitivo)
        except LatidoAgotadoException as exc:
            onda.guillotina_disparada = True
            onda.motivo_guillotina = str(exc)

        # =====================================================================
        # TIEMPO 2: DIASTOLE RECURRENTE (Top-Down Talamocortical: S3 -> S1/S2)
        # =====================================================================
        fuerza_reentrada = 0.0
        if self.talamo is not None:
            fuerza_reentrada, self.priors_talamo_actuales = self.talamo.procesar_reentrada_diastole(
                onda, self.soma, self.activa, self.proactiva
            )

        # Arbitraje en el Ganglio Basal (TribunalMotor) y ejecucion fisica
        pieza_ejec, res_fisico = self.tribunal.arbitrar_y_ejecutar(onda, self.soma, self.actuador)
        if res_fisico is not None and res_fisico.exito and res_fisico.comando == V_Comando.MOVER and res_fisico.nueva_ubicacion:
            self.activa.registrar_transicion_topologica(nodo_actual, res_fisico.nueva_ubicacion)

        # Plasticidad Sinaptica en Linea via TD(lambda) y Trazas de Elegibilidad
        if res_fisico is not None:
            recompensa_td = float((self.soma.dopamina - self.soma.DOPAMINA_BASAL) / 35.0)
            if res_fisico.intoxicacion_aguda or not res_fisico.exito:
                recompensa_td -= 0.50
            elif res_fisico.delta_alimentacion > 0:
                recompensa_td += 0.25

            ids_activados = set(pieza_ejec.inputs)
            comp_ganador = onda.metricas.get("componente_ganador")
            if comp_ganador:
                ids_activados.add(str(comp_ganador))

            ultimo_delta_td = 0.0
            for sistema in self.sistemas:
                if hasattr(sistema, "actualizar_plasticidad_td"):
                    ultimo_delta_td = sistema.actualizar_plasticidad_td(recompensa_td, ids_activados)
            onda.metricas["delta_td"] = round(float(ultimo_delta_td), 4)

        # Calculo O(1) de Phi (IIT Tononi) sin teatro computacional
        phi = CalculadorasEstructurales.calcular_phi_tononi(
            onda, fuerza_reentrada=fuerza_reentrada, jitter_silicio=eta_silicio
        )
        onda.metricas["phi"] = phi
        onda.metricas["fuerza_reentrada"] = fuerza_reentrada

        # Evaluacion de Autopoiesis AST y Ventana Clinica (25 latidos)
        if self.cirujano is not None:
            self.cirujano.auditar_ciclo(onda, self.soma, self.sistemas)

        # Keyframing Episodico por Arousal / Sorpresa
        self._gestionar_keyframing_episodico(onda)
        self.ef_ultimo_latido = onda.reactiva.ef
        return onda

    def _gestionar_keyframing_episodico(self, onda: Onda) -> None:
        max_arousal = 0.0
        for dic in onda.reactiva.ev.values():
            for p in dic.values():
                if p.arousal > max_arousal:
                    max_arousal = p.arousal
        hay_sorpresa = "Sorpresa" in onda.reactiva.ev

        if self._episodio_abierto is None and (max_arousal >= 0.58 or hay_sorpresa):
            self._episodio_abierto = Episodio(
                id_episodio=f"Ep_{self.arquetipo.id_individuo}_{self.ciclo_actual}",
                ubicacion_principal=onda.ubicacion_actual,
                ciclo_inicio=self.ciclo_actual,
            )
            self._vitalidad_inicio_ep = self.soma.vitalidad

        if self._episodio_abierto is not None:
            ejec = onda.reactiva.ef.get("Ejecucion", {}).get("Ejecucion")
            cmd_str = str(ejec.product.get("comando", "")) if ejec else ""
            self._episodio_abierto.ondas_resumen.append({
                "ciclo": self.ciclo_actual,
                "ubicacion": onda.ubicacion_actual,
                "comando": cmd_str,
                "phi": onda.metricas.get("phi", 0.0),
            })
            longitud = self.ciclo_actual - self._episodio_abierto.ciclo_inicio + 1
            cambio_nodo = onda.ubicacion_actual != self._episodio_abierto.ubicacion_principal
            if longitud >= 5 or cambio_nodo or not self.soma.esta_vivo:
                self._episodio_abierto.ciclo_fin = self.ciclo_actual
                delta_vit = self.soma.vitalidad - self._vitalidad_inicio_ep
                self._episodio_abierto.balance_vital = round(delta_vit, 3)
                self._episodio_abierto.resuelto = delta_vit >= -1.5 and self.soma.esta_vivo
                self.activa.banco_episodico.append(self._episodio_abierto)
                self._episodio_abierto = None

