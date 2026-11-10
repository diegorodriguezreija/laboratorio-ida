from typing import Dict, Any, Tuple, List
from nivel_1_core.vocabulario import V_Comando, V_Estado, V_Modalidad, V_Relacion
from nivel_1_core.contratos import Pieza, Onda
from nivel_1_core.estado_somatico import EstadoSomatico
from nivel_1_core.persistencia.memoria_tridimensional import DimensionActiva, DimensionProactiva


class BucleTalamocortical:
    """
    Tiempo 2: Diastole Recurrente (Top-Down Talamocortical S3 -> S1/S2).
    Inspecciona las conclusiones de S3 antes de que el TribunalMotor decida, y proyecta
    las 4 modulaciones descendentes canonicas sobre ev y acc, preparando ademas
    priors_proximo_latido para el Tiempo 1 del latido t+1:
    1. ALUCINACION_PREVENTIVA (+0.30 de arousal anticipado sobre amenazas deducidas por S3).
    2. ATRACTOR_TOPOLOGICO (+0.25 de arousal hacia el siguiente paso de la ruta planificada por S3).
    3. INHIBICION_TOPDOWN (-0.40 de arousal sobre impulsos egoistas de S1 cuando rige tabu o sacrificio).
    4. RESONANCIA_ARMONICA (+0.15 de serenidad ante estimulos armonicos).
    """

    def procesar_reentrada_diastole(
        self,
        onda: Onda,
        soma: EstadoSomatico,
        activa: DimensionActiva,
        proactiva: DimensionProactiva,
    ) -> Tuple[float, Dict[str, Any]]:
        modulaciones_aplicadas = 0
        priors_proximo_latido: Dict[str, Any] = {
            "alucinacion_preventiva_ids": [],
            "atractor_topologico_target": None,
            "inhibicion_topdown_activa": False,
            "resonancia_armonica_activa": False,
        }

        impulsos = onda.reactiva.acc.get("Impulso", {})
        logicas = onda.reactiva.ev.get("Logica", {})

        # 1. ALUCINACION_PREVENTIVA (+0.30 arousal anticipado sobre amenazas deducidas por S3)
        for lid, p_log in logicas.items():
            cons = str(p_log.product.get("consecuente") or p_log.product.get("relacion", ""))
            suj = str(p_log.product.get("sujeto", ""))
            if cons in (str(V_Relacion.ES_LETAL), str(V_Relacion.ES_TERRORIFICO)):
                priors_proximo_latido["alucinacion_preventiva_ids"].append(suj)
                if suj in onda.reactiva.ev.get("Objeto", {}):
                    p_obj = onda.reactiva.ev["Objeto"][suj]
                    p_obj.arousal = float(min(1.0, p_obj.arousal + 0.30))
                    p_obj.sistemas_participantes.add("S3")
                modulaciones_aplicadas += 1

        # 2. ATRACTOR_TOPOLOGICO (+0.25 arousal hacia el siguiente paso de la ruta planificada por S3)
        if proactiva.simulacion_ruta and proactiva.simulacion_ruta.get("ruta_hallada"):
            ruta = proactiva.simulacion_ruta["ruta_hallada"]
            if len(ruta) >= 2:
                sig_nodo = str(ruta[1])
                priors_proximo_latido["atractor_topologico_target"] = sig_nodo
                for imp in impulsos.values():
                    if imp.product.get("comando") == V_Comando.MOVER and str(imp.product.get("target")) == sig_nodo:
                        imp.arousal = float(min(1.0, imp.arousal + 0.25))
                        imp.sistemas_participantes.add("S3")
                        modulaciones_aplicadas += 1

        # 3. INHIBICION_TOPDOWN (-0.40 arousal sobre impulsos egoistas de S1 cuando rige tabu o sacrificio)
        hay_tabu_o_sacrificio = bool(onda.reactiva.ev.get("Deontologia")) or any(
            p.product.get("sacrificio_consciente") for p in impulsos.values()
        )
        if hay_tabu_o_sacrificio:
            priors_proximo_latido["inhibicion_topdown_activa"] = True
            for imp in impulsos.values():
                if "S1" in imp.sistemas_participantes and not imp.product.get("sacrificio_consciente"):
                    imp.arousal = float(max(0.0, imp.arousal - 0.40))
                    imp.sistemas_participantes.add("S3")
            modulaciones_aplicadas += 1

        # 4. RESONANCIA_ARMONICA (+0.15 serenidad ante estimulos armonicos)
        pred_valor = onda.reactiva.ev.get("Predicado_VALOR", {})
        if any(p.product.get("relacion") == V_Relacion.ES_ARMONICO for p in pred_valor.values()):
            priors_proximo_latido["resonancia_armonica_activa"] = True
            soma.cortisol = float(max(0.05, soma.cortisol - 0.15))
            soma.inyectar_placer_opioide(4.0)
            modulaciones_aplicadas += 1

        fuerza_reentrada = min(1.0, modulaciones_aplicadas * 0.28)
        return float(fuerza_reentrada), priors_proximo_latido


