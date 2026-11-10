"""
Componentes Neurocognitivos para el Mundo Crafter en IdA v12.0.
Implementa:
- CompCrafterS1: Reflejos instantáneos (< 5 ms) de huida, nocicepción y forrajeo urgente.
- CompCrafterS2: Construcción ontológica, modulación límbica y ritmo circadiano (ansiedad nocturna).
- CompCrafterS3: Planificación causal deliberativa, progresión tecnológica (Tech Tree) y navegación A*.
"""

from typing import Dict, Any, List, Tuple, Set, Optional
from collections import deque
import numpy as np

from nivel_1_core.vocabulario import V_Comando, V_Relacion, V_Modalidad
from nivel_1_core.contratos import Pieza, Onda
from nivel_2_sistemas.sistema_base import ComponenteCognitivoBase


class CompCrafterS1(ComponenteCognitivoBase):
    """
    Componente Reactivo S1: Reflejos de Supervivencia Inmediata en Crafter (< 5 ms).
    - Mandato Primordial: No colisión letal (evitar lava, escapar de depredadores adyacentes).
    - Reflejos Viscerales: Deglución de agua urgente si deshidratado, ataque inmediato a depredador si acorralado.
    - Gradiente Apetitivo: Locomoción reactiva hacia el nutriente o recurso más saliente.
    """

    def __init__(self, peso_sinaptico: float = 1.20):
        super().__init__("Comp_CrafterS1", "S1", peso_sinaptico=peso_sinaptico)

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        prop = onda.reactiva.ev.get("Propiocepcion", {})
        if not prop:
            return False

        p_prop = next(iter(prop.values()))
        nodos_adyacentes: List[str] = list(p_prop.product.get("nodos_adyacentes", []))
        historial = list(p_prop.product.get("historial_nodos", []))
        nodo_actual = str(p_prop.product.get("ubicacion", ""))

        if not nodos_adyacentes:
            # Sin salida inmediata -> esperar o defender
            p_esp = Pieza(
                id=f"Imp_S1_Espera_{onda.ciclo}",
                tipo_componente="Impulso",
                arousal=0.85,
                trust=0.90,
                product={"comando": V_Comando.ESPERAR, "target": "NOOP", "origen_sistema": "S1"},
                inputs=[p_prop.id, self.id_componente],
                sistemas_participantes={"S1"},
            )
            self.emitir_impulso(onda, p_esp, coste_amplitud=0)
            return True

        escena = onda.reactiva.ev.get("Escena", {})

        # Extraer estado somático
        p_estado = next((p for p in escena.values() if p.tipo_componente == "Estado_Entorno"), None)
        salud = int(p_estado.product.get("salud", 9)) if p_estado else 9
        comida = int(p_estado.product.get("comida", 9)) if p_estado else 9
        bebida = int(p_estado.product.get("bebida", 9)) if p_estado else 9
        energia = int(p_estado.product.get("energia", 9)) if p_estado else 9
        daylight = float(p_estado.product.get("daylight", 1.0)) if p_estado else 1.0
        sleeping = bool(p_estado.product.get("sleeping", False)) if p_estado else False
        logros_actuales = set(p_estado.product.get("logros_actuales", [])) if p_estado else set()

        # Obtener coordenadas del agente
        try:
            partes = nodo_actual.replace("nodo_", "").split("_")
            px, py = int(partes[0]), int(partes[1])
        except Exception:
            px, py = 32, 32

        # ---------------------------------------------------------------------
        # 1. CIRCUITO TACTICO PAG (SUSTANCIA GRIS PERIACUEDUCTAL): COMBATE Y EVASION
        # ---------------------------------------------------------------------
        # La PAG coordina la defensa biológica activa (dlPAG: contraataque, cierre)
        # y evasiva/repliegue (vlPAG: desenganche, ruptura de línea balística).
        depredadores: List[Pieza] = []
        lavas_adyacentes: Set[Tuple[int, int]] = set()

        for p in escena.values():
            if p.tipo_componente == "Amenaza_Predador":
                depredadores.append(p)
            elif p.tipo_componente == "Peligro_Lava":
                lx = int(p.product.get("x", -1))
                ly = int(p.product.get("y", -1))
                if abs(lx - px) + abs(ly - py) <= 1:
                    lavas_adyacentes.add((lx, ly))

        # Filtrar nodos adyacentes para NUNCA entrar en lava
        nodos_seguros: List[str] = []
        for n in nodos_adyacentes:
            try:
                np_partes = n.replace("nodo_", "").split("_")
                nx, ny = int(np_partes[0]), int(np_partes[1])
                if (nx, ny) not in lavas_adyacentes:
                    nodos_seguros.append(n)
            except Exception:
                nodos_seguros.append(n)

        if not nodos_seguros:
            nodos_seguros = nodos_adyacentes

        tiene_espada = any(
            int(p_estado.product.get(w, 0)) > 0
            for w in ("wood_sword", "stone_sword", "iron_sword")
        ) if p_estado else False

        # Consultar memoria epigenetica de traumas ancestrales (Barrera de Weismann) y Arquetipo
        activa_s1 = ctx.get("activa")
        arquetipo_s1 = ctx.get("arquetipo")
        resp_s1 = float(getattr(arquetipo_s1, "responsabilidad", 0.50)) if arquetipo_s1 else 0.50
        miedo_s1 = float(getattr(arquetipo_s1, "umbral_miedo", 0.45)) if arquetipo_s1 else 0.45

        traumas_ancestrales = activa_s1.indice_por_tipo.get("Aversion_Traumatica", {}) if activa_s1 else {}
        patrones_s1 = activa_s1.indice_por_tipo.get("Patron_Exito_Estrategico", {}) if activa_s1 else {}
        verdades_s1 = activa_s1.indice_por_tipo.get("Proposicion_VERDAD", {}) if activa_s1 else {}

        precaucion_depredador = any("Depredador" in tid for tid in traumas_ancestrales)
        precaucion_metabolica = any(("Inanicion" in tid or "Deshidratacion" in tid) for tid in traumas_ancestrales)
        tiene_herencia_metabolica = precaucion_metabolica or bool(verdades_s1) or len(patrones_s1) >= 3
        tiene_herencia_combate = precaucion_depredador or len(patrones_s1) >= 3

        salud_min_combate = 5 if (tiene_herencia_combate or miedo_s1 >= 0.55) else 2
        umbral_visceral_urgente = 4 if (tiene_herencia_metabolica and resp_s1 >= 0.65) else 1

        if depredadores:
            # Ordenar por cercanía
            depredadores.sort(key=lambda p: int(p.product.get("distancia_manhattan", 99)))
            pred_mas_cercano = depredadores[0]
            dist_min = int(pred_mas_cercano.product.get("distancia_manhattan", 99))
            tipo_mas_cercano = str(pred_mas_cercano.product.get("tipo_entidad", "Zombie"))
            amenazas_inmediatas = [p for p in depredadores if int(p.product.get("distancia_manhattan", 99)) <= 2]

            # A. AMENAZA A DISTANCIA 1 (CONTACTO CUERPO A CUERPO INMINENTE)
            if dist_min == 1:
                # Si solo hay 1 depredador y disponemos de vitalidad o arma: dlPAG (Contraataque frontal)
                if len(amenazas_inmediatas) <= 1 and (salud >= salud_min_combate or tiene_espada):
                    pred_nodo = str(pred_mas_cercano.product.get("target_nodo", ""))
                    p_atk = Pieza(
                        id=f"Imp_S1_Atacar_{onda.ciclo}",
                        tipo_componente="Impulso",
                        arousal=0.99,
                        trust=0.98,
                        product={
                            "comando": V_Comando.ATACAR,
                            "target": pred_nodo,
                            "origen_sistema": "S1",
                            "es_supervivencia_pag": True,
                        },
                        inputs=[p_prop.id, pred_mas_cercano.id, self.id_componente],
                        sistemas_participantes={"S1"},
                    )
                    self.emitir_impulso(onda, p_atk, coste_amplitud=1)
                    return True
                else:
                    # Riesgo de colapso o cerco múltiple (salud <= 3 o >= 2 enemigos): vlPAG (Desenganche y Repliegue)
                    def evaluacion_repliegue(n_id: str) -> float:
                        try:
                            n_parts = n_id.replace("nodo_", "").split("_")
                            nx_c, ny_c = int(n_parts[0]), int(n_parts[1])
                            dists = [
                                abs(nx_c - int(p.product.get("x", px))) + abs(ny_c - int(p.product.get("y", py)))
                                for p in depredadores
                            ]
                            return float(min(dists)) + 0.1 * float(sum(dists) / len(dists))
                        except Exception:
                            return 0.0

                    nodos_huida = sorted(nodos_seguros, key=evaluacion_repliegue, reverse=True)
                    mejor_huida = nodos_huida[0]
                    p_huida = Pieza(
                        id=f"Imp_S1_Repliegue_{onda.ciclo}",
                        tipo_componente="Impulso",
                        arousal=0.98,
                        trust=0.96,
                        product={
                            "comando": V_Comando.MOVER,
                            "target": mejor_huida,
                            "origen_sistema": "S1",
                            "es_supervivencia_pag": True,
                        },
                        inputs=[p_prop.id, pred_mas_cercano.id, self.id_componente],
                        sistemas_participantes={"S1"},
                    )
                    self.emitir_impulso(onda, p_huida, coste_amplitud=1)
                    return True

            # B. AMENAZA BALISTICA: ESQUELETO EN CORREDOR DE TIRO (DISTANCIA 2 A 4)
            esqueletos_en_tiro = []
            for p in depredadores:
                if str(p.product.get("tipo_entidad", "")) == "Skeleton":
                    ex = int(p.product.get("x", px))
                    ey = int(p.product.get("y", py))
                    d_man = int(p.product.get("distancia_manhattan", 99))
                    if d_man <= 4 and (ex == px or ey == py):
                        esqueletos_en_tiro.append((p, d_man, ex, ey))

            if esqueletos_en_tiro:
                skel_p, skel_dist, skel_x, skel_y = esqueletos_en_tiro[0]
                if salud >= 5 or tiene_espada:
                    # Cierre de distancia (Rush): Trabarlo en combate cuerpo a cuerpo donde es vulnerable
                    def distancia_a_esqueleto(n_id: str) -> float:
                        try:
                            n_parts = n_id.replace("nodo_", "").split("_")
                            return float(abs(int(n_parts[0]) - skel_x) + abs(int(n_parts[1]) - skel_y))
                        except Exception:
                            return 99.0

                    nodos_rush = sorted(nodos_seguros, key=distancia_a_esqueleto)
                    p_rush = Pieza(
                        id=f"Imp_S1_RushEsqueleto_{onda.ciclo}",
                        tipo_componente="Impulso",
                        arousal=0.97,
                        trust=0.95,
                        product={
                            "comando": V_Comando.MOVER,
                            "target": nodos_rush[0],
                            "origen_sistema": "S1",
                            "es_supervivencia_pag": True,
                        },
                        inputs=[p_prop.id, skel_p.id, self.id_componente],
                        sistemas_participantes={"S1"},
                    )
                    self.emitir_impulso(onda, p_rush, coste_amplitud=1)
                    return True
                else:
                    # Ruptura de línea de tiro (Evasión ortogonal): Desplazarse fuera del eje cardinal
                    def romper_eje_balistico(n_id: str) -> float:
                        try:
                            n_parts = n_id.replace("nodo_", "").split("_")
                            nx_b, ny_b = int(n_parts[0]), int(n_parts[1])
                            en_eje = (nx_b == skel_x or ny_b == skel_y)
                            dist_e = abs(nx_b - skel_x) + abs(ny_b - skel_y)
                            return float(dist_e if not en_eje else -5.0)
                        except Exception:
                            return 0.0

                    nodos_evasion = sorted(nodos_seguros, key=romper_eje_balistico, reverse=True)
                    p_evasion = Pieza(
                        id=f"Imp_S1_EvasionBalistica_{onda.ciclo}",
                        tipo_componente="Impulso",
                        arousal=0.97,
                        trust=0.95,
                        product={
                            "comando": V_Comando.MOVER,
                            "target": nodos_evasion[0],
                            "origen_sistema": "S1",
                            "es_supervivencia_pag": True,
                        },
                        inputs=[p_prop.id, skel_p.id, self.id_componente],
                        sistemas_participantes={"S1"},
                    )
                    self.emitir_impulso(onda, p_evasion, coste_amplitud=1)
                    return True

            # C. ZOMBI A DISTANCIA 2 (PROXIMIDAD TACTICA)
            if dist_min == 2 and tipo_mas_cercano == "Zombie":
                if (salud >= 6 or tiene_espada) and len(amenazas_inmediatas) <= 1:
                    # Posicionarse para interceptar
                    zx = int(pred_mas_cercano.product.get("x", px))
                    zy = int(pred_mas_cercano.product.get("y", py))
                    def coste_acercar_zombi(n_id: str) -> float:
                        try:
                            n_parts = n_id.replace("nodo_", "").split("_")
                            return float(abs(int(n_parts[0]) - zx) + abs(int(n_parts[1]) - zy))
                        except Exception:
                            return 99.0

                    nodos_intercep = sorted(nodos_seguros, key=coste_acercar_zombi)
                    p_intercep = Pieza(
                        id=f"Imp_S1_IntercepZombie_{onda.ciclo}",
                        tipo_componente="Impulso",
                        arousal=0.95,
                        trust=0.94,
                        product={
                            "comando": V_Comando.MOVER,
                            "target": nodos_intercep[0],
                            "origen_sistema": "S1",
                            "es_supervivencia_pag": True,
                        },
                        inputs=[p_prop.id, pred_mas_cercano.id, self.id_componente],
                        sistemas_participantes={"S1"},
                    )
                    self.emitir_impulso(onda, p_intercep, coste_amplitud=1)
                    return True
                elif salud <= 4 or len(amenazas_inmediatas) >= 2:
                    # Mantener distancia de seguridad (standoff >= 2 casillas)
                    zx = int(pred_mas_cercano.product.get("x", px))
                    zy = int(pred_mas_cercano.product.get("y", py))
                    def distancia_alejamiento(n_id: str) -> float:
                        try:
                            n_parts = n_id.replace("nodo_", "").split("_")
                            return float(abs(int(n_parts[0]) - zx) + abs(int(n_parts[1]) - zy))
                        except Exception:
                            return 0.0

                    nodos_dist = sorted(nodos_seguros, key=distancia_alejamiento, reverse=True)
                    p_dist = Pieza(
                        id=f"Imp_S1_Standoff_{onda.ciclo}",
                        tipo_componente="Impulso",
                        arousal=0.95,
                        trust=0.92,
                        product={
                            "comando": V_Comando.MOVER,
                            "target": nodos_dist[0],
                            "origen_sistema": "S1",
                            "es_supervivencia_pag": True,
                        },
                        inputs=[p_prop.id, pred_mas_cercano.id, self.id_componente],
                        sistemas_participantes={"S1"},
                    )
                    self.emitir_impulso(onda, p_dist, coste_amplitud=1)
                    return True

        # ---------------------------------------------------------------------
        # 2. EMERGENCIAS VISCERALES URGENTES (SEDIENTO O HAMBRIENTO)
        # ---------------------------------------------------------------------
        # Prioridad absoluta: Si la sed o el hambre bajan del umbral visceral (modulado por Weismann),
        # el organismo no puede distraerse con labores técnicas; debe beber o comer inmediatamente.
        if bebida <= umbral_visceral_urgente:
            aguas = [p for p in escena.values() if p.tipo_componente == "Nutriente_Agua"]
            if aguas:
                aguas.sort(key=lambda p: int(p.product.get("distancia_manhattan", 99)))
                agua_cercana = aguas[0]
                dist_a = int(agua_cercana.product.get("distancia_manhattan", 99))
                if dist_a == 1:
                    p_beber = Pieza(
                        id=f"Imp_S1_Beber_{onda.ciclo}",
                        tipo_componente="Impulso",
                        arousal=0.99,
                        trust=0.98,
                        product={
                            "comando": V_Comando.DEGLUTIR,
                            "target": str(agua_cercana.product.get("target_nodo", "")),
                            "origen_sistema": "S1",
                        },
                        inputs=[p_prop.id, agua_cercana.id, self.id_componente],
                        sistemas_participantes={"S1"},
                    )
                    self.emitir_impulso(onda, p_beber, coste_amplitud=1)
                    return True
                else:
                    # Acercarse al agua con máxima urgencia y anti-oscilación
                    ultimos_vis = set(historial[-4:]) if historial else set()
                    ax, ay = int(agua_cercana.product.get("x", px)), int(agua_cercana.product.get("y", py))
                    def coste_a_agua(nid: str) -> float:
                        try:
                            parts = nid.replace("nodo_", "").split("_")
                            pen = 2.5 if nid in ultimos_vis else 0.0
                            return float(abs(int(parts[0]) - ax) + abs(int(parts[1]) - ay)) + pen
                        except Exception:
                            return 99.0
                    nodos_hacia_agua = sorted(nodos_seguros, key=coste_a_agua)
                    p_mov_agua = Pieza(
                        id=f"Imp_S1_NavAgua_{onda.ciclo}",
                        tipo_componente="Impulso",
                        arousal=0.97,
                        trust=0.96,
                        product={"comando": V_Comando.MOVER, "target": nodos_hacia_agua[0], "origen_sistema": "S1"},
                        inputs=[p_prop.id, agua_cercana.id, self.id_componente],
                        sistemas_participantes={"S1"},
                    )
                    self.emitir_impulso(onda, p_mov_agua, coste_amplitud=1)
                    return True
            else:
                # Si el agua no está en la fóvea visual pero la sed apremia, consultar el Mapa Hipocampal Alocéntrico
                ultimos_vis = set(historial[-4:]) if historial else set()
                activa = ctx.get("activa")
                hitos_agua = activa.consultar_hitos_alocentricos(categoria="fuente_agua") if activa else []
                if hitos_agua:
                    hitos_agua.sort(key=lambda h: abs(int(h["propiedades"].get("x", px)) - px) + abs(int(h["propiedades"].get("y", py)) - py))
                    hx = int(hitos_agua[0]["propiedades"].get("x", px))
                    hy = int(hitos_agua[0]["propiedades"].get("y", py))
                    def coste_a_agua_mem(nid: str) -> float:
                        try:
                            parts = nid.replace("nodo_", "").split("_")
                            pen = 2.5 if nid in ultimos_vis else 0.0
                            return float(abs(int(parts[0]) - hx) + abs(int(parts[1]) - hy)) + pen
                        except Exception:
                            return 99.0
                    nodos_hacia_mem = sorted(nodos_seguros, key=coste_a_agua_mem)
                    p_mov_agua_mem = Pieza(
                        id=f"Imp_S1_HomingAgua_{onda.ciclo}",
                        tipo_componente="Impulso",
                        arousal=0.96,
                        trust=0.95,
                        product={"comando": V_Comando.MOVER, "target": nodos_hacia_mem[0], "origen_sistema": "S1"},
                        inputs=[p_prop.id, self.id_componente],
                        sistemas_participantes={"S1"},
                    )
                    self.emitir_impulso(onda, p_mov_agua_mem, coste_amplitud=1)
                    return True

        if comida <= umbral_visceral_urgente:
            comidas = [p for p in escena.values() if p.tipo_componente == "Nutriente_Alimento"]
            if comidas:
                comidas.sort(key=lambda p: int(p.product.get("distancia_manhattan", 99)))
                comida_cercana = comidas[0]
                dist_c = int(comida_cercana.product.get("distancia_manhattan", 99))
                if dist_c == 1:
                    p_comer = Pieza(
                        id=f"Imp_S1_Comer_{onda.ciclo}",
                        tipo_componente="Impulso",
                        arousal=0.98,
                        trust=0.98,
                        product={
                            "comando": V_Comando.DEGLUTIR,
                            "target": str(comida_cercana.product.get("target_nodo", "")),
                            "origen_sistema": "S1",
                        },
                        inputs=[p_prop.id, comida_cercana.id, self.id_componente],
                        sistemas_participantes={"S1"},
                    )
                    self.emitir_impulso(onda, p_comer, coste_amplitud=1)
                    return True
                else:
                    # Acercarse a la comida con máxima urgencia y anti-oscilación
                    ultimos_vis = set(historial[-4:]) if historial else set()
                    cx_t, cy_t = int(comida_cercana.product.get("x", px)), int(comida_cercana.product.get("y", py))
                    def coste_a_comida(nid: str) -> float:
                        try:
                            parts = nid.replace("nodo_", "").split("_")
                            pen = 2.5 if nid in ultimos_vis else 0.0
                            return float(abs(int(parts[0]) - cx_t) + abs(int(parts[1]) - cy_t)) + pen
                        except Exception:
                            return 99.0
                    nodos_hacia_comida = sorted(nodos_seguros, key=coste_a_comida)
                    p_mov_comida = Pieza(
                        id=f"Imp_S1_NavComida_{onda.ciclo}",
                        tipo_componente="Impulso",
                        arousal=0.96,
                        trust=0.95,
                        product={"comando": V_Comando.MOVER, "target": nodos_hacia_comida[0], "origen_sistema": "S1"},
                        inputs=[p_prop.id, comida_cercana.id, self.id_componente],
                        sistemas_participantes={"S1"},
                    )
                    self.emitir_impulso(onda, p_mov_comida, coste_amplitud=1)
                    return True

        # ---------------------------------------------------------------------
        # 3. GRADIENTE APETITIVO GENERAL Y FORRAJE ECOLOGICO (ANTI-OSCILACION)
        # ---------------------------------------------------------------------
        if sleeping or (daylight < 0.25 and not depredadores and energia <= 6 and "wake_up" not in logros_actuales):
            return False
        ultimos_visitados = set(historial[-4:]) if historial else set()
        candidatos_nuevos = [n for n in nodos_seguros if n not in ultimos_visitados]
        nodo_anterior = historial[-2] if len(historial) >= 2 else None
        candidatos = candidatos_nuevos if candidatos_nuevos else [n for n in nodos_seguros if n != nodo_anterior]
        if not candidatos:
            candidatos = nodos_seguros

        # Encontrar la pieza de escena más saliente según estado homeostático real
        # Si la sed está satisfecha (bebida >= 7), no buscar agua.
        # Si el hambre está satisfecha (comida >= 7), no forrajear comida inmediata.
        pool_tipos: List[str] = []
        if bebida <= 6:
            pool_tipos.append("Nutriente_Agua")
        if comida <= 6:
            pool_tipos.append("Nutriente_Alimento")
        pool_tipos.append("Recurso_Material")
        pool_tipos.append("Estacion_Trabajo")

        objetivos = [
            p for p in escena.values()
            if p.tipo_componente in pool_tipos
        ]
        if not objetivos:
            objetivos = [
                p for p in escena.values()
                if p.tipo_componente in ("Nutriente_Alimento", "Nutriente_Agua", "Recurso_Material")
            ]

        if objetivos:
            # Ordenar por proximidad y saliencia
            objetivos.sort(key=lambda p: (int(p.product.get("distancia_manhattan", 99)), -p.arousal))
            target_obj = objetivos[0]
            dist_obj = int(target_obj.product.get("distancia_manhattan", 99))
            tox = int(target_obj.product.get("x", px))
            toy = int(target_obj.product.get("y", py))

            # Si hay agua o alimento adyacente y existe déficit moderado, deglutir oportunistamente
            if dist_obj == 1 and (
                (target_obj.tipo_componente == "Nutriente_Agua" and bebida <= 7)
                or (target_obj.tipo_componente == "Nutriente_Alimento" and comida <= 7)
            ):
                p_forraje = Pieza(
                    id=f"Imp_S1_Forraje_{onda.ciclo}",
                    tipo_componente="Impulso",
                    arousal=0.88,
                    trust=0.92,
                    product={
                        "comando": V_Comando.DEGLUTIR,
                        "target": str(target_obj.product.get("target_nodo", f"nodo_{tox}_{toy}")),
                        "origen_sistema": "S1",
                    },
                    inputs=[p_prop.id, target_obj.id, self.id_componente],
                    sistemas_participantes={"S1"},
                )
                self.emitir_impulso(onda, p_forraje, coste_amplitud=1)
                return True

            def coste_hacia_objetivo(n_id: str) -> float:
                try:
                    n_parts = n_id.replace("nodo_", "").split("_")
                    return float(abs(int(n_parts[0]) - tox) + abs(int(n_parts[1]) - toy))
                except Exception:
                    return 0.0

            candidatos.sort(key=coste_hacia_objetivo)

        mejor_candidato = candidatos[0]
        p_mov = Pieza(
            id=f"Imp_S1_Mov_{onda.ciclo}",
            tipo_componente="Impulso",
            arousal=0.72,
            trust=0.68,
            product={"comando": V_Comando.MOVER, "target": mejor_candidato, "origen_sistema": "S1"},
            inputs=[p_prop.id, self.id_componente],
            sistemas_participantes={"S1"},
        )
        self.emitir_impulso(onda, p_mov, coste_amplitud=1)
        return True


