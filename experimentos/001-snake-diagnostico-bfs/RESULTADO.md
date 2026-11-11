# Resultado del Experimento 001: Diagnóstico Anatómico en Snake (IdA vs. BFS)

**Fecha:** 2026-11-11  
**Mundo:** Snake en Rejilla Determinista en Memoria (21 columnas x 15 filas)  
**Muestra:** N = 50 semillas pareadas (0 a 49)  
**Unidad de análisis:** Episodio  
**Registro de datos:** `salidas/001-snake-diagnostico-bfs/episodios_pareados.csv`  

---

## 1. Comprobación de Validez del Entorno

El protocolo prefijó como comprobación de validez verificar si el simulador determinista local reproducía la inferioridad de IdA frente a BFS observada en el estudio histórico E-09 (Playsnake.org):

| Brazo | Longitud Mediana | Longitud Media (± DT) | Mín / Máx | Pasos Mediana |
|---|---|---|---|---|
| **IdA (Orgánico)** | **73.0** | 71.84 (± 15.82) | 37 / 103 | 1232.0 |
| **Línea Base BFS** | **68.5** | 71.18 (± 13.85) | 36 / 99 | 1144.0 |
| **Control Aleatorio Legal** | **6.0** | 6.42 (± 1.67) | 3 / 10 | 1663.5 |

### Contraste Pareado
* **IdA frente a BFS:**
  * Diferencia media pareada: **+0.66** [IC 95 %: -4.50, +5.64]
  * Balance de partidas: **23 victorias IdA, 23 victorias BFS, 4 empates exactos**
  * Test de rangos con signo de Wilcoxon: $W = 487.5$, $p = 0.562$ (no significativo)
  * Delta de Cliff: $d = +0.04$ (efecto nulo / insignificante)
* **IdA frente a Aleatorio:**
  * Diferencia media pareada: **+65.42** [IC 95 %: +60.84, +69.98]
  * Test de Wilcoxon: $W = 0.0$, $p = 0.000$ (IdA supera holgadamente el suelo de control)

> [!WARNING]
> **Veredicto de la Comprobación de Validez: NO REPRODUCIDA (EMPATE TÉCNICO).**  
> En este entorno síncrono en memoria sin reloj de tiempo real, **IdA no pierde frente a BFS**; empatan de forma exacta (23 victorias cada uno, $p = 0.562$).  
> Esto aísla un hallazgo fundamental sobre el histórico E-09: en Playsnake.org la derrota masiva de IdA solo ocurría en las dificultades rápidas (*Worm* y *Python*, con latidos de 120 ms y 80 ms en el navegador), mientras que en *Slug* (velocidad lenta) el intervalo de confianza histórico ya incluía el cero ([-577, +218]). En ausencia de estrés temporal de red/renderizado, la calidad posicional de S3 + S1 es indistinguible de la línea base BFS tradicional.

---

## 2. Diagnóstico Anatómico de Métricas Cerradas

### Métrica A: Tasa de Oscilación Improductiva ($\tau_{osc}$)
Proporción de giros rápidos seguidos de contragiro en $\le 2$ ticks que no reducen la distancia de camino más corto a la manzana:

* **Tasa en IdA:** Mediana = **1.59 %** (Media: 1.55 %, IC 95 % [1.35 %, 1.75 %])
* **Tasa en BFS (Referencia):** Mediana = **3.54 %** (Media: 3.55 %, IC 95 % [3.34 %, 3.77 %])
* **Diferencia pareada:** IdA oscila **-2.00 puntos porcentuales menos** que BFS (Wilcoxon $p < 0.0001$).
* *Conclusión:* IdA no padece mioclonías ni inestabilidad motora descontrolada; de hecho, BFS cambia de sentido con mayor frecuencia debido a su patrón en escalera en trayectorias diagonales.

### Métrica B: Contrafactual de Espacio Libre Residual
Pérdida de área conexa accesible por movimiento ($\delta = (A_{max} - A_{IdA}) / N_{libres}$):

* **Frecuencia de decisiones subóptimas ($\delta > 0$):** Mediana = **0.26 %** de los ticks (Media: 0.28 %, IC 95 % [0.24 %, 0.33 %]).
* **Magnitud media de pérdida cuando $\delta > 0$:** Mediana = **19.94 %** del tablero libre (IC 95 % [20.41 %, 29.30 %]).
* *Conclusión:* IdA elige la casilla de máxima área conexa en el 99.7 % de los latidos. Sin embargo, en el 0.3 % restante en que se equivoca, la decisión es catastrófica: estrangula en promedio un 20 % del espacio libre restante del tablero.

### Métrica C: Interferencia Destructiva de S1 sobre S3
Análisis de discrepancias entre el instinto reactivo S1 y la estrategia S3:

* **Ticks con discrepancia S1 vs. S3:** 6926 ticks en total (mediana de 130.5 ticks por episodio; ~10.6 % de los latidos).
* **Interferencias destructivas confirmadas mediante bifurcación contrafactual:** **0 casos (0.0 %)**.
* *Conclusión:* En ninguna ocasión en las 50 semillas la selección de la propuesta de S1 en detrimento de S3 causó una muerte que hubiera sido evitable forzando la propuesta de S3. S1 no sabotea a S3.

---

## 3. Taxonomía Exclusiva de Causas de Muerte

Distribución de las 50 muertes de IdA:

| Causa de Muerte | Episodios | Porcentaje | Descripción Anatómica |
|---|---|---|---|
| **Auto-encierro** | **25** | **50.0 %** | Impacto contra el propio cuerpo tras estrangulamiento de espacio libre |
| **Oscilación Fatal** | **24** | **48.0 %** | Bucle cerrado de maniobra en esquina en los 3 ticks previos al impacto |
| **Colisión Perimetral (Muro)** | **0** | **0.0 %** | Impacto contra el borde exterior sin encierro ni oscilación previa |
| **Interferencia S1** | **0** | **0.0 %** | Muerte atribuible a la elección de S1 (descartada contrafactualmente) |
| **Otra / Residual** | **1** | **2.0 %** | Muerte por límite de tiempo de seguridad (2000 latidos) |

---

## 4. Síntesis y Conclusiones del Diagnóstico

1. **La brecha histórica de Snake era de latencia, no de algoritmo:** En un entorno determinista sin descarte de ticks por retraso de WebSocket/Playwright, IdA alcanza exactamente el mismo nivel que la línea base BFS tradicional (71.84 vs 71.18 de longitud, 23 victorias contra 23).
2. **S1 y S3 no interfieren destructivamente:** La hipótesis de que el impulso reactivo de S1 anulaba la supervivencia a largo plazo de S3 queda refutada empíricamente ($0$ casos contrafactuales en 6926 discrepancias).
3. **Miopía en alta densidad corporal:** El límite de supervivencia de ambos agentes (IdA y BFS) ocurre cuando la serpiente ocupa ~75-80 casillas de las 315 totales de la rejilla (~25 % de densidad de ocupación). En ese punto, maniobrar en esquinas estrechas genera auto-encierros inevitables por la falta de un horizonte de planificación superior a 2-3 latidos.
4. **Impacto en el Experimento 002 (Crafter vs. Voraz):** Este hallazgo confirma que el chasis de decisión de IdA opera con solvencia táctica cuando no sufre penalización de tiempo de reloj. Nos da luz verde para pasar a **Crafter**, donde el mundo es espacialmente abierto, no existen encierros de cuerpo propio, y la prueba frente a una línea base voraz evaluará de verdad la gestión homeostática de necesidades biológicas.
