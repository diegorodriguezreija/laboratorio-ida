from typing import Dict, Any, List, Tuple, Set, Optional
from collections import deque
import numpy as np

from nivel_1_core.vocabulario import V_Comando, V_Relacion
from nivel_1_core.contratos import Pieza, Onda
from nivel_2_sistemas.sistema_base import ComponenteCognitivoBase


class CompSupervivenciaSnakeS1(ComponenteCognitivoBase):
    """
    Componente Reactivo S1: CPG de Supervivencia Innata y Reflejos en Snake.
    1. Ejecuta en < 5 ms.
    2. Su mandato primordial es la no-colision en el latido inmediato (evitar paredes y cuerpo propio).
    3. Si no hay peligro inminente, sigue el gradiente apetitivo hacia el nutriente.
    4. Implementa anti-backtracking para no girar 180 grados sobre si mismo.
    """

    def __init__(self, peso_sinaptico: float = 1.2):
        super().__init__("Comp_SupervivenciaSnakeS1", "S1", peso_sinaptico=peso_sinaptico)

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        prop = onda.reactiva.ev.get("Propiocepcion", {})
        if not prop:
            return False

        p_prop = next(iter(prop.values()))
        nodos_adyacentes: List[str] = list(p_prop.product.get("nodos_adyacentes", []))
        historial = list(p_prop.product.get("historial_nodos", []))
        nodo_actual = str(p_prop.product.get("ubicacion", ""))

        if not nodos_adyacentes:
            # Atrapado sin salida fisica inmediata -> Inmovilidad tonica
            p_colapso = Pieza(
                id=f"Imp_Colapso_{onda.ciclo}",
                tipo_componente="Impulso",
                arousal=0.98,
                trust=0.99,
                product={"comando": V_Comando.COLAPSO, "target": "Colapso_Total"},
                inputs=[p_prop.id, self.id_componente],
            )
            self.emitir_impulso(onda, p_colapso, coste_amplitud=0)
            return True

        # Caso especial: Juego en espera de inicio o reinicio
        if "INICIAR_PARTIDA" in nodos_adyacentes:
            p_inicio = Pieza(
                id=f"Imp_Iniciar_{onda.ciclo}",
                tipo_componente="Impulso",
                arousal=0.95,
                trust=0.99,
                product={"comando": V_Comando.MOVER, "target": "INICIAR_PARTIDA"},
                inputs=[p_prop.id, self.id_componente],
            )
            self.emitir_impulso(onda, p_inicio, coste_amplitud=0)
            return True

        # Buscar el Alimento en Escena
        escena = onda.reactiva.ev.get("Escena", {})
        p_alimento: Optional[Pieza] = None
        for p in escena.values():
            if str(p.product.get("relacion")) == str(V_Relacion.ES_NUTRITIVO):
                p_alimento = p
                break

        nodo_anterior = historial[-2] if len(historial) >= 2 else None

        # Filtrar anti-backtracking: descartar volver a la casilla previa inmediata si hay opciones
        candidatos_seguros = [n for n in nodos_adyacentes if n != nodo_anterior]
        if not candidatos_seguros:
            candidatos_seguros = list(nodos_adyacentes)

        # ---------------------------------------------------------------------
        # MODULACION DE PERSONALIDAD: MEMORIA ANCESTRAL VS INSTINTO INMEDIATO
        # ---------------------------------------------------------------------
        arquetipo = ctx.get("arquetipo")
        responsabilidad = float(getattr(arquetipo, "responsabilidad", 0.70)) if arquetipo else 0.70
        apertura = float(getattr(arquetipo, "apertura", 0.70)) if arquetipo else 0.70
        neuroticismo = float(getattr(arquetipo, "neuroticismo", 0.35)) if arquetipo else 0.35

        # Mayor responsabilidad y neuroticismo -> mayor reverencia y obediencia a traumas ancestrales
        # Mayor apertura e impulsividad -> mayor peso al apetito inmediato
        peso_memoria_ancestral = 0.4 + (responsabilidad * 0.4) + (neuroticismo * 0.2)
        peso_instinto = 0.6 + (apertura * 0.4) - (responsabilidad * 0.2)

        # Consulta ultra-rapida O(1) de memoria activa ancestral
        activa = ctx.get("activa")
        aversion_muro_perimetral = False
        if activa and hasattr(activa, "indice_identidad"):
            for cajon in activa.indice_identidad.values():
                for p in cajon.values():
                    if p.tipo_componente == "Aversion_Traumatica" and p.product.get("tipo_trauma") == "COLISION_MURO_PERIMETRAL":
                        aversion_muro_perimetral = True
                        break

        fx = int(p_alimento.product.get("x", 10)) if p_alimento else 10
        fy = int(p_alimento.product.get("y", 7)) if p_alimento else 7

        obstaculos_s1: Set[Tuple[int, int]] = set()
        for p in escena.values():
            if p.tipo_componente == "Estado_Entorno":
                raw_cuerpo = p.product.get("cuerpo_coords", [])
                if raw_cuerpo:
                    obstaculos_s1.update(tuple(c) for c in raw_cuerpo[:-1])
            elif p.tipo_componente == "Obstaculo_Letal":
                ox, oy = int(p.product.get("x", -1)), int(p.product.get("y", -1))
                if ox >= 0 and oy >= 0:
                    obstaculos_s1.add((ox, oy))

        def evaluar_candidato_s1(nid: str) -> float:
            partes = nid.replace("nodo_", "").split("_")
            if len(partes) != 2 or not (partes[0].isdigit() and partes[1].isdigit()):
                return 999.0
            cx, cy = int(partes[0]), int(partes[1])
            dist_comida = abs(cx - fx) + abs(cy - fy)
            coste = dist_comida * peso_instinto

            # Lookahead reflejo de 2 pasos: descartar casillas que no tengan salidas reales libres en el siguiente latido
            salidas_inmediatas = 0
            for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
                sx, sy = cx + dx, cy + dy
                if 0 <= sx < 21 and 0 <= sy < 15:
                    if f"nodo_{sx}_{sy}" != nodo_actual and (sx, sy) not in obstaculos_s1:
                        salidas_inmediatas += 1
            if salidas_inmediatas == 0:
                coste += 180.0
            elif salidas_inmediatas == 1:
                coste += 40.0  # Desincentivo a entrar en un rincón estrecho

            # Reflejo preventivo: Si los antepasados murieron en bordes exteriores, cautela suave salvo que el alimento este alli
            if aversion_muro_perimetral and (cx, cy) != (fx, fy):
                if cx <= 0 or cx >= 20 or cy <= 0 or cy >= 14:
                    coste += (2.5 * peso_memoria_ancestral)

            return coste

        candidatos_ordenados = sorted(candidatos_seguros, key=evaluar_candidato_s1)
        mejor_nodo = candidatos_ordenados[0]
        arousal_final = 0.78 if p_alimento else 0.70

        # Emitir Impulso Motor de S1 al canal acc
        p_imp = Pieza(
            id=f"Imp_S1_{mejor_nodo}",
            tipo_componente="Impulso",
            arousal=arousal_final,
            trust=0.82,
            product={"comando": V_Comando.MOVER, "target": mejor_nodo, "origen_sistema": "S1"},
            inputs=[p_prop.id, self.id_componente],
        )
        self.emitir_impulso(onda, p_imp, coste_amplitud=1)
        return True