class CompCrafterS2(ComponenteCognitivoBase):
    """
    Componente Límbico S2: Escalera Ontológica, Ritmo Circadiano y Afecto de Supervivencia.
    - Proposiciones formales:
      - Vaca_ES_NUTRITIVO (DEMOSTRADO)
      - Agua_ES_BEBIBLE (DEMOSTRADO)
      - Zombie_ES_LETAL / Esqueleto_ES_LETAL (DEMOSTRADO)
      - Noche_ES_PELIGROSA (DEMOSTRADO)
    - Modulación Circadiana: La noche induce miedo somático y activa el impulso de cobijo / descanso.
    - Modulación de Personalidad (Big Five & Epigenética):
      - Alto Neuroticismo incrementa el arousal ante depredadores y oscuridad.
      - Alta Apertura fomenta la curiosidad por recursos distantes.
    """

    def __init__(self, peso_sinaptico: float = 1.15):
        super().__init__("Comp_CrafterS2", "S2", peso_sinaptico=peso_sinaptico)

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        escena = onda.reactiva.ev.get("Escena", {})
        if not escena:
            return False

        p_estado = next((p for p in escena.values() if p.tipo_componente == "Estado_Entorno"), None)
        if not p_estado:
            return False

        daylight = float(p_estado.product.get("daylight", 1.0))
        fase_circadiana = str(p_estado.product.get("fase_circadiana", "DIA"))
        energia = int(p_estado.product.get("energia", 9))
        salud = int(p_estado.product.get("salud", 9))

        # Moduladores epigenéticos de personalidad
        arquetipo = ctx.get("arquetipo")
        neuroticismo = float(getattr(arquetipo, "neuroticismo", 0.40)) if arquetipo else 0.40
        apertura = float(getattr(arquetipo, "apertura", 0.65)) if arquetipo else 0.65
        umbral_miedo = float(getattr(arquetipo, "umbral_miedo", 0.60)) if arquetipo else 0.60

        # ---------------------------------------------------------------------
        # 1. PROPOSICIONES ONTOLOGICAS DE ESCENA
        # ---------------------------------------------------------------------
        proposiciones_ontologicas: List[Dict[str, Any]] = []

        # A. Proposición Circadiana
        es_noche = daylight < 0.25
        arousal_circadiano = float(np.clip(0.40 + (0.50 * (1.0 - daylight)) + (0.20 * neuroticismo), 0.2, 1.0))

        prop_noche = {
            "id": f"Prop_Circadiana_{onda.ciclo}",
            "sujeto": "Ciclo_Nocturno",
            "predicado": {
                "fase": fase_circadiana,
                "daylight": daylight,
                "relacion": V_Relacion.ES_TERRORIFICO if es_noche else V_Relacion.ES_SEGURO,
            },
            "modalidad": V_Modalidad.DEMOSTRADO,
            "trust": 0.99,
        }
        proposiciones_ontologicas.append(prop_noche)

        p_prop_circ = Pieza(
            id=prop_noche["id"],
            tipo_componente="Proposicion_Ontologica",
            arousal=arousal_circadiano,
            trust=0.99,
            product=prop_noche,
            inputs=[self.id_componente],
            sistemas_participantes={"S2"},
        )
        onda.reactiva.proyectar_atencion_ev(self.id_componente, p_prop_circ, onda_ref=onda, coste_amplitud=0)

        # B. Proposiciones sobre Entidades y Recursos en Escena
        for p in escena.values():
            rel = p.product.get("relacion")
            if rel in (V_Relacion.ES_NUTRITIVO, V_Relacion.ES_LETAL, V_Relacion.ES_SEGURO, V_Relacion.ES_FIABLE):
                prop_ent = {
                    "id": f"Prop_{p.id}",
                    "sujeto": str(p.product.get("sujeto", p.id)),
                    "tipo_entidad": str(p.product.get("tipo_entidad", "")),
                    "relacion": rel,
                    "distancia": p.product.get("distancia_manhattan", 0),
                    "modalidad": V_Modalidad.DEMOSTRADO,
                    "trust": p.trust,
                }
                proposiciones_ontologicas.append(prop_ent)

        # C. Consolidación en el Mapa Cognitivo Alocéntrico Hipocampal (Place Cells)
        activa = ctx.get("activa")
        if activa is not None:
            for p in escena.values():
                t_nodo = str(p.product.get("target_nodo", ""))
                px_e = p.product.get("x")
                py_e = p.product.get("y")
                if not t_nodo or px_e is None or py_e is None:
                    continue

                if p.tipo_componente == "Estacion_Trabajo":
                    activa.registrar_hito_alocentrico(
                        ubicacion=t_nodo,
                        categoria="estacion_trabajo",
                        tipo_entidad=str(p.product.get("tipo_entidad", "")),
                        ciclo=onda.ciclo,
                        permanencia=1.0,
                        propiedades={"x": px_e, "y": py_e},
                    )
                elif p.tipo_componente == "Nutriente_Agua":
                    activa.registrar_hito_alocentrico(
                        ubicacion=t_nodo,
                        categoria="fuente_agua",
                        tipo_entidad="agua",
                        ciclo=onda.ciclo,
                        permanencia=0.95,
                        propiedades={"x": px_e, "y": py_e},
                    )
                elif p.tipo_componente == "Recurso_Material" and p.product.get("tipo_entidad") in ("stone", "coal", "iron"):
                    activa.registrar_hito_alocentrico(
                        ubicacion=t_nodo,
                        categoria="yacimiento_mineral",
                        tipo_entidad=str(p.product.get("tipo_entidad", "")),
                        ciclo=onda.ciclo,
                        permanencia=0.90,
                        propiedades={"x": px_e, "y": py_e},
                    )

        # ---------------------------------------------------------------------
        # 2. IMPULSO LIMBICO DE SUEÑO / REPOSO SI ES DE NOCHE Y SEGURO
        # ---------------------------------------------------------------------
        hay_depredadores = any(p.tipo_componente == "Amenaza_Predador" for p in escena.values())
        sleeping = bool(p_estado.product.get("sleeping", False))

        if sleeping or (es_noche and not hay_depredadores and (energia <= 7 or salud < 9)):
            # Emitir impulso de sueño reparador (alostático y desbloqueo del logro wake_up)
            p_dormir = Pieza(
                id=f"Imp_S2_Dormir_{onda.ciclo}",
                tipo_componente="Impulso",
                arousal=0.98,
                trust=0.99,
                product={"comando": V_Comando.ESPERAR, "target": "DORMIR", "origen_sistema": "S2", "dormir": True},
                inputs=[p_prop_circ.id, self.id_componente],
                sistemas_participantes={"S2"},
            )
            self.emitir_impulso(onda, p_dormir, coste_amplitud=1)

        return True


