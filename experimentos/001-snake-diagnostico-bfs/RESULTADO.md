# Resultado del Experimento 001: Diagnóstico Anatómico en Snake (IdA vs. BFS)

**Fecha:** 2026-11-11  
**Mundo:** Snake en Rejilla Determinista en Memoria (21 columnas x 15 filas)  
**Muestra:** N = 50 semillas pareadas (0 a 49)  
**Unidad de análisis:** Episodio (N = 50 pares observados)  
**Registro de datos:** `salidas/001-snake-diagnostico-bfs/episodios_pareados.csv`  

---

## 1. Comprobación de Validez del Entorno

La regla fijada a priori establecía que el simulador debía reproducir la derrota observada históricamente en E-09 para que el diagnóstico tuviese sentido como explicación de aquel resultado:

| Brazo | Longitud Mediana | Longitud Media (± DT) | Mín / Máx | Pasos Mediana | Balance de Victorias |
|---|---|---|---|---|---|
| **IdA (Orgánico)** | **73.0** | 71.84 (± 15.82) | 37 / 103 | 1232.0 | **23 victorias** |
| **Línea Base BFS** | **68.5** | 71.18 (± 13.85) | 36 / 99 | 1144.0 | **23 victorias** |
| **Control Aleatorio Legal** | **6.0** | 6.42 (± 1.67) | 3 / 10 | 1663.5 | 0 victorias (4 empates IdA-BFS) |

### Contraste Pareado
* **IdA frente a BFS:**
  * Diferencia media pareada: **+0.66** [IC 95 %: -4.50, +5.64]
  * Test de rangos con signo de Wilcoxon (por episodio): $W = 487.5$, $p = 0.562$ (no significativo)
  * Delta de Cliff: $d = +0.04$
* **IdA frente a Aleatorio:**
  * Diferencia media pareada: **+65.42** [IC 95 %: +60.84, +69.98]
  * Test de Wilcoxon: $W = 0.0$, $p = 0.000$

> [!WARNING]
> **Veredicto: LA COMPROBACIÓN DE VALIDEZ FALLA.**  
> El simulador síncrono en memoria **no reproduce la derrota de E-09**. En condiciones síncronas sin límite de tiempo por latido, IdA y BFS no muestran diferencias estadísticamente detectables.  
> *Consecuencia metodológica:* Este experimento **no responde a la pregunta original** («¿por qué perdió IdA en E-09?»). Las métricas A, B y C que siguen constituyen una caracterización anatómica del comportamiento de IdA en régimen síncrono, no una explicación demostrada de aquella derrota histórica en la web.

---

## 2. Hipótesis Explicativa: El Coste del Ciclo Cognitivo

A la vista de que en condiciones síncronas la diferencia entre IdA y BFS desaparece (el IC 95 % descarta diferencias medias mayores a unas 5–6 unidades de longitud), se formula la siguiente **hipótesis post-hoc (pendiente de prueba en 001b)**:
* En Playsnake.org el juego avanzaba en tiempo real (120 ms por tick en Worm, 80 ms en Python).
* La tubería cognitiva completa de IdA (S1 + S2 + S3 + bucle talamocortical + Tribunal con evaluación de árbitros contrafactuales) acumula una latencia que, sumada al puente de automatización de Chromium, provocaba descarte o retraso de órdenes en el navegador web.
* La línea base BFS, con un cálculo directo en menos de 1 ms, no sufría descarte de comandos.
* *Nota sobre Slug:* En la velocidad lenta de Playsnake (Slug), el IC 95 % histórico ya incluía el cero ([-577, +218]), lo que es compatible con esta hipótesis pero no la demuestra, dado el elevado ancho de ese intervalo.

---

## 3. Diagnóstico Anatómico en Régimen Síncrono

### Métrica A: Tasa de Oscilación Improductiva ($\tau_{osc}$)
Proporción de giros seguidos de contragiro en $\le 2$ ticks que no reducen la distancia de camino más corto (BFS) a la manzana:

* **Tasa mediana en IdA:** 1.59 % (Media: 1.55 %, IC 95 % [1.35 %, 1.75 %])
* **Tasa mediana en BFS:** 3.54 % (Media: 3.55 %, IC 95 % [3.34 %, 3.77 %])
* **Contraste pareado (por episodio, N = 50):** Wilcoxon $W = 10.0$, $p < 0.0001$.
* *Análisis:* BFS presenta una tasa de cambio de sentido significativamente mayor debido a que su búsqueda de camino más corto avanza en trayectorias diagonales mediante alternancia ortogonal en escalera. En campo abierto, IdA no presenta mioclonías ni inestabilidad motora.

