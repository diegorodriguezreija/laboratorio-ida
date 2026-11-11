# Experimento 002: Contraste de Rendimiento en Crafter 2D — IdA v12.0 vs. Agente Voraz

**Fecha de ejecución:** 2026-11-11  
**Rama:** `feature/002-crafter-ida-vs-voraz`  
**Registro de datos brutos:** `salidas/002-crafter-ida-vs-voraz/episodios_pareados.csv` (120 episodios: 40 semillas $\times$ 3 brazos)  
**Resumen estadístico JSON:** `salidas/002-crafter-ida-vs-voraz/resumen_estadistico.json`  
**Pregunta formal prefijada:** [PREGUNTA.md](PREGUNTA.md)

---

## 1. Resumen Ejecutivo y Veredicto

Se evaluó el rendimiento de **IdA v12.0** (arquetipo seleccionado `Hominis_G12` con axiomas ancestrales weismannianos consolidados) frente a una **Línea Base Tradicional Voraz** (`crafter_voraz.py`) y un **Control Aleatorio Uniforme** sobre las mismas **40 semillas pareadas** (3000 a 3039) de la partición de evaluación reservada de Crafter 2D. Se mantuvo paridad estricta de observación (ventana local de visión $9 \times 9$, radio 6) e inventario.

* **Veredicto:** **Mejora clara en progresión técnica (Crafter Score y logros desbloqueados); diferencia no significativa en supervivencia pura.**
  - **Métrica Primaria (Crafter Score Canónico):** IdA alcanza un Crafter Score de **22.07 %** frente al **6.46 %** del agente voraz y el **1.20 %** del agente aleatorio (+15.61 puntos porcentuales netos; factor de mejora de 3.42x).
  - **Logros desbloqueados por episodio:** Media pareada de $+5.88$ logros a favor de IdA [95 % CI: $+4.90, +6.80$], Wilcoxon pareado $W = 5.5$, $p < 10^{-6}$, Cliff's $\delta = 0.852$ (efecto grande). IdA superó al agente voraz en 38 de 40 semillas (1 empate, 1 derrota; test de signos $p < 10^{-6}$).
  - **Métrica Secundaria de Supervivencia:** IdA promedió $282.2$ pasos (mediana $247.0$, IQR $68.8$) vs. $248.4$ pasos del voraz (mediana $216.5$, IQR $65.3$). Diferencia media pareada $+33.9$ pasos [95 % CI: $-9.0, +76.6$], Wilcoxon $W = 298.5$, $p = 0.134$ (no significativo al nivel $\alpha = 0.05$).

---

## 2. Resultados Numéricos Consolidados

### Comparativa Global por Brazo ($N = 40$ semillas pareadas)

| Métrica | IdA v12.0 (Bioinspirado) | Agente Voraz (Línea Base) | Control Aleatorio (Suelo) | Diferencia Pareada (IdA − Voraz) | IC 95 % Bootstrap | Wilcoxon $p$-valor | Cliff's $\delta$ |
|---|---|---|---|---|---|---|---|
| **Crafter Score Poblacional** | **22.07 %** | 6.46 % | 1.20 % | **+15.61 pp** | — | — | — |
| **Logros por episodio (Media $\pm$ SD)** | **11.53 $\pm$ 2.64** | 5.65 $\pm$ 2.68 | 2.32 $\pm$ 0.73 | **+5.88** | **[+4.90, +6.80]** | **$p < 10^{-6}$** | **+0.852** (Grande) |
| **Logros por episodio (Mediana, IQR)** | **12.0 (3.25)** | 5.0 (2.00) | 2.0 (1.00) | **+6.0** | — | — | — |
| **Pasos de vida (Media $\pm$ SD)** | **282.2 $\pm$ 111.4** | 248.4 $\pm$ 95.8 | 211.5 $\pm$ 76.1 | **+33.9** | **[−9.0, +76.6]** | $p = 0.134$ | **+0.261** (Pequeño) |
| **Pasos de vida (Mediana, IQR)** | **247.0 (68.8)** | 216.5 (65.3) | 200.0 (52.0) | **+30.5** | — | — | — |

*Nota sobre la hipótesis $H_2$ (supervivencia):* Aunque la dirección favorece a IdA ($+33.9$ pasos de media, 24 victorias vs. 16 derrotas en supervivencia), el intervalo de confianza cruza el cero ([$-9.0, +76.6$]) y el test no alcanza significación estadística ($p = 0.134$). No se puede rechazar la hipótesis nula de igual duración vital.

---

## 3. Desglose de Tasas de Éxito por Logro ($s_i \in [0, 100]$ %)

De los 22 logros oficiales de Crafter, se desglosan las tasas de consecución según la taxonomía funcional prefijada:

