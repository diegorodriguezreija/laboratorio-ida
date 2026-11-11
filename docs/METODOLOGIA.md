# Metodología Experimental del Laboratorio IdA

El Laboratorio IdA tiene un propósito específico: **verificar empíricamente si el diseño bioinspirado de IdA supera a líneas base tradicionales en cada mundo, en qué situaciones, cuánto, y dónde no**.

Para que las conclusiones sean científicamente válidas y reproducibles, toda la experimentación sigue un marco metodológico estricto.

---

## 1. Principios Metodológicos Fundamentales

### 1.1. Preregistro Obligatorio
Antes de lanzar una simulación, cada experimento debe documentar en su ficha `PREGUNTA.md`:
- La hipótesis concreta.
- Las dos variantes o brazos a contrastar.
- El mundo y la lista exacta de semillas.
- La métrica cuantitativa primaria.
- El **umbral de veredicto fijado a priori**.

> **Regla de oro:** Si los datos no alcanzan el umbral preestablecido, el veredicto es *«no mejora»* o *«empeora»*. Está terminantemente prohibido ajustar los umbrales o cambiar la métrica a posteriori para maquillar un resultado negativo.

### 1.2. Partición Sagrada de Semillas
Para evitar el sobreajuste (overfitting) a mundos procedurales, las semillas se particionan en rangos estrictos:

| Rango | Uso | Regla de acceso |
|---|---|---|
| **0 – 999** | **Desarrollo** | Calibración inicial, depuración y pruebas de mecanismo. |
| **2000 – 2999** | **Diagnóstico / Test** | Pruebas exploratorias controladas (utilizadas en fase v12/v14). |
| **3000 – 3999** | **Reserva (Held-out)** | Evaluación final oficial de hipótesis. Se abre **una sola vez**. (Las semillas 3000–3039 ya fueron consumidas en N1/H1/H7/H2). |
| **4000 – 4039** | **Reserva Intacta** | Destinada a futuras evaluaciones definitivas en el laboratorio. |

### 1.3. Diseño Pareado
Todas las condiciones se evalúan sobre **las mismas semillas exactas** en ambos brazos:
- Brazo A (Base) y Brazo B (Variante / Línea Base) reciben idénticos mapas y sucesiones de eventos procedurales.
- En Ajedrez: 50 partidas pareadas por rival, alternando colores y con aperturas aleatorias de 4 medias jugadas para eliminar sesgo de apertura.
- En Crafter y Snake: misma semilla procedural del generador de terreno y distribución de recursos.

### 1.4. Tratamiento del Ruido
El núcleo bio-somático incluye un generador termodinámico de ruido físico.
- **Modo normal:** Reproducción estadística (los intervalos de confianza capturan la dispersión estocástica real).
- **Modo `--aislar-ruido`:** Fija la semilla pseudoaleatoria interna del organismo para permitir reproducción paso a paso idéntica (bit a bit) en pruebas canario y verificación de trayectorias.

---

## 2. Batería Estadística

Dado que los datos de supervivencia y rendimiento en agentes no siguen distribuciones normales, el laboratorio emplea estadística no paramétrica rigurosa (`herramientas/estadistica.py`):

1. **Diferencia de Medianas e Intervalos de Confianza:**
   - Estimación de la diferencia con IC del 95 % mediante **remuestreo bootstrap pareado** (10 000 remuestreos por pares).
2. **Contraste de Hipótesis:**
   - **Test de rangos con signo de Wilcoxon** para distribuciones continuas pareadas.
   - **Test de Signos** para dominancia ordinal directa.
   - **Intervalo de Wilson** para proporciones y tasas de victoria en torneos (ej. Ajedrez).
3. **Tamaño del Efecto:**
   - **Delta de Cliff (\(d\))**: cuantifica la dominancia en \([-1, 1]\). Un \(|d| < 0,147\) se considera despreciable; \(|d| \ge 0,474\) se considera grande.
4. **Control de Errores Múltiples:**
   - Corrección secuencial de **Holm-Bonferroni** dentro de cada familia de hipótesis para acotar la tasa de falsos descubrimientos a \(\alpha = 0,05\).

---

## 3. Protocolo de Ablaciones del Árbitro

Para desentrañar si el rendimiento procede del arbitraje motor o de la heurística periférica, se utilizan dos niveles de ablación:

- **Nivel a (Ablación interna):** El árbitro simplificado (ej. mayor arousal, jerarquía fija) elige la acción candidata, pero se mantiene la maquinaria periférica del Tribunal (acecho, colapso tónico por daño crítico, desesperación por inanición).
- **Nivel b (Ablación estricta):** El árbitro emite directamente la acción al actuador sin pasar por ninguna rutina de salvaguarda periférica.

---

## 4. Registro Contrafactual

Para auditar qué sistemas aportan valor, en cada latido el sistema calcula en paralelo qué habrían decidido los árbitros alternativos (A0 a A7):
- **Acuerdo contrafactual:** Porcentaje de pasos en que un árbitro simple (ej. A1 mayor arousal) coincide exactamente con A0 (Tribunal bio-somático).
- Permite detectar **colinealidad**: si dos árbitros coinciden en el 96 % de las decisiones, ninguna prueba estadística podrá separarlos a menos que se analicen de forma aislada los latidos de desacuerdo (R3).

---

## 5. Reglas para una Comparación Justa con Líneas Base Tradicionales

Para contrastar el organismo bioinspirado contra agentes tradicionales (BFS, heurísticas voraces, minimax):

1. **Misma información disponible:** El sensor del mundo entrega exactamente la misma representación de estado al agente tradicional y al organismo de IdA.
2. **Mismo presupuesto de afinación:** No se permite ajustar hiperparámetros de IdA con 100 semillas mientras la línea base se deja con valores arbitrarios por defecto.
3. **Mismo presupuesto de cómputo por decisión:** Ambas variantes deben resolver su decisión dentro de plazos comparables (plazo cooperativo del latido).
4. **Independencia de versión:** Las variantes nacen en `variantes/<nombre>/` y documentan en `CAMBIOS.md` la desviación respecto a `base/`.

---

## 6. Evolución del Método: De la v14 al Laboratorio

La versión 14 acumuló un aparato metodológico hipertrófico: preregistros de diez páginas, compuertas en cascada (A1, A2, B, C, D, E), y decenas de observadores que ralentizaban la investigación sin producir mejoras sustanciales en la conducta del individuo.

**La lección de la v14:**
- **La burocracia de preregistro no sustituye a la simplicidad experimental.**
- En este laboratorio, el método se concentra en lo esencial: **una sola pregunta por experimento**, una ficha de 5 campos predefinida, y contraste pareado con línea base.
