# Stack técnico y justificación

Versión 12.0.0 · 7 de noviembre de 2026.

IdA es, ante todo, un proyecto para aprender y practicar ingeniería de software. Este documento recoge cada tecnología, patrón y técnica que **existe en el código**: dónde está, por qué se eligió, qué se aprendió y qué evidencia lo respalda. Cuando una elección no tiene una justificación plenamente coherente con el proyecto, se dice. Resumen en inglés: [`docs/en/STACK_Y_JUSTIFICACION.en.md`](en/STACK_Y_JUSTIFICACION.en.md).

**Autoría:** idea original, diseño, dirección y verificación por el autor; generación de código, pruebas y análisis dirigidos por agentes de IA.

Etiquetas de estado: *activo, efecto medido* · *activo, efecto no medido* · *preparado, no conectado* · *simulado* · *experimental*.

---

## 1. Lenguaje y calidad

### Python 3.11, `typing` y `dataclasses` · Lenguaje
- **Dónde:** todo el repositorio; `@dataclass` en `nivel_1_core/contratos.py` (`Pieza`, `Arquetipo`) y `estado_somatico.py`.
- **Qué es:** clases de datos con tipos declarados, que generan constructor y representación.
- **Por qué aquí:** los contratos entre capas son estructuras de datos; tiparlas hace explícita la frontera.
- **Qué se aprendió:** un `dataclass` puede tener su atributo sombreado por una `property` en una subclase (técnica usada en `fijar_cortisol` para que una manipulación experimental no se pudiera sobrescribir).
- **Evidencia:** `tests_arquitectura/test_funcional_neurobiologia.py::test_manipulacion_h2_fija_el_cortisol_aunque_el_core_lo_reescriba`.
- **Estado:** activo.
- **En producción:** comprobación estática de tipos (`mypy`/`pyright`) en la CI, que aquí no se usa.

### Enumerados como vocabulario cerrado · Lenguaje / diseño
- **Dónde:** `nivel_1_core/vocabulario.py` (`V_Comando`, `V_Relacion`, `V_Modalidad`, `V_Estado`…).
- **Qué es:** un conjunto finito de comandos y relaciones que el core entiende; los mundos traducen sus acciones a ese vocabulario.
- **Por qué aquí:** es lo que permite que el core no conozca ningún mundo.
- **Qué se aprendió:** un vocabulario cerrado hace barato el linter (lo que no está en el vocabulario es sospechoso), pero obliga a los mundos a forzar analogías (en ajedrez, «DEGLUTIR» significa capturar).
- **Evidencia:** `test_linter_pureza.py`; adaptadores de `nivel_3_componentes/mundos/`.
- **Estado:** activo.
- **En producción:** vocabulario versionado con migraciones explícitas.

### `MappingProxyType` para inmutabilidad · Lenguaje
- **Dónde:** `contratos.py`, canal `ei` de `DimensionReactiva`.
- **Qué es:** una vista de solo lectura de un diccionario.
- **Por qué aquí:** el estado inicial de cada latido no debe modificarse durante el latido.
- **Qué se aprendió:** solo protege el primer nivel; los objetos que contiene siguen siendo mutables.
- **Evidencia:** `contratos.py:148-150`.
- **Estado:** activo.
- **En producción:** estructuras inmutables de verdad (`frozen=True` o copias profundas) donde importe.

### `pytest` · Calidad
- **Dónde:** `tests_arquitectura/` y `nivel_3_componentes/mundos/mundo_ajedrez/tests/`.
- **Qué es:** el marco de tests. Se usan parametrización, `tmp_path`, `monkeypatch`, marcas (`network`), `importorskip` y tests que lanzan subprocesos.
- **Por qué aquí:** la arquitectura y la seguridad se defienden con tests, no con documentación.
- **Qué se aprendió:** un test que «se salta» en silencio si falta un fichero (`if ruta.exists()`) no protege nada; se sustituyó por un fixture versionado.
- **Evidencia:** `python -m pytest -q` (salida en `docs/RESULTADOS_Y_VERIFICACION.md`).
- **Estado:** activo.
- **En producción:** cobertura de líneas en la CI y separación entre tests rápidos y lentos.

