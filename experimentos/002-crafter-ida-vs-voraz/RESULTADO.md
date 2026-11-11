# Experimento 002: Contraste de Rendimiento en Crafter 2D — IdA v12.0 vs. Agente Voraz

**Fecha de ejecución:** 2026-11-11  
**Rama:** `feature/002-crafter-ida-vs-voraz`  
**Registro de datos brutos:** `salidas/002-crafter-ida-vs-voraz/episodios_pareados.csv` (120 episodios: 40 semillas $\times$ 3 brazos)  
**Resumen estadístico JSON:** `salidas/002-crafter-ida-vs-voraz/resumen_estadistico.json`  
**Ficha formal a priori:** [PREGUNTA.md](PREGUNTA.md)

---

## 1. Resumen Ejecutivo y Veredicto

Se evaluó el rendimiento de **IdA v12.0** (arquetipo seleccionado `Hominis_G12` con axiomas ancestrales weismannianos consolidados) frente a una **Línea Base Tradicional Voraz sin memoria** (`crafter_voraz.py`) y un **Control Aleatorio Uniforme** sobre las mismas **40 semillas pareadas** (3000 a 3039) de la partición de evaluación reservada de Crafter 2D. Se mantuvo paridad de observación (ventana local de visión $9 \times 9$, radio 6) e inventario.

* **Veredicto:** **Mejora clara frente a la línea base voraz reactiva sin memoria (+15.61 pp de Crafter Score, IC 95 %: [+12.34 %, +18.41 %]; +5.88 logros por episodio, $p < 10^{-6}$). Diferencia en supervivencia pura no significativa (+33.9 pasos, $p = 0.067$ unilateral).**
* **Alcance y Límite de la Conclusión:** La ventaja observada demuestra la superioridad de IdA frente a un sistema heurístico reactivo clásico que carece de memoria espacial. Dado que el agente voraz olvida la ubicación de los recursos tan pronto salen de su campo de visión local ($9 \times 9$), los datos presentes no permiten atribuir de forma causal la ventaja a los componentes bioinspirados (sistemas límbico/afectivo o arbitraje triúnico) frente a lo que aportaría una memoria espacial convencional. Dicha atribución queda pendiente de verificación en el Experimento 002b (voraz con memoria de mapa vs. IdA con ablación de memoria).

---

## 2. Declaración de Desviación del Pre-registro

En [PREGUNTA.md](PREGUNTA.md), la sección 2 postulaba:
> *«$H_0$: La mediana de la diferencia pareada en el Crafter Score poblacional entre IdA y el Agente Voraz en las mismas semillas es igual a cero [...] evaluada con un test de Wilcoxon pareado».*

**Desviación metodológica:** El *Crafter Score* (Hafner, 2021) es formalmente una métrica agregada poblacional (la media geométrica de las tasas de éxito $s_i$ de los 22 logros calculadas sobre el total de la muestra $N=40$). Al ser una función no lineal de las tasas agregadas, no existe una cifra de Crafter Score univariante e independiente por semilla que permita aplicar directamente el test de rangos con signo de Wilcoxon sobre diferencias individuales de score.

**Corrección aplicada:**
1. Para contrastar la métrica primaria agregada, se construyó un **Intervalo de Confianza Bootstrap al 95 % de la diferencia poblacional pareada** ($\text{CrafterScore}_{\text{IdA}} - \text{CrafterScore}_{\text{Voraz}}$) mediante $B = 10.000$ remuestreos de las 40 semillas pareadas.
2. Como contraste inferencial complementario a nivel de episodio pareado por semilla, se evaluó el **número total de logros desbloqueados por episodio** mediante el test de Wilcoxon pareado bilateral y el test de signos binomial.

---

## 3. Resultados Numéricos Consolidados

### Comparativa Global por Brazo ($N = 40$ semillas pareadas)

| Métrica | IdA v12.0 (Bioinspirado) | Agente Voraz (Sin Memoria) | Control Aleatorio (Suelo) | Diferencia Pareada (IdA − Voraz) | IC 95 % Bootstrap (10.000 réplicas) | $p$-valor | Tamaño del Efecto |
|---|---|---|---|---|---|---|---|
| **Crafter Score Poblacional** | **22.07 %** | 6.46 % | 1.20 % | **+15.61 pp** | **[+12.34 %, +18.41 %]** | — | — |
| **Logros por episodio (Media $\pm$ SD)** | **11.53 $\pm$ 2.64** | 5.65 $\pm$ 2.68 | 2.38 $\pm$ 0.73 | **+5.88 logros** | **[+4.90, +6.80]** | **$p < 10^{-6}$** (Wilcoxon bilateral) | Cliff's $\delta = +0.852$ (Grande) |
| **Logros por episodio (Mediana, IQR)** | **12.0 (3.25)** | 5.0 (2.00) | 2.0 (1.00) | **+6.0 logros** | — | **$p < 10^{-6}$** (Signos: 38 V / 1 E / 1 D) | — |
| **Pasos de vida (Media $\pm$ SD)** | **282.2 $\pm$ 111.4** | 248.4 $\pm$ 95.8 | 211.5 $\pm$ 76.1 | **+33.9 pasos** | **[−9.0, +76.6]** | $p = 0.067$ (Unilateral $H_2$) / $p = 0.134$ (Bilateral) | Cliff's $\delta = +0.261$ (Pequeño) |
| **Pasos de vida (Mediana, IQR)** | **247.0 (68.8)** | 216.5 (65.3) | 200.0 (52.0) | **+30.5 pasos** | — | $p = 0.268$ (Signos: 24 V / 0 E / 16 D) | — |

