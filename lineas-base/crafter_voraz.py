"""
Línea base tradicional voraz para el entorno Crafter 2D (Danijar Hafner, ICLR 2022).

Implementa un sistema experto basado en reglas heurísticas voraces con RESTRICCIÓN DE INFORMACIÓN:
- Opera EXCLUSIVAMENTE sobre la vista local observable (radio 6 en torno al agente, idéntico a IdA).
- No accede a la matriz global 64x64 de Crafter ni a coordenadas fuera de su ventana.
- Aplica una jerarquía fija y determinista de prioridades vitales y tecnológicas.
"""

from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple

# Constantes de acción de Crafter
ACC_NOOP = "noop"
ACC_MOVE_LEFT = "move_left"
ACC_MOVE_RIGHT = "move_right"
ACC_MOVE_UP = "move_up"
ACC_MOVE_DOWN = "move_down"
ACC_DO = "do"
ACC_SLEEP = "sleep"
ACC_PLACE_STONE = "place_stone"
ACC_PLACE_TABLE = "place_table"
ACC_PLACE_FURNACE = "place_furnace"
ACC_PLACE_PLANT = "place_plant"
ACC_MAKE_WOOD_PICKAXE = "make_wood_pickaxe"
ACC_MAKE_STONE_PICKAXE = "make_stone_pickaxe"
ACC_MAKE_IRON_PICKAXE = "make_iron_pickaxe"
ACC_MAKE_WOOD_SWORD = "make_wood_sword"
ACC_MAKE_STONE_SWORD = "make_stone_sword"
ACC_MAKE_IRON_SWORD = "make_iron_sword"

ACCION_MOVIMIENTO = {
    (0, -1): ACC_MOVE_UP,
    (0, 1): ACC_MOVE_DOWN,
    (-1, 0): ACC_MOVE_LEFT,
    (1, 0): ACC_MOVE_RIGHT,
}

DIRECCIONES_CARDINALES = [
    (0, -1),  # Norte / Arriba
    (0, 1),   # Sur / Abajo
    (-1, 0),  # Oeste / Izquierda
    (1, 0),   # Este / Derecha
]

MATERIALES_CAMINABLES = {"grass", "path", "sand"}