### Módulo `ast` y plegado de constantes · Análisis estático
- **Dónde:** `tests_arquitectura/test_linter_pureza.py`; también `nivel_2_sistemas/autopoiesis_ast.py`.
- **Qué es:** analizar el árbol sintáctico de Python en lugar del texto. El linter pliega concatenaciones y f-strings para detectar cadenas partidas.
- **Por qué aquí:** es la función de aptitud que mantiene limpio el core.
- **Qué se aprendió:** un linter léxico tiene límites claros; se midieron (14 de 23 trucos detectados) y se complementó con una prueba metamórfica de conducta.
- **Evidencia:** `analisis/resultados/N7_cobertura_linter.csv`; `test_metamorfico_aislamiento.py`.
- **Estado:** activo.
- **En producción:** reglas de `import-linter` o `ruff` para las dependencias entre capas y el linter propio solo para el vocabulario.

### Integración continua · Calidad
- **Dónde:** `.github/workflows/ci.yml`.
- **Qué es:** ejecutar los tests en cada *push* en Ubuntu y Windows con Python 3.11 y 3.12.
- **Por qué aquí:** reproducibilidad real en más de un sistema.
- **Estado:** en marcha; los cuatro trabajos (Ubuntu y Windows, Python 3.11 y 3.12) pasan en el repositorio. En Windows instala con `PYTHONUTF8=1` porque `crafter` solo se publica como sdist.

## 2. Arquitectura y patrones

### Puertos y adaptadores (arquitectura hexagonal) · Arquitectura
- **Dónde:** puertos `ISensorEntorno` e `IActuadorEntorno` (`contratos.py`); adaptadores en `nivel_3_componentes/mundos/*/adaptador_*.py`.
- **Qué es:** el núcleo define interfaces y cada mundo las implementa; el núcleo no depende de ninguna tecnología externa.
- **Por qué aquí:** seis mundos muy distintos (sistema de archivos, rejilla 2D, navegador web, tablero con UCI, un mundo sintético y un tutorial) se conectan con los mismos dos métodos.
- **Qué se aprendió:** el puerto es estable; lo caro de cada mundo no es el adaptador, sino el conocimiento de dominio de sus componentes.
- **Evidencia:** `analisis/resultados/coste_adaptacion.csv`; el ejemplo mínimo usa 73 líneas de adaptador.
- **Estado:** activo.
- **En producción:** el mismo patrón, con contratos documentados y probados por cada adaptador (tests de contrato).

### Inversión de control e inyección de dependencias · Arquitectura
- **Dónde:** `GestorOndaCore.__init__` recibe sensor, actuador, sistemas, árbitro y motores; los runners lo ensamblan.
- **Por qué aquí:** el core no importa nada del nivel 3 y el linter lo comprueba.
- **Qué se aprendió:** inyectar con valores por defecto que conservan la conducta anterior permitió añadir árbitros y modos de ablación sin romper los mundos.
- **Evidencia:** `nivel_1_core/gestor_onda.py:28-66`; regla «no importar nivel 3» en el linter.
- **Estado:** activo.
- **En producción:** un contenedor o una función de ensamblaje única por aplicación.

### Pizarra (*blackboard*) con presupuesto · Patrón
- **Dónde:** `DimensionReactiva` (`ei`, `ev`, `acc`, `ef`) en `contratos.py`.
- **Qué es:** un espacio compartido donde varios sistemas escriben propuestas sin conocerse entre sí; cada escritura consume «amplitud».
- **Por qué aquí:** S1, S2 y S3 compiten sin acoplarse.
- **Qué se aprendió:** la pizarra facilita la telemetría (todo pasa por un sitio), pero hace fácil que un sistema sobrescriba datos de otro: se descubrió con el cortisol (ver lecciones).
- **Evidencia:** `docs/ARQUITECTURA.md` §2.
- **Estado:** activo.

### Pipeline de componentes por estaciones · Patrón
- **Dónde:** `SistemaCognitivoTriunico` en `nivel_2_sistemas/sistema_base.py`; los mundos sustituyen o inyectan componentes en estaciones.
- **Estado:** activo.

### Estrategia intercambiable: árbitros · Patrón
- **Dónde:** `nivel_1_core/arbitros.py` (A0–A7), inyectados en `TribunalMotor`.
- **Qué es:** la regla de decisión es un objeto intercambiable.
- **Por qué aquí:** permite comparar el árbitro por defecto con alternativas simples con los mismos órganos (H1).
- **Evidencia:** `docs/RESULTADOS_TABLAS.md` (H1).
- **Estado:** activo, efecto medido (Crafter).

