# Diseño de las hipótesis H3, H4, H5, H6, H8 y H9 (hoja de ruta)

**Estado: diseño, no ejecutado.** Este texto se extrajo el 7 de noviembre de 2026 del plan interno de evaluación del core. Ninguna de estas hipótesis se ha ejecutado. Cuando se ejecute una, se fechará y congelará aquí su diseño final antes de medir, como se hizo con [`H1_H7_H2.md`](H1_H7_H2.md).

Reglas comunes (las mismas de H1, H7 y H2): semillas separadas (desarrollo 0–999, test 2000–2999, reserva 3000–3999), ruido físico fijado o repeticiones con suelo de ruido declarado, intervalos bootstrap pareados y Wilcoxon con corrección de Holm, y publicación del resultado sea cual sea.

| Id | Hipótesis (falsable) | Qué la refutaría |
| --- | --- | --- |
| H3 | El plazo acotado (guillotina) permite degradación elegante bajo presupuestos de tiempo estrictos | Sin guillotina, o con un órgano único, el rendimiento bajo plazo no es peor |
| H4 | Un linaje que evoluciona se adapta a entornos cambiantes mejor que un controlador fijo | El baseline afinado a mano para un régimen rinde igual en regímenes no vistos |
| H5 | La herencia epigenética (axiomas) transmite información útil cuando esta no puede estar codificada a mano | Un linaje con axiomas verdaderos rinde igual que uno vacío o que uno con axiomas falsos |
| H6 | La plasticidad (TD(λ), Hebb) mejora el rendimiento con órganos genéricos | Con α = 0 el rendimiento es igual |
| H8 | El core es reutilizable: añadir un mundo nuevo no exige tocar los niveles 1 y 2 y cuesta poco | Hay que modificar el core, o el coste de adaptación es comparable a escribir un agente específico |
| H9 (opcional) | El patrón de arbitraje con presupuesto es útil fuera de los juegos (agente con LLM) | Un enrutador simple logra el mismo coste y calidad |

## H6 – Plasticidad

- **Condiciones:** `td_alpha` y `hebb_alpha` ∈ {0; 0,02; 0,08; 0,2}, además de pesos sinápticos fijos en 1,0 con la misma semilla.
- **Mundos:** Bosque (allí deciden los componentes genéricos del nivel 2) y un mundo de juego.
- **Comprobación previa:** con α = 0 la secuencia de acciones debe coincidir con la referencia sin plasticidad (ya existe un test; ampliarlo al Bosque).
- **Medidas:** curva de rendimiento por episodio y evolución de pesos; qué componentes ganan peso.
- **Éxito:** mejora monótona o con óptimo interior, con un IC que excluya cero frente a α = 0.
- **Dato previo (N5, no es resultado de H6):** en Crafter y en ajedrez la matriz hebbiana no actualiza pesos (0 actualizaciones en los episodios contados), porque esos mundos sustituyen el componente genérico de S1. H6 solo tiene sentido allí donde la plasticidad se ejerce.

## H3 – Plazo acotado

- **Condiciones:** `guillotina_ms` ∈ {inf, 120, 60, 30, 15} más órganos pesados forzados (BFS profundo en Snake o Crafter, minimax de 3 ply en ajedrez).
- **Medidas:** puntuación; latencia p50/p95/p99/máx; número de disparos de la guillotina; calidad de decisión frente al caso sin plazo, y número de cálculos huérfanos.
- **Condición técnica necesaria:** en Python los hilos no se pueden matar. Un `timeout` con `asyncio.to_thread` deja el hilo consumiendo CPU (cálculo huérfano). Un plazo real exige:
  1. algoritmos *anytime* que comprueben el reloj (BFS que mire `time.perf_counter()` en cada expansión; minimax con profundización iterativa que devuelva la mejor jugada completada), o
  2. procesos con interrupción real (`multiprocessing` con `terminate()`).
  Hasta que se evalúe con un corte real, H3 se describe como *plazo cooperativo*.
- **Éxito:** menor degradación que un órgano único sin plazo y que un esquema de corte fijo.
- **Dato previo (N5):** la guillotina no se disparó en ninguno de los episodios contados, ni siquiera con el presupuesto de 8 ms que fuerza la demo.

## H4 – Adaptación a entornos cambiantes

- **Comprobación previa de dosis-respuesta:** verificar que los órganos de dominio leen el arquetipo (rasgos). Si no lo leen, la selección no tiene sobre qué actuar.
- **Regímenes previstos:** ajedrez, régimen A = rival pasivo (minimax de 1 ply) y régimen B = rival táctico (minimax de 3 ply). El diseño original también usaba Snake con un simulador local; ese simulador se descartó (decisión D5), así que en Snake H4 no es viable con un coste razonable.
- **Diseño:** ≥ 10 linajes independientes evolucionan en A y se evalúan en B, no visto, con un número fijo de generaciones adicionales.
- **Comparación:** (a) baseline fijo afinado para A, (b) baseline fijo afinado para B, (c) baseline generalista, (d) linaje que se adapta, (e) linaje congelado.
- **Éxito:** (d) supera a (a) y (c) en B y se acerca a (b), con IC pareado por semilla.

## H5 – Herencia con información que no se puede codificar a mano

- **Mundo:** Bosque o el mundo de ejemplo mínimo, con asignaciones aleatorias por linaje (por ejemplo, qué entidades son letales) generadas con semilla y desconocidas para el código.
- **Condiciones:** linaje `vacio`, `real`, `barajado` y `ajeno`.
- **Medidas:** muertes por la causa objetivo, supervivencia y tiempo hasta la primera ingesta letal.
- **Éxito:** `real` supera a `vacio`, y `barajado` y `ajeno` empeoran o no mejoran.

## H8 – Reutilización y coste de adaptación

- **Medidas por mundo:** líneas de código del nivel 3, archivos tocados y modificaciones en los niveles 1 y 2 (objetivo: 0).
- **Mundo nuevo:** el mundo de ejemplo mínimo (`nivel_3_componentes/mundos/mundo_ejemplo_minimo/`) se añadió sin modificar los niveles 1 y 2. Es un primer dato, no la medición de H8: no se registraron horas ni se comparó con un agente específico.
- **Éxito:** coste menor que el de un agente específico y rendimiento comparable a un baseline simple.

## H9 (opcional) – Agente con LLM y presupuesto

- **Idea:** arbitrar entre un camino rápido y barato (reglas, caché, clasificador pequeño) y otro lento y caro (LLM), con presupuesto de coste y latencia; el estado somático se sustituye por consumo de tokens, latencia y saldo.
- **Implementación:** un adaptador de nivel 3, sin tocar el core.
- **Baselines:** siempre LLM, siempre rápido, enrutador por umbral fijo y enrutador aleatorio.
- **Métricas:** éxito de tarea, coste por tarea y latencia p95.
- **Éxito:** mejor frontera coste/calidad que los baselines, con N ≥ 100 tareas e IC.
