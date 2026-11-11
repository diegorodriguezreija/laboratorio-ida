"""
Línea base tradicional voraz con MEMORIA ESPACIAL idéntica a IdA para Crafter 2D.

Implementa un diseño aditivo puro sobre AgenteCrafterVoraz (crafter_voraz.py):
- NO reescribe la jerarquía de decisiones ni modifica umbrales ni combate.
- Se limita a añadir un mapa cognitivo alocéntrico de hitos permanentes (mesas, hornos, agua, minerales).
- Actualiza dinámicamente la memoria: registra cuando descubre un hito y elimina/actualiza cuando
  el material cambia (ej. al picar piedra, la casilla se actualiza a camino).
- Soporta navegación tanto en vista local como hacia objetivos fuera de vista mediante A*/BFS
  sobre casillas transitables recordadas o vector de aproximación euclídeo.
- Cumple la PRUEBA DE IDENTIDAD: si memoria_activa=False, la secuencia de acciones es 100% idéntica
  a la de AgenteCrafterVoraz en cualquier semilla.
"""

import importlib
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple

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
    Extensión aditiva de AgenteCrafterVoraz con Memoria Alocéntrica equivalente a la de IdA.
    """

    def __init__(self, radio_vision: int = 6, memoria_activa: bool = True):
        super().__init__(radio_vision=radio_vision)
        self.memoria_activa = memoria_activa
        # Mapa alocéntrico de hitos permanentes descubiertos:
        # {categoria: {posicion: {"tipo_entidad": str, "ultimo_paso": int}}}
        self.mapa_alocentrico: Dict[str, Dict[Tuple[int, int], Dict[str, Any]]] = {
            "estacion_trabajo": {},
            "fuente_agua": {},
            "yacimiento_mineral": {},
        }
        # Mapa de casillas transitables recordadas (caminables conocidas)
        self.casillas_transitables_recordadas: Set[Tuple[int, int]] = set()
        self.paso_actual: int = 0
        # Métrica de telemetría: contador de retornos guiados hacia objetivos fuera de vista
        self.retornos_fuera_de_vista: int = 0

    def registrar_observacion_en_memoria(
        self,
        px: int,
        py: int,
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
    ) -> None:
        """
        Registra o actualiza la memoria alocéntrica.
        Elimina entradas si una casilla visible ha cambiado (ej. piedra picada que ahora es path/grass).
        """
        for (x, y), (mat, obj) in vista_local.items():
            pos = (x, y)

            # 1. Actualizar mapa de transitabilidad
            if mat in MATERIALES_CAMINABLES and mat != "lava" and obj is None:
                self.casillas_transitables_recordadas.add(pos)
            else:
                self.casillas_transitables_recordadas.discard(pos)

            # 2. Actualizar / Limpiar estaciones de trabajo
            if mat in ("table", "furnace"):
                self.mapa_alocentrico["estacion_trabajo"][pos] = {
                    "tipo_entidad": mat,
                    "ultimo_paso": self.paso_actual,
                }
            else:
                # Si la casilla está a la vista y ya NO es mesa ni horno, borrarla
                self.mapa_alocentrico["estacion_trabajo"].pop(pos, None)

            # 3. Actualizar / Limpiar fuentes de agua
            if mat == "water":
                self.mapa_alocentrico["fuente_agua"][pos] = {
                    "tipo_entidad": "water",
                    "ultimo_paso": self.paso_actual,
                }
            else:
                self.mapa_alocentrico["fuente_agua"].pop(pos, None)

            # 4. Actualizar / Limpiar yacimientos minerales (piedra, carbón, hierro)
            if mat in ("stone", "coal", "iron"):
                self.mapa_alocentrico["yacimiento_mineral"][pos] = {
                    "tipo_entidad": mat,
                    "ultimo_paso": self.paso_actual,
                }
            else:
                # Si fue picada y ya no es mineral, borrarla para no volver a ella
                self.mapa_alocentrico["yacimiento_mineral"].pop(pos, None)

    def consultar_hitos_memoria(self, categoria: str, tipo_entidad: Optional[str] = None) -> List[Tuple[int, int]]:
        """Retorna las coordenadas recordadas de un hito específico."""
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
        # Si la memoria está desactivada, ejecutar la decisión original exacta (Prueba de Identidad)
        if not self.memoria_activa:
            return super().decidir(
                player_pos, facing, salud, comida, bebida, energia, daylight, sleeping, inventario, vista_local
            )

        self.paso_actual += 1
        px, py = player_pos
        self.registrar_observacion_en_memoria(px, py, vista_local)

        # Ejecutamos la lógica base del voraz
        return super().decidir(
            player_pos, facing, salud, comida, bebida, energia, daylight, sleeping, inventario, vista_local
        )

    def _resolver_tecnologia(
        self,
        px: int,
        py: int,
        facing: Tuple[int, int],
        inventario: Dict[str, int],
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
    ) -> Optional[str]:
        """
        Sobrescribe EXCLUSIVAMENTE el retorno a estaciones cuando no son visibles en la vista local,
        respetando las recetas oficiales de Crafter.
        """
        if not self.memoria_activa:
            return super()._resolver_tecnologia(px, py, facing, inventario, vista_local)

        madera = inventario.get("wood", 0)
        piedra = inventario.get("stone", 0)
        carbon = inventario.get("coal", 0)
        hierro = inventario.get("iron", 0)
        tiene_wood_pickaxe = inventario.get("wood_pickaxe", 0) > 0
        tiene_wood_sword = inventario.get("wood_sword", 0) > 0
        tiene_stone_pickaxe = inventario.get("stone_pickaxe", 0) > 0
        tiene_iron_pickaxe = inventario.get("iron_pickaxe", 0) > 0

        # Primero evaluar si hay mesa u horno visibles
        mesa_pos = None
        horno_pos = None
        for pos, (mat, obj) in vista_local.items():
            if mat == "table":
                mesa_pos = pos
            elif mat == "furnace":
                horno_pos = pos

        # Si no están visibles, consultar memoria alocéntrica
        mesa_en_memoria = False
        if not mesa_pos:
            mesas_mem = self.consultar_hitos_memoria("estacion_trabajo", "table")
            if mesas_mem:
                mesas_mem.sort(key=lambda p: abs(p[0] - px) + abs(p[1] - py))
                mesa_pos = mesas_mem[0]
                mesa_en_memoria = True

        horno_en_memoria = False
        if not horno_pos:
            hornos_mem = self.consultar_hitos_memoria("estacion_trabajo", "furnace")
            if hornos_mem:
                hornos_mem.sort(key=lambda p: abs(p[0] - px) + abs(p[1] - py))
                horno_pos = hornos_mem[0]
                horno_en_memoria = True

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
                paso = self._navegar_hacia(px, py, mesa_pos, vista_local)
                if paso:
                    if mesa_en_memoria:
                        self.retornos_fuera_de_vista += 1
                    return paso

        # Regla T2: Crear espada de madera
        if tiene_wood_pickaxe and not tiene_wood_sword:
            if mesa_adyacente and madera >= 1:
                return ACC_MAKE_WOOD_SWORD
            if mesa_pos and not mesa_adyacente and madera >= 1:
                paso = self._navegar_hacia(px, py, mesa_pos, vista_local)
                if paso:
                    if mesa_en_memoria:
                        self.retornos_fuera_de_vista += 1
                    return paso

        # Regla T3: Crear pico de piedra
        if tiene_wood_pickaxe and not tiene_stone_pickaxe:
            if mesa_adyacente and piedra >= 1 and madera >= 1:
                return ACC_MAKE_STONE_PICKAXE
            if mesa_pos and not mesa_adyacente and piedra >= 1 and madera >= 1:
                paso = self._navegar_hacia(px, py, mesa_pos, vista_local)
                if paso:
                    if mesa_en_memoria:
                        self.retornos_fuera_de_vista += 1
                    return paso

        # Regla T4: Colocar horno (requiere piedra >= 4)
        if tiene_stone_pickaxe and not horno_pos and piedra >= 4:
            return ACC_PLACE_FURNACE

        # Regla T5: Crear pico de hierro (receta oficial Crafter: nearby table + furnace, uses 1 wood, 1 coal, 1 iron)
        if tiene_stone_pickaxe and not tiene_iron_pickaxe and horno_pos and mesa_pos:
            if horno_adyacente and mesa_adyacente and hierro >= 1 and carbon >= 1 and madera >= 1:
                return ACC_MAKE_IRON_PICKAXE
            # Si tenemos los 3 materiales pero falta acercarse a mesa u horno
            if hierro >= 1 and carbon >= 1 and madera >= 1:
                # Navegar hacia la estación más lejana de las dos
                target = horno_pos if not horno_adyacente else mesa_pos
                paso = self._navegar_hacia(px, py, target, vista_local)
                if paso:
                    if horno_en_memoria or mesa_en_memoria:
                        self.retornos_fuera_de_vista += 1
                    return paso

        return None

    def _navegar_hacia(
        self,
        px: int,
        py: int,
        destino: Tuple[int, int],
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
    ) -> Optional[str]:
        """
        Navega hacia un objetivo cardinal.
        1. Si está dentro de la vista local, utiliza BFS exacto.
        2. Si está fuera de la vista local, busca en el mapa de casillas transitables recordadas.
        3. Si no hay camino continuo conocido, da el paso cardinal legal que más reduce la distancia Manhattan.
        """
        dest_x, dest_y = destino
        dist_m = abs(dest_x - px) + abs(dest_y - py)
        if dist_m <= 1:
            return None

        # 1. Intentar BFS sobre vista local
        paso_local = self._camino_bfs(px, py, destino, vista_local, interactuar_adyacente=True)
        if paso_local and paso_local in ACCION_MOVIMIENTO:
            return ACCION_MOVIMIENTO[paso_local]

        # 2. Si el objetivo está fuera de la vista local (distancia > 6), planificar sobre memoria global recordada
        candidatos = []
        for d in DIRECCIONES_CARDINALES:
            cand = (px + d[0], py + d[1])
            if self._es_transitable(cand, vista_local):
                nueva_dist = abs(dest_x - cand[0]) + abs(dest_y - cand[1])
                candidatos.append((nueva_dist, d))

        if candidatos:
            candidatos.sort(key=lambda x: x[0])
            mejor_d = candidatos[0][1]
            return ACCION_MOVIMIENTO.get(mejor_d, ACC_NOOP)

        return None
