# Resultado del Experimento 001: Diagnóstico Anatómico en Snake (IdA vs. BFS)

**Fecha:** 2026-11-11  
**Mundo:** Snake en Rejilla Determinista en Memoria (21 columnas x 15 filas)  
**Muestra:** N = 50 semillas pareadas (0 a 49)  
**Unidad de análisis:** Episodio (N = 50 pares observados)  
**Registro de datos:** `salidas/001-snake-diagnostico-bfs/episodios_pareados.csv`  

---

## 1. Comprobación de Validez del Entorno

La regla fijada a priori establecía que el simulador debía reproducir la derrota de IdA observada históricamente en E-09 para que el diagnóstico tuviese sentido como explicación de aquel resultado:

| Brazo | Longitud Mediana | Longitud Media (± DT) | Mín / Máx | Pasos Mediana | Episodios Censurados (2000 ticks) |
|---|---|---|---|---|---|
| **IdA (Orgánico)** | **73.0** | 71.84 (± 15.82) | 37 / 103 | 1232.0 | 1 de 50 (2.0 %) |
| **Línea Base BFS** | **68.5** | 71.18 (± 13.85) | 36 / 99 | 1144.0 | 3 de 50 (6.0 %) |
| **Control Aleatorio Legal** | **6.0** | 6.42 (± 1.67) | 3 / 10 | 1663.5 | 0 de 50 (0.0 %) |

### Contraste Pareado
* **IdA frente a BFS:**
  * Balance de partidas: **23 victorias IdA, 23 victorias BFS, 4 empates exactos**
  * Diferencia media pareada: **+0.66** [IC 95 %: -4.50, +5.64]
  * Test de rangos con signo de Wilcoxon (por episodio): $W = 487.5$, $p = 0.562$ (no significativo)
  * Delta de Cliff: $d = +0.04$
* **IdA frente a Aleatorio:**
  * Diferencia media pareada: **+65.42** [IC 95 %: +60.84, +69.98]
  * Test de Wilcoxon: $W = 0.0$, $p < 0.0001$

> [!WARNING]
> **Veredicto: LA COMPROBACIÓN DE VALIDEZ FALLA.**  
> El simulador síncrono en memoria **no reproduce la derrota de E-09**. En condiciones síncronas sin límite de tiempo por latido, IdA y BFS no muestran diferencias estadísticamente detectables (el IC 95 % descarta diferencias medias mayores a unas 5–6 unidades de longitud).  
> *Consecuencia metodológica:* Este experimento **no responde a la pregunta original** («¿por qué perdió IdA en E-09?»). Las métricas que siguen caracterizan el comportamiento de IdA en régimen síncrono, pero no explican aquella derrota histórica en la web.

---

## 2. Análisis de la Hipótesis de Latencia y Limitaciones de E-09

Inicialmente se formuló la hipótesis de que la brecha observada en Playsnake.org se debía a que el ciclo cognitivo de IdA excedía el plazo de tiempo real de los ticks web (120 ms en Worm, 80 ms en Python).

Sin embargo, la **calibración empírica directa** sobre esta máquina debilita de forma decisiva esta explicación:
* **Latencia real del latido de IdA:** Media = **3.16 ms** (máximo = 4.48 ms, DT = 0.41 ms).
* **Latencia de BFS:** Media = **0.50 ms** (máximo = 0.65 ms).
* *Interpretación:* Incluso en su latido más lento, el cálculo interno de IdA consume **menos del 6 % del presupuesto de 80 ms** de Python y menos del 4 % de Worm. La diferencia neta entre IdA y BFS es de apenas ~2.7 ms por tick.

Si en E-09 la línea base BFS también atravesaba el puente de Chromium/Playwright (como documenta `medir_snake.py`), los retrasos de IPC y renderizado afectaban a ambos brazos por igual. Por tanto, **el coste de cálculo interno de IdA no puede explicar por sí solo la brecha histórica de E-09**.

