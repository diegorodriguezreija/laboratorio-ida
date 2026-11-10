"""
Adaptador Sensoriomotor de Membrana para Crafter (DeepMind / Danijar Hafner).
Implementa ISensorEntorno e IActuadorEntorno conectando el Nivel 3 con el Core de IdA v12.0.
"""

from typing import Tuple, List, Dict, Any, Optional, Set
import numpy as np
try:
    import crafter
except ImportError:
    crafter = None

from nivel_1_core.vocabulario import V_Comando, V_Relacion
from nivel_1_core.contratos import (
    Pieza,
    ResultadoEfectoEntorno,
    ISensorEntorno,
    IActuadorEntorno,
)


class AdaptadorCrafter(ISensorEntorno, IActuadorEntorno):
    """
    Adaptador de Membrana para el entorno 2D procedural Crafter.
    Traduce el estado procedimental y metabólico de Crafter al espacio neurosimbólico
    y somático de IdA v12.0.
    """

    ACCIONES_MAP = {
        "noop": 0,
        "move_left": 1,
        "move_right": 2,
        "move_up": 3,
        "move_down": 4,
        "do": 5,
        "sleep": 6,
        "place_stone": 7,
        "place_table": 8,
        "place_furnace": 9,
        "place_plant": 10,
        "make_wood_pickaxe": 11,
        "make_stone_pickaxe": 12,
        "make_iron_pickaxe": 13,
        "make_wood_sword": 14,
        "make_stone_sword": 15,
        "make_iron_sword": 16,
    }

    MATERIALES_RECURSOS = {"tree", "stone", "coal", "iron", "diamond"}
    MATERIALES_ESTACIONES = {"table", "furnace"}
    MATERIALES_CAMINABLES = {"grass", "path", "sand"}

    def __init__(
        self,
        seed: Optional[int] = None,
        radio_vision: int = 6,
        max_pasos: int = 10000,
    ):
        self.seed = seed
        self.radio_vision = radio_vision
        self.max_pasos = max_pasos

        self.env: Optional[crafter.Env] = None
        self._conectado: bool = False
        self.ultimo_obs: Optional[np.ndarray] = None
        self.ultimo_info: Dict[str, Any] = {}
        self.partida_terminada: bool = False
        self.recompensa_acumulada: float = 0.0
        self.pasos_actuales: int = 0

        # Estado somático previo para cálculo de deltas
        self.salud_previa: int = 9
        self.comida_previa: int = 9
        self.bebida_previa: int = 9
        self.energia_previa: int = 9
        self.logros_desbloqueados: Set[str] = set()

    def conectar(self) -> None:
        """Inicializa el entorno Crafter."""
        if crafter is None:
            raise ImportError("Falta la librería crafter. Instálala con: pip install -e \".[crafter]\"")
        if self._conectado and self.env is not None:
            return

        self.env = crafter.Env(
            area=(64, 64),
            view=(9, 9),
            size=(64, 64),
            reward=True,
            length=self.max_pasos,
            seed=self.seed,
        )
        # Reemplazar los conjuntos no ordenados de _chunks por listas deterministas con interfaz de set
        # para garantizar que el orden de iteración sobre criaturas en _balance_object sea 100% reproducible
        class _DeterministicChunkSet(list):
            def add(self, item: Any) -> None:
                if item not in self:
                    self.append(item)

        self.ultimo_obs = self.env.reset()
        if hasattr(self.env, "_world") and hasattr(self.env._world, "_chunks"):
            chunks_det = {}
            for k, v in self.env._world._chunks.items():
                s = _DeterministicChunkSet(sorted(v, key=lambda o: (int(o.pos[0]), int(o.pos[1]), type(o).__name__)))
                chunks_det[k] = s
            import collections
            new_dd = collections.defaultdict(_DeterministicChunkSet)
            new_dd.update(chunks_det)
            self.env._world._chunks = new_dd
        self.partida_terminada = False
        self.recompensa_acumulada = 0.0
        self.pasos_actuales = 0
        self.logros_desbloqueados = set()

        # Captura inicial de info
        player = self.env._player
        self.salud_previa = player.health
        self.comida_previa = player.inventory.get("food", 9)
        self.bebida_previa = player.inventory.get("drink", 9)
        self.energia_previa = player.inventory.get("energy", 9)
        self.ultimo_info = {
            "inventory": player.inventory.copy(),
            "achievements": player.achievements.copy(),
            "player_pos": player.pos.copy(),
            "daylight": float(self.env._world.daylight),
            "facing": tuple(player.facing),
            "sleeping": bool(player.sleeping),
        }
        self._conectado = True

    def desconectar(self) -> None:
        """Cierra el entorno Crafter limpiamente."""
        if not self._conectado:
            return
        if self.env is not None:
            try:
                self.env.close()
            except Exception:
                pass
            self.env = None
        self._conectado = False

    def reiniciar(self, seed: Optional[int] = None) -> None:
        """Reinicia la simulación para una nueva generación o episodio."""
        if seed is not None:
            self.seed = seed
        self.desconectar()
        self.conectar()

    # =========================================================================
    # PUERTO SENSOR (ISensorEntorno)
    # =========================================================================
    def percibir_mundo(self) -> Tuple[str, List[Pieza], List[str]]:
        """
        Transduce la ventana sensorial local de Crafter al espacio neurosimbólico.
        Retorna:
        - id_nodo_actual: "nodo_{px}_{py}"
        - piezas_escena: Lista de Piezas formales con su Tensor Sensorial 6D
        - nodos_adyacentes: Lista de nodos cardinales libres y seguros
        """
        if not self._conectado or self.env is None:
            self.conectar()

        player = self.env._player
        px, py = int(player.pos[0]), int(player.pos[1])
        id_nodo_actual = f"nodo_{px}_{py}"
        world = self.env._world
        daylight = float(world.daylight)

        piezas_escena: List[Pieza] = []
        nodos_adyacentes: List[str] = []

        # 1. Exploración de nodos cardinales inmediatos
        movimientos_cardinales = [
            ("NORTE", px, py - 1, (0, -1)),
            ("SUR", px, py + 1, (0, 1)),
            ("ESTE", px + 1, py, (1, 0)),
            ("OESTE", px - 1, py, (-1, 0)),
        ]

        for card, nx, ny, ddir in movimientos_cardinales:
            if 0 <= nx < 64 and 0 <= ny < 64:
                mat, obj = world[(nx, ny)]
                # Un nodo es transitable si es material caminable, sin lava y sin objeto bloqueante
                if mat in self.MATERIALES_CAMINABLES and mat != "lava" and obj is None:
                    nodos_adyacentes.append(f"nodo_{nx}_{ny}")

        # 2. Transducción de entidades en la vecindad local (radio de visión)
        xmin = max(0, px - self.radio_vision)
        xmax = min(64, px + self.radio_vision + 1)
        ymin = max(0, py - self.radio_vision)
        ymax = min(64, py + self.radio_vision + 1)

        for x in range(xmin, xmax):
            for y in range(ymin, ymax):
                if x == px and y == py:
                    continue  # La casilla del propio agente se maneja en propiocepción

                mat, obj = world[(x, y)]
                dist_manhattan = abs(x - px) + abs(y - py)
                norm_dist = max(1.0, float(dist_manhattan))
                dx = float(x - px)
                dy = float(y - py)
                dir_vector = (dx / norm_dist, dy / norm_dist)
                proximidad = max(0.0, 1.0 - (dist_manhattan / (self.radio_vision * 2.0)))

                # A. OBJETOS VIVOS / MOVILES
                if obj is not None:
                    tipo_cls = type(obj).__name__

                    if tipo_cls == "Cow":
                        # Nutriente móvil de alta energía
                        # 6D: [proximidad, magnitud, cinematica, entropia, nutricion, nocicepcion]
                        t_sens = np.array([proximidad, 0.85, 0.20, 0.15, 0.95, 0.0], dtype=np.float64)
                        p = Pieza(
                            id=f"vaca_{x}_{y}",
                            tipo_componente="Nutriente_Alimento",
                            arousal=float(min(1.0, 0.45 + 0.50 * proximidad)),
                            trust=0.95,
                            tensor_sensorial=t_sens,
                            product={
                                "sujeto": f"vaca_{x}_{y}",
                                "tipo_entidad": "Cow",
                                "target_nodo": f"nodo_{x}_{y}",
                                "x": x,
                                "y": y,
                                "relacion": V_Relacion.ES_NUTRITIVO,
                                "distancia_manhattan": dist_manhattan,
                                "vector_relativo": dir_vector,
                            },
                            inputs=["Sensor_Crafter_Ecologico"],
                        )
                        piezas_escena.append(p)

                    elif tipo_cls == "Plant":
                        # Alimento vegetal estático (solo consumible cuando está maduro: ripe=True)
                        ripe = bool(getattr(obj, "ripe", True))
                        valor_nutricion = 0.85 if ripe else 0.10
                        t_sens = np.array([proximidad, 0.60, 0.0, 0.05, valor_nutricion, 0.0], dtype=np.float64)
                        p = Pieza(
                            id=f"planta_{x}_{y}",
                            tipo_componente="Nutriente_Alimento" if ripe else "Cultivo_En_Crecimiento",
                            arousal=float(min(1.0, (0.55 if ripe else 0.20) + 0.40 * proximidad)),
                            trust=0.95 if ripe else 0.85,
                            tensor_sensorial=t_sens,
                            product={
                                "sujeto": f"planta_{x}_{y}",
                                "tipo_entidad": "Plant",
                                "target_nodo": f"nodo_{x}_{y}",
                                "x": x,
                                "y": y,
                                "ripe": ripe,
                                "relacion": V_Relacion.ES_NUTRITIVO if ripe else V_Relacion.ES_SEGURO,
                                "distancia_manhattan": dist_manhattan,
                                "vector_relativo": dir_vector,
                            },
                            inputs=["Sensor_Crafter_Ecologico"],
                        )
                        piezas_escena.append(p)

                    elif tipo_cls in ("Zombie", "Skeleton"):
                        # Depredador nocivo/letal
                        es_esqueleto = (tipo_cls == "Skeleton")
                        magnitud = 0.95 if es_esqueleto else 0.90
                        t_sens = np.array([proximidad, magnitud, 0.70, 0.60, 0.0, 0.99], dtype=np.float64)
                        p = Pieza(
                            id=f"depredador_{tipo_cls}_{x}_{y}",
                            tipo_componente="Amenaza_Predador",
                            arousal=float(min(1.0, 0.65 + 0.35 * proximidad)),
                            trust=0.98,
                            tensor_sensorial=t_sens,
                            product={
                                "sujeto": f"depredador_{tipo_cls}_{x}_{y}",
                                "tipo_entidad": tipo_cls,
                                "target_nodo": f"nodo_{x}_{y}",
                                "x": x,
                                "y": y,
                                "relacion": V_Relacion.ES_LETAL,
                                "distancia_manhattan": dist_manhattan,
                                "vector_relativo": dir_vector,
                            },
                            inputs=["Sensor_Crafter_Ecologico"],
                        )
                        piezas_escena.append(p)

                    elif tipo_cls == "Arrow":
                        # Proyectil nociceptivo inmediato
                        t_sens = np.array([proximidad, 0.98, 1.0, 0.80, 0.0, 1.0], dtype=np.float64)
                        p = Pieza(
                            id=f"flecha_{x}_{y}",
                            tipo_componente="Amenaza_Predador",
                            arousal=0.99,
                            trust=0.99,
                            tensor_sensorial=t_sens,
                            product={
                                "sujeto": f"flecha_{x}_{y}",
                                "tipo_entidad": "Arrow",
                                "target_nodo": f"nodo_{x}_{y}",
                                "x": x,
                                "y": y,
                                "relacion": V_Relacion.ES_LETAL,
                                "distancia_manhattan": dist_manhattan,
                                "vector_relativo": dir_vector,
                            },
                            inputs=["Sensor_Crafter_Ecologico"],
                        )
                        piezas_escena.append(p)

                # B. ELEMENTOS DEL TERRENO Y RECURSOS
                if mat == "water":
                    # Hidratación somática (nutrición hídrica)
                    t_sens = np.array([proximidad, 0.75, 0.0, 0.05, 0.90, 0.0], dtype=np.float64)
                    p = Pieza(
                        id=f"agua_{x}_{y}",
                        tipo_componente="Nutriente_Agua",
                        arousal=float(min(1.0, 0.30 + 0.50 * proximidad)),
                        trust=0.95,
                        tensor_sensorial=t_sens,
                        product={
                            "sujeto": f"agua_{x}_{y}",
                            "tipo_entidad": "water",
                            "target_nodo": f"nodo_{x}_{y}",
                            "x": x,
                            "y": y,
                            "relacion": V_Relacion.ES_NUTRITIVO,
                            "distancia_manhattan": dist_manhattan,
                            "vector_relativo": dir_vector,
                        },
                        inputs=["Sensor_Crafter_Ecologico"],
                    )
                    piezas_escena.append(p)

                elif mat == "lava":
                    # Muerte térmica instantánea
                    t_sens = np.array([proximidad, 1.0, 0.0, 0.10, 0.0, 1.0], dtype=np.float64)
                    p = Pieza(
                        id=f"lava_{x}_{y}",
                        tipo_componente="Peligro_Lava",
                        arousal=float(min(1.0, 0.75 + 0.25 * proximidad)),
                        trust=0.99,
                        tensor_sensorial=t_sens,
                        product={
                            "sujeto": f"lava_{x}_{y}",
                            "tipo_entidad": "lava",
                            "target_nodo": f"nodo_{x}_{y}",
                            "x": x,
                            "y": y,
                            "relacion": V_Relacion.ES_LETAL,
                            "distancia_manhattan": dist_manhattan,
                            "vector_relativo": dir_vector,
                        },
                        inputs=["Sensor_Crafter_Ecologico"],
                    )
                    piezas_escena.append(p)

                elif mat in self.MATERIALES_RECURSOS:
                    # Recursos recolectables para crafting
                    t_sens = np.array([proximidad, 0.60, 0.0, 0.05, 0.10, 0.0], dtype=np.float64)
                    p = Pieza(
                        id=f"recurso_{mat}_{x}_{y}",
                        tipo_componente="Recurso_Material",
                        arousal=float(min(1.0, 0.25 + 0.35 * proximidad)),
                        trust=0.92,
                        tensor_sensorial=t_sens,
                        product={
                            "sujeto": f"recurso_{mat}_{x}_{y}",
                            "tipo_entidad": mat,
                            "target_nodo": f"nodo_{x}_{y}",
                            "x": x,
                            "y": y,
                            "relacion": V_Relacion.ES_SEGURO,
                            "distancia_manhattan": dist_manhattan,
                            "vector_relativo": dir_vector,
                        },
                        inputs=["Sensor_Crafter_Ecologico"],
                    )
                    piezas_escena.append(p)

                elif mat in self.MATERIALES_ESTACIONES:
                    # Estaciones de trabajo colocadas
                    t_sens = np.array([proximidad, 0.70, 0.0, 0.02, 0.10, 0.0], dtype=np.float64)
                    p = Pieza(
                        id=f"estacion_{mat}_{x}_{y}",
                        tipo_componente="Estacion_Trabajo",
                        arousal=float(min(1.0, 0.30 + 0.40 * proximidad)),
                        trust=0.95,
                        tensor_sensorial=t_sens,
                        product={
                            "sujeto": f"estacion_{mat}_{x}_{y}",
                            "tipo_entidad": mat,
                            "target_nodo": f"nodo_{x}_{y}",
                            "x": x,
                            "y": y,
                            "relacion": V_Relacion.ES_FIABLE,
                            "distancia_manhattan": dist_manhattan,
                            "vector_relativo": dir_vector,
                        },
                        inputs=["Sensor_Crafter_Ecologico"],
                    )
                    piezas_escena.append(p)

        # Filtrado foveal de membrana: conservar todas las entidades vivas, estaciones y peligros inmediatos,
        # y limitar materiales repetitivos del terreno (agua, árboles, rocas) a los 3 más cercanos de cada tipo
        # para no saturar el presupuesto de amplitud de la Onda con decenas de bloques idénticos.
        piezas_prioritarias: List[Pieza] = []
        por_material: Dict[str, List[Pieza]] = {}
        for p_esc in piezas_escena:
            if p_esc.tipo_componente in ("Nutriente_Agua", "Recurso_Material", "Peligro_Lava"):
                t_ent = str(p_esc.product.get("tipo_entidad", p_esc.tipo_componente))
                por_material.setdefault(t_ent, []).append(p_esc)
            else:
                piezas_prioritarias.append(p_esc)

        for t_ent, lista_m in por_material.items():
            lista_m.sort(key=lambda p_item: int(p_item.product.get("distancia_manhattan", 99)))
            limite_k = 2 if t_ent == "lava" else 3
            piezas_prioritarias.extend(lista_m[:limite_k])

        piezas_escena = piezas_prioritarias

        # 3. Pieza de Telemetría Somática y Ritmo Circadiano
        inv = player.inventory
        fase_circadiana = "NOCHE" if daylight < 0.25 else ("DIA" if daylight > 0.60 else "CREPUSCULO")
        nodos_caminables_locales: Set[Tuple[int, int]] = set()
        for x in range(xmin, xmax):
            for y in range(ymin, ymax):
                mat_c, obj_c = world[(x, y)]
                if (x == px and y == py) or (mat_c in self.MATERIALES_CAMINABLES and mat_c != "lava" and obj_c is None):
                    nodos_caminables_locales.add((x, y))

        p_estado = Pieza(
            id="estado_somatico_crafter",
            tipo_componente="Estado_Entorno",
            arousal=0.85 if daylight < 0.25 or inv.get("health", 9) <= 3 else 0.35,
            trust=0.99,
            product={
                "salud": int(inv.get("health", 9)),
                "comida": int(inv.get("food", 9)),
                "bebida": int(inv.get("drink", 9)),
                "energia": int(inv.get("energy", 9)),
                "madera": int(inv.get("wood", 0)),
                "piedra": int(inv.get("stone", 0)),
                "carbon": int(inv.get("coal", 0)),
                "hierro": int(inv.get("iron", 0)),
                "diamante": int(inv.get("diamond", 0)),
                "sapling": int(inv.get("sapling", 0)),
                "wood_pickaxe": int(inv.get("wood_pickaxe", 0)),
                "stone_pickaxe": int(inv.get("stone_pickaxe", 0)),
                "iron_pickaxe": int(inv.get("iron_pickaxe", 0)),
                "wood_sword": int(inv.get("wood_sword", 0)),
                "stone_sword": int(inv.get("stone_sword", 0)),
                "iron_sword": int(inv.get("iron_sword", 0)),
                "daylight": daylight,
                "fase_circadiana": fase_circadiana,
                "player_pos": (px, py),
                "facing": tuple(player.facing),
                "sleeping": bool(player.sleeping),
                "pasos": self.pasos_actuales,
                "muerto": bool(player.health <= 0),
                "nodos_caminables": list(nodos_caminables_locales),
                "logros_actuales": list(self.logros_desbloqueados),
            },
            inputs=["Sensor_Crafter_Somatico"],
        )
        piezas_escena.append(p_estado)

        return id_nodo_actual, piezas_escena, nodos_adyacentes

    # =========================================================================
    # PUERTO ACTUADOR (IActuadorEntorno)
    # =========================================================================
    def ejecutar_comando_fisico(
        self,
        comando: V_Comando,
        target: str,
        factor_fauces: float = 1.0,
        payload_extra: Optional[Dict[str, Any]] = None,
    ) -> ResultadoEfectoEntorno:
        """
        Materializa un V_Comando en una acción física de Crafter (0-16).
        Devuelve las consecuencias biológicas reales en ResultadoEfectoEntorno.
        """
        if not self._conectado or self.env is None:
            return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        player = self.env._player
        px, py = int(player.pos[0]), int(player.pos[1])
        facing_actual = tuple(player.facing)

        accion_idx = 0  # noop por defecto

        # ---------------------------------------------------------------------
        # 1. LOCOMOCION (MOVER / ACECHAR)
        # ---------------------------------------------------------------------
        if comando in (V_Comando.MOVER, V_Comando.ACECHAR):
            if target in ("OESTE", "IZQUIERDA", "LEFT", "move_left"):
                accion_idx = self.ACCIONES_MAP["move_left"]
            elif target in ("ESTE", "DERECHA", "RIGHT", "move_right"):
                accion_idx = self.ACCIONES_MAP["move_right"]
            elif target in ("NORTE", "ARRIBA", "UP", "move_up"):
                accion_idx = self.ACCIONES_MAP["move_up"]
            elif target in ("SUR", "ABAJO", "DOWN", "move_down"):
                accion_idx = self.ACCIONES_MAP["move_down"]
            elif target.startswith("nodo_"):
                partes = target.replace("nodo_", "").split("_")
                if len(partes) == 2 and partes[0].lstrip("-").isdigit() and partes[1].lstrip("-").isdigit():
                    tx, ty = int(partes[0]), int(partes[1])
                    dx = tx - px
                    dy = ty - py
                    if abs(dx) >= abs(dy) and dx != 0:
                        accion_idx = self.ACCIONES_MAP["move_right"] if dx > 0 else self.ACCIONES_MAP["move_left"]
                    elif dy != 0:
                        accion_idx = self.ACCIONES_MAP["move_down"] if dy > 0 else self.ACCIONES_MAP["move_up"]

        # ---------------------------------------------------------------------
        # 2. INTERACCION FISICA: DEGLUTIR / ATACAR / COGER / ASIMILAR / EXPLORAR
        # ---------------------------------------------------------------------
        elif comando in (V_Comando.DEGLUTIR, V_Comando.ATACAR, V_Comando.COGER, V_Comando.ASIMILAR):
            accion_clave = target.lower()
            if f"make_{accion_clave}" in self.ACCIONES_MAP:
                accion_clave = f"make_{accion_clave}"
            elif f"place_{accion_clave}" in self.ACCIONES_MAP:
                accion_clave = f"place_{accion_clave}"

            if accion_clave in self.ACCIONES_MAP:
                if accion_clave.startswith("place_"):
                    # En Crafter, place_* coloca en player.pos + player.facing y requiere terreno válido y libre
                    valid_where = (
                        {"grass"} if accion_clave == "place_plant"
                        else ({"grass", "sand", "path", "water", "lava"} if accion_clave == "place_stone" else {"grass", "sand", "path"})
                    )
                    tx_f = px + facing_actual[0]
                    ty_f = py + facing_actual[1]
                    es_valido = False
                    if 0 <= tx_f < 64 and 0 <= ty_f < 64:
                        mat_f, obj_f = self.env._world[(tx_f, ty_f)]
                        if obj_f is None and mat_f in valid_where:
                            es_valido = True

                    if es_valido:
                        accion_idx = self.ACCIONES_MAP[accion_clave]
                    else:
                        # Si hay un árbol o vaca enfrente, despejar con 'do'; si no, dar un paso hacia terreno despejado
                        if 0 <= tx_f < 64 and 0 <= ty_f < 64:
                            mat_f, obj_f = self.env._world[(tx_f, ty_f)]
                        else:
                            mat_f, obj_f = None, None

                        if mat_f == "tree" or (obj_f is not None and type(obj_f).__name__ in ("Cow", "Zombie", "Skeleton")):
                            accion_idx = self.ACCIONES_MAP["do"]
                        else:
                            dirs_mov = [
                                (-1, 0, "move_left"),
                                (1, 0, "move_right"),
                                (0, -1, "move_up"),
                                (0, 1, "move_down"),
                            ]
                            mejor_mov = None
                            for dx_m, dy_m, m_name in dirs_mov:
                                p1x, p1y = px + dx_m, py + dy_m
                                p2x, p2y = px + 2 * dx_m, py + 2 * dy_m
                                if 0 <= p1x < 64 and 0 <= p1y < 64:
                                    m1, o1 = self.env._world[(p1x, p1y)]
                                    if m1 in self.MATERIALES_CAMINABLES and m1 != "lava" and o1 is None:
                                        if mejor_mov is None:
                                            mejor_mov = m_name
                                        if 0 <= p2x < 64 and 0 <= p2y < 64:
                                            m2, o2 = self.env._world[(p2x, p2y)]
                                            if m2 in valid_where and o2 is None:
                                                mejor_mov = m_name
                                                break
                            accion_idx = self.ACCIONES_MAP[mejor_mov] if mejor_mov else self.ACCIONES_MAP[accion_clave]
                else:
                    accion_idx = self.ACCIONES_MAP[accion_clave]
            else:
                # En Crafter, 'do' interactúa con la casilla situada en player.pos + player.facing
                # Si el target es un nodo específico adyacente, comprobamos si estamos encarándolo
                necesita_encarar = None
                if target.startswith("nodo_"):
                    partes = target.replace("nodo_", "").split("_")
                    if len(partes) == 2 and partes[0].lstrip("-").isdigit() and partes[1].lstrip("-").isdigit():
                        tx, ty = int(partes[0]), int(partes[1])
                        req_facing = (tx - px, ty - py)
                        if req_facing != facing_actual:
                            necesita_encarar = req_facing

                if necesita_encarar is not None:
                    # Rotar primero hacia el objetivo moviéndose en su dirección
                    fx, fy = necesita_encarar
                    if fx < 0:
                        accion_idx = self.ACCIONES_MAP["move_left"]
                    elif fx > 0:
                        accion_idx = self.ACCIONES_MAP["move_right"]
                    elif fy < 0:
                        accion_idx = self.ACCIONES_MAP["move_up"]
                    elif fy > 0:
                        accion_idx = self.ACCIONES_MAP["move_down"]
                else:
                    accion_idx = self.ACCIONES_MAP["do"]

        # ---------------------------------------------------------------------
        # 3. DESCANSO / SUEÑO / ESPERA
        # ---------------------------------------------------------------------
        elif comando == V_Comando.ESPERAR:
            desea_dormir = (
                target in ("DORMIR", "sleep", "REPOSO")
                or (payload_extra and payload_extra.get("dormir", False))
                or player.inventory.get("energy", 9) <= 2
            )
            if desea_dormir:
                accion_idx = self.ACCIONES_MAP["sleep"]
            else:
                accion_idx = self.ACCIONES_MAP["noop"]

        # ---------------------------------------------------------------------
        # EJECUCION EN CRAFTER
        # ---------------------------------------------------------------------
        salud_antes = int(player.health)
        comida_antes = int(player.inventory.get("food", 9))
        bebida_antes = int(player.inventory.get("drink", 9))
        energia_antes = int(player.inventory.get("energy", 9))

        obs, reward, done, info = self.env.step(accion_idx)
        self.ultimo_obs = obs
        self.ultimo_info = info
        self.recompensa_acumulada += float(reward)
        self.pasos_actuales += 1
        self.partida_terminada = bool(done)

        salud_despues = int(player.health)
        comida_despues = int(player.inventory.get("food", 9))
        bebida_despues = int(player.inventory.get("drink", 9))
        energia_despues = int(player.inventory.get("energy", 9))

        # Registrar nuevos logros
        for logro, count in info.get("achievements", {}).items():
            if count > 0:
                self.logros_desbloqueados.add(logro)

        # Cálculo de deltas somáticos normalizados al Core (~0-100) a través del contrato oficial
        # En Crafter, max es 9 (~11.1% por unidad). Compensamos la deriva metabólica basal (+0.8) cuando se mantiene estable.
        delta_comida = (comida_despues - comida_antes) * 11.1 + (bebida_despues - bebida_antes) * 5.5 + 0.8
        delta_energia = (energia_despues - energia_antes) * 11.1 + 0.35
        delta_salud = salud_despues - salud_antes

        dano_subsistemas: Dict[str, float] = {}
        if salud_despues <= 0:
            dano_subsistemas = {"core": -100.0, "locomocion": -100.0, "fauces": -100.0, "sensores": -100.0}
        elif delta_salud != 0:
            delta_vital = float(delta_salud * 11.2)
            dano_subsistemas = {
                "core": delta_vital,
                "locomocion": delta_vital * 0.8,
                "fauces": delta_vital * 0.6,
                "sensores": delta_vital * 0.6,
            }

        intoxicacion = (salud_despues == 0 and salud_antes > 0 and self.env._world[player.pos][0] == "lava")

        new_px, new_py = int(player.pos[0]), int(player.pos[1])
        nueva_ubicacion = f"nodo_{new_px}_{new_py}"

        # Catarsis Epistémica si asimiló nutrición con éxito
        verdad_verificada = None
        if delta_comida > 0:
            verdad_verificada = {"sujeto": target, "relacion": V_Relacion.ES_NUTRITIVO}

        return ResultadoEfectoEntorno(
            exito=True,
            comando=comando,
            target=target,
            nueva_ubicacion=nueva_ubicacion,
            delta_alimentacion=delta_comida,
            delta_energia=delta_energia,
            dano_subsistemas=dano_subsistemas,
            intoxicacion_aguda=intoxicacion,
            recurso_agotado=bool(player.inventory.get("wood", 0) == 0),
            objeto_cargado={
                "salud": salud_despues,
                "comida": comida_despues,
                "bebida": bebida_despues,
                "energia": energia_despues,
                "logros": list(self.logros_desbloqueados),
                "muerto": bool(salud_despues <= 0),
                "inventario": info.get("inventory", {}),
            },
            verdad_verificada=verdad_verificada,
        )