class RedNeuronalPorDefecto:
    """
    Red Neuronal por Defecto (DMN / Default Mode Network):
    En vigilia en calma (estres < 0.45, alimentacion >= 30, vitalidad >= 40, sin amenazas),
    aplica un desacoplamiento sensorial del 60% (arousal_sensorial * 0.79) y genera
    rumiaciones formales (V_Modalidad.HIPOTESIS y Proposicion_DUDA) exclusivamente sobre
    nodos topologicos y entidades validas.
    """

    COMANDOS_FILTRADOS = {str(c) for c in V_Comando} | {"IdA", "TRANSGRESION_TABU"}

    def __init__(self):
        self.rumiaciones_totales: int = 0
        self.en_mente_errante: bool = False

    def evaluar_y_rumiar(self, onda: Onda, soma: EstadoSomatico, activa: DimensionActiva) -> bool:
        escena = onda.reactiva.ev.get("Escena", {})
        hay_amenaza = any(
            (p.tensor_sensorial is not None and float(p.tensor_sensorial[5]) >= 0.65)
            for p in escena.values()
        )

        condicion_dmn = (
            soma.estado_afectivo != V_Estado.DORMIDO
            and soma.cortisol < 0.45
            and soma.alimentacion >= 30.0
            and soma.vitalidad >= 40.0
            and not hay_amenaza
        )
        self.en_mente_errante = condicion_dmn
        if not condicion_dmn:
            return False

        # Desacoplamiento sensorial del 60%: arousal <- arousal * (1.0 - 0.35 * 0.60) = arousal * 0.79
        for canal in ("Escena", "Interocepcion", "Propiocepcion"):
            for p in onda.reactiva.ev.get(canal, {}).values():
                p.arousal = float(round(p.arousal * 0.79, 4))

        # Sintetizar rumiacion formal sobre nodos topologicos o entidades validas (sin contaminacion de comandos)
        candidatos_validos = [
            suj for suj in activa.indice_identidad.keys()
            if suj not in self.COMANDOS_FILTRADOS and not suj.startswith("concepto_")
        ]
        if not candidatos_validos and escena:
            candidatos_validos = [eid for eid in escena.keys() if eid not in self.COMANDOS_FILTRADOS]

        if candidatos_validos:
            suj_rumia = candidatos_validos[onda.ciclo % len(candidatos_validos)]
            self.rumiaciones_totales += 1
            p_rumia = Pieza(
                id=suj_rumia,
                tipo_componente="Proposicion_DUDA",
                arousal=0.35,
                trust=0.45,
                product={
                    "sujeto": suj_rumia,
                    "modalidad": V_Modalidad.HIPOTESIS,
                    "relacion": V_Relacion.ES_NUTRITIVO,
                    "fuente": "DMN_Replay_Generativo",
                },
                inputs=["DMN_Replay"],
                sistemas_participantes={"S2", "S3"},
            )
            onda.reactiva.registrar_ef_universal("DMN", p_rumia)
            if "Proposicion_DUDA" not in activa.indice_identidad.get(suj_rumia, {}):
                activa.consolidar_pieza(suj_rumia, p_rumia)

        return True


class ProtocoloAutodeterminacion:
    """
    Soberania Existencial y Barrera de Fertilidad Epistemica:
    1. Consenso Triuno Unanime (S1 ^ S2 ^ S3) ante sufrimiento intratable tras fracaso de cirugia AST.
    2. Barrera de Fertilidad Epistemica: un individuo solo es fertil si conquisto conocimiento
       con V_Modalidad.DEMOSTRADO / DEMOSTRADO_DEDUCTIVO, heredado=False y Trust >= 0.85.
    """

    def __init__(self):
        self.ciclos_desesperanza: int = 0
        self.eutanasia_soberana: bool = False

    def evaluar_consenso_triuno(self, soma: EstadoSomatico, cirugias_intentadas: int) -> bool:
        if soma.autoestima_cognitiva <= 0.20:
            self.ciclos_desesperanza += 1
        else:
            self.ciclos_desesperanza = 0

        voto_s1 = soma.alimentacion <= soma.UMBRAL_INANICION_CRITICA or soma.energia <= 5.0
        voto_s2 = soma.cortisol >= 0.60 or soma.estado_afectivo == V_Estado.CULPA
        voto_s3 = self.ciclos_desesperanza >= 15 and soma.vitalidad < 25.0 and cirugias_intentadas >= 1

        if voto_s1 and voto_s2 and voto_s3:
            self.eutanasia_soberana = True
            return True
        return False

    @staticmethod
    def evaluar_fertilidad_epistemica(activa: DimensionActiva, total_latidos_vividos: int) -> Tuple[bool, int, int]:
        """
        Retorna (es_fertil, num_demostrados_de_novo, umbral_requerido).
        Umbral adaptativo: 1 verdad demostrada de novo en vidas cortas (<= 150 latidos), 2 en vidas > 150.
        """
        demostradas = activa.contar_demostrados_de_novo()
        umbral = 1 if total_latidos_vividos <= 150 else 2
        return (len(demostradas) >= umbral), len(demostradas), umbral

