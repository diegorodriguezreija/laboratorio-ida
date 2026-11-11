# Experimento 001: Diagnóstico Anatómico en Snake (IdA vs. BFS)

## 1. Pregunta Experimental
¿Qué mecanismo intrínseco del chasis bioinspirado de IdA explica su inferioridad de rendimiento frente al agente tradicional BFS en Snake: el auto-encierro por pérdida de espacio libre residual, la interferencia destructiva de S1 sobre S3, o la inestabilidad por bucles de oscilación?

## 2. Brazos del Experimento
* **Brazo A (IdA Orgánico):** Organismo completo con niveles 1 y 2 (CPG reactivo S1, evaluación prospectiva S3, Tribunal Motor A0 modulado por estado somático).
* **Brazo B (Línea Base Tradicional BFS):** Agente determinista clásico (`lineas-base/snake_bfs.py`) que selecciona el primer paso del camino más corto a la manzana si deja espacio suficiente; si no, maximiza el área libre conexa por flood-fill.
* **Brazo C (Suelo de Referencia / Aleatorio Legal):** Agente que selecciona uniformemente al azar entre los movimientos que no colisionan en el tick inmediato, utilizado para calibrar la escala inferior.

## 3. Entorno y Reproducibilidad
* **Mundo:** Rejilla determinista de Snake en memoria de 21 columnas por 15 filas (mismas dimensiones y reglas que Playsnake.org, sin dependencia de red ni latencia externa).
* **Semillas pareadas:** 50 semillas fijas (0 a 49). Cada semilla determina de forma unívoca la celda inicial de la serpiente y la secuencia pseudoaleatoria de aparición de manzanas en celdas desocupadas.
* **Límite de tiempo:** Máximo 2000 latidos por episodio para prevenir bucles cerrados infinitos.
* **Generadores de números aleatorios:** Reinicializados con la semilla específica al inicio de cada episodio.

## 4. Métricas de Diagnóstico (Definidas a Priori)

### Métrica A: Tasa de oscilación improductiva ($\tau_{osc}$)
* **Definición:** Proporción de ticks donde el agente ejecuta un giro seguido de otro en sentido contrario en $\le 2$ ticks (reversión ortogonal rápida) que **no reduce** la distancia de camino más corto hacia la manzana.
* **Referencia:** Se calcula tanto para IdA como para BFS; BFS sirve como cota de referencia para distinguir oscilaciones de patrones legítimos en escalera.

### Métrica B: Contrafactual de espacio libre residual ($\Delta_{area}$ y $\delta$)
* **Definición:** En cada estado $s_t$ alcanzado por IdA, se calcula el área conexa libre resultante de la acción elegida por IdA ($A_{IdA}$) frente al área máxima que dejaba la mejor acción legal disponible ($A_{max}$):
  $$\Delta_{area}(s_t) = A_{max}(s_t) - A_{IdA}(s_t)$$
  $$\delta(s_t) = \frac{A_{max}(s_t) - A_{IdA}(s_t)}{N_{libres}(s_t)}$$
* **Convención de flood-fill:** En todos los cálculos se asume que la cola se libera al avanzar un tick, salvo si en ese instante se consume una manzana.
* **Reporte por episodio:**
  1. Frecuencia de ticks con $\delta > 0$ (tasa de decisiones subóptimas de espacio).
  2. Magnitud media de $\delta$ condicionada a $\delta > 0$.

### Métrica C: Interferencia destructiva de S1 sobre S3 ($\tau_{interf}$)
* **Denominador:** Ticks donde las propuestas de S1 y S3 discrepan ($N_{discrepancia}$).
* **Comprobación contrafactual:** Si el árbitro selecciona la acción de S1 y la serpiente muere en $\le 5$ ticks, se bifurca el estado $s_t$ en el simulador determinista forzando la acción que propuso S3:
  * Si forzando S3 la serpiente sobrevive $\ge 6$ ticks $\implies$ interferencia destructiva confirmada.
  * Si forzando S3 la muerte también ocurre en $\le 5$ ticks $\implies$ muerte inevitable (no imputable a S1).

### Taxonomía Exclusiva de Causa de Muerte
Cada muerte de IdA en los 50 episodios se asigna a exactamente una categoría bajo la siguiente precedencia:
1. **Interferencia destructiva S1:** Confirmada mediante la prueba contrafactual de la Métrica C.
2. **Auto-encierro:** Presencia de $\delta > 0$ en los 3 ticks inmediatamente previos al choque contra el propio cuerpo.
3. **Oscilación fatal:** Reversión improductiva en los 3 ticks previos al impacto.
4. **Colisión perimetral / Muro:** Choque contra el borde exterior sin pérdida previa de área ni oscilación.
5. **Otra:** Cualquier evento residual no clasificado en las categorías anteriores.

## 5. Unidad de Análisis y Contraste Estadístico
* La **unidad de análisis formal es el episodio** (N = 50 observaciones pareadas).
* Las métricas tick a tick se agregan a nivel de episodio (medias o tasas por episodio).
* Contraste pareado mediante el test de rangos con signo de Wilcoxon, delta de Cliff y remuestreo bootstrap (10 000 iteraciones, IC 95 %).

## 6. Comprobaciones de Validez e Hipótesis
1. **Comprobación de validez del simulador:** La longitud final de BFS debe ser significativamente superior a la de IdA ($p < 0.05$, unilateral), confirmando que el entorno local reproduce fielmente la brecha observada en el histórico E-09.
2. **Hipótesis H-B (Auto-encierro):** La mediana de la frecuencia de $\delta > 0$ en IdA es superior a 0.05 ($p < 0.05$, unilateral).
3. **Hipótesis H-C (Interferencia S1):** La tasa de interferencia destructiva confirmada en episodios con discrepancia es significativamente distinta de cero.
