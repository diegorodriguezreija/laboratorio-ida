import math
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, List, Dict, Any, Optional, Set
import numpy as np
try:
    from playwright.sync_api import sync_playwright, Browser, Page, Playwright
except ImportError:
    sync_playwright = None
    Browser = Any
    Page = Any
    Playwright = Any

from nivel_1_core.vocabulario import V_Comando, V_Relacion
from nivel_1_core.contratos import (
    Pieza,
    ResultadoEfectoEntorno,
    ISensorEntorno,
    IActuadorEntorno,
)


class AdaptadorSnakeWeb(ISensorEntorno, IActuadorEntorno):
    """
    Adaptador Sensoriomotor de Membrana para Playsnake.org.
    Implementa ISensorEntorno e IActuadorEntorno utilizando Playwright en hilo aislado (Worker).
    Garantiza compatibilidad total con el bucle asyncio del Core de IdA v12.
    """

    ANCHO_TABLERO: int = 21
    ALTO_TABLERO: int = 15
    URL_SNAKE: str = "https://playsnake.org/"

    def __init__(self, headless: bool = True, nivel_dificultad: int = 0):
        self.headless = headless
        self.nivel_dificultad = nivel_dificultad
        self._executor = ThreadPoolExecutor(max_workers=1)

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None

        self.cabeza_actual: Tuple[int, int] = (10, 2)
        self.ultima_cabeza_viva: Tuple[int, int] = (10, 2)
        self.cuerpo_actual: List[Tuple[int, int]] = [(10, 2), (10, 1), (10, 0)]
        self.comida_actual: Optional[Tuple[int, int]] = None
        self.estado_juego_web: str = "intro"
        self.puntuacion_actual: int = 0
        self._ultimo_score_premiado: int = 0
        self.ultima_direccion: str = "SUR"
        self._ultimo_hash_celdas: str = ""
        self._conectado: bool = False

    def conectar(self) -> None:
        """Inicializa Playwright en el worker thread."""
        if sync_playwright is None:
            raise ImportError("Falta Playwright. Instálalo con: pip install -e \".[snake]\" y después: python -m playwright install chromium")
        if self._conectado:
            return

        def _init():
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-background-timer-throttling", "--disable-renderer-backgrounding"],
            )
            self._page = self._browser.new_page()
            self._page.goto(self.URL_SNAKE, timeout=20000)
            time.sleep(1.0)
            self._despejar_consentimiento_si_existe_sync()
            self._iniciar_partida_web_sync()
            return True

        self._executor.submit(_init).result()
        self._conectado = True

    def desconectar(self) -> None:
        """Cierra el navegador y detiene Playwright limpiamente sin fugas de pipes."""
        if not self._conectado:
            return

        def _cleanup():
            if self._page:
                try:
                    self._page.close()
                except Exception:
                    pass
                self._page = None
            if self._browser:
                try:
                    self._browser.close()
                except Exception:
                    pass
                self._browser = None
            if self._playwright:
                try:
                    self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None

        try:
            self._executor.submit(_cleanup).result(timeout=6.0)
        except Exception:
            pass
        finally:
            try:
                self._executor.shutdown(wait=True)
            except Exception:
                pass
        self._conectado = False

    def iniciar_partida_web(self) -> None:
        """Inicia o reinicia la partida ejecutando de forma segura en el worker thread."""
        if not self._conectado:
            return
        try:
            self._executor.submit(self._iniciar_partida_web_sync).result(timeout=10.0)
        except Exception:
            pass

    def _despejar_consentimiento_si_existe_sync(self) -> bool:
        if not self._page:
            return False
        try:
            consent_btn = self._page.query_selector(".fc-cta-consent")
            if consent_btn and consent_btn.is_visible():
                consent_btn.click()
                time.sleep(0.5)
                return True
        except Exception:
            pass
        return False

    def _iniciar_partida_web_sync(self) -> None:
        """Reinicia la partida de forma 100% limpia navegando de nuevo o recargando para evitar pausas/grises."""
        if not self._page:
            return
        try:
            # 1. Navegar de forma limpia a la URL para purgar estado de juego anterior, pausas y DOM viejo
            self._page.goto(self.URL_SNAKE, timeout=15000)
            time.sleep(0.3)
            self._despejar_consentimiento_si_existe_sync()

            # 2. Localizar y pulsar el selector de dificultad deseado
            selector = f".game nav .level[data-level='{self.nivel_dificultad}']"
            self._page.wait_for_selector(selector, timeout=5000)
            btn = self._page.query_selector(selector)
            if btn and btn.is_visible():
                btn.click()
                time.sleep(1.2)
            else:
                # Fallback de click en tablero
                board = self._page.query_selector(".game .board")
                if board:
                    board.click()
                    time.sleep(0.3)
                    btn_retry = self._page.query_selector(selector)
                    if btn_retry:
                        btn_retry.click()
                        time.sleep(1.2)

            self.estado_juego_web = "playing"
            self.cabeza_actual = (10, 2)
            self.cuerpo_actual = [(10, 2), (10, 1), (10, 0)]
            self.puntuacion_actual = 0
            self._ultimo_score_premiado = 0
            self.ultima_direccion = "SUR"
            self._ultimo_hash_celdas = ""
        except Exception as e:
            pass

    # =========================================================================
    # PUERTO SENSORIAL (ISensorEntorno)
    # =========================================================================
    def percibir_mundo(self) -> Tuple[str, List[Pieza], List[str]]:
        if not self._conectado:
            self.conectar()

        prev_hash = self._ultimo_hash_celdas

        def _eval():
            return self._page.evaluate("""async (prevHash) => {
                const readDom = () => {
                    const game = document.querySelector('.game');
                    const cells = Array.from(document.querySelectorAll('.game .board .cell'));
                    const snakeCells = [];
                    let foodCell = null;
                    cells.forEach((cell, idx) => {
                        const x = idx % 21;
                        const y = Math.floor(idx / 21);
                        if (cell.classList.contains('snake')) {
                            snakeCells.push({ x, y });
                        }
                        if (cell.classList.contains('food')) {
                            foodCell = { x, y };
                        }
                    });
                    const scoreEl = document.querySelector('.info .score');
                    const score = scoreEl ? parseInt(scoreEl.textContent, 10) || 0 : 0;
                    const consentRoot = document.querySelector('.fc-consent-root');
                    const isConsent = consentRoot && consentRoot.offsetParent !== null;
                    const gameClass = game ? game.className : '';
                    const hash = snakeCells.map(c => c.x + ',' + c.y).join(';');
                    return { gameClass, snakeCells, foodCell, score, isConsent, hash };
                };

                let state = readDom();
                if (prevHash && state.gameClass.includes('playing') && state.hash === prevHash) {
                    const t0 = performance.now();
                    while (performance.now() - t0 < 210) {
                        await new Promise(r => setTimeout(r, 8));
                        state = readDom();
                        if (!state.gameClass.includes('playing') || state.hash !== prevHash) {
                            break;
                        }
                    }
                }
                return state;
            }""", prev_hash)

        estado_dom = self._executor.submit(_eval).result()
        self._ultimo_hash_celdas = str(estado_dom.get("hash", ""))

        game_class = str(estado_dom.get("gameClass", ""))
        score_dom = int(estado_dom.get("score", 0))

        # Re-resolver ubicacion de cabeza y cuerpo manteniendo orden estricto [cabeza, ..., cola]
        celdas_snake = [(c["x"], c["y"]) for c in estado_dom.get("snakeCells", [])]

        # DETECCION INFALIBLE DE FIN DE PARTIDA / MUERTE:
        # 1. Clase explicita en el DOM ('ended', 'game-over')
        # 2. Reseteo de puntuacion de golpe mientras ya se habian obtenido puntos
        # 3. La serpiente vuelve a tener su tamano inicial (3 celdas) despues de haber crecido
        ha_reseteado_score = self.puntuacion_actual > 0 and score_dom == 0
        ha_reseteado_cuerpo = len(self.cuerpo_actual) > 5 and len(celdas_snake) <= 3

        if "ended" in game_class or "over" in game_class or ha_reseteado_score or ha_reseteado_cuerpo:
            self.estado_juego_web = "ended"
        elif "playing" in game_class:
            self.estado_juego_web = "playing"
        elif "countdown" in game_class:
            self.estado_juego_web = "countdown"
        else:
            self.estado_juego_web = "intro"

        self.puntuacion_actual = score_dom
        if celdas_snake:
            set_actual = set(celdas_snake)
            set_previo = set(self.cuerpo_actual)
            nuevas = [c for c in celdas_snake if c not in set_previo]
            if nuevas:
                pendientes = list(nuevas)
                ref = self.cabeza_actual
                cadena_nueva: List[Tuple[int, int]] = []
                while pendientes:
                    sig = min(pendientes, key=lambda c: abs(c[0] - ref[0]) + abs(c[1] - ref[1]))
                    pendientes.remove(sig)
                    cadena_nueva.append(sig)
                    ref = sig
                nuevas_head_first = list(reversed(cadena_nueva))
                sobrevivientes = [c for c in self.cuerpo_actual if c in set_actual]
                self.cuerpo_actual = nuevas_head_first + sobrevivientes
                self.cabeza_actual = self.cuerpo_actual[0]
            elif set_actual == {(10, 2), (10, 1), (10, 0)}:
                self.cuerpo_actual = [(10, 2), (10, 1), (10, 0)]
                self.cabeza_actual = (10, 2)
            elif self.cabeza_actual not in set_actual:
                self.cuerpo_actual = list(celdas_snake)
                self.cabeza_actual = self.cuerpo_actual[0]
            if self.estado_juego_web == "playing":
                self.ultima_cabeza_viva = self.cabeza_actual

        if estado_dom.get("foodCell"):
            fc = estado_dom["foodCell"]
            self.comida_actual = (fc["x"], fc["y"])
        else:
            self.comida_actual = None

        hx, hy = self.cabeza_actual
        id_nodo_actual = f"nodo_{hx}_{hy}"

        # Nodos adyacentes cardinales libres
        nodos_adyacentes: List[str] = []
        set_cuerpo: Set[Tuple[int, int]] = set(self.cuerpo_actual)

        movimientos_cardinales = [
            ("NORTE", hx, hy - 1),
            ("SUR", hx, hy + 1),
            ("ESTE", hx + 1, hy),
            ("OESTE", hx - 1, hy),
        ]

        for card, nx, ny in movimientos_cardinales:
            if 0 <= nx < self.ANCHO_TABLERO and 0 <= ny < self.ALTO_TABLERO:
                if (nx, ny) not in set_cuerpo or (nx, ny) == self.cuerpo_actual[-1]:
                    nodos_adyacentes.append(f"nodo_{nx}_{ny}")

        if self.estado_juego_web in ("ended", "intro"):
            nodos_adyacentes.append("INICIAR_PARTIDA")

        # Generar Piezas de Escena formalmente tipadas con Tensor Sensorial 6D
        piezas_escena: List[Pieza] = []

        if self.comida_actual:
            fx, fy = self.comida_actual
            dx = float(fx - hx)
            dy = float(fy - hy)
            dist_manhattan = abs(fx - hx) + abs(fy - hy)
            norm_euc = math.hypot(dx, dy) or 1.0

            prox = float(max(0.0, 1.0 - (dist_manhattan / 36.0)))
            tensor_alimento = np.array([0.9, prox, 0.95, 0.05, 0.3, 0.9], dtype=np.float64)

            p_alimento = Pieza(
                id=f"alimento_{fx}_{fy}",
                tipo_componente="Alimento",
                arousal=float(min(1.0, 0.4 + 0.6 * prox)),
                trust=0.98,
                tensor_sensorial=tensor_alimento,
                product={
                    "sujeto": f"alimento_{fx}_{fy}",
                    "target_nodo": f"nodo_{fx}_{fy}",
                    "x": fx,
                    "y": fy,
                    "relacion": V_Relacion.ES_NUTRITIVO,
                    "distancia_manhattan": dist_manhattan,
                    "vector_luminico": (dx / norm_euc, dy / norm_euc),
                },
                inputs=["Sensor_Snake_Web"],
            )
            piezas_escena.append(p_alimento)

        # Amenazas inmediatas (Paredes o Cuerpo adyacente)
        for card, nx, ny in movimientos_cardinales:
            es_pared = not (0 <= nx < self.ANCHO_TABLERO and 0 <= ny < self.ALTO_TABLERO)
            es_cuerpo = (nx, ny) in set_cuerpo and (nx, ny) != self.cuerpo_actual[-1]

            if es_pared or es_cuerpo:
                tensor_amenaza = np.array([0.9, 1.0, 0.0, 0.99, 0.2, 0.9], dtype=np.float64)
                p_letal = Pieza(
                    id=f"obstaculo_{nx}_{ny}",
                    tipo_componente="Obstaculo_Letal",
                    arousal=0.95,
                    trust=0.99,
                    tensor_sensorial=tensor_amenaza,
                    product={
                        "sujeto": f"obstaculo_{nx}_{ny}",
                        "target_nodo": f"nodo_{nx}_{ny}",
                        "x": nx,
                        "y": ny,
                        "cardinal_bloqueado": card,
                        "relacion": V_Relacion.ES_LETAL,
                    },
                    inputs=["Sensor_Snake_Web"],
                )
                piezas_escena.append(p_letal)

        p_estado = Pieza(
            id="estado_juego_snake",
            tipo_componente="Estado_Entorno",
            arousal=0.7 if self.estado_juego_web == "ended" else 0.3,
            trust=0.99,
            product={
                "estado_web": self.estado_juego_web,
                "score": self.puntuacion_actual,
                "longitud_serpiente": len(self.cuerpo_actual),
                "posicion_cola": self.cuerpo_actual[-1] if self.cuerpo_actual else None,
                "cuerpo_coords": list(self.cuerpo_actual),
                "is_consent": bool(estado_dom.get("isConsent")),
            },
            inputs=["Sensor_Snake_Web"],
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
        if not self._conectado:
            return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        def _act():
            # 1. Reinicio explicito o si ya termino antes de actuar
            if target == "INICIAR_PARTIDA":
                self._iniciar_partida_web_sync()
                return "INICIADO"
            if self.estado_juego_web == "ended":
                return "ENDED"
            if self.estado_juego_web == "intro":
                self._iniciar_partida_web_sync()
                return "INICIADO"

            # 2. Locomocion
            if comando in (V_Comando.MOVER, V_Comando.ACECHAR):
                tecla = None
                hx, hy = self.cabeza_actual

                if target == "NORTE" or target.endswith("_NORTE"):
                    tecla = "ArrowUp"
                    self.ultima_direccion = "NORTE"
                elif target == "SUR" or target.endswith("_SUR"):
                    tecla = "ArrowDown"
                    self.ultima_direccion = "SUR"
                elif target == "ESTE" or target.endswith("_ESTE"):
                    tecla = "ArrowRight"
                    self.ultima_direccion = "ESTE"
                elif target == "OESTE" or target.endswith("_OESTE"):
                    tecla = "ArrowLeft"
                    self.ultima_direccion = "OESTE"
                elif target.startswith("nodo_"):
                    partes = target.replace("nodo_", "").split("_")
                    if len(partes) == 2 and partes[0].lstrip("-").isdigit() and partes[1].lstrip("-").isdigit():
                        tx, ty = int(partes[0]), int(partes[1])
                        dx = tx - hx
                        dy = ty - hy
                        if dy < 0:
                            tecla = "ArrowUp"
                            self.ultima_direccion = "NORTE"
                        elif dy > 0:
                            tecla = "ArrowDown"
                            self.ultima_direccion = "SUR"
                        elif dx > 0:
                            tecla = "ArrowRight"
                            self.ultima_direccion = "ESTE"
                        elif dx < 0:
                            tecla = "ArrowLeft"
                            self.ultima_direccion = "OESTE"

                if tecla and self._page:
                    try:
                        self._page.keyboard.press(tecla)
                    except Exception:
                        pass

            # 3. Censura
            if comando == V_Comando.CENSURAR:
                self._despejar_consentimiento_si_existe_sync()

            # 4. Check ended
            try:
                game_el = self._page.query_selector(".game")
                clase = game_el.get_attribute("class") if game_el else ""
                if "ended" in (clase or ""):
                    self.estado_juego_web = "ended"
                    return "ENDED"
            except Exception:
                pass
            return "OK"

        res_str = self._executor.submit(_act).result()

        if res_str == "ENDED":
            return ResultadoEfectoEntorno(
                exito=False,
                comando=comando,
                target=target,
                dano_subsistemas={"core": -100.0, "locomocion": -100.0, "sensores": -50.0},
                delta_alimentacion=-10.0,
                delta_energia=-20.0,
            )

        delta_ali = 0.0
        delta_ene = -0.02
        recompensa = 0.0
        comida_target = f"nodo_{self.comida_actual[0]}_{self.comida_actual[1]}" if self.comida_actual else ""

        if self.puntuacion_actual > self._ultimo_score_premiado:
            self._ultimo_score_premiado = self.puntuacion_actual
            delta_ali = 25.0
            delta_ene = 15.0
            recompensa = 0.85
        elif target == comida_target and comida_target:
            delta_ali = 10.0
            delta_ene = 5.0
            recompensa = 0.40
        elif comando == V_Comando.DEGLUTIR and self.comida_actual and self.cabeza_actual == self.comida_actual:
            delta_ali = 30.0
            delta_ene = 15.0
            recompensa = 0.85

        return ResultadoEfectoEntorno(
            exito=True,
            comando=comando,
            target=target,
            nueva_ubicacion=f"nodo_{self.cabeza_actual[0]}_{self.cabeza_actual[1]}",
            delta_alimentacion=delta_ali,
            delta_energia=delta_ene,
        )


AdaptadorArcadeSnake = AdaptadorSnakeWeb