### Telemetría pasiva y evaluación contrafactual · Observabilidad
- **Dónde:** `TribunalMotor._evaluar_registro_contrafactual`.
- **Qué es:** en cada latido se registra qué habría elegido cada árbitro alternativo, sin afectar a la decisión.
- **Qué se aprendió:** mostró que el árbitro por defecto y «mayor producto arousal × confianza» coinciden en la mayoría de latidos, así que sus resultados no podían diferir mucho (colinealidad).
- **Evidencia:** tablas de acuerdo contrafactual en `docs/RESULTADOS_TABLAS.md`.
- **Estado:** activo.

### Funciones de aptitud arquitectónicas · Arquitectura evolutiva
- **Dónde:** linter AST y prueba metamórfica; tests de seguridad y de licencias.
- **Qué es:** tests automáticos que fallan cuando la arquitectura se degrada.
- **Estado:** activo.

### Contratos versionados · Gobernanza
- **Dónde:** `__version__` en `nivel_1_core` y `nivel_2_sistemas`; reglas en `docs/GOBERNANZA_Y_CONTRATOS.md`.
- **Estado:** activo (las reglas se documentan; no hay un test que compruebe la compatibilidad entre versiones).

### «Generadores centrales de patrones» (CPG) · Metáfora de diseño
- **Dónde:** los componentes de dominio de Snake y Ajedrez se describen como CPG en sus docstrings.
- **Por qué aquí:** *adoptado como metáfora biológica*; técnicamente son componentes con heurísticas de dominio. En un producto real los habría llamado «políticas de dominio».
- **Estado:** nombre, no mecanismo.

## 3. Concurrencia y tiempo

### `asyncio` y `asyncio.wait_for` · Concurrencia
- **Dónde:** `GestorOndaCore.ejecutar_latido` y `sistema_base.py:106`.
- **Qué es:** cada componente se ejecuta con el tiempo que queda del latido; si se agota, la «guillotina» corta y el Tribunal decide con lo que haya.
- **Por qué aquí:** para modelar un presupuesto de decisión por latido.
- **Qué se aprendió (lección principal):** un plazo cooperativo solo corta en los `await`. Un cálculo síncrono (BFS, minimax) no se interrumpe, y un hilo de Python no se puede matar. Por eso se llama «plazo cooperativo» y nunca «tiempo real». La guillotina no se disparó en ningún episodio contado (N5).
- **Evidencia:** `analisis/resultados/N5_mecanismos_conectados.csv`; diseño de H3 en `analisis/preregistro/H3_H9_diseno.md`.
- **Estado:** activo; efecto no medido.
- **En producción:** algoritmos *anytime* o procesos con `terminate()` para tener un plazo real.

### Hilos y ejecutores · Concurrencia
- **Dónde:** `ThreadPoolExecutor` en `adaptador_snake.py` (Playwright síncrono) y `componentes_ajedrez.py` (consulta a Ollama).
- **Por qué aquí:** las librerías síncronas no deben bloquear el bucle de eventos.
- **Estado:** activo.

## 4. Datos

### SQLite en modo WAL · Persistencia
- **Dónde:** `nivel_1_core/persistencia/motor_sqlite_wal.py` (`PRAGMA journal_mode=WAL`).
- **Por qué aquí:** *adoptado para aprender esta tecnología*. Con un solo proceso escritor, en un producto real habría usado SQLite en modo normal o simples ficheros JSON.
- **Qué se aprendió:** se escribe pero nada vuelve a leerlo (`cargar_hacia_activa` no se llama); la herencia real viaja por los JSON de linaje.
- **Estado:** activo solo escritura.

### PostgreSQL con pgvector, Docker y Terraform · Persistencia / infraestructura
- **Dónde:** `nivel_0_demiurgo/` (compose, SQL con índice HNSW, Terraform); `motor_pgvector.py`.
- **Por qué aquí:** *adoptado para aprender estas tecnologías*. El código no tiene driver de PostgreSQL: el «almacén vectorial» funciona siempre en memoria con numpy y, además, nadie escribe en él.
- **Estado:** preparado, no conectado.
- **En producción:** conectar con `psycopg`, migraciones y tests de integración contra un contenedor efímero; o no usar una base vectorial si no hay datos que la justifiquen.