### Métrica B: Contrafactual de Espacio Libre Residual
Pérdida de área conexa accesible por movimiento ($\delta = (A_{max} - A_{IdA}) / N_{libres}$):

* **Frecuencia de decisiones subóptimas ($\delta > 0$):** Mediana = **0.26 %** de los ticks (Media: 0.28 %, IC 95 % [0.24 %, 0.33 %]). Representa en promedio entre 3 y 4 ticks por episodio.
* **Magnitud media de pérdida cuando $\delta > 0$:** Mediana = **19.94 %** del tablero libre (IC 95 % [20.41 %, 29.30 %]).
* *Cruce con el desenlace:* Aunque IdA maximiza el espacio libre conexo en más del 99.7 % de los latidos, ese 0.28 % de decisiones con $\delta > 0$ coincide de forma sistemática con la entrada a cuellos de botella irreversibles que precipitan el auto-encierro en los episodios.

### Métrica C: Interferencia Destructiva de S1 sobre S3
Evaluación contrafactual de desacuerdos entre el instinto reactivo S1 y la estrategia S3:

* **Ticks totales con discrepancia S1 vs. S3:** 6 926 ticks (mediana de 130.5 ticks por episodio; ~10.6 % del total).
* **Discrepancias en la ventana crítica pre-muerte ($\le 5$ ticks del choque):** Se registraron discrepancias activas en 41 de los 50 episodios (tasa de 0.82 discrepancias por muerte).
* **Interferencias destructivas confirmadas mediante bifurcación contrafactual:** **0 casos (0.0 %)**.
* *Análisis:* En todas las bifurcaciones donde se forzó la propuesta de S3 desde el punto de desacuerdo previo a la muerte, la serpiente pereció igualmente en $\le 5$ ticks. El 0 % no se debe a ausencia de desacuerdos durante la agonía, sino a que cuando la discrepancia ocurrió cerca del final, el espacio ya estaba cerrado y ninguna alternativa era viable. S1 no sabotea a S3.

---

## 4. Comparativa de Causas de Muerte (IdA frente a BFS)

Clasificación exhaustiva de las 50 muertes en ambos brazos:

| Causa de Muerte | IdA (Casos) | IdA (%) | BFS (Casos) | BFS (%) | Descripción Mecánica |
|---|---|---|---|---|---|
| **Auto-encierro** | **49** | **98.0 %** | **2** | **4.0 %** | Colisión contra el propio cuerpo al agotarse el espacio conexo |
| **Colisión Perimetral (Muro)** | **0** | **0.0 %** | **45** | **90.0 %** | Impacto contra el borde exterior al no existir salidas legales |
| **Límite de Tiempo (Tope 2000 ticks)** | **1** | **2.0 %** | **3** | **6.0 %** | Episodio censurado por alcanzar el techo de seguridad |
| **Interferencia Destructiva S1** | **0** | **0.0 %** | — | — | Descartada contrafactualmente mediante bifurcación |

### Diagnóstico de la diferencia en la colisión final
* **Mecanismo idéntico:** Ambos agentes mueren al alcanzar longitudes elevadas ($L \approx 70-80$, ocupando el 25 % del tablero) cuando el espacio libre restante queda fragmentado.
* **Diferencia de contacto final:**
  * BFS prioriza maximizar el área libre en cada tick; al quedarse con 0 casillas legales libres, su última dirección inercial lo estampa de frente contra el muro perimetral (90 % de sus muertes).
  * IdA cuenta con un fuerte componente de evitación perimetral en S1 (`CompSupervivenciaSnakeS1`); cuando se queda sin salidas, dobla hacia el interior esquivando el muro exterior, impactando en consecuencia contra su propio cuerpo (98 % de sus muertes).
  * Ambos colapsan por el mismo fenómeno: **saturación espacial del recinto**.

---

## 5. Síntesis Final

1. **Validez externa:** El experimento síncrono no reproduce la brecha de E-09. La hipótesis de que la derrota histórica se debió al coste del ciclo cognitivo bajo tiempo real queda planteada para contrastarse formalmente con latencia simulada (Experimento 001b).
2. **Capacidad táctica de IdA:** En condiciones síncronas, la modulación multi-sistema de IdA es competitiva con la línea base BFS tradicional (longitud media 71.84 frente a 71.18, IC 95 % [-4.50, +5.64]).
3. **Paso a Crafter:** Dado que el benchmark oficial de Crafter opera de forma síncrona por turnos (sin reloj de tiempo real externo), la latencia del ciclo cognitivo no afectará a la validez de las mediciones en Crafter, donde el contraste frente a un agente voraz evaluará de verdad la regulación homeostática.