Las causas más plausibles de la discrepancia residen en factores externos de la plataforma web que no forman parte del simulador:
1. **Diferencias de métrica:** En Playsnake.org la puntuación registrada incluía bonificaciones temporales y de velocidad (puntuaciones de 1500–3500 puntos), mientras que aquí se mide longitud lineal estricta.
2. **Buffer de entrada del navegador:** Playsnake procesaba eventos de teclado en tiempo real; discrepancias sutiles en la emisión asíncrona de eventos pueden haber provocado pérdida de teclas o giros descartados.
3. **Lectura asíncrona del DOM:** El scraping de celdas mediante `page.evaluate()` en Chromium introducía jitter no determinista.

---

## 3. Diagnóstico Anatómico en Régimen Síncrono

### Métrica A: Tasa de Oscilación Improductiva ($\tau_{osc}$)
Proporción de giros seguidos de contragiro en $\le 2$ ticks que no reducen la distancia de camino más corto a la manzana:

* **Tasa en IdA:** Mediana = **1.59 %** (Media: 1.55 %, IC 95 % [1.35 %, 1.75 %])
* **Tasa en BFS:** Mediana = **3.54 %** (Media: 3.55 %, IC 95 % [3.34 %, 3.77 %])
* **Contraste pareado (Wilcoxon sobre los 50 pares de episodios):** $W = 10.0$, $p < 0.0001$.
* *Análisis:* BFS presenta una tasa de cambio de sentido significativamente superior debido a su avance ortogonal en escalera en diagonales. IdA no presenta mioclonías motoras en campo abierto.

### Métrica B: Contrafactual de Espacio Libre Residual
Pérdida de área conexa accesible por movimiento ($\delta = (A_{max} - A_{IdA}) / N_{libres}$), comparada contra la acción legal que maximiza el flood-fill conexo ($A_{max}$):

* **Frecuencia de decisiones subóptimas ($\delta > 0$):** Mediana = **0.26 %** de los ticks (Media: 0.28 %, IC 95 % [0.24 %, 0.33 %]). Representa en promedio unos 3.3 ticks por episodio (164 ticks en total sobre 61 648 latidos).
* **Magnitud de la pérdida cuando $\delta > 0$:** Mediana = **18.08 %** del tablero libre (Media: 24.00 %, IC 95 % [20.41 %, 29.30 %]).
* **Asociación temporal con la muerte (comparación contra tasa base):**
  * La tasa global por tick de decisiones con $\delta > 0$ es de **0.261 %**.
  * En una ventana aleatoria cualquiera de 30 ticks, la probabilidad esperable por azar de encontrar al menos un tick con $\delta > 0$ es de solo el **7.55 %** ($1 - (1 - 0.00261)^{30}$).
  * Frente a ese 7.55 % basal, en el **57.1 % de las muertes por auto-encierro (28 de 49 episodios)** se registró al menos un tick con $\delta > 0$ en los 30 ticks previos al colapso.
  * La presencia de decisiones subóptimas de espacio en la ventana terminal es **7.6 veces superior a la tasa base**, confirmando una asociación temporal directa con el desenlace fatal.

### Métrica C: Interferencia de S1 sobre S3 y Origen de $\delta > 0$
1. **Bifurcación contrafactual en agonía:**
   * En 41 de los 50 episodios (**82.0 %**) hubo al menos una discrepancia entre S1 y S3 en la ventana de los 5 ticks previos a la muerte.
   * **Interferencias destructivas confirmadas:** **0 casos (0.0 %)**. En todos los episodios donde se forzó la propuesta de S3 desde el punto de desacuerdo, la serpiente pereció igualmente en $\le 5$ ticks (situación ya terminal).