class AgenteCrafterVoraz:
    """
    Agente voraz basado en prioridades biológicas y de progresión técnica.
    
    Jerarquía de Decisión (fijada a priori):
    1. HUIR / COMBATIR AMENAZAS INMEDIATAS:
       - Si hay depredador adyacente (distancia 1):
         * Si salud >= 4 o tiene espada: atacar con 'do' en dirección al depredador.
         * Si no: dar un paso alejándose del depredador hacia una casilla caminable y segura.
       - Si hay flecha u hostil a distancia 2: maniobra evasiva alejándose.
    2. DESHIDRATACIÓN CRÍTICA (bebida <= 4):
       - Si hay agua adyacente (distancia 1): girar y 'do' sobre el agua.
       - Si hay agua visible: mover en el camino más corto hacia ella.
    3. INANICIÓN CRÍTICA (comida <= 4):
       - Si hay planta madura adyacente o vaca adyacente: encarar y 'do'.
       - Si hay comida visible: mover en camino más corto hacia ella.
    4. SUEÑO CRÍTICO / NOCHE REPARADORA:
       - Si energia <= 2 y no hay depredadores visibles: 'sleep'.
       - Si es de noche (daylight < 0.2), no hay depredadores visibles y energia <= 6: 'sleep'.
    5. HIDRATACIÓN PREVENTIVA (bebida <= 7 y agua visible adyacente): 'do' sobre agua.
    6. NUTRICIÓN PREVENTIVA (comida <= 7 y planta/vaca visible adyacente): 'do'.
    7. FABRICACIÓN TECNOLÓGICA (Tech Tree):
       - Si tiene madera >= 2 y no tiene mesa de trabajo en inventario ni cerca: colocar mesa ('place_table') o fabricar pico de madera si mesa adyacente.
       - Si tiene madera >= 1 y mesa adyacente y pickaxe de madera == 0: 'make_wood_pickaxe'.
       - Si tiene madera >= 1 y mesa adyacente y wood_sword == 0: 'make_wood_sword'.
       - Si tiene piedra >= 1 y mesa adyacente y stone_pickaxe == 0: 'make_stone_pickaxe'.
       - Si tiene piedra >= 4 y no tiene horno: 'place_furnace'.
       - Si tiene hierro >= 1 y horno adyacente y iron_pickaxe == 0: 'make_iron_pickaxe'.
    8. RECOLECCIÓN DE RECURSOS VISIBLES:
       - Árbol (tree): si madera < 4 -> acercarse e interactuar con 'do'.
       - Piedra (stone): si tiene pico y piedra < 6 -> acercarse e interactuar con 'do'.
       - Carbón (coal) / Hierro (iron): si tiene pico adecuado -> acercarse e interactuar con 'do'.
    9. EXPLORACIÓN ACTIVA:
       - Mover hacia la casilla caminable observable que maximice la distancia al historial de los últimos pasos.
    """

    def __init__(self, radio_vision: int = 6):
        self.radio_vision = radio_vision
        self.historial_posiciones: deque = deque(maxlen=16)

    def decidir(
        self,
        player_pos: Tuple[int, int],
        facing: Tuple[int, int],
        salud: int,
        comida: int,
        bebida: int,
        energia: int,
        daylight: float,
        sleeping: bool,
        inventario: Dict[str, int],
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
    ) -> str:
        """
        Recibe únicamente la información observable localmente y devuelve el nombre de la acción.
        vista_local es un diccionario con claves (x, y) relativas o absolutas dentro de la ventana de visión,
        y valores (material, objeto).
        """
        px, py = player_pos
        self.historial_posiciones.append((px, py))

        # Si ya está durmiendo y la energía aún no está llena, continuar durmiendo si no hay amenaza
        amenazas_visibles = [
            (pos, obj) for pos, (mat, obj) in vista_local.items()
            if obj is not None and type(obj).__name__ in ("Zombie", "Skeleton", "Arrow")
        ]

        if sleeping:
            if amenazas_visibles:
                # Despertar ante peligro
                return ACC_NOOP
            if energia < 9:
                return ACC_SLEEP
            return ACC_NOOP

        # -------------------------------------------------------------
        # 1. AMENAZAS INMEDIATAS (Depredadores y proyectiles)
        # -------------------------------------------------------------
        if amenazas_visibles:
            # Ordenar por distancia Manhattan al jugador
            amenazas_visibles.sort(key=lambda t: abs(t[0][0] - px) + abs(t[0][1] - py))
            pos_amenaza, obj_amenaza = amenazas_visibles[0]
            dist_amenaza = abs(pos_amenaza[0] - px) + abs(pos_amenaza[1] - py)
            dx = pos_amenaza[0] - px
            dy = pos_amenaza[1] - py

            tiene_espada = (
                inventario.get("wood_sword", 0) > 0 or
                inventario.get("stone_sword", 0) > 0 or
                inventario.get("iron_sword", 0) > 0
            )

            # A distancia 1: combate o escape
            if dist_amenaza == 1:
                # Si tenemos salud suficiente o arma, atacar
                if salud >= 4 or tiene_espada:
                    dir_esperada = (dx, dy)
                    if facing == dir_esperada:
                        return ACC_DO
                    # Girar hacia la amenaza
                    if dir_esperada in ACCION_MOVIMIENTO:
                        return ACCION_MOVIMIENTO[dir_esperada]
                else:
                    # Huir en sentido opuesto
                    escape_dir = self._buscar_paso_huida(px, py, pos_amenaza, vista_local)
                    if escape_dir:
                        return ACCION_MOVIMIENTO[escape_dir]

            elif dist_amenaza == 2:
                # Amenaza cercana: alejarse si salud baja
                if salud <= 5:
                    escape_dir = self._buscar_paso_huida(px, py, pos_amenaza, vista_local)
                    if escape_dir:
                        return ACCION_MOVIMIENTO[escape_dir]

        # -------------------------------------------------------------
        # 2. SED CRÍTICA (bebida <= 4)
        # -------------------------------------------------------------
        if bebida <= 4:
            accion_agua = self._interactuar_o_acercar_material(
                px, py, facing, "water", vista_local, interact_es_do=True
            )
            if accion_agua:
                return accion_agua

        # -------------------------------------------------------------
        # 3. HAMBRE CRÍTICA (comida <= 4)
        # -------------------------------------------------------------
        if comida <= 4:
            accion_comida = self._buscar_comida(px, py, facing, vista_local)
            if accion_comida:
                return accion_comida

        # -------------------------------------------------------------
        # 4. SUEÑO CRÍTICO / NOCHE REPARADORA
        # -------------------------------------------------------------
        if not amenazas_visibles:
            if energia <= 2:
                return ACC_SLEEP
            if daylight < 0.2 and energia <= 6:
                return ACC_SLEEP

        # -------------------------------------------------------------
        # 5. SED PREVENTIVA (bebida <= 7)
        # -------------------------------------------------------------
        if bebida <= 7:
            # Solo si está a distancia 1 para no desviar la progresión
            for d in DIRECCIONES_CARDINALES:
                pos = (px + d[0], py + d[1])
                mat, obj = vista_local.get(pos, (None, None))
                if mat == "water":
                    if facing == d:
                        return ACC_DO
                    return ACCION_MOVIMIENTO[d]

        # -------------------------------------------------------------
        # 6. NUTRICIÓN PREVENTIVA (comida <= 7)
        # -------------------------------------------------------------
        if comida <= 7:
            # Solo si está a distancia 1
            for d in DIRECCIONES_CARDINALES:
                pos = (px + d[0], py + d[1])
                mat, obj = vista_local.get(pos, (None, None))
                if obj is not None:
                    tipo = type(obj).__name__
                    if (tipo == "Plant" and getattr(obj, "ripe", True)) or tipo == "Cow":
                        if facing == d:
                            return ACC_DO
                        return ACCION_MOVIMIENTO[d]

        # -------------------------------------------------------------
        # 7. PROGRESIÓN TECNOLÓGICA (Tech Tree de Crafter)
        # -------------------------------------------------------------
        accion_tech = self._resolver_tecnologia(px, py, facing, inventario, vista_local)
        if accion_tech:
            return accion_tech

        # -------------------------------------------------------------
        # 8. RECOLECCIÓN DE RECURSOS VISIBLES
        # -------------------------------------------------------------
        madera = inventario.get("wood", 0)
        piedra = inventario.get("stone", 0)
        carbon = inventario.get("coal", 0)
        hierro = inventario.get("iron", 0)
        tiene_pico_madera = inventario.get("wood_pickaxe", 0) > 0
        tiene_pico_piedra = inventario.get("stone_pickaxe", 0) > 0

        # Recoger madera si < 4
        if madera < 4:
            accion_arbol = self._interactuar_o_acercar_material(
                px, py, facing, "tree", vista_local, interact_es_do=True
            )
            if accion_arbol:
                return accion_arbol

        # Recoger piedra si tiene pico y piedra < 5
        if (tiene_pico_madera or tiene_pico_piedra) and piedra < 5:
            accion_piedra = self._interactuar_o_acercar_material(
                px, py, facing, "stone", vista_local, interact_es_do=True
            )
            if accion_piedra:
                return accion_piedra

        # Recoger carbón / hierro si tiene pico de piedra
        if tiene_pico_piedra:
            if hierro < 2:
                accion_hierro = self._interactuar_o_acercar_material(
                    px, py, facing, "iron", vista_local, interact_es_do=True
                )
                if accion_hierro:
                    return accion_hierro
            if carbon < 2:
                accion_carbon = self._interactuar_o_acercar_material(
                    px, py, facing, "coal", vista_local, interact_es_do=True
                )
                if accion_carbon:
                    return accion_carbon

        # Si aún no tenemos suficiente madera, buscar árbol
        accion_arbol = self._interactuar_o_acercar_material(
            px, py, facing, "tree", vista_local, interact_es_do=True
        )
        if accion_arbol:
            return accion_arbol

        # -------------------------------------------------------------
        # 9. EXPLORACIÓN ACTIVA (Evasión de bucles / movimiento libre)
        # -------------------------------------------------------------
        return self._explorar(px, py, facing, vista_local)

    # -----------------------------------------------------------------
    # MÉTODOS AUXILIARES DE NAVEGACIÓN Y ACCIÓN LOCAL
    # -----------------------------------------------------------------
    def _es_transitable(self, pos: Tuple[int, int], vista_local: Dict[Tuple[int, int], Tuple[str, Any]]) -> bool:
        if pos not in vista_local:
            return False
        mat, obj = vista_local[pos]
        if mat not in MATERIALES_CAMINABLES or mat == "lava":
            return False
        if obj is not None:
            # Los objetos bloquean salvo que sean consumibles/atravesables
            return False
        return True

    def _buscar_paso_huida(
        self,
        px: int,
        py: int,
        pos_amenaza: Tuple[int, int],
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
    ) -> Optional[Tuple[int, int]]:
        """Elige el movimiento cardinal libre que maximice la distancia a la amenaza."""
        mejores = []
        ax, ay = pos_amenaza
        dist_actual = abs(ax - px) + abs(ay - py)

        for d in DIRECCIONES_CARDINALES:
            cand = (px + d[0], py + d[1])
            if self._es_transitable(cand, vista_local):
                nueva_dist = abs(ax - cand[0]) + abs(ay - cand[1])
                mejores.append((nueva_dist, d))

        if not mejores:
            return None
        mejores.sort(key=lambda x: x[0], reverse=True)
        return mejores[0][1]

    def _buscar_comida(
        self,
        px: int,
        py: int,
        facing: Tuple[int, int],
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
    ) -> Optional[str]:
        """Busca plantas maduras o vacas a la vista y avanza hacia ellas o interactúa."""
        objetivos = []
        for pos, (mat, obj) in vista_local.items():
            if obj is not None:
                tipo = type(obj).__name__
                if (tipo == "Plant" and getattr(obj, "ripe", True)) or tipo == "Cow":
                    dist = abs(pos[0] - px) + abs(pos[1] - py)
                    objetivos.append((dist, pos))

        if not objetivos:
            return None

        objetivos.sort(key=lambda x: x[0])
        dist, mejor_pos = objetivos[0]

        if dist == 1:
            dx = mejor_pos[0] - px
            dy = mejor_pos[1] - py
            if facing == (dx, dy):
                return ACC_DO
            return ACCION_MOVIMIENTO.get((dx, dy), ACC_NOOP)

        paso = self._camino_bfs(px, py, mejor_pos, vista_local, interactuar_adyacente=True)
        if paso and paso in ACCION_MOVIMIENTO:
            return ACCION_MOVIMIENTO[paso]
        return None

    def _interactuar_o_acercar_material(
        self,
        px: int,
        py: int,
        facing: Tuple[int, int],
        material_target: str,
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
        interact_es_do: bool = True,
    ) -> Optional[str]:
        """Localiza el recurso de material más cercano en la vista local."""
        candidatos = []
        for pos, (mat, obj) in vista_local.items():
            if mat == material_target:
                dist = abs(pos[0] - px) + abs(pos[1] - py)
                candidatos.append((dist, pos))

        if not candidatos:
            return None

        candidatos.sort(key=lambda x: x[0])
        dist, pos_obj = candidatos[0]

        if dist == 1:
            dx = pos_obj[0] - px
            dy = pos_obj[1] - py
            if facing == (dx, dy):
                return ACC_DO if interact_es_do else ACC_NOOP
            return ACCION_MOVIMIENTO.get((dx, dy), ACC_NOOP)

        paso = self._camino_bfs(px, py, pos_obj, vista_local, interactuar_adyacente=True)
        if paso and paso in ACCION_MOVIMIENTO:
            return ACCION_MOVIMIENTO[paso]
        return None

    def _resolver_tecnologia(
        self,
        px: int,
        py: int,
        facing: Tuple[int, int],
        inventario: Dict[str, int],
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
    ) -> Optional[str]:
        """Aplica las reglas de progresión de herramientas y mesas."""
        madera = inventario.get("wood", 0)
        piedra = inventario.get("stone", 0)
        hierro = inventario.get("iron", 0)
        tiene_wood_pickaxe = inventario.get("wood_pickaxe", 0) > 0
        tiene_wood_sword = inventario.get("wood_sword", 0) > 0
        tiene_stone_pickaxe = inventario.get("stone_pickaxe", 0) > 0
        tiene_iron_pickaxe = inventario.get("iron_pickaxe", 0) > 0

        # Verificar si hay una mesa de trabajo adyacente o visible
        mesa_pos = None
        horno_pos = None
        for pos, (mat, obj) in vista_local.items():
            if mat == "table":
                mesa_pos = pos
            elif mat == "furnace":
                horno_pos = pos

        mesa_adyacente = False
        if mesa_pos:
            mesa_adyacente = (abs(mesa_pos[0] - px) + abs(mesa_pos[1] - py) <= 1)

        horno_adyacente = False
        if horno_pos:
            horno_adyacente = (abs(horno_pos[0] - px) + abs(horno_pos[1] - py) <= 1)

        # Regla T1: Crear pico de madera
        if not tiene_wood_pickaxe:
            if mesa_adyacente and madera >= 1:
                return ACC_MAKE_WOOD_PICKAXE
            if not mesa_pos and madera >= 2:
                # Colocar mesa en casilla transitable adyacente o encarada
                return ACC_PLACE_TABLE
            if mesa_pos and not mesa_adyacente:
                paso = self._camino_bfs(px, py, mesa_pos, vista_local, interactuar_adyacente=True)
                if paso and paso in ACCION_MOVIMIENTO:
                    return ACCION_MOVIMIENTO[paso]

        # Regla T2: Crear espada de madera si hay madera y mesa adyacente
        if tiene_wood_pickaxe and not tiene_wood_sword and mesa_adyacente and madera >= 1:
            return ACC_MAKE_WOOD_SWORD

        # Regla T3: Crear pico de piedra
        if tiene_wood_pickaxe and not tiene_stone_pickaxe:
            if mesa_adyacente and piedra >= 1 and madera >= 1:
                return ACC_MAKE_STONE_PICKAXE
            if mesa_pos and not mesa_adyacente and piedra >= 1 and madera >= 1:
                paso = self._camino_bfs(px, py, mesa_pos, vista_local, interactuar_adyacente=True)
                if paso and paso in ACCION_MOVIMIENTO:
                    return ACCION_MOVIMIENTO[paso]

        # Regla T4: Colocar horno
        if tiene_stone_pickaxe and not horno_pos and piedra >= 4:
            return ACC_PLACE_FURNACE

        # Regla T5: Crear pico de hierro
        if tiene_stone_pickaxe and not tiene_iron_pickaxe and horno_pos:
            if horno_adyacente and mesa_adyacente and hierro >= 1 and madera >= 1:
                return ACC_MAKE_IRON_PICKAXE

        return None

    def _camino_bfs(
        self,
        inicio_x: int,
        inicio_y: int,
        destino: Tuple[int, int],
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
        interactuar_adyacente: bool = True,
    ) -> Optional[Tuple[int, int]]:
        """
        Calcula el primer paso cardinal hacia el objetivo usando BFS sobre casillas transitables.
        Si interactuar_adyacente es True, el objetivo se considera alcanzado cuando la distancia Manhattan es 1.
        """
        inicio = (inicio_x, inicio_y)
        dest_x, dest_y = destino

        if interactuar_adyacente and (abs(dest_x - inicio_x) + abs(dest_y - inicio_y) <= 1):
            return None

        cola = deque([inicio])
        visitados = {inicio}
        padres: Dict[Tuple[int, int], Tuple[Tuple[int, int], Tuple[int, int]]] = {}

        meta_encontrada = None

        while cola:
            actual = cola.popleft()
            cx, cy = actual

            if interactuar_adyacente:
                if abs(dest_x - cx) + abs(dest_y - cy) == 1:
                    meta_encontrada = actual
                    break
            else:
                if actual == destino:
                    meta_encontrada = actual
                    break

            for d in DIRECCIONES_CARDINALES:
                vecino = (cx + d[0], cy + d[1])
                if vecino not in visitados and self._es_transitable(vecino, vista_local):
                    visitados.add(vecino)
                    padres[vecino] = (actual, d)
                    cola.append(vecino)

        if not meta_encontrada:
            return None

        # Reconstruir camino hacia atrás para encontrar el primer paso desde inicio
        curr = meta_encontrada
        primer_paso = None
        while curr != inicio:
            p_padre, dir_paso = padres[curr]
            if p_padre == inicio:
                primer_paso = dir_paso
                break
            curr = p_padre

        return primer_paso

    def _explorar(
        self,
        px: int,
        py: int,
        facing: Tuple[int, int],
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
    ) -> str:
        """Elige el movimiento cardinal transitable que menos veces haya sido visitado recientemente."""
        candidatos = []
        for d in DIRECCIONES_CARDINALES:
            cand = (px + d[0], py + d[1])
            if self._es_transitable(cand, vista_local):
                # Penalizar si está en historial reciente
                frecuencia = sum(1 for p in self.historial_posiciones if p == cand)
                # Bonificar mantener la dirección actual (inercia)
                bono_inercia = -0.5 if d == facing else 0.0
                puntuacion = frecuencia + bono_inercia
                candidatos.append((puntuacion, d))

        if not candidatos:
            return ACC_NOOP

        candidatos.sort(key=lambda x: x[0])
        mejor_dir = candidatos[0][1]
        return ACCION_MOVIMIENTO.get(mejor_dir, ACC_NOOP)
