"""
Línea base tradicional voraz con MEMORIA ESPACIAL idéntica a IdA para Crafter 2D.

Implementa el mismo mapa cognitivo alocéntrico de hitos permanentes que IdA:
- Registra mesas de trabajo ('table'), hornos ('furnace'), fuentes de agua y minerales cuando aparecen en la vista local (radio 6).
- Mantiene la memoria persistente en coordenadas absolutas de los hitos descubiertos.
- Al acumular recursos para fabricar (ej. madera >= 1 para pico, o piedra >= 1 para herramientas de piedra),
  si la mesa de trabajo no está visible pero sí está en la memoria alocéntrica, utiliza A* para navegar
  de regreso a la mesa.
- No altera la regla de combate con esqueletos (mantiene paridad con crafter_voraz.py).
"""

from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple

import importlib

modulo_voraz_base = importlib.import_module("lineas-base.crafter_voraz")
ACC_DO = modulo_voraz_base.ACC_DO
ACC_MAKE_IRON_PICKAXE = modulo_voraz_base.ACC_MAKE_IRON_PICKAXE
ACC_MAKE_STONE_PICKAXE = modulo_voraz_base.ACC_MAKE_STONE_PICKAXE
ACC_MAKE_STONE_SWORD = modulo_voraz_base.ACC_MAKE_STONE_SWORD
ACC_MAKE_WOOD_PICKAXE = modulo_voraz_base.ACC_MAKE_WOOD_PICKAXE
ACC_MAKE_WOOD_SWORD = modulo_voraz_base.ACC_MAKE_WOOD_SWORD
ACC_NOOP = modulo_voraz_base.ACC_NOOP
ACC_PLACE_FURNACE = modulo_voraz_base.ACC_PLACE_FURNACE
ACC_PLACE_TABLE = modulo_voraz_base.ACC_PLACE_TABLE
ACC_SLEEP = modulo_voraz_base.ACC_SLEEP
ACCION_MOVIMIENTO = modulo_voraz_base.ACCION_MOVIMIENTO
DIRECCIONES_CARDINALES = modulo_voraz_base.DIRECCIONES_CARDINALES
MATERIALES_CAMINABLES = modulo_voraz_base.MATERIALES_CAMINABLES
AgenteCrafterVoraz = modulo_voraz_base.AgenteCrafterVoraz