### `numpy` y proyección L2 de 384 dimensiones · Cálculo
- **Dónde:** tensores 6D en todo el core; `MotorPgVectorHNSW.generar_embedding_384d` (proyección determinista con SHA-256 del identificador y normalización L2).
- **Qué se aprendió:** un embedding derivado del hash del nombre hace que la conducta pueda depender del vocabulario; hoy no ocurre porque el almacén está vacío (límite documentado de la prueba metamórfica).
- **Estado:** numpy activo; embedding preparado, sin uso efectivo.

## 5. IA y búsqueda

### Aprendizaje hebbiano de tres factores · Plasticidad
- **Dónde:** `MatrizHebbianaTresFactores` (`plasticidad_td_hebbiana.py`), usada por el S1 genérico.
- **Qué se aprendió:** solo actualiza pesos donde decide el S1 genérico (Bosque); en Crafter y Ajedrez, 0 actualizaciones (N5).
- **Estado:** activo, efecto no medido (H6 pendiente).

### TD(λ) y error de predicción de recompensa · Aprendizaje por refuerzo
- **Dónde:** `MotorTDLambda`; `SistemaCognitivoTriunico.actualizar_plasticidad_td`, llamado en cada latido.
- **Estado:** activo, efecto no medido (H6 pendiente). Un test comprueba que con α = 0 la conducta es idéntica a la referencia.

### Algoritmos evolutivos: arquetipos y linajes · Optimización
- **Dónde:** runners de Crafter y Ajedrez (selección del mejor arquetipo del linaje y variación gaussiana de sus rasgos); en Snake los rasgos de cada generación se sortean alrededor de un centro fijo, sin selección. En los tres, herencia de axiomas en JSON.
- **Qué se aprendió:** en Crafter, la evolución redescubre parámetros que también se pueden fijar a mano, y la herencia de axiomas no mostró efecto (estudio factorial).
- **Estado:** activo; efecto medido (ver resultados de herencia).

### BFS y *flood fill* · Búsqueda
- **Dónde:** `componentes_snake.py` (S3 de Snake), `componentes_crafter.py`, `s3_racional.py`; baseline BFS en `analisis/medir_snake.py`.
- **Qué se aprendió:** un *flood fill* que ignoraba el propio cuerpo de la serpiente dejaba que se encerrara; hay un test que fija la corrección.
- **Estado:** activo.

### Minimax con poda alfa-beta · Búsqueda
- **Dónde:** `RivalBotLocal` en `adaptador_ajedrez.py` (rival local de 1 a 3 ply).
- **Estado:** activo (como rival, no como parte de IdA).

### LLM local asíncrono (Ollama) · IA generativa
- **Dónde:** `CompAjedrezS3` en `componentes_ajedrez.py` (`localhost:11434`, en un hilo, con tiempo límite).
- **Por qué aquí:** probar el LLM como «pensamiento latente» opcional, no como decisor.
- **Estado:** opcional; no medido. El órgano «imaginación LLM» del S3 genérico está **simulado** (no llama a ningún LLM).

### Model Context Protocol (JSON-RPC 2.0) · Integración
- **Dónde:** `servidor_mcp_telemetria.py`; lo usa la demo de `main.py`.
- **Por qué aquí:** *adoptado para aprender el protocolo*. Es un despachador en proceso, sin transporte de red.
- **Estado:** activo solo en la demo.

## 6. Entornos y herramientas

| Tecnología | Dónde | Estado |
|---|---|---|
| Crafter (Hafner, 2021) | `mundo_crafter/` | Activo, mundo principal de medición |
| python-chess, UCI y Stockfish | `mundo_ajedrez/` (GPL-3.0-or-later) | Activo; Stockfish opcional y externo |
| Playwright (Chromium) | `nivel_3_componentes/mundos/mundo_arcade_snake/adaptador_snake.py` | Experimental: depende de un sitio de terceros |
| Tkinter y Pillow | Visor `--gui` de `mundo_crafter_runner.py` | Opcional |
| imageio | GIF de replays de Crafter | Opcional |

## 7. Experimentación y estadística

### Preregistro y particiones de semillas · Método
- **Dónde:** `analisis/preregistro/`; semillas de desarrollo 0–999, test 2000–2999 y reserva 3000–3999 (las cifras públicas usan la reserva 3000–3039, una sola vez).
- **Estado:** activo.