*Detalle sobre la hipótesis $H_2$ (supervivencia):* Al contrastar la hipótesis unilateral pre-registrada ($H_{2,1}: \text{Pasos}_{\text{IdA}} > \text{Pasos}_{\text{Voraz}}$), el test de Wilcoxon arroja $W = 298.5, p = 0.067$ ($p = 0.134$ en versión bilateral). Pese a una tendencia favorable (+33.9 pasos de media, 24 episodios con mayor duración frente a 16), el intervalo de confianza cruza el cero ([$-9.0, +76.6$]), por lo que **no se rechaza la hipótesis nula de igual duración vital al nivel $\alpha = 0.05$**.

*Corrección de errata en control aleatorio:* El recuento exacto de logros en el brazo aleatorio es de $95$ logros totales repartidos en 40 semillas, arrojando una media exacta de **2.375 logros por episodio** (reportada inicialmente de forma redondeada como 2.32).

---

## 4. Desglose de Tasas de Éxito por Logro ($s_i \in [0, 100]$ %)

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

## 5. Análisis Mecanístico e Hipótesis Falsables

### 5.1 El Factor de la Memoria Espacial vs. Diseño Bioinspirado
El análisis de comportamiento muestra que el agente voraz coloca la mesa de trabajo (`place_table`) en el 100 % de los episodios, pero solo llega a fabricar el pico de madera en el 32.5 %. La causa es directa: tan pronto coloca la mesa, una necesidad metabólica prioritaria (sed o caza) o una amenaza hace que el agente se mueva unos pasos. Al superar las 6 casillas de distancia, la mesa desaparece de su vista local y, al no contar con memoria persistente de objetos pasados, el voraz queda en un bucle errante buscando árboles nuevos sin volver a su mesa.
IdA, por su parte, mantiene en la estructura de memoria de $S_3$ los nodos observados recientemente. Esta diferencia no demuestra por sí misma la superioridad de una arquitectura bioinspirada frente a una tradicional: **cualquier agente clásico provisto de un mapa de memoria local y un algoritmo de ruta (A*) habría recordado la mesa de trabajo**. 

### 5.2 Combate con Esqueletos: Exposición y Tasa Condicionada
La diferencia en `defeat_skeleton` (60.0 % en IdA vs. 0.0 % en el voraz) se auditó empíricamente para verificar si se debía a una falta de exposición del voraz (por picar menos piedra) o a incapacidad táctica de combate:
* En las 40 semillas, el agente voraz tuvo al menos un esqueleto dentro de su campo de visión local en **31 de las 40 semillas (77.5 % de exposición)**, y estuvo bajo fuego directo de proyectiles de flecha en **21 semillas (52.5 %)**.
* Su tasa de victoria condicionada a la presencia de esqueletos fue del **0.0 % (0 / 31)**. En IdA, la tasa de victoria fue del **60.0 % (24 / 40)**.
* **Hipótesis del mecanismo:** Los esqueletos en Crafter retroceden si el agente se acerca a distancia $\le 3$ casillas y disparan flechas balísticas a distancia $\le 5$ casillas (`crafter/objects.py:Skeleton.update`). El agente voraz, al detectar peligro cercano, ejecuta una huida en sentido opuesto alejándose del hostil, manteniéndose perpetuamente en la zona de tiro sin alcanzarlo. La hipótesis a contrastar formalmente es si la aproximación agresiva en combate cuerpo a cuerpo es suficiente para resolver el enfrentamiento, o si se requiere un componente deliberativo específico.

---

## 6. Asimetría de Ajuste Metodológica

Debe consignarse formalmente la asimetría en el esfuerzo de calibración:
* El espécimen de IdA evaluado (`Hominis_G12`) proviene de un linaje evolutivo previo de 12 generaciones donde se seleccionaron rasgos de personalidad somática (apertura 0.63, responsabilidad 0.71, neuroticismo 0.45, umbral de miedo 0.54) y se acumularon 33 axiomas ancestrales weismannianos a partir de ejecuciones en semillas de Crafter diferentes a las de evaluación (semillas de entrenamiento históricas, ajenas al rango 3000–3039).
* La línea base voraz (`crafter_voraz.py`) se implementó con una jerarquía de reglas fijada a priori en un único diseño, sin proceso de sintonización evolutiva ni optimización iterativa de parámetros.
* Aunque no existe fuga de datos sobre las semillas de evaluación (3000–3039), **el esfuerzo de ajuste no fue simétrico**.

---

## 7. Propuesta de Trabajo Siguiente: Experimento 002b

Para responder a las incógnitas que este experimento deja abiertas y determinar con rigor si la ventaja proviene del chasis bioinspirado o meramente de la memoria espacial, se pre-registrará el **Experimento 002b** con dos nuevos brazos sobre las mismas 40 semillas:
1. **Línea Base Voraz con Memoria Espacial (`crafter_voraz_memoria.py`)**: Registra en un mapa local los recursos permanentes observados (mesas de trabajo colocadas, hornos, fuentes de agua) y utiliza A* para regresar a ellos cuando su inventario lo requiera.
2. **Brazo IdA con Ablación de Memoria Proactiva ($S_3$ despojado de memoria de contexto o memoria episódica acotada al tick presente)**.

Si IdA mantiene ventaja significativa frente a un voraz dotado de memoria equivalente, la hipótesis del beneficio del chasis bioinspirado quedará empíricamente sustentada.