class CompCrafterS3(ComponenteCognitivoBase):
    """
    Componente Deliberativo S3: Causal Tech Tree y Planificación Estratégica en Crafter.
    - Progresión Tecnológica de Supervivencia:
      1. Forrajeo y Agua (asegurar reservas basales).
      2. Recolección de Madera (talar árbol -> wood >= 1).
      3. Crafteo de Mesa y Pico de Madera (place_table, make_wood_pickaxe).
      4. Minería de Piedra y Carbón (make_stone_pickaxe, make_stone_sword).
      5. Fundición y Armamento (place_furnace, make_iron_sword).
    - Planificación de Rutas Topológicas (BFS):
      - Guía la navegación multi-paso hacia el objetivo estratégico activo.
      - Veta impulsos impulsivos de S1 que caigan en trampas o se alejen del objetivo.
    """

    def __init__(self, peso_sinaptico: float = 1.35):
        super().__init__("Comp_CrafterS3", "S3", peso_sinaptico=peso_sinaptico)

    @classmethod
    def _calcular_camino_bfs(
        cls,
        inicio: Tuple[int, int],
        destino: Tuple[int, int],
        nodos_caminables: Set[Tuple[int, int]],
        max_pasos: int = 50,
    ) -> List[Tuple[int, int]]:
        """Calcula el camino más corto entre dos puntos evitando obstáculos."""
        if inicio == destino:
            return [inicio]

        cola = deque([(inicio, [inicio])])
        visitados: Set[Tuple[int, int]] = {inicio}

        while cola and len(visitados) < max_pasos:
            actual, camino = cola.popleft()
            cx, cy = actual

            for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
                nx, ny = cx + dx, cy + dy
                vecino = (nx, ny)

                if vecino == destino:
                    return camino + [vecino]

                if vecino in nodos_caminables and vecino not in visitados:
                    visitados.add(vecino)
                    cola.append((vecino, camino + [vecino]))

        return []

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        prop = onda.reactiva.ev.get("Propiocepcion", {})
        if not prop:
            return False

        p_prop = next(iter(prop.values()))
        nodo_actual = str(p_prop.product.get("ubicacion", ""))
        nodos_adyacentes: List[str] = list(p_prop.product.get("nodos_adyacentes", []))
        if not nodos_adyacentes:
            return False

        escena = onda.reactiva.ev.get("Escena", {})
        p_estado = next((p for p in escena.values() if p.tipo_componente == "Estado_Entorno"), None)
        if not p_estado:
            return False

        inv = p_estado.product
        salud = int(inv.get("salud", 9))
        comida = int(inv.get("comida", 9))
        bebida = int(inv.get("bebida", 9))
        energia = int(inv.get("energia", 9))
        madera = int(inv.get("madera", 0))
        piedra = int(inv.get("piedra", 0))
        carbon = int(inv.get("carbon", 0))
        hierro = int(inv.get("hierro", 0))
        diamante = int(inv.get("diamante", 0))
        wood_pickaxe = int(inv.get("wood_pickaxe", 0))
        stone_pickaxe = int(inv.get("stone_pickaxe", 0))
        iron_pickaxe = int(inv.get("iron_pickaxe", 0))
        wood_sword = int(inv.get("wood_sword", 0))
        stone_sword = int(inv.get("stone_sword", 0))
        iron_sword = int(inv.get("iron_sword", 0))
        sapling = int(inv.get("sapling", 0))
        historial = list(p_prop.product.get("historial_nodos", []))
        nodos_caminables_raw = inv.get("nodos_caminables", [])
        nodos_caminables: Set[Tuple[int, int]] = {
            (int(c[0]), int(c[1])) for c in nodos_caminables_raw if isinstance(c, (list, tuple)) and len(c) == 2
        }

        try:
            partes = nodo_actual.replace("nodo_", "").split("_")
            px, py = int(partes[0]), int(partes[1])
        except Exception:
            px, py = 32, 32

        # ---------------------------------------------------------------------
        # 1. EVALUACION DEL OBJETIVO ESTRATEGICO DEL ARBOL TECNOLOGICO
        #    (Modulada causalmente por Arquetipo + Linaje Epigenético Weismann)
        # ---------------------------------------------------------------------
        activa = ctx.get("activa")
        arquetipo = ctx.get("arquetipo")
        resp_s3 = float(getattr(arquetipo, "responsabilidad", 0.50)) if arquetipo else 0.50
        apertura_s3 = float(getattr(arquetipo, "apertura", 0.50)) if arquetipo else 0.50

        patrones_exito = activa.indice_por_tipo.get("Patron_Exito_Estrategico", {}) if activa else {}
        logros_ancestrales = {
            str(p.product.get("logro_obtenido", ""))
            for p in patrones_exito.values()
        }
        aversiones_mem = activa.indice_por_tipo.get("Aversion_Traumatica", {}) if activa else {}
        proposiciones_mem = activa.indice_por_tipo.get("Proposicion_VERDAD", {}) if activa else {}

        madurez_intermedia = (
            (len(logros_ancestrales) >= 4 or len(aversiones_mem) > 0 or len(proposiciones_mem) > 0)
            and resp_s3 >= 0.56
        )
        madurez_epigenetica = (
            (len(logros_ancestrales) >= 6 or len(aversiones_mem) > 0 or len(proposiciones_mem) >= 2)
            and resp_s3 >= 0.65
        )
        # Umbral alostático progresivo: 1 (fundador) -> 3 (madurez intermedia) -> 4 (madurez plena)
        umbral_alostatico_s3 = 4 if madurez_epigenetica else (3 if madurez_intermedia else 1)

        # Inhibición Homeostática y de Alarma Vital: Si hay sed/hambre por debajo del umbral alostático,
        # sueño activo o amenazas letales inminentes (distancia <= 2), S3 no distrae con labores pasivas
        if bebida <= umbral_alostatico_s3 or comida <= umbral_alostatico_s3:
            return False

        sleeping = bool(inv.get("sleeping", False))
        daylight = float(inv.get("daylight", 1.0))
        logros_actuales = set(inv.get("logros_actuales", []))
        hay_depredadores_escena = any(p.tipo_componente == "Amenaza_Predador" for p in escena.values())
        if sleeping or (daylight < 0.25 and not hay_depredadores_escena and energia <= 6 and "wake_up" not in logros_actuales):
            return False

        meta_accion: Optional[str] = None
        tipo_meta: str = "FORRAJE"

        # Comprobar presencia de mesa de trabajo y horno adyacentes (distancia Chebyshev <= 1)
        mesas_en_escena = [
            m for m in escena.values()
            if m.tipo_componente == "Estacion_Trabajo" and m.product.get("tipo_entidad") == "table"
        ]
        mesas_cercanas = [
            m for m in mesas_en_escena
            if max(abs(int(m.product.get("x", 99)) - px), abs(int(m.product.get("y", 99)) - py)) <= 1
        ]
        mesa_adyacente = len(mesas_cercanas) > 0

        hornos_en_escena = [
            m for m in escena.values()
            if m.tipo_componente == "Estacion_Trabajo" and m.product.get("tipo_entidad") == "furnace"
        ]
        hornos_cercanos = [
            m for m in hornos_en_escena
            if max(abs(int(m.product.get("x", 99)) - px), abs(int(m.product.get("y", 99)) - py)) <= 1
        ]
        horno_adyacente = len(hornos_cercanos) > 0

        # Radio de memoria alocéntrica de mesa: 2 (novato) -> 6 (intermedio) -> 12 (maduro)
        radio_mesa = 12 if madurez_epigenetica else (6 if madurez_intermedia else 2)
        # Gratificación diferida: 2 (novato) -> 3 (intermedio) -> 4 (maduro)
        stock_madera_mesa = 4 if madurez_epigenetica else (3 if madurez_intermedia else 2)
        horizonte_bfs = 80 if madurez_epigenetica else (32 if madurez_intermedia else 8)

        hitos_mesa_mem = activa.consultar_hitos_alocentricos(categoria="estacion_trabajo", tipo_entidad="table") if (activa and madurez_intermedia) else []
        hay_mesa_conocida = bool(mesas_en_escena) or any(
            abs(int(h["propiedades"].get("x", 99)) - px) + abs(int(h["propiedades"].get("y", 99)) - py) <= radio_mesa
            for h in hitos_mesa_mem
        )

        amenazas_inmediatas = [
            p for p in escena.values()
            if p.tipo_componente == "Amenaza_Predador" and int(p.product.get("distancia_manhattan", 99)) <= 2
        ]
        if amenazas_inmediatas:
            # Si hay amenazas inmediatas, S3 solo interviene si puede armar al organismo al instante
            if madurez_epigenetica and mesa_adyacente and horno_adyacente and hierro >= 1 and carbon >= 1 and madera >= 1 and iron_sword == 0:
                meta_accion = "make_iron_sword"
            elif madurez_epigenetica and mesa_adyacente and piedra >= 1 and madera >= 1 and stone_sword == 0:
                meta_accion = "make_stone_sword"
            elif mesa_adyacente and madera >= 1 and wood_sword == 0:
                meta_accion = "make_wood_sword"
            else:
                return False

        # Prioridad 1: Ampliación de affordance mecánica si estamos adyacentes a la mesa
        if mesa_adyacente:
            if madera >= 1 and wood_pickaxe == 0:
                meta_accion = "make_wood_pickaxe"
            elif madera >= 1 and wood_sword == 0 and (madurez_epigenetica or "make_wood_sword" in logros_ancestrales or apertura_s3 >= 0.50):
                meta_accion = "make_wood_sword"
            elif piedra >= 1 and madera >= 1 and stone_pickaxe == 0 and (madurez_epigenetica or "make_wood_pickaxe" in logros_ancestrales or resp_s3 >= 0.55):
                meta_accion = "make_stone_pickaxe"
            elif piedra >= 1 and madera >= 1 and stone_sword == 0 and (madurez_epigenetica or "make_stone_sword" in logros_ancestrales):
                meta_accion = "make_stone_sword"
            elif piedra >= 4 and stone_pickaxe > 0 and not horno_adyacente and not hornos_en_escena and madurez_epigenetica:
                meta_accion = "place_furnace"
            elif horno_adyacente and hierro >= 1 and carbon >= 1 and madera >= 1 and iron_pickaxe == 0 and madurez_epigenetica:
                meta_accion = "make_iron_pickaxe"
            elif horno_adyacente and hierro >= 1 and carbon >= 1 and madera >= 1 and iron_sword == 0 and madurez_epigenetica:
                meta_accion = "make_iron_sword"
            elif not horno_adyacente and hornos_en_escena and hierro >= 1 and carbon >= 1 and madera >= 1 and (iron_pickaxe == 0 or iron_sword == 0) and madurez_epigenetica:
                tipo_meta = "BUSCAR_HORNO"
            elif sapling >= 1 and (madurez_epigenetica or "place_plant" in logros_ancestrales):
                meta_accion = "place_plant"
            elif wood_pickaxe > 0 and (stone_pickaxe == 0 or (stone_sword == 0 and madurez_epigenetica)):
                if madera < 1:
                    tipo_meta = "TALAR_MADERA"
                else:
                    tipo_meta = "MINAR_PIEDRA"
            elif stone_pickaxe > 0 and madurez_epigenetica and (hierro < 1 or carbon < 1 or (piedra < 4 and not horno_adyacente and not hornos_en_escena)):
                if madera < 1:
                    tipo_meta = "TALAR_MADERA"
                else:
                    tipo_meta = "MINAR_PIEDRA"
            else:
                tipo_meta = "TALAR_MADERA"
        # Prioridad 2: Si ya conocemos una mesa cercana y tenemos los materiales para fabricar, ir a la mesa
        elif hay_mesa_conocida and (
            (wood_pickaxe == 0 and madera >= 1)
            or (wood_sword == 0 and madera >= 1 and wood_pickaxe > 0 and madurez_intermedia)
            or ((stone_pickaxe == 0 or (stone_sword == 0 and madurez_epigenetica)) and piedra >= 1 and madera >= 1 and madurez_intermedia)
            or (stone_pickaxe > 0 and piedra >= 4 and not horno_adyacente and madurez_epigenetica)
            or (stone_pickaxe > 0 and hierro >= 1 and carbon >= 1 and madera >= 1 and (iron_pickaxe == 0 or iron_sword == 0) and madurez_epigenetica)
        ):
            tipo_meta = "BUSCAR_MESA"
        # Prioridad 3: Si no hay mesa cercana y acumulamos >= stock_madera_mesa, colocar mesa
        elif madera >= stock_madera_mesa and wood_pickaxe == 0:
            meta_accion = "place_table"
        # Prioridad 4: Si no hay mesa cercana pero ya tenemos piedra + 3 de madera, colocar mesa
        elif not hay_mesa_conocida and madera >= 3 and piedra >= 1 and (stone_pickaxe == 0 or stone_sword == 0) and madurez_intermedia:
            meta_accion = "place_table"
        # Prioridad 5: Talar madera inicial hasta reunir stock_madera_mesa unidades
        elif wood_pickaxe == 0:
            tipo_meta = "TALAR_MADERA"
        # Prioridad 6: Si tenemos pico de madera y nos falta pico/espada de piedra, reunir madera y minar piedra
        elif wood_pickaxe > 0 and (stone_pickaxe == 0 or (stone_sword == 0 and madurez_epigenetica)):
            if madera < (2 if madurez_epigenetica else 1):
                tipo_meta = "TALAR_MADERA"
            else:
                tipo_meta = "MINAR_PIEDRA"
        # Prioridad 7: Cultivo de esqueje recolectado
        elif sapling >= 1 and (madurez_epigenetica or "place_plant" in logros_ancestrales):
            meta_accion = "place_plant"
        # Prioridad 8: Si ya tenemos pico de piedra y piedra sobrante, colocar bloque defensivo de piedra una vez
        elif stone_pickaxe > 0 and stone_sword > 0 and piedra >= 1 and "place_stone" not in logros_actuales and madurez_epigenetica:
            meta_accion = "place_stone"
        # Prioridad 9: Con pico de piedra, minar hierro, carbón y piedra para horno y metalurgia
        elif stone_pickaxe > 0 and madurez_epigenetica:
            if madera < 2:
                tipo_meta = "TALAR_MADERA"
            else:
                tipo_meta = "MINAR_PIEDRA"
        # Prioridad 9: Talar madera para reponer reservas estructurales
        elif madera < 3:
            tipo_meta = "TALAR_MADERA"
        else:
            tipo_meta = "EXPLORAR"

        # ---------------------------------------------------------------------
        # 2. EJECUCION DE CRAFTING DIRECTO SI SE CUMPLEN CONDICIONES
        # ---------------------------------------------------------------------
        if meta_accion is not None:
            consolidado_weismann = meta_accion in logros_ancestrales
            p_craft = Pieza(
                id=f"Imp_S3_Craft_{meta_accion}_{onda.ciclo}",
                tipo_componente="Impulso",
                arousal=0.96 if consolidado_weismann else (0.93 if madurez_epigenetica else 0.88),
                trust=0.98 if consolidado_weismann else (0.94 if madurez_epigenetica else 0.89),
                product={
                    "comando": V_Comando.COGER,
                    "target": meta_accion,
                    "origen_sistema": "S3",
                    "meta_tecnologica": meta_accion,
                    "consolidado_weismann": consolidado_weismann,
                },
                inputs=[p_prop.id, self.id_componente],
                sistemas_participantes={"S3"},
            )
            self.emitir_impulso(onda, p_craft, coste_amplitud=1)
            return True

        # ---------------------------------------------------------------------
        # 3. NAVEGACION TOPOLOGICA HACIA EL OBJETIVO ESTRATEGICO
        # ---------------------------------------------------------------------
        candidatos_entidad: List[Pieza] = []

        if tipo_meta == "BUSCAR_AGUA":
            candidatos_entidad = [p for p in escena.values() if p.tipo_componente == "Nutriente_Agua"]
        elif tipo_meta == "BUSCAR_COMIDA":
            candidatos_entidad = [p for p in escena.values() if p.tipo_componente == "Nutriente_Alimento"]
        elif tipo_meta == "TALAR_MADERA":
            candidatos_entidad = [
                p for p in escena.values()
                if p.tipo_componente == "Recurso_Material" and p.product.get("tipo_entidad") == "tree"
            ]
        elif tipo_meta == "MINAR_PIEDRA":
            tipos_minables = {"stone", "coal"}
            if stone_pickaxe > 0:
                tipos_minables.add("iron")
            if iron_pickaxe > 0:
                tipos_minables.add("diamond")
            candidatos_entidad = [
                p for p in escena.values()
                if p.tipo_componente == "Recurso_Material" and p.product.get("tipo_entidad") in tipos_minables
            ]
        elif tipo_meta == "BUSCAR_MESA":
            candidatos_entidad = list(mesas_en_escena)
        elif tipo_meta == "BUSCAR_HORNO":
            candidatos_entidad = list(hornos_en_escena)

        if not candidatos_entidad:
            # Consulta al Mapa Cognitivo Alocéntrico Hipocampal si el objetivo no está en la fóvea visual
            if activa is not None:
                if tipo_meta == "BUSCAR_MESA" and hitos_mesa_mem:
                    hitos_m = sorted(
                        hitos_mesa_mem,
                        key=lambda h: abs(int(h["propiedades"].get("x", px)) - px) + abs(int(h["propiedades"].get("y", py)) - py),
                    )
                    mx = int(hitos_m[0]["propiedades"].get("x", px))
                    my = int(hitos_m[0]["propiedades"].get("y", py))
                    p_mem_mesa = Pieza(
                        id=f"Hito_Memoria_Mesa_{mx}_{my}",
                        tipo_componente="Estacion_Trabajo",
                        arousal=0.93,
                        trust=hitos_m[0]["permanencia"],
                        product={
                            "x": mx,
                            "y": my,
                            "target_nodo": hitos_m[0]["ubicacion"],
                            "distancia_manhattan": abs(mx - px) + abs(my - py),
                            "tipo_entidad": "table",
                        },
                    )
                    candidatos_entidad = [p_mem_mesa]

                elif tipo_meta == "MINAR_PIEDRA" and madurez_epigenetica:
                    hitos_p = activa.consultar_hitos_alocentricos(categoria="yacimiento_mineral")
                    if stone_pickaxe == 0:
                        hitos_p = [h for h in hitos_p if h.get("tipo_entidad") in ("stone", "coal")]
                    if hitos_p:
                        hitos_p.sort(key=lambda h: abs(int(h["propiedades"].get("x", px)) - px) + abs(int(h["propiedades"].get("y", py)) - py))
                        sx = int(hitos_p[0]["propiedades"].get("x", px))
                        sy = int(hitos_p[0]["propiedades"].get("y", py))
                        t_ent = str(hitos_p[0].get("tipo_entidad", "stone"))
                        p_mem_piedra = Pieza(
                            id=f"Hito_Memoria_Piedra_{sx}_{sy}",
                            tipo_componente="Recurso_Material",
                            arousal=0.90,
                            trust=hitos_p[0]["permanencia"],
                            product={
                                "x": sx,
                                "y": sy,
                                "target_nodo": hitos_p[0]["ubicacion"],
                                "distancia_manhattan": abs(sx - px) + abs(sy - py),
                                "tipo_entidad": t_ent,
                            },
                        )
                        candidatos_entidad = [p_mem_piedra]

        if not candidatos_entidad:
            # Fallback: cualquier recurso útil o forrajeo general
            candidatos_entidad = [
                p for p in escena.values()
                if p.tipo_componente in ("Nutriente_Alimento", "Nutriente_Agua", "Recurso_Material")
            ]

        if candidatos_entidad:
            # Priorizar minerales de mayor valor tecnológico cuando buscamos minar
            def prioridad_entidad(p: Pieza) -> Tuple[int, int]:
                dist_e = int(p.product.get("distancia_manhattan", 99))
                t_e = str(p.product.get("tipo_entidad", ""))
                bonus = 0
                if tipo_meta == "MINAR_PIEDRA":
                    if t_e == "diamond" and iron_pickaxe > 0:
                        bonus = -4
                    elif t_e == "iron" and stone_pickaxe > 0 and hierro == 0:
                        bonus = -3
                    elif t_e == "coal" and carbon == 0:
                        bonus = -2
                return (dist_e + bonus, dist_e)

            candidatos_entidad.sort(key=prioridad_entidad)
            target_pieza = candidatos_entidad[0]
            tx = int(target_pieza.product.get("x", px))
            ty = int(target_pieza.product.get("y", py))
            dist = int(target_pieza.product.get("distancia_manhattan", 99))

            # Si ya estamos adyacentes a la entidad recolectable/nutritiva: interactuar con ella ('do')
            if dist == 1 and target_pieza.tipo_componente != "Estacion_Trabajo":
                cmd = (
                    V_Comando.DEGLUTIR if target_pieza.tipo_componente in ("Nutriente_Alimento", "Nutriente_Agua")
                    else V_Comando.COGER
                )
                p_interact = Pieza(
                    id=f"Imp_S3_Interact_{onda.ciclo}",
                    tipo_componente="Impulso",
                    arousal=0.95,
                    trust=0.97,
                    product={
                        "comando": cmd,
                        "target": str(target_pieza.product.get("target_nodo", f"nodo_{tx}_{ty}")),
                        "origen_sistema": "S3",
                        "objetivo": target_pieza.id,
                    },
                    inputs=[p_prop.id, target_pieza.id, self.id_componente],
                    sistemas_participantes={"S3"},
                )
                self.emitir_impulso(onda, p_interact, coste_amplitud=1)
                return True

            # Si está más lejos, calcular ruta BFS evitando obstáculos y oscilaciones
            mejor_nodo = None
            if nodos_caminables:
                # Añadir el destino al conjunto caminable para que el BFS llegue a la casilla adyacente
                caminables_bfs = set(nodos_caminables) | {(tx, ty)}
                camino = self._calcular_camino_bfs((px, py), (tx, ty), caminables_bfs, max_pasos=horizonte_bfs)
                if len(camino) >= 2:
                    nx_bfs, ny_bfs = camino[1]
                    cand_bfs = f"nodo_{nx_bfs}_{ny_bfs}"
                    if cand_bfs in nodos_adyacentes:
                        mejor_nodo = cand_bfs

            ultimos_visitados = set(historial[-4:]) if historial else set()

            def coste_hacia_target(n_id: str) -> float:
                try:
                    n_parts = n_id.replace("nodo_", "").split("_")
                    penalizacion_osc = 2.5 if n_id in ultimos_visitados else 0.0
                    return float(abs(int(n_parts[0]) - tx) + abs(int(n_parts[1]) - ty)) + penalizacion_osc
                except Exception:
                    return 99.0

            if mejor_nodo is None or mejor_nodo in ultimos_visitados:
                nodos_ordenados = sorted(nodos_adyacentes, key=coste_hacia_target)
                mejor_nodo = nodos_ordenados[0]

            # Veto selectivo de S1: S3 solo modula la marcha exploratoria pasiva (Imp_S1_Mov).
            # PRINCIPIO BIOLOGICO INQUEBRANTABLE: El neocortex JAMAS veta defensas PAG, ataques, ni sed/hambre
            impulsos_acc = onda.reactiva.acc.get("Impulso", {})
            for imp in impulsos_acc.values():
                if imp.product.get("es_supervivencia_pag"):
                    continue
                if imp.product.get("comando") in (V_Comando.ATACAR, V_Comando.DEGLUTIR):
                    continue
                if any(k in imp.id for k in ("Huida", "Repliegue", "Beber", "Comer", "Evasion", "Rush")):
                    continue

                t_s1 = str(imp.product.get("target", ""))
                if t_s1 != mejor_nodo:
                    imp.arousal = 0.10
                    imp.trust = 0.20
                    imp.product["veto_s3_estrategico"] = True

            p_mov_s3 = Pieza(
                id=f"Imp_S3_Nav_{onda.ciclo}",
                tipo_componente="Impulso",
                arousal=0.93,
                trust=0.98,
                product={
                    "comando": V_Comando.MOVER,
                    "target": mejor_nodo,
                    "origen_sistema": "S3",
                    "meta_estrategica": tipo_meta,
                    "destino_final": (tx, ty),
                },
                inputs=[p_prop.id, target_pieza.id, self.id_componente],
                sistemas_participantes={"S3"},
            )
            self.emitir_impulso(onda, p_mov_s3, coste_amplitud=1)
            return True

        return False
