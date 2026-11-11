"""
Línea base tradicional voraz con MEMORIA ESPACIAL idéntica a IdA para Crafter 2D.

Implementa un diseño aditivo puro sobre AgenteCrafterVoraz (crafter_voraz.py):
- NO reescribe la jerarquía de decisiones ni modifica umbrales ni combate.
- Se limita a añadir un mapa cognitivo alocéntrico de hitos permanentes (mesas, hornos, agua, minerales).
- Actualiza dinámicamente la memoria: registra cuando descubre un hito y elimina/actualiza cuando
  el material cambia (ej. al picar piedra, la casilla se actualiza a camino).
- Soporta navegación tanto en vista local como hacia objetivos fuera de vista mediante BFS
  sobre casillas transitables recordadas.
- Métrica de telemetría: retornos_fuera_de_vista contabiliza viajes COMPLETADOS que se iniciaron
  estando el objetivo fuera de la ventana de visión local y concluyeron alcanzando la adyacencia.
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
        # Métrica de telemetría: contador de viajes completos hacia objetivos iniciados fuera de vista
        self.retornos_fuera_de_vista: int = 0
        self._viaje_activo_pos: Optional[Tuple[int, int]] = None
        self._viaje_activo_es_fuera_de_vista: bool = False

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

        # Monitorear si hemos completado un viaje iniciado fuera de vista
        if self._viaje_activo_pos is not None:
            vx, vy = self._viaje_activo_pos
            if abs(vx - px) + abs(vy - py) <= 1:
                if self._viaje_activo_es_fuera_de_vista:
                    self.retornos_fuera_de_vista += 1
                self._viaje_activo_pos = None
                self._viaje_activo_es_fuera_de_vista = False

        # Ejecutamos la lógica base del voraz
        return super().decidir(
            player_pos, facing, salud, comida, bebida, energia, daylight, sleeping, inventario, vista_local
        )

    def _interactuar_o_acercar_material(
        self,
        px: int,
        py: int,
        facing: Tuple[int, int],
        material_target: str,
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
        interact_es_do: bool = True,
    ) -> Optional[str]:
        """
        Extensión aditiva: si el material no está en la vista local, consulta memoria alocéntrica.
        """
        if not self.memoria_activa:
            return super()._interactuar_o_acercar_material(
                px, py, facing, material_target, vista_local, interact_es_do
            )

        # Primero probar con el comportamiento base sobre la vista local
        paso_local = super()._interactuar_o_acercar_material(
            px, py, facing, material_target, vista_local, interact_es_do
        )
        if paso_local is not None:
            return paso_local

        # Si no está visible, consultar memoria alocéntrica (equivalente a IdA S3)
        if material_target == "water":
            hitos = self.consultar_hitos_memoria("fuente_agua", "water")
        elif material_target in ("stone", "coal", "iron"):
            hitos = self.consultar_hitos_memoria("yacimiento_mineral", material_target)
        else:
            hitos = []

        if hitos:
            hitos.sort(key=lambda p: abs(p[0] - px) + abs(p[1] - py))
            target = hitos[0]
            # Iniciar viaje hacia recurso recordado si aplica
            if self._viaje_activo_pos != target:
                self._viaje_activo_pos = target
                self._viaje_activo_es_fuera_de_vista = True
            return self._navegar_hacia(px, py, target, vista_local, interactuar_adyacente=True)

        return None

    def _resolver_tecnologia(
        self,
        px: int,
        py: int,
        facing: Tuple[int, int],
        inventario: Dict[str, int],
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
    ) -> Optional[str]:
        """
        Sobrescribe el retorno a estaciones cuando no son visibles en la vista local,
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
                if self._viaje_activo_pos != mesa_pos:
                    self._viaje_activo_pos = mesa_pos
                    self._viaje_activo_es_fuera_de_vista = mesa_en_memoria
                return self._navegar_hacia(px, py, mesa_pos, vista_local)

        # Regla T2: Crear espada de madera
        if tiene_wood_pickaxe and not tiene_wood_sword:
            if mesa_adyacente and madera >= 1:
                return ACC_MAKE_WOOD_SWORD
            if mesa_pos and not mesa_adyacente and madera >= 1:
                if self._viaje_activo_pos != mesa_pos:
                    self._viaje_activo_pos = mesa_pos
                    self._viaje_activo_es_fuera_de_vista = mesa_en_memoria
                return self._navegar_hacia(px, py, mesa_pos, vista_local)

        # Regla T3: Crear pico de piedra
        if tiene_wood_pickaxe and not tiene_stone_pickaxe:
            if mesa_adyacente and piedra >= 1 and madera >= 1:
                return ACC_MAKE_STONE_PICKAXE
            if mesa_pos and not mesa_adyacente and piedra >= 1 and madera >= 1:
                if self._viaje_activo_pos != mesa_pos:
                    self._viaje_activo_pos = mesa_pos
                    self._viaje_activo_es_fuera_de_vista = mesa_en_memoria
                return self._navegar_hacia(px, py, mesa_pos, vista_local)

        # Regla T4: Colocar horno (requiere piedra >= 4)
        if tiene_stone_pickaxe and not horno_pos and piedra >= 4:
            return ACC_PLACE_FURNACE

        # Regla T5: Crear pico de hierro (receta oficial Crafter: nearby table + furnace, uses 1 wood, 1 coal, 1 iron)
        if tiene_stone_pickaxe and not tiene_iron_pickaxe and horno_pos and mesa_pos:
            if horno_adyacente and mesa_adyacente and hierro >= 1 and carbon >= 1 and madera >= 1:
                return ACC_MAKE_IRON_PICKAXE
            if hierro >= 1 and carbon >= 1 and madera >= 1:
                target = horno_pos if not horno_adyacente else mesa_pos
                target_mem = horno_en_memoria if not horno_adyacente else mesa_en_memoria
                if self._viaje_activo_pos != target:
                    self._viaje_activo_pos = target
                    self._viaje_activo_es_fuera_de_vista = target_mem
                return self._navegar_hacia(px, py, target, vista_local)

        return None

    def _navegar_hacia(
        self,
        px: int,
        py: int,
        destino: Tuple[int, int],
        vista_local: Dict[Tuple[int, int], Tuple[str, Any]],
        interactuar_adyacente: bool = True,
    ) -> Optional[str]:
        """
        Navega hacia un objetivo destino usando BFS sobre casillas transitables recordadas y visibles.
        Si destino está adyacente (distancia Manhattan <= 1) e interactuar_adyacente es True, retorna None.
        Si la ruta completa no está explorada, avanza hacia el nodo transitable conocido más cercano al objetivo.
        """
        dest_x, dest_y = destino
        dist_m = abs(dest_x - px) + abs(dest_y - py)
        if interactuar_adyacente and dist_m <= 1:
            return None
        if not interactuar_adyacente and dist_m == 0:
            return None

        # Si el destino está visible en la vista local, usar BFS local
        if destino in vista_local:
            paso_local = self._camino_bfs(px, py, destino, vista_local, interactuar_adyacente=interactuar_adyacente)
            if paso_local and paso_local in ACCION_MOVIMIENTO:
                return ACCION_MOVIMIENTO[paso_local]

        # BFS global sobre el conjunto de casillas transitables recordadas + vista actual
        def _es_transitable_nodo(pos: Tuple[int, int]) -> bool:
            if pos in vista_local:
                return self._es_transitable(pos, vista_local)
            return pos in self.casillas_transitables_recordadas

        cola = deque([(px, py)])
        visitados = {(px, py)}
        padres: Dict[Tuple[int, int], Tuple[Tuple[int, int], Tuple[int, int]]] = {}
        meta_encontrada: Optional[Tuple[int, int]] = None
        nodo_mas_cercano = (px, py)
        min_dist_al_destino = dist_m

        while cola:
            actual = cola.popleft()
            cx, cy = actual
            d_actual = abs(dest_x - cx) + abs(dest_y - cy)

            if d_actual < min_dist_al_destino:
                min_dist_al_destino = d_actual
                nodo_mas_cercano = actual

            if interactuar_adyacente:
                if d_actual == 1:
                    meta_encontrada = actual
                    break
            else:
                if d_actual == 0:
                    meta_encontrada = actual
                    break

            for d in DIRECCIONES_CARDINALES:
                vecino = (cx + d[0], cy + d[1])
                if vecino not in visitados and _es_transitable_nodo(vecino):
                    visitados.add(vecino)
                    padres[vecino] = (actual, d)
                    cola.append(vecino)

        target = meta_encontrada if meta_encontrada else (nodo_mas_cercano if nodo_mas_cercano != (px, py) else None)
        if not target:
            return None

        curr = target
        primer_paso = None
        while curr != (px, py):
            p_padre, dir_paso = padres[curr]
            if p_padre == (px, py):
                primer_paso = dir_paso
                break
            curr = p_padre

        if primer_paso and primer_paso in ACCION_MOVIMIENTO:
            return ACCION_MOVIMIENTO[primer_paso]

        return None