class AgenteCrafterVorazMemoria(AgenteCrafterVoraz):
    """
    Agente voraz tradicional dotado de Memoria Alocéntrica equivalente a la de IdA.
    """

    def __init__(self, radio_vision: int = 6):
        super().__init__(radio_vision=radio_vision)
        # Memoria alocéntrica de hitos espaciales descubiertos:
        # {categoria: {posicion_tupla: {"tipo_entidad": str, "ultimo_paso": int}}}
        self.mapa_alocentrico: Dict[str, Dict[Tuple[int, int], Dict[str, Any]]] = {
            "estacion_trabajo": {},
            "fuente_agua": {},
            "yacimiento_mineral": {},
        }
        self.paso_actual: int = 0

    def registrar_observacion_en_memoria(
        self,
        px: int,
        py: int,
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
    ) -> None:
        """Actualiza el mapa alocéntrico con los hitos descubiertos en el campo visual actual."""
        for (x, y), (mat, obj) in vista_local.items():
            if mat == "table":
                self.mapa_alocentrico["estacion_trabajo"][(x, y)] = {
                    "tipo_entidad": "table",
                    "ultimo_paso": self.paso_actual,
                }
            elif mat == "furnace":
                self.mapa_alocentrico["estacion_trabajo"][(x, y)] = {
                    "tipo_entidad": "furnace",
                    "ultimo_paso": self.paso_actual,
                }
            elif mat == "water":
                self.mapa_alocentrico["fuente_agua"][(x, y)] = {
                    "tipo_entidad": "water",
                    "ultimo_paso": self.paso_actual,
                }
            elif mat in ("stone", "coal", "iron"):
                self.mapa_alocentrico["yacimiento_mineral"][(x, y)] = {
                    "tipo_entidad": mat,
                    "ultimo_paso": self.paso_actual,
                }

    def consultar_hitos_memoria(self, categoria: str, tipo_entidad: Optional[str] = None) -> List[Tuple[int, int]]:
        """Retorna las posiciones recordadas de una categoría y tipo de entidad."""
        hitos = self.mapa_alocentrico.get(categoria, {})
        posiciones = []
        for pos, info in hitos.items():
            if tipo_entidad is None or info.get("tipo_entidad") == tipo_entidad:
                posiciones.append(pos)
        return posiciones

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
        self.paso_actual += 1
        px, py = player_pos

        # 1. Registrar lo visto en el mapa alocéntrico
        self.registrar_observacion_en_memoria(px, py, vista_local)

        # 2. Las prioridades críticas 1 a 6 (amenaza inmediata, sed crítica, hambre crítica, sueño)
        # se evalúan de forma idéntica para preservar la paridad biológica
        amenazas_visibles = [
            (pos, obj) for pos, (mat, obj) in vista_local.items()
            if obj is not None and type(obj).__name__ in ("Zombie", "Skeleton", "Arrow")
        ]

        if sleeping:
            if amenazas_visibles:
                return ACC_NOOP
            if energia < 9:
                return ACC_SLEEP
            return ACC_NOOP

        # Amenazas inmediatas (combate / evasión)
        if amenazas_visibles:
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
            if dist_amenaza == 1:
                if salud >= 4 or tiene_espada:
                    dir_esperada = (dx, dy)
                    if facing == dir_esperada:
                        return ACC_DO
                    if dir_esperada in ACCION_MOVIMIENTO:
                        return ACCION_MOVIMIENTO[dir_esperada]
                else:
                    escape_dir = self._buscar_paso_huida(px, py, pos_amenaza, vista_local)
                    if escape_dir:
                        return ACCION_MOVIMIENTO[escape_dir]
            elif dist_amenaza == 2 and salud <= 5:
                escape_dir = self._buscar_paso_huida(px, py, pos_amenaza, vista_local)
                if escape_dir:
                    return ACCION_MOVIMIENTO[escape_dir]

        # Sed crítica (bebida <= 4)
        if bebida <= 4:
            accion_agua = self._interactuar_o_acercar_material(
                px, py, facing, "water", vista_local, interact_es_do=True
            )
            if accion_agua:
                return accion_agua
            # Si no hay agua visible en la fóvea pero sí en la memoria, navegar a la más cercana
            hitos_agua = self.consultar_hitos_memoria("fuente_agua", "water")
            if hitos_agua:
                hitos_agua.sort(key=lambda p: abs(p[0] - px) + abs(p[1] - py))
                paso_mem = self._camino_bfs(px, py, hitos_agua[0], vista_local, interactuar_adyacente=True)
                if paso_mem and paso_mem in ACCION_MOVIMIENTO:
                    return ACCION_MOVIMIENTO[paso_mem]

        # Hambre crítica (comida <= 4)
        if comida <= 4:
            accion_comida = self._buscar_comida(px, py, facing, vista_local)
            if accion_comida:
                return accion_comida

        # Sueño / Noche
        if not amenazas_visibles:
            if energia <= 2:
                return ACC_SLEEP
            if daylight < 0.2 and energia <= 6:
                return ACC_SLEEP

        # Sed y nutrición preventiva
        if bebida <= 7:
            for d in DIRECCIONES_CARDINALES:
                pos = (px + d[0], py + d[1])
                mat, obj = vista_local.get(pos, (None, None))
                if mat == "water":
                    if facing == d:
                        return ACC_DO
                    return ACCION_MOVIMIENTO[d]

        if comida <= 7:
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
        # 7. PROGRESIÓN TECNOLÓGICA CON MEMORIA ALOCÉNTRICA
        # -------------------------------------------------------------
        accion_tech = self._resolver_tecnologia_con_memoria(
            px, py, facing, inventario, vista_local
        )
        if accion_tech:
            return accion_tech

        # -------------------------------------------------------------
        # 8. RECOLECCIÓN DE RECURSOS (con memoria de yacimientos)
        # -------------------------------------------------------------
        madera = inventario.get("wood", 0)
        piedra = inventario.get("stone", 0)
        carbon = inventario.get("coal", 0)
        hierro = inventario.get("iron", 0)
        tiene_pico_madera = inventario.get("wood_pickaxe", 0) > 0
        tiene_pico_piedra = inventario.get("stone_pickaxe", 0) > 0

        # Madera
        if madera < 4:
            accion_arbol = self._interactuar_o_acercar_material(
                px, py, facing, "tree", vista_local, interact_es_do=True
            )
            if accion_arbol:
                return accion_arbol

        # Piedra con memoria si no visible
        if (tiene_pico_madera or tiene_pico_piedra) and piedra < 5:
            accion_piedra = self._interactuar_o_acercar_material(
                px, py, facing, "stone", vista_local, interact_es_do=True
            )
            if accion_piedra:
                return accion_piedra
            hitos_piedra = self.consultar_hitos_memoria("yacimiento_mineral", "stone")
            if hitos_piedra:
                hitos_piedra.sort(key=lambda p: abs(p[0] - px) + abs(p[1] - py))
                paso_p = self._camino_bfs(px, py, hitos_piedra[0], vista_local, interactuar_adyacente=True)
                if paso_p and paso_p in ACCION_MOVIMIENTO:
                    return ACCION_MOVIMIENTO[paso_p]

        # Hierro / Carbón con memoria
        if tiene_pico_piedra:
            if hierro < 2:
                accion_hierro = self._interactuar_o_acercar_material(
                    px, py, facing, "iron", vista_local, interact_es_do=True
                )
                if accion_hierro:
                    return accion_hierro
                hitos_hierro = self.consultar_hitos_memoria("yacimiento_mineral", "iron")
                if hitos_hierro:
                    hitos_hierro.sort(key=lambda p: abs(p[0] - px) + abs(p[1] - py))
                    paso_fe = self._camino_bfs(px, py, hitos_hierro[0], vista_local, interactuar_adyacente=True)
                    if paso_fe and paso_fe in ACCION_MOVIMIENTO:
                        return ACCION_MOVIMIENTO[paso_fe]

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

        # Exploración activa anti-bucles
        return self._explorar(px, py, facing, vista_local)

    def _resolver_tecnologia_con_memoria(
        self,
        px: int,
        py: int,
        facing: Tuple[int, int],
        inventario: Dict[str, int],
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
    ) -> Optional[str]:
        """Aplica la progresión tecnológica consultando la memoria alocéntrica de mesas y hornos."""
        madera = inventario.get("wood", 0)
        piedra = inventario.get("stone", 0)
        hierro = inventario.get("iron", 0)
        tiene_wood_pickaxe = inventario.get("wood_pickaxe", 0) > 0
        tiene_wood_sword = inventario.get("wood_sword", 0) > 0
        tiene_stone_pickaxe = inventario.get("stone_pickaxe", 0) > 0
        tiene_iron_pickaxe = inventario.get("iron_pickaxe", 0) > 0

        # 1. Comprobar presencia de mesa en escena local
        mesas_visibles = [pos for pos, (mat, obj) in vista_local.items() if mat == "table"]
        mesa_pos = mesas_visibles[0] if mesas_visibles else None

        # Si no es visible, consultar memoria alocéntrica
        if not mesa_pos:
            mesas_mem = self.consultar_hitos_memoria("estacion_trabajo", "table")
            if mesas_mem:
                mesas_mem.sort(key=lambda p: abs(p[0] - px) + abs(p[1] - py))
                mesa_pos = mesas_mem[0]

        hornos_visibles = [pos for pos, (mat, obj) in vista_local.items() if mat == "furnace"]
        horno_pos = hornos_visibles[0] if hornos_visibles else None
        if not horno_pos:
            hornos_mem = self.consultar_hitos_memoria("estacion_trabajo", "furnace")
            if hornos_mem:
                hornos_mem.sort(key=lambda p: abs(p[0] - px) + abs(p[1] - py))
                horno_pos = hornos_mem[0]

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
                return ACC_PLACE_TABLE
            if mesa_pos and not mesa_adyacente and madera >= 1:
                # Volver a la mesa recordada
                paso = self._camino_bfs(px, py, mesa_pos, vista_local, interactuar_adyacente=True)
                if paso and paso in ACCION_MOVIMIENTO:
                    return ACCION_MOVIMIENTO[paso]

        # Regla T2: Crear espada de madera
        if tiene_wood_pickaxe and not tiene_wood_sword:
            if mesa_adyacente and madera >= 1:
                return ACC_MAKE_WOOD_SWORD
            if mesa_pos and not mesa_adyacente and madera >= 1:
                paso = self._camino_bfs(px, py, mesa_pos, vista_local, interactuar_adyacente=True)
                if paso and paso in ACCION_MOVIMIENTO:
                    return ACCION_MOVIMIENTO[paso]

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
            if mesa_pos and not mesa_adyacente and hierro >= 1 and madera >= 1:
                paso = self._camino_bfs(px, py, mesa_pos, vista_local, interactuar_adyacente=True)
                if paso and paso in ACCION_MOVIMIENTO:
                    return ACCION_MOVIMIENTO[paso]

        return None