class CompEstrategiaSnakeS3(ComponenteCognitivoBase):
    """
    Componente Deliberativo S3: Estrategia Topologica y Prevencion de Trampas (Antienredos).
    1. Evalua el volumen de espacio libre accesible (Flood Fill) desde cada direccion candidata.
    2. Veta caminos apetitivos pero ciegos (bolsillos cerrados donde el cuerpo encerraria la cabeza).
    3. Cuando halla una ruta segura hacia el alimento con suficiente espacio de maniobra, emite
       un impulso deliberativo de alto Arousal y Trust que prevalece sobre S1 en el Tribunal Motor.
    """

    ANCHO: int = 21
    ALTO: int = 15

    def __init__(self, peso_sinaptico: float = 1.35):
        super().__init__("Comp_EstrategiaSnakeS3", "S3", peso_sinaptico=peso_sinaptico)

    @classmethod
    def _contar_espacio_accesible(cls, inicio: Tuple[int, int], obstaculos: Set[Tuple[int, int]], limite_profundidad: int = 60) -> int:
        """BFS de inundacion rapida para estimar el area de maniobra libre."""
        if inicio in obstaculos:
            return 0
        cola = deque([inicio])
        visitados: Set[Tuple[int, int]] = {inicio}

        while cola and len(visitados) < limite_profundidad:
            cx, cy = cola.popleft()
            for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < cls.ANCHO and 0 <= ny < cls.ALTO:
                    vecino = (nx, ny)
                    if vecino not in obstaculos and vecino not in visitados:
                        visitados.add(vecino)
                        cola.append(vecino)
        return len(visitados)

    @classmethod
    def _distancia_bfs(cls, inicio: Tuple[int, int], destino: Tuple[int, int], obstaculos: Set[Tuple[int, int]]) -> Optional[int]:
        """Calcula la distancia real mas corta en rejilla esquivando el cuerpo propio."""
        if inicio == destino:
            return 0
        if inicio in obstaculos:
            return None
        cola = deque([(inicio[0], inicio[1], 0)])
        visitados: Set[Tuple[int, int]] = {inicio}
        while cola:
            cx, cy, d = cola.popleft()
            for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
                nx, ny = cx + dx, cy + dy
                if (nx, ny) == destino:
                    return d + 1
                if 0 <= nx < cls.ANCHO and 0 <= ny < cls.ALTO:
                    vecino = (nx, ny)
                    if vecino not in obstaculos and vecino not in visitados:
                        visitados.add(vecino)
                        cola.append((nx, ny, d + 1))
        return None

    @classmethod
    def _simular_estela_proactiva(
        cls,
        inicio: Tuple[int, int],
        cuerpo_actual: List[Tuple[int, int]],
        alimento: Optional[Tuple[int, int]],
        obstaculos_fijos: Set[Tuple[int, int]],
        horizonte: int = 4,
    ) -> Dict[str, Any]:
        """
        Proyeccion Proactiva de Huella Temporal (Forward Trajectory Footprint).
        Simula el desplazamiento del cuerpo K pasos hacia el alimento
        para detectar si la estela corporal propia estrangula la salida futura.
        """
        if not cuerpo_actual:
            return {"riesgo_encierro": False, "salidas_futuras": 2, "pasos_libres": horizonte}

        # Estado inicial proyectado con el primer paso en 'inicio'
        cuerpo_sim = [inicio] + list(cuerpo_actual[:-1])
        pasos_completados = 1
        fx, fy = alimento if alimento else inicio

        for paso in range(1, horizonte):
            hx, hy = cuerpo_sim[0]
            obstaculos_en_paso = set(cuerpo_sim[:-1]) | obstaculos_fijos

            candidatos_paso: List[Tuple[Tuple[int, int], int]] = []
            for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
                nx, ny = hx + dx, hy + dy
                if 0 <= nx < cls.ANCHO and 0 <= ny < cls.ALTO:
                    if (nx, ny) not in obstaculos_en_paso:
                        dist = abs(nx - fx) + abs(ny - fy)
                        candidatos_paso.append(((nx, ny), dist))

            if not candidatos_paso:
                # Se queda sin salidas antes de completar el horizonte
                return {
                    "riesgo_encierro": True,
                    "salidas_futuras": 0,
                    "pasos_libres": paso,
                }

            # Elegir la casilla mas cercana al alimento (gradiente apetitivo)
            candidatos_paso.sort(key=lambda x: x[1])
            siguiente_cabeza = candidatos_paso[0][0]
            cuerpo_sim = [siguiente_cabeza] + cuerpo_sim[:-1]
            pasos_completados += 1

        # Verificar cuantas salidas libres y que area alcanzable tiene la cabeza proyectada al final del horizonte
        cabeza_final = cuerpo_sim[0]
        obstaculos_finales = set(cuerpo_sim[:-1]) | obstaculos_fijos
        salidas_finales = 0
        for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
            vx, vy = cabeza_final[0] + dx, cabeza_final[1] + dy
            if 0 <= vx < cls.ANCHO and 0 <= vy < cls.ALTO:
                if (vx, vy) not in obstaculos_finales:
                    salidas_finales += 1

        area_futura = cls._contar_espacio_accesible(
            cabeza_final,
            obstaculos_finales,
            limite_profundidad=len(cuerpo_actual) + 5,
        )
        riesgo = (salidas_finales <= 1) or (area_futura < len(cuerpo_actual))
        return {
            "riesgo_encierro": riesgo,
            "salidas_futuras": salidas_finales,
            "area_futura": area_futura,
            "pasos_libres": pasos_completados,
        }

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        prop = onda.reactiva.ev.get("Propiocepcion", {})
        if not prop:
            return False

        p_prop = next(iter(prop.values()))
        nodos_adyacentes: List[str] = [n for n in p_prop.product.get("nodos_adyacentes", []) if n.startswith("nodo_")]
        if not nodos_adyacentes:
            return False

        nodo_actual = str(p_prop.product.get("ubicacion", "nodo_10_2"))
        partes_act = nodo_actual.replace("nodo_", "").split("_")
        if len(partes_act) != 2:
            return False
        hx, hy = int(partes_act[0]), int(partes_act[1])

        # Recoger obstaculos conocidos a partir de las piezas de escena
        escena = onda.reactiva.ev.get("Escena", {})
        obstaculos: Set[Tuple[int, int]] = set()
        p_alimento: Optional[Pieza] = None
        longitud_serpiente = 3
        cuerpo_coords: List[Tuple[int, int]] = []

        for p in escena.values():
            if p.tipo_componente == "Obstaculo_Letal":
                ox = int(p.product.get("x", -1))
                oy = int(p.product.get("y", -1))
                if ox >= 0 and oy >= 0:
                    obstaculos.add((ox, oy))
            elif p.tipo_componente == "Alimento":
                p_alimento = p
            elif p.tipo_componente == "Estado_Entorno":
                longitud_serpiente = int(p.product.get("longitud_serpiente", 3))
                raw_cuerpo = p.product.get("cuerpo_coords", [])
                if raw_cuerpo:
                    cuerpo_coords = [tuple(c) for c in raw_cuerpo]

        # Incluir todos los segmentos del cuerpo (salvo la punta de la cola que avanza) en el mapa de obstaculos del Flood Fill
        if cuerpo_coords:
            obstaculos.update(cuerpo_coords[:-1])
            longitud_serpiente = max(longitud_serpiente, len(cuerpo_coords))

        coord_alimento: Optional[Tuple[int, int]] = None
        if p_alimento:
            coord_alimento = (int(p_alimento.product.get("x", 0)), int(p_alimento.product.get("y", 0)))

        cola_coord: Optional[Tuple[int, int]] = cuerpo_coords[-1] if cuerpo_coords else None

        # Determinar si procede activar la proyeccion proactiva adaptativa
        activar_proactiva = longitud_serpiente >= 6
        horizonte_proactivo = 4 if longitud_serpiente >= 10 else 3

        # Analizar cada direccion candidata evaluando espacio accesible, ruta BFS real y proyeccion de estela
        evaluaciones: List[Dict[str, Any]] = []
        for nid in nodos_adyacentes:
            partes = nid.replace("nodo_", "").split("_")
            nx, ny = int(partes[0]), int(partes[1])
            area_libre = self._contar_espacio_accesible(
                (nx, ny),
                obstaculos,
                limite_profundidad=max(60, longitud_serpiente * 3),
            )

            dist_manz = 999
            if coord_alimento:
                dist_bfs = self._distancia_bfs((nx, ny), coord_alimento, obstaculos)
                if dist_bfs is not None:
                    dist_manz = dist_bfs
                else:
                    dist_manz = abs(nx - coord_alimento[0]) + abs(ny - coord_alimento[1]) + 80

            cola_alcanzable = True
            if cola_coord and longitud_serpiente >= 5:
                cola_alcanzable = self._distancia_bfs((nx, ny), cola_coord, obstaculos) is not None

            # Proyeccion de estela proactiva si la serpiente ya tiene longitud para autoencerrarse
            riesgo_proactivo = False
            salidas_futuras = 2
            if activar_proactiva and cuerpo_coords:
                res_proactivo = self._simular_estela_proactiva(
                    inicio=(nx, ny),
                    cuerpo_actual=cuerpo_coords,
                    alimento=coord_alimento,
                    obstaculos_fijos=obstaculos,
                    horizonte=horizonte_proactivo,
                )
                riesgo_proactivo = res_proactivo["riesgo_encierro"]
                salidas_futuras = res_proactivo["salidas_futuras"]

            evaluaciones.append({
                "target": nid,
                "coord": (nx, ny),
                "area_libre": area_libre,
                "dist_alimento": dist_manz,
                "cola_alcanzable": cola_alcanzable,
                "riesgo_proactivo": riesgo_proactivo,
                "salidas_futuras": salidas_futuras,
            })

        # ---------------------------------------------------------------------
        # CONSULTA DE MEMORIA ANCESTRAL ACTIVA (TRAUMAS Y PATRONES EXITOSOS)
        # ---------------------------------------------------------------------
        activa = ctx.get("activa")
        aversion_muros = False
        aversion_encierros = False
        patron_desentrampe_activo = False
        bonus_desentrampe = 1.0

        if activa and hasattr(activa, "indice_identidad"):
            for cajon in activa.indice_identidad.values():
                for p in cajon.values():
                    if p.tipo_componente == "Aversion_Traumatica":
                        tt = str(p.product.get("tipo_trauma", ""))
                        if "MURO" in tt:
                            aversion_muros = True
                        elif "ENCERRONA" in tt or "PROPIA" in tt:
                            aversion_encierros = True
                    elif p.tipo_componente == "Patron_Exito_Estrategico":
                        if p.product.get("estrategia") == "DESAHOGO_PERIMETRAL_AMPLIO":
                            if longitud_serpiente >= int(p.product.get("umbral_longitud", 6)):
                                patron_desentrampe_activo = True
                                bonus_desentrampe = float(p.product.get("peso_area_libre_bonus", 1.6))

        # Modulacion de Personalidad: Memoria Ancestral vs Instinto Inmediato
        arquetipo = ctx.get("arquetipo")
        apertura = float(getattr(arquetipo, "apertura", 0.70)) if arquetipo else 0.70
        responsabilidad = float(getattr(arquetipo, "responsabilidad", 0.70)) if arquetipo else 0.70
        neuroticismo = float(getattr(arquetipo, "neuroticismo", 0.35)) if arquetipo else 0.35
        umbral_miedo = float(getattr(arquetipo, "umbral_miedo", 0.60)) if arquetipo else 0.60

        peso_memoria_ancestral = 0.4 + (responsabilidad * 0.4) + (neuroticismo * 0.2)
        peso_comida = 1.0 + (apertura * 0.8) - (neuroticismo * 0.3)
        peso_espacio = 0.4 + (umbral_miedo * 1.1) + (neuroticismo * 0.7)

        # Si el patron positivo de desentrampe esta activo (cuerpo largo), potenciar peso del espacio
        if patron_desentrampe_activo:
            peso_espacio *= bonus_desentrampe

        # Descartar caminos cuya area alcanzable sea inferior a la longitud del cuerpo
        area_minima = int(longitud_serpiente * 1.4) if aversion_encierros else max(longitud_serpiente, min(12, longitud_serpiente + 1))
        viables = [e for e in evaluaciones if e["area_libre"] >= area_minima]
        if not viables:
            # Emergencia: quedarse con el de mayor area libre posible
            viables = sorted(evaluaciones, key=lambda x: x["area_libre"], reverse=True)

        if not viables:
            return False

        def evaluar_coste_s3(e: Dict[str, Any]) -> float:
            c = (e["dist_alimento"] * peso_comida) - (min(e["area_libre"], area_minima + 8) * 0.18 * peso_espacio)

            # Penalizacion si pierde contacto topologico con su propia cola en cuerpos medianos/largos
            if not e["cola_alcanzable"] and longitud_serpiente >= 5:
                c += 65.0 * peso_espacio

            # Penalizacion si el area libre no cubre la longitud corporal completa
            if e["area_libre"] < longitud_serpiente:
                c += 250.0 + (longitud_serpiente - e["area_libre"]) * 35.0

            # Penalizacion proactiva si la proyeccion anticipa estrangulamiento de salida o bolsillo cerrado
            if e["riesgo_proactivo"]:
                c += (45.0 * peso_espacio)
                if e["salidas_futuras"] == 0:
                    c += 180.0  # Callejon mortal anticipado

            # Si hay trauma de muro perimetral, cautela en paredes exteriores salvo que el alimento este en esa casilla
            if aversion_muros and e["coord"] != coord_alimento:
                cx, cy = e["coord"]
                if cx <= 0 or cx >= 20 or cy <= 0 or cy >= 14:
                    c += (2.5 * peso_memoria_ancestral)
            return c

        # Si hay opciones viables que no presenten riesgo de encierro proactivo, preferirlas
        sin_riesgo_futuro = [e for e in viables if not e["riesgo_proactivo"]]
        pool_seleccion = sin_riesgo_futuro if sin_riesgo_futuro else viables

        pool_seleccion.sort(key=evaluar_coste_s3)
        mejor = pool_seleccion[0]

        # Verificar si hay impulsos de S1 en acc que llevaban a una trampa de encierro
        impulsos_acc = onda.reactiva.acc.get("Impulso", {})
        for imp in impulsos_acc.values():
            target_s1 = str(imp.product.get("target", ""))
            # Si S1 eligio un camino con area menor que la longitud corporal o con riesgo proactivo de encierro, S3 lo veta
            if target_s1 != mejor["target"]:
                peor_eval = next((e for e in evaluaciones if e["target"] == target_s1), None)
                if peor_eval:
                    trampa_reactiva = (
                        peor_eval["area_libre"] < max(longitud_serpiente, area_minima)
                        and mejor["area_libre"] > peor_eval["area_libre"]
                    )
                    trampa_proactiva = peor_eval["riesgo_proactivo"] and (
                        not mejor["riesgo_proactivo"] or peor_eval["salidas_futuras"] < mejor["salidas_futuras"]
                    )
                    if trampa_reactiva or trampa_proactiva:
                        imp.arousal = 0.05
                        imp.trust = 0.10
                        imp.product["veto_s3_antienredo"] = True

        # Emitir Impulso Deliberado S3 con alta dominancia
        p_imp_s3 = Pieza(
            id=f"Imp_S3_Estrategico_{mejor['target']}",
            tipo_componente="Impulso",
            arousal=0.92,
            trust=0.94,
            product={
                "comando": V_Comando.MOVER,
                "target": mejor["target"],
                "origen_sistema": "S3",
                "area_asegurada": mejor["area_libre"],
                "riesgo_proactivo": mejor["riesgo_proactivo"],
                "salidas_futuras": mejor["salidas_futuras"],
                "dist_objetivo": mejor["dist_alimento"],
            },
            inputs=[p_prop.id, self.id_componente],
            sistemas_participantes={"S3"},
        )
        self.emitir_impulso(onda, p_imp_s3, coste_amplitud=1)
        return True