| Categoría | Logro Oficial | IdA v12.0 (%) | Agente Voraz (%) | Control Aleatorio (%) | Brecha (IdA − Voraz) |
|---|---|---|---|---|---|
| **Supervivencia Básica** | `collect_wood` | 100.0 % | 100.0 % | 15.0 % | +0.0 pp |
| | `place_table` | 100.0 % | 100.0 % | 0.0 % | +0.0 pp |
| | `collect_drink` | 92.5 % | 85.0 % | 5.0 % | +7.5 pp |
| | `eat_cow` | 70.0 % | 80.0 % | 0.0 % | −10.0 pp |
| | `wake_up` | 27.5 % | 17.5 % | 95.0 % | +10.0 pp |
| | `eat_plant` | 0.0 % | 0.0 % | 0.0 % | +0.0 pp |
| **Combate y Hostiles** | `defeat_zombie` | **85.0 %** | 70.0 % | 0.0 % | **+15.0 pp** |
| | `defeat_skeleton` | **60.0 %** | **0.0 %** | 0.0 % | **+60.0 pp** |
| **Herramientas de Madera** | `make_wood_pickaxe` | **97.5 %** | 32.5 % | 0.0 % | **+65.0 pp** |
| | `make_wood_sword` | **97.5 %** | 20.0 % | 0.0 % | **+77.5 pp** |
| **Progresión de Piedra** | `collect_stone` | **97.5 %** | 17.5 % | 0.0 % | **+80.0 pp** |
| | `make_stone_pickaxe` | **80.0 %** | 15.0 % | 0.0 % | **+65.0 pp** |
| | `make_stone_sword` | **70.0 %** | **0.0 %** | 0.0 % | **+70.0 pp** |
| | `place_stone` | **57.5 %** | **0.0 %** | 0.0 % | **+57.5 pp** |
| | `place_furnace` | **47.5 %** | 15.0 % | 0.0 % | **+32.5 pp** |
| **Minerales Avanzados** | `collect_coal` | **42.5 %** | 7.5 % | 0.0 % | **+35.0 pp** |
| | `collect_iron` | **22.5 %** | 5.0 % | 0.0 % | **+17.5 pp** |
| | `make_iron_pickaxe` | **5.0 %** | 0.0 % | 0.0 % | **+5.0 pp** |
| | `make_iron_sword` | 0.0 % | 0.0 % | 0.0 % | +0.0 pp |
| | `collect_diamond` | 0.0 % | 0.0 % | 0.0 % | +0.0 pp |
| **Otros / Entorno** | `collect_sapling` | 0.0 % | 0.0 % | 65.0 % | +0.0 pp |
| | `place_plant` | 0.0 % | 0.0 % | 57.5 % | +0.0 pp |

---

## 4. Análisis Mecanístico del Contraste

### 4.1 ¿Dónde radica la ventaja de IdA?
1. **Cohesión secuencial en el árbol tecnológico:**
   Tanto IdA como el agente voraz desbloquean el primer escalón (`collect_wood` y `place_table` al 100.0 %). Sin embargo, tras colocar la mesa, el agente voraz con frecuencia se dispersa o se ve interrumpido por demandas metabólicas locales repetitivas (beber agua o pastorear vacas), perdiendo la referencia de la mesa de trabajo (que cae fuera de su vista si se aleja más de 6 casillas). Solo fabrica el pico de madera en el 32.5 % de las semillas y la espada en el 20.0 %.
   En contraste, IdA, gracias al anclaje ontológico de $S_3$ y la modulación de saliencia en la onda de activación, encadena de forma persistente la fabricación inmediata (`make_wood_pickaxe` 97.5 %, `make_wood_sword` 97.5 %), lo que desbloquea la minería de piedra al 97.5 % (frente al 17.5 % del voraz).
2. **Defensa activa frente a hostiles complejos (esqueletos):**
   El agente voraz derrota zombis en el 70.0 % de los casos (combate cuerpo a cuerpo sencillo), pero es incapaz de lidiar con proyectiles balísticos a distancia: su tasa de `defeat_skeleton` es exactamente del **0.0 %**.
   IdA, a través del subsistema reactivo $S_1$ (circuito periacueductal PAG que triangula trayectorias balísticas y acorta distancias bajo agresión) apoyado en $S_3$, alcanza una tasa de eliminación de esqueletos del **60.0 %**.
3. **Profundidad mineral:**
   La cadena tecnológica superior de IdA se traduce en acceso a carbón (42.5 % vs 7.5 %) y extracción de hierro (22.5 % vs 5.0 %), llegando a fabricar herramientas de hierro (`make_iron_pickaxe` 5.0 % vs 0.0 %).

### 4.2 ¿Por qué no hay ventaja significativa en supervivencia pura?
La duración del episodio no muestra una separación concluyente ($+33.9$ pasos, $p = 0.134$). Tanto IdA como el agente voraz disponen de mecanismos funcionales para beber agua (92.5 % vs 85.0 %) y cazar vacas (70.0 % vs 80.0 %). La mayor parte de las muertes en ambos agentes ocurren en torno al paso 200–300 cuando cae la noche o cuando se acumulan múltiples depredadores en zonas sin luz. IdA no vive sustancialmente más tiempo, sino que **utiliza el mismo tiempo vital de forma incomparablemente más estructurada**, transformando un tiempo similar de supervivencia en progreso tecnológico profundo.

---

## 5. Conclusiones y Cumplimiento de Criterios

1. **Hipótesis $H_1$ (Crafter Score):** Rechazada la hipótesis nula. IdA supera al agente tradicional voraz bajo las mismas condiciones de observación local con una ventaja de $+15.61$ puntos de Crafter Score (22.07 % vs 6.46 %) y $+5.88$ logros por vida ($p < 10^{-6}$).
2. **Hipótesis $H_2$ (Supervivencia):** No rechazada la hipótesis nula. El diseño bioinspirado no otorga una prolongación vital estadísticamente separable de una heurística voraz simple ($p = 0.134$).
3. **Validez metodológica:** Cumplida en paridad estricta. Ni IdA ni la línea base accedieron a información global. La jerarquía de decisiones del agente voraz permaneció inalterada desde su formulación a priori en `PREGUNTA.md`.