### Diseño pareado, bootstrap, Wilcoxon, Holm-Bonferroni y delta de Cliff · Estadística
- **Dónde:** `analisis/estadistica.py` (usa `scipy.stats`).
- **Qué es:** cada condición se compara en las mismas semillas; intervalo bootstrap de la diferencia media (10 000 remuestreos), test de rangos con signo, corrección por comparaciones múltiples y tamaño de efecto no paramétrico.
- **Estado:** activo.

### Intervalo de Wilson · Estadística
- **Dónde:** `analisis/generar_tablas.py` (puntuación en ajedrez).
- **Estado:** activo.

### Datos ordenados (CSV por episodio) y tablas generadas por script · Reproducibilidad
- **Dónde:** `analisis/resultados/`; `analisis/generar_tablas.py` produce `docs/RESULTADOS_TABLAS.md` con el SHA-256 de cada CSV.
- **Estado:** activo.

### Control del ruido y del RNG · Reproducibilidad
- **Dónde:** `--aislar-ruido`; RNG propio con semilla en el árbitro A4; corrección del orden de un `set()` en el motor de Crafter (`_DeterministicChunkSet`).
- **Estado:** activo.

### Prueba metamórfica · Verificación
- **Dónde:** `tests_arquitectura/test_metamorfico_aislamiento.py`.
- **Estado:** activo.

## 8. Proceso

- **Trabajo con agentes de IA bajo reglas explícitas:** `AGENTS.md`. Se declaran la autoría y los límites.
- **Auditoría propia y retirada de cifras:** fe de erratas en `docs/RESULTADOS_Y_VERIFICACION.md`.
- **Git:** un commit por cambio; etiqueta `n1-codigo-congelado` para el código medido en N1.
- **Documentación verificada contra el código:** matriz N5 y discrepancias registradas.

---

## Habilidades demostradas y su evidencia

| Habilidad | Evidencia |
|---|---|
| Gobernanza arquitectónica automatizada | `tests_arquitectura/test_linter_pureza.py`, `analisis/resultados/N7_cobertura_linter.csv` |
| Verificación de conducta con pruebas metamórficas | `tests_arquitectura/test_metamorfico_aislamiento.py` |
| Diseño de interfaces estables entre capas | `nivel_1_core/contratos.py`, tutorial en `docs/GOBERNANZA_Y_CONTRATOS.md` |
| Seguridad de ejecución con tests | `tests_arquitectura/test_seguridad_ejecucion.py` |
| Separación de licencias comprobada | `tests_arquitectura/test_licencias_y_aislamiento.py`, `NOTICE` |
| Diseño experimental y estadística | `analisis/preregistro/`, `analisis/estadistica.py`, `analisis/generar_tablas.py` |
| Instrumentación y observabilidad | `analisis/n5_mecanismos_conectados.py`, telemetría contrafactual |
| Detección de errores de medición | `analisis/verificar_manipulacion_cortisol.py` y sus CSV antes y después |

## Lecciones aprendidas

1. **Comprobar que la manipulación llega.** En H2, fijar el cortisol al principio de cada latido no bastaba: el propio core lo reescribía antes de decidir. El resultado anterior («sin efecto») se había medido sin la manipulación prevista.
2. **Un confinamiento parcial no es un confinamiento.** El mundo Bosque confinaba los movimientos, pero no las acciones que borran o truncan: un objetivo `../fichero` escapaba del sandbox.
3. **Nada debe fallar en silencio.** El harness terminaba sin error con mundos no implementados, y el ajedrez sustituía Stockfish por el rival local si no arrancaba. Ahora ambos fallan de forma explícita.
4. **La colinealidad oculta diferencias.** Si dos árbitros eligen lo mismo casi siempre, compararlos no puede dar una diferencia grande; la telemetría contrafactual lo hace visible antes de medir.
5. **Los hilos de Python no se pueden matar** y un plazo cooperativo no es tiempo real.
6. **El orden de iteración de un `set()`** puede romper la reproducibilidad.
7. **Una medición con N = 1 no es una medición.** Se retiraron cifras de versiones anteriores basadas en un individuo o en 5 partidas.
8. **Un mecanismo documentado no es un mecanismo conectado.** La memoria vectorial se consultaba, pero nunca se escribía; la base SQLite se escribía, pero nunca se leía.

## Declaración de uso de IA

Idea original, diseño, dirección y verificación por el autor; generación de código, pruebas y análisis dirigidos por agentes de IA.