2. **Origen de las decisiones subóptimas de espacio ($\delta > 0$):**
   * De los 164 ticks con $\delta > 0$ registrados en las 50 semillas:
     * En **101 ticks (61.6 %)**: S1 y S3 coincidían en proponer la misma acción.
     * En **63 ticks (38.4 %)**: fue el propio **S3 quien propuso la acción con pérdida de área** frente a una alternativa distinta de S1.
     * En **0 ticks (0.0 %)**: la pérdida de área se debió a S1 imponiéndose sobre una alternativa de mayor espacio propuesta por S3.
   * *Diagnóstico:* Los datos demuestran con certeza que S1 nunca se impuso a una alternativa mejor de S3. En el 61.6 % de los fallos ambos sistemas convergieron en la misma casilla, y en el 38.4 % restante el fallo provino del horizonte prospectivo de S3.

---

## 4. Comparativa de Causas de Muerte (IdA frente a BFS)

Clasificación exhaustiva de las 50 muertes:

| Causa de Muerte | IdA (Casos) | IdA (%) | BFS (Casos) | BFS (%) | Descripción Mecánica |
|---|---|---|---|---|---|
| **Auto-encierro** | **49** | **98.0 %** | **2** | **4.0 %** | Colisión contra el propio cuerpo al agotarse el espacio conexo |
| **Colisión Perimetral (Muro)** | **0** | **0.0 %** | **45** | **90.0 %** | Impacto contra el borde exterior al no existir salidas legales |
| **Límite de Tiempo (Tope 2000 ticks)** | **1** | **2.0 %** | **3** | **6.0 %** | Episodio censurado por alcanzar el techo de seguridad |
| **Oscilación Fatal (Revisada)** | **0** | **0.0 %** | **0** | **0.0 %** | *(Ver nota abajo)* |
| **Interferencia Destructiva S1** | **0** | **0.0 %** | — | — | Descartada contrafactualmente mediante bifurcación |

> **Nota sobre la revisión de causas de muerte:**  
> En una inspección preliminar, 24 casos fueron etiquetados provisionalmente como «oscilación fatal» debido a que el algoritmo detectó cambios de sentido en los 3 ticks finales. El análisis detallado demostró que correspondían a giros en U forzados por la ausencia de salidas dentro de un bolsillo ya cerrado. Al unificar la taxonomía bajo la regla a priori (colisión contra el cuerpo = auto-encierro), los 49 casos se agrupan en su causa real.

### Mecanismo de saturación en ambos brazos
Ambos agentes colapsan al alcanzar longitudes elevadas ($L \approx 70-80$, ocupando el 25 % del tablero) cuando el espacio libre restante queda fragmentado. La diferencia en el contacto final reside en los reflejos:
* La línea base BFS (heurística voraz de camino más corto que maximiza área por flood-fill si el camino no es seguro) avanza en su dirección inercial cuando las opciones legales se reducen a cero, chocando contra el muro (90 % de sus muertes).
* IdA cuenta con un veto perimetral en S1; al quedarse sin salidas, gira hacia el interior, colisionando contra su propio cuerpo (98 % de sus muertes).

---

## 5. Síntesis Final

1. **Validez externa:** El experimento síncrono no reproduce la brecha de E-09. La hipótesis de que la derrota histórica se debió al coste de cálculo interno queda empíricamente debilitada al medir que IdA consume menos del 6 % del presupuesto de tick. Las diferencias observadas en la web apuntan a factores del entorno de ejecución (buffer de teclado, métrica de puntuación, renderizado del DOM).
2. **Capacidad táctica de IdA:** En condiciones síncronas, IdA y BFS no muestran diferencias detectables en longitud final (media 71.84 frente a 71.18, IC 95 % [-4.50, +5.64], 23 victorias por brazo).
3. **El origen de los auto-encierros:** Las decisiones con pérdida de espacio conexo ocurren con una frecuencia 7.6 veces mayor a la tasa base en los 30 ticks previos al colapso. En el 61.6 % de ellas S1 y S3 coincidían, y en el 38.4 % provinieron del horizonte prospectivo de S3; en ningún caso S1 se impuso a una propuesta mejor de S3.
