# Laboratorio IdA – Dossier de investigación

**Pregunta central: ¿supera el diseño orgánico de IdA a un diseño tradicional en cada mundo, en qué situaciones y cuánto?**

Recopilación de todo lo investigado, medido y descubierto hasta ahora sobre esa pregunta, reunido a partir de los informes, preregistros y adjuntos de esta conversación (v12, v13 y v14). Fecha: 11 de noviembre de 2026.

> **Cómo leer este dossier.** Cada cifra lleva su origen. Cuando una cifra procede de mis notas y no de un informe que haya podido releer, lo dejo marcado como *(de mis notas, a verificar)*. Las cifras de la v12 que luego se retiraron están en la sección 11 y no deben reutilizarse.

---

## 1. Resumen y respuesta honesta

**Lo que se puede decir hoy.**

1. **Sí hay casos medidos en los que el diseño orgánico mejora algo, pero ninguno es todavía una prueba limpia de «orgánico frente a tradicional» en el sentido pleno.** Los mejores resultados comparan IdA con líneas base sencillas (un jugador de ajedrez de 1 ply, jerarquías fijas de sistemas) o consigo mismo.
2. **Donde hay una comparación con un agente tradicional real, el resultado es mixto.** En Ajedrez, IdA gana claramente a los oponentes minimax locales y no se distingue de la línea base contra Stockfish. En Snake, IdA puntúa *menos* que un buscador de rutas (BFS) en Worm y Python.
3. **En Crafter no existe todavía una línea base tradicional.** Las comparaciones son internas: el Tribunal frente a árbitros más simples, arquetipos frente a arquetipos, con y sin ciertos módulos.
4. **Los módulos que más se anuncian (cortisol, axiomas heredados, plasticidad, REM, tálamo, DMN) no tienen efecto medido en el rendimiento.** Algunos cambian la conducta (por ejemplo el reparto de decisiones) pero no los resultados.
5. **La v14 buscó que la experiencia (activa y proactiva) influyera en las decisiones y no lo consiguió.** Lo activo ayudó poco dentro de una vida; lo proactivo, tal como estaba hecho, empeoró frente a predecir siempre lo más frecuente; y un cuello de botella en el arbitraje impide que una experiencia que *añade candidatos* llegue a decidir.

### Tabla resumen: dónde mejoró, empató o empeoró

| # | Mundo | Comparación | Resultado | Veredicto |
| --- | --- | --- | --- | --- |
| 1 | Ajedrez | IdA frente a línea base de 1 ply (misma evaluación), contra minimax local nivel 1, 2 y 3 | +0,46, +0,52 y +0,21 puntos por partida (puntuaciones 0,97, 0,99 y 0,99) | **Mejora clara** |
| 2 | Ajedrez | Ídem contra Stockfish UCI_Elo 1320 y 1500 | +0,03 [−0,06; +0,13] y +0,00 [−0,04; +0,05] | **Empate** (no se distingue) |
| 3 | Crafter | Tribunal (A0) frente a jerarquía fija S1>S2>S3 y S3>S2>S1 | +8,85 y +2,30 logros por vida, p Holm < 0,001 | **Mejora clara** frente a jerarquías fijas |
| 4 | Crafter | Tribunal frente a «mayor arousal» y «mayor producto» | +0,72 [+0,05; +1,52] (p Holm 0,116) y +0,62 [−0,05; +1,43] (p Holm 0,147) | **Empate** (colinealidad del 96 %) |
| 5 | Crafter | Con S2 activo (H7) frente a S2 neutro | +1,40 logros, pero −536 pasos vividos y más muertes por depredador | **Mejora con coste** |
| 6 | Crafter | Arquetipo seleccionado frente a arquetipo fundador | Crafter Score poblacional 5,74 % → 22,31 % | **Mejora**, pero un arquetipo fijado a mano rinde igual |
| 7 | Crafter | Axiomas heredados frente a vacíos (mismo arquetipo) | +0,00 logros [−0,07; +0,07] | **Sin efecto** |
| 8 | Crafter | Cortisol dinámico frente a fijo (H2) | Entre −0,35 y +0,12 logros, no significativo | **Sin efecto en logros** (cambia el reparto de decisiones) |
| 9 | Snake | IdA frente a BFS, puntuación media | Slug −192,3 [−577; +218]; Worm −417,2 [−746; −90]; Python −615,2 [−972; −258] | **Peor** en Worm y Python; no concluyente en Slug |
| 10 | Mundo mínimo | Con frente a sin experiencia | Viven más y comen menos setas tóxicas | **Indicado** (una semilla, 4 vidas por grupo) |
| 11 | Crafter (v14) | Episodio parecido recuperado frente a línea base de la misma vida | +6,3 puntos de acierto de signo [+1,5; +11,2] | **Mejora pequeña** (y de predicción, no de rendimiento) |
| 12 | Crafter (v14) | Expectativas proactivas frente a predecir lo más frecuente | −5,8 puntos [−9,0; −3,1] | **Peor** |

---

## 2. Definiciones y qué se ha comparado con qué

| Término | Definición de trabajo |
| --- | --- |
| **Diseño orgánico** | IdA o una variante suya: cuerpo con estado vital, tres sistemas (S1 supervivencia, S2 valor, S3 verdad) que proponen, un tribunal (A0) que decide con una ponderación, experiencia, conocimiento formal legible y linaje |
| **Diseño tradicional (línea base)** | Un agente convencional y sencillo para el mundo: reglas fijas, búsqueda clásica o jerarquías de prioridad, sin cuerpo simulado ni experiencia propia |
| **Variante** | Una copia modificada de IdA, con una lista corta de cambios respecto a su versión de origen |
| **Superar** | Mejor resultado en la medida del mundo, con las mismas semillas y el mismo presupuesto, y con una diferencia mayor que el umbral fijado antes de ejecutar |
| **Situaciones** | Condiciones del mundo alteradas de forma controlada (escasez, peligros nuevos, mundo cambiante, ruido) |
| **Cuánto** | Diferencia relativa de medianas entre variante y línea base, con el rango entre semillas |

### Qué «tradicional» ha existido de verdad hasta ahora

| Mundo | Línea base que se usó | ¿Es un diseño tradicional real? |
| --- | --- | --- |
| Ajedrez | Jugador de 1 ply con la misma evaluación; oponentes minimax locales (niveles 1 a 3) y Stockfish | **Sí**, aunque el de 1 ply es débil |
| Snake | BFS (búsqueda en anchura de la ruta a la comida) | **Sí** |
| Crafter | Árbitros más simples con los mismos órganos (jerarquías fijas, mayor arousal, mayor producto) | **No**: son variantes de IdA, no un agente ajeno |
| Crafter | Agentes de RL (PPO, Rainbow, DreamerV3) | **No válida**: la comparación se retiró (un máximo frente a medias, entornos no comparables) |
| Mundo mínimo y archivos | Ninguna | — |

---

## 3. Cronología de las investigaciones

| Fecha | Qué | Resultado clave |
| --- | --- | --- |
| 7 nov 2026 | **v12: preregistro de H1, H7 y H2** (commit base `3b42837`, tag `v12.0-baseline-pre-core-eval`), partición de semillas y diseño factorial de herencia | Predicciones a priori: H1 apoyada 0,25; H7 0,05; H2 0,35 |
| 7–8 nov | **v12: re-medición N1 a N4** sobre semillas de reserva 3000–3039 (Crafter), 50 partidas pareadas por rival (Ajedrez), 180 episodios (Snake) | Secciones 5 y 6 |
| 7–8 nov | **v12: auditoría de publicación** | 12 hallazgos, entre ellos que la manipulación de cortisol de H2 no llegaba al Tribunal (sección 11) |
| 8 nov | **v13: escaparate** (registro de latidos, visor, biografías, demo de la guillotina, episodios publicados, linaje de 6 generaciones) | Infraestructura de observación; núcleo sin cambios; canario SHA-256 `46856cb3…c250e9` |
| 9 nov | **v14, pasos 0 a 3:** sonda, hallazgos documentados, activa observada y proactiva observada | +6,3 y −5,8 puntos (sección 9) |
| 9 nov | **v14, E2 a E4:** calibración del cuerpo de Crafter (A), curiosidad intrínseca (B), tres observadores (C) | Bloque A cerrado en la puerta A1; B «no recomendado»; C observado (sección 10) |
| 9 nov | **v14, E5:** diagnóstico del arbitraje, corrección de la carga falsa, curiosidad con regla nueva y tres observadores | Cerrado con resultados negativos *(de mis notas, a verificar)* (sección 10) |
| 9 nov | **v14, E6:** contrafactual del arbitraje, repetición de la carga, curiosidad en el ejemplo mínimo y activa por modulación | **Diseñado, no ejecutado** |
| 10 nov | Decisión: crear el laboratorio en un repositorio aparte para medir y comparar | Este dossier |

---

## 4. Metodología

### 4.1. Principios del método usado hasta ahora

1. **Preregistro.** Hipótesis, criterios de éxito y de refutación, semillas y análisis se escribían y se fijaban en git *antes* de ejecutar. En la v14, el commit del preregistro debía ser anterior a los de medición, y el informe lo demostraba con la hora de cada commit.
2. **Partición de semillas.** Desarrollo 0–999 (ajustes y comprobaciones), test 2000–2999 (fase de diagnóstico) y reserva 3000–3999 (se abre una sola vez). Las cifras públicas de Crafter usan la reserva 3000–3039 una única vez (N1); no deben reutilizarse para afirmaciones nuevas. Quedan sin tocar 4000–4039 y el resto de test. En la v14 se usaron solo semillas de desarrollo: 0–9, 10–29, 30–49, 90–129, 130–169, 170–209, 210–249 y 250–289.
3. **Diseño pareado.** Todas las condiciones se evalúan en las mismas semillas y se compara semilla a semilla. En Ajedrez, 50 partidas pareadas por rival (colores alternos y aperturas aleatorias de 4 medias jugadas).
4. **Estadística** (`analisis/estadistica.py`): diferencia media con IC 95 % por bootstrap (10 000 remuestreos), Wilcoxon de rangos con signo, test de signos, delta de Cliff y corrección de Holm-Bonferroni dentro de cada familia de comparaciones. En Ajedrez, intervalo de Wilson para la puntuación.
5. **Ablaciones del árbitro, en dos niveles.** *Nivel a:* el árbitro simple decide, pero se mantiene la maquinaria periférica del Tribunal (acecho, desesperación por inanición, colapso tónico). *Nivel b:* el árbitro simple emite directamente la acción, sin esa maquinaria.
6. **Registro contrafactual.** En cada latido se anota qué habrían elegido en paralelo los árbitros A0 a A7, y se estratifica el acuerdo por estrés bajo o alto, alimentación normal o inanición, y desacuerdos que acabaron en muerte en ≤ 5 pasos.
7. **No regresión (canario).** Con todos los flags apagados, la v14 debe dar el mismo CSV de H7 que la v13 (SHA-256 `46856cb3756feb81fb3271524e2566b3f1356a3409d5c8199c12028fa0c250e9`). Los observadores no pueden alterar la trayectoria (22 de 22 trayectorias idénticas).
8. **Modificadores medidos por pares con flag apagado por defecto**, y resultado final «recomendado», «no recomendado» o «no ejercitada».
9. **Topes de coste** (aceptados el 9 nov): mediana ≤ 0,5 ms y p99 ≤ 5 ms por latido en el camino crítico, el 1 % del plazo en el p99 y mantenimiento ≤ 25 ms.
10. **Ruido.** El ruido físico del núcleo es real y está activo en las mediciones públicas, de modo que la reproducción es *estadística*, no exacta. Con `--aislar-ruido` las trayectorias son reproducibles. En el factorial, dos condiciones que debían comportarse igual (C1 y C2) coincidieron en 38 de 40 semillas.

### 4.2. Métricas

| Mundo | Medida primaria usada |
| --- | --- |
| Crafter | Crafter Score poblacional (media geométrica ajustada de las tasas de éxito de los 22 logros), logros únicos por vida, pasos vividos y causa de muerte |
| Snake | Puntuación media, mediana e IQR, pasos de supervivencia, muertes por colisión |
| Ajedrez | Puntuación de torneo (victorias + tablas/2), con intervalo de Wilson |
| v14 | Acierto del signo del balance del episodio (con IC por partidas), calibración, coste por latido |

**Crafter Score:** \( S = \exp\left(\tfrac{1}{22}\sum_{i=1}^{22}\ln(1+s_i)\right) - 1 \), con \( s_i \) la tasa de éxito (0–100 %) de cada logro. Hay una sola función en el código, con test de equivalencia.

### 4.3. Lecciones de método

- **Medir mucho no dio resultados visibles.** La v14 acumuló preregistros, puertas y observadores sin producir mejoras claras. De ahí la ficha corta del laboratorio: una pregunta por experimento.
- **Los datos de diagnóstico no sirven de resultado.** La cifra de herencia 6,1 % → 19,8 % (semillas 2000–2019) se retiró por usar semillas ya vistas, y se sustituyó por 5,74 % → 22,31 % en la reserva.
- **Hay que verificar que la manipulación llega.** La manipulación del cortisol de H2 no llegaba al Tribunal (0 % de arbitrajes con 0,30, 0,60 y 0,90), así que el «sin efecto» anterior no valía. Tras corregirlo (100 %), se volvió a medir.
- **Un máximo no se compara con una media.** Se retiraron las comparaciones del mejor individuo con medias publicadas.
- **N = 1 y N = 5 no son resultados.** Se sustituyeron por 40 semillas y 50 partidas.
- **La colinealidad limita lo que se puede concluir.** «Mayor arousal» y «mayor producto» coinciden con el Tribunal en el 96,0 % y el 96,7 % de los latidos; el diseño no puede separarlos.

### 4.4. Reglas para una comparación justa con una línea base (propuestas para el laboratorio)

- **Mismo presupuesto de afinación** para IdA y para la línea base.
- **Mismo presupuesto de cómputo por decisión.** IdA tiene un plazo cooperativo por latido; la línea base no debe tener mucho más tiempo.
- **Misma información del mundo** para ambas.
- **Semillas de ajuste y de prueba separadas.**
- **Una sola cosa cambia entre las dos ramas.**
- **Veredicto escrito antes de ejecutar** y mantenido aunque el resultado no encaje.

---

## 5. Resultados por hipótesis

### 5.1. Hipótesis preregistradas (v12, Crafter, 40 semillas de reserva 3000–3039)

| Id | Hipótesis | Predicción a priori | Resultado | Veredicto |
| --- | --- | --- | --- | --- |
| **H1** | El Tribunal (A0) supera a árbitros más simples con los mismos órganos | Apoyada 0,25; refutada por A1 o A3 0,75 | Frente a jerarquías fijas: **+8,85** [+7,95; +9,68] frente a S1>S2>S3 y **+2,30** [+1,82; +2,80] frente a S3>S2>S1 (p Holm < 0,001). Frente a «mayor arousal»: +0,72 [+0,05; +1,52], p Holm = 0,116. Frente a «mayor producto»: +0,62 [−0,05; +1,43], p Holm = 0,147 | **Apoyada** frente a jerarquías; **no apoyada** frente a reglas de un solo criterio |
| **H7** | S2 (con su regla de sueño en Crafter) contribuye | Apoyada 0,05 | **+1,40** logros [+0,65; +2,23], p = 0,002; **−536** pasos vividos [−731; −345]; muertes por depredador 34/40 frente a 16/40 | **Apoyada, con un coste** |
| **H2** | Acoplar el cortisol al score mejora el rendimiento | Apoyada 0,35 | Entre −0,35 y +0,12 logros frente al cortisol dinámico; ninguna significativa tras Holm (p ≥ 0,19). El % de decisiones de S1 va de 32,7 (cortisol 0,05) a 38,7 (0,90) | **No apoyada** en logros; sí cambia la conducta |
| **Herencia** | Un arquetipo seleccionado mejora en semillas nuevas | — | Crafter Score poblacional 5,74 % → 22,31 %; +5,22 logros [+4,35; +6,03], p < 0,001 | **Apoyada** |
| **Herencia** | Los axiomas heredados (barrera de Weismann) aportan rendimiento | — | Con el mismo arquetipo: +0,00 [−0,07; +0,07]; 38 de 40 semillas iguales. Sin arquetipo: +0,40 [−0,05; +0,88], p = 0,123. Un placebo de 33 axiomas de otros mundos da el mismo resultado | **No apoyada** |

**Nota sobre el criterio preregistrado de H1.** El preregistro decía que H1 *se refuta* si cualquier árbitro simple iguala o supera al Tribunal (IC pareado que incluye el cero). Frente a «mayor arousal» y «mayor producto» el IC incluye el cero (tras Holm), de modo que, aplicado al pie de la letra, el criterio llevaría a considerar H1 refutada y a reformular el Tribunal como infraestructura de observabilidad, veto y trazabilidad, no como una ventaja heurística. Es una lectura mía del preregistro; el informe publicado la presenta como «apoyada frente a jerarquías, no apoyada frente a reglas simples».

**H1 en el nivel b de ablación** (el árbitro elige directamente): mismo patrón. +8,65 y +2,05 frente a jerarquías fijas; +0,53 [−0,15; +1,27] frente a «mayor arousal» y +0,42 [−0,25; +1,18] frente a «mayor producto», sin significación.

**Lectura de la herencia.** La evolución redescubre parámetros que también se pueden fijar a mano: el arquetipo «mediano» de la generación 8 rinde exactamente igual que el «récord» de la 12 (22,31 %), y el arquetipo de H1 fijado a mano da la misma media de logros (11,62). No es aprendizaje del árbol tecnológico, que está codificado en el nivel 3.

### 5.2. Estudio factorial de herencia en semillas de diagnóstico (2000–2019, retirado como resultado)

Se conserva como evidencia del proceso, no como resultado. Diseño 2×2 con controles placebo y mediano, N = 20.

| Condición | Crafter Score poblacional | Logros únicos | Logros (media) | Fitness (media) |
| --- | --- | --- | --- | --- |
| C1 arquetipo récord + axiomas récord | 19,58 | 16 | 11,15 | 65,91 |
| C2 arquetipo récord + axiomas vacíos | 19,79 | 16 | 11,25 | 65,84 |
| C3 arquetipo fundador + axiomas récord | 6,71 | 11 | 7,05 | 61,77 |
| C4 control negativo (fundador + vacíos) | 6,13 | 11 | 6,55 | 61,47 |
| C5 placebo (arquetipo récord + 33 axiomas placebo) | 19,79 | 16 | 11,25 | 65,84 |
| C6 linaje mediano G8 | 19,79 | 16 | 11,25 | 66,42 |

Efectos del análisis factorial: arquetipo +4,70 logros (p < 0,001), axiomas +0,50 (p = 0,47), interacción −0,60 (p = 0,54). Frente al control vacío, C1, C2, C5 y C6 dan +4,6 a +4,7 logros (IC95 % [3,2; 5,95], Cliff δ = 0,81, 18 victorias, 1 empate y 1 derrota en 20 semillas), y C3 solo +0,5 (IC [−0,15; 1,2]). **Conclusión idéntica a la de la reserva: el arquetipo importa, los axiomas no.**

### 5.3. Hipótesis diseñadas y no medidas

| Id | Hipótesis | Estado |
| --- | --- | --- |
| **H3** | El plazo acotado permite degradación elegante | Pendiente: la guillotina no se disparó en ningún episodio contado |
| **H4** | Adaptación a entornos cambiantes | Pendiente; el diseño que usaba Snake local se descartó |
| **H5** | Herencia de información no codificable a mano | Pendiente |
| **H6** | La plasticidad (TD(λ), Hebb) mejora el rendimiento | Pendiente: implementada, sin efecto demostrado |
| **H8** | Reutilización del core | Pendiente (dato previo: el mundo de ejemplo mínimo se añadió sin tocar los niveles 1 y 2) |
| **H9** | Arbitraje con presupuesto fuera de los juegos | Pendiente (opcional) |
| R2, R3, R6, R7 | Réplicas y análisis ampliados (R3 separaría A0 de las reglas simples; R7, réplicas independientes del linaje) | No realizados |

---

## 6. Resultados por mundo frente a diseños tradicionales

### 6.1. Ajedrez (N3, 50 partidas pareadas por rival, sin Ollama)

Línea base: jugador de 1 ply con la misma evaluación. Datos: `N3_ajedrez.csv`.

| Rival | IdA: puntuación (Wilson 95 %) | Línea base 1 ply | IdA − línea base (puntos por partida) |
| --- | --- | --- | --- |
| Minimax local nivel 1 | 0,97 [0,88; 0,99] | 0,51 | **+0,46** [+0,39; +0,53] |
| Minimax local nivel 2 | 0,99 [0,91; 1,00] | 0,47 | **+0,52** [+0,45; +0,59] |
| Minimax local nivel 3 (alfa-beta 3 ply) | 0,99 [0,91; 1,00] | 0,78 | **+0,21** [+0,14; +0,28] |
| Stockfish UCI_Elo 1320 | 0,09 [0,04; 0,20] | 0,06 | +0,03 [−0,06; +0,13] |
| Stockfish UCI_Elo 1500 | 0,02 [0,00; 0,11] | 0,02 | +0,00 [−0,04; +0,05] |

- Contra minimax nivel 3: **49 victorias, 1 tabla, 0 derrotas.** Contra Stockfish 1320: 4 V, 1 T, 45 D. Contra Stockfish 1500: 1 V, 0 T, 49 D.
- Ninguna partida llegó al tope de seguridad ni hubo sustituciones de Stockfish. **No se publica ningún ELO.**
- **Lectura honesta:** IdA mejora mucho sobre un jugador de 1 ply, así que su heurística táctica (huida de jaques, capturas favorables, centro, enroque) añade valor sobre una evaluación pura. Pero la línea base de 1 ply es débil: falta una línea base de 2 y 3 ply para separar el efecto de «mejor evaluación» del de «búsqueda». Contra un motor fuerte, IdA no se distingue de esa línea base.

### 6.2. Snake web (N2, 180 episodios frente a BFS, orden aleatorio, playsnake.org)

30 episodios por dificultad y agente, con un tope de 300 s por episodio. Sin censuras ni errores del sitio. Medido del 7 nov a las 23:52 al 8 nov a las 03:44.

| Dificultad | IdA − BFS en puntuación media (IC 95 %) | Veredicto |
| --- | --- | --- |
| Slug | −192,3 [−577,2; +217,5] | No concluyente (el IC incluye el 0) |
| Worm | −417,2 [−745,5; −90,3] | **IdA peor** |
| Python | −615,2 [−972,2; −258,2] | **IdA peor** |

- **Concurrencia declarada:** el estudio coincidió con las pruebas de arranque limpio (N8) desde el episodio 61. El signo se mantiene en los episodios 1–60 y 61–180 (`evidencias/N2_sensibilidad_concurrencia.txt`).
- Medición de una sola máquina y un solo día; el sitio puede cambiar. Snake en Linux no se ha probado.
- **Las cifras anteriores de Snake se retiraron** (sección 11).
- **Lectura honesta:** un buscador de rutas sencillo supera a IdA en Snake cuando la velocidad sube. El diseño orgánico no aporta ventaja aquí, y queda por diagnosticar por qué pierde (autoencierro, latencia, reglas de S1/S3).

### 6.3. Crafter (N1, 40 semillas de reserva 3000–3039)

- **No hay línea base tradicional.** Se compara el Tribunal con árbitros más simples (sección 5.1) y con variantes de IdA.
- **Acuerdo contrafactual:** «mayor arousal» y «mayor producto» habrían elegido lo mismo que A0 en el 96,0 % y el 96,7 % de los latidos. Esa colinealidad explica por qué H1 no puede separarlos.
- **Cuerpo simulado frente al juego:** la alimentación simulada se parece a la del juego (r = 0,90, desfase 0) y la vitalidad a la salud (r = 0,80), pero desplazada hacia abajo (sección 10).
- **La vista del agente es de 13×13**, no la estándar del benchmark. Por eso las cifras de Crafter Score no son comparables con la literatura, y todas las comparaciones publicadas son entre variantes de IdA con el mismo adaptador.

### 6.4. Mundo mínimo y mundo de archivos (Bosque)

- **Mundo mínimo:** con una semilla y 4 vidas por grupo, los individuos con experiencia viven más y comen menos setas tóxicas que sin ella. **Es una indicación, no una demostración** (palabras del propio manifiesto).
- **Mundo de archivos (Bosque):** sirve como entorno determinista de pruebas; las comparaciones de v14 allí son casi triviales porque el resultado es casi siempre el mismo.
- **Reutilización del core (H8, dato previo):** el mundo de ejemplo mínimo se añadió sin tocar los niveles 1 y 2.

---

## 7. Dónde el diseño orgánico mejoró, y con qué matices

Esta sección reúne los casos en que IdA obtuvo una ventaja medida. Cada uno lleva su matiz, porque casi ninguno prueba por sí solo que el diseño orgánico supere a uno tradicional bien hecho.

### 7.1. Ajedrez frente a un jugador de 1 ply (mejora clara)

- **Resultado:** +0,46, +0,52 y +0,21 puntos por partida frente a la línea base de 1 ply contra minimax de niveles 1, 2 y 3. Contra minimax 3, 49 victorias, 1 tabla y 0 derrotas.
- **Matiz 1:** la línea base de 1 ply es débil. No se midió 2 ply ni 3 ply con la misma evaluación, así que no se sabe cuánto de la mejora lo da el diseño orgánico y cuánto lo da simplemente buscar más.
- **Matiz 2:** el conocimiento táctico (huida de jaques, capturas favorables, centro, enroque) está codificado en el nivel 3, no aprendido.
- **Matiz 3:** contra Stockfish la ventaja desaparece (sección 8).
- **Pregunta abierta para el laboratorio:** ¿IdA con 1 ply y su arbitraje supera a un minimax de 2 ply con la misma evaluación?

### 7.2. Crafter: el Tribunal frente a jerarquías fijas

- **Resultado:** +8,85 logros frente a S1>S2>S3 y +2,30 frente a S3>S2>S1, con significación fuerte tras Holm.
- **Matiz:** una jerarquía fija es una línea base débil. Frente a reglas de un solo criterio («mayor arousal», «mayor producto»), la ventaja es de +0,72 y +0,62, no significativa tras la corrección. El acuerdo del 96 % impide saber si el arbitraje en sí aporta algo.
- **Lectura:** el arbitraje compite bien con reglas fijas de prioridad, pero no se ha demostrado que supere a una regla simple y bien elegida.

### 7.3. Crafter: S2 (H7), una mejora con coste

- **Resultado:** +1,40 logros por vida [+0,65; +2,23], p = 0,002.
- **Coste:** −536 pasos vividos [−731; −345]. Las muertes por depredador pasan de 16 a 34 de 40. S2 consigue más logros porque se arriesga más y muere antes.
- **Lectura:** es una mejora en «logros por vida» y un empeoramiento en «supervivencia». La métrica elegida decide quién gana.

### 7.4. Herencia: el arquetipo seleccionado

- **Resultado:** Crafter Score poblacional de 5,74 % a 22,31 % y +5,22 logros por vida (p < 0,001) en semillas de reserva.
- **Matiz 1:** el arquetipo mediano de la generación 8 rinde igual que el récord de la 12, de modo que seguir seleccionando no ayuda.
- **Matiz 2:** un arquetipo fijado a mano para H1 da la misma media de logros (11,62). La evolución redescubre parámetros que un diseñador podría fijar.
- **Matiz 3:** los axiomas heredados no aportan nada medible.
- **Matiz 4:** un solo linaje. Sin réplicas independientes (R7) no se sabe cuánta de esta mejora es casualidad del linaje.

### 7.5. v14: la experiencia activa durante la vida y entre vidas

El caso más próximo a «el orgánico mejoró algo en algún aspecto» en la v14.

- **Dentro de una vida (paso 2):** 578 episodios. Con experiencia activa, el signo del episodio acierta el 45,2 % de las veces, frente al 38,9 % de la base: **+6,3 puntos** [+1,5; +11,2]. Medido en 20 vidas (semillas 10–29) y 5 221 latidos.
- **Entre vidas (paso 0 de control):** con la huella de apertura, **+24 puntos** (IC +8 a +44); con la huella completa, **+29** (IC +8 a +45). La partida se juega distinta el 66,3 % de las veces frente al 37,1 % de la base con huella de apertura, y el 60,6 % con huella completa.
- **Matiz 1:** es una mejora en una métrica interna (acierto del signo del balance), no en el rendimiento del juego.
- **Matiz 2:** el efecto es modesto y el IC inferior (+1,5) está cerca del cero.
- **Matiz 3:** la diferencia entre vidas depende de la huella heredada, que no se ha comparado con una regla fijada a mano.

### 7.6. Otras señales débiles a favor

- **Mundo mínimo:** con experiencia, los individuos viven más y comen menos setas tóxicas (una semilla, 4 vidas por grupo).
- **Latencia y plazo:** la decisión cuesta 1,5–8 ms frente a plazos de 2 500–5 000 ms. Hay 84–97 % de margen y los 100 ms de guillotina nunca se usan. Es un buen dato de coste, pero no un resultado de rendimiento.
- **Trazabilidad:** el Tribunal deja un registro de qué árbitro decidió y por qué. Es una ventaja de observabilidad, no de rendimiento.

---

## 8. Dónde empató o empeoró

### 8.1. Snake frente a BFS

Con 180 episodios, IdA queda por debajo de BFS en Worm (−417,2) y Python (−615,2), y es no concluyente en Slug (−192,3, IC [−577,2; +217,5]). Un algoritmo clásico de búsqueda de rutas gana al diseño orgánico.

### 8.2. Ajedrez frente a Stockfish

Contra Stockfish 1320, 4 V, 1 T y 45 D (0,09 frente a 0,06 de la línea base). Contra 1500, 1 V y 49 D. Sin ventaja sobre la línea base de 1 ply.

### 8.3. Árbitros simples en Crafter

«Mayor arousal» y «mayor producto» igualan al Tribunal (IC incluye el cero tras Holm), con un 96 % de acuerdo.

### 8.4. Cortisol (H2)

Ningún efecto significativo en logros (−0,35 a +0,12; p Holm ≥ 0,19). La conducta cambia (más decisiones de S1 cuando sube el cortisol) pero no rinde.

### 8.5. Axiomas heredados

+0,00 [−0,07; +0,07]; 38 de 40 semillas iguales. Con el placebo de 33 axiomas, idéntico resultado.

### 8.6. Modo proactivo de la v14

El modo proactivo **empeora**: −5,8 puntos [−9,0; −3,1], con un acierto del 42,0 % frente al 47,8 %. La calibración alta (≥ 0,9) solo se da el 34 % de las veces. De 33 expectativas demostradas, 31 dejan de serlo.

### 8.7. Curiosidad

Cambio cero: 40 de 40 trayectorias idénticas. De 1 156 a 1 416 propuestas por conjunto, ninguna llega a ganar el arbitraje.

### 8.8. Lugar seguro

Sin ventaja: −0,14 [−0,45; +0,18].

### 8.9. Identidad y diferenciación entre individuos

El acuerdo entre individuos es alto: «todos se parecen». Correlación dentro de individuo r = −0,21, entre individuos r = −0,26, CCI = −0,14. No hay personalidad medible.

### 8.10. Vocabulario del observador

0 lagunas de vocabulario detectadas, así que no hay nada que corregir ahí.

### 8.11. Beber agua

Mejora el balance solo el 16 % de las veces (n = 1 332), por debajo de lo esperado.

---

## 9. La v14, pasos 0 a 3

### 9.1. Paso 0: observación sin cambiar la conducta

- **Amplitud:** sobra entre el 84 % y el 97 % de la amplitud disponible.
- **Latencia:** 1,5–8 ms por decisión frente a plazos de 2 500–5 000 ms. Los 100 ms de guillotina nunca se usan.
- **Alimentación del soma:** la mediana es 5,8 frente a 6–9 en el juego. El miedo está activo el 77 % del tiempo.
- **Episodios:** 270. El signo del balance acierta el 72 % de las veces frente al 39 % de la base (el índice de acierto dentro del conjunto, sin control de dificultad).

### 9.2. Paso 2: experiencia activa

Ver sección 7.5. Se midieron 578 episodios, con 45,2 % de acierto frente a 38,9 % (+6,3 [+1,5; +11,2]) en 20 vidas y 5 221 latidos.

### 9.3. Paso 3: tablas y observadores

- Hay tablas de expectativas por contexto y un bucle propio de S3 con 25,5 expectativas sin validar de media.
- Los observadores no alteran la trayectoria (22 de 22 idénticas).
- **Coste:** latido de Crafter 8,79 ms; observador mediana 0,42 ms, p95 0,95 ms y máximo 64 ms. Con el observador apagado el máximo fue 96 ms (27 latidos > 25 ms), de modo que los atípicos vienen del sistema, no del observador. Se aceptó el tope absoluto de latencia.

### 9.3 bis. Resultado general de la v14

Con todo activo: +6,3 puntos de acierto con experiencia activa; −5,8 con la función proactiva. La mayoría de módulos añadidos no tuvieron efecto medible. El balance es modesto y fue lo que motivó pasar a un laboratorio con preguntas más pequeñas.

---

## 10. Encargos E2 a E5

### 10.1. E2–E4: diagnóstico del cuerpo simulado

- **A1, saturación:** urgencia de S1 80,6 %, miedo 80,1 %, peligro de S1 100 % (binario), alimentación 47,6 %, vitalidad 35,2 %. Los indicadores se saturan y pierden resolución.
- **P1, lastre de carga:** 40,5 %, por debajo del umbral del 60 %. Con ello, la puerta de A1 se cierra sin A2.
- **Correlaciones:** alimentación frente a comida + bebida, r = 0,90; vitalidad frente a salud, r = 0,80.
- **Entropía de los indicadores:** 1,72 bits.
- **B, pesos 0,3/0,5/0,7:** cambio 0 en la decisión.

### 10.2. E5 (de mis notas, a verificar contra el informe)

> **Aviso:** esta subsección procede de mis notas de trabajo y no de la lectura directa del informe de E5. Las cifras exactas deben confirmarse adjuntando ese informe.

- **Cuello de botella del arbitraje:** en calma, S3 con objetivo gana el 96 % de los arbitrajes con gran margen; solo el 1,15 % de los latidos en calma dejan hueco a otro sistema.
- **Corrección de la carga falsa:** reduce el descenso inexplicado del 44,6 % al 15,5 % y el miedo del 74 % al 57 %.
- **Bloques planificados:** D (diagnóstico del arbitraje), E (corrección de la carga falsa), F (curiosidad con una regla nueva, condicionada a D) y G (tres observadores: G1 franja de peligro en la clave proactiva, G2 conocimiento formal legible, G3 balance con sed).

### 10.3. E6

Diseñado, no ejecutado. Es una de las tareas que se dieron por aparcadas al pasar al laboratorio.

---

## 11. Fallos, auditoría y cifras retiradas

### 11.1. Auditoría de la v12

Doce hallazgos. Los más relevantes:

- Un secreto en el repositorio de trabajo (clave de Gemini, ya revocada).
- Credenciales de PostgreSQL en el código.
- Autopoiesis activa por defecto.
- Fuga del sandbox del Bosque mediante `../`.
- Fallos silenciosos en el arnés y en Stockfish.
- Dos fórmulas distintas del Crafter Score.
- Cortisol de H2 que no llegaba al Tribunal.
- Mecanismos documentados pero no conectados.
- El linter detecta 14 de 23 evasiones.

### 11.2. Fe de erratas: cifras y afirmaciones retiradas

| Retirado | Motivo |
| --- | --- |
| ELO de ajedrez | Sin base estadística suficiente |
| Crafter Score 3,63 % | Fórmula inconsistente |
| Scores de un solo individuo (7,15 % G24, G15, etc.) | Máximo contra media, N = 1 |
| Comparaciones con PPO, Rainbow, DreamerV3 | No comparables (vista 13×13, sin protocolo) |
| Ajedrez 17V/2T/0D y datos G72–G81 | No existen |
| 0/0/15 contra Stockfish (N = 5) | Sustituido por 50 partidas pareadas |
| Snake «100 % supervivencia» y récords (1 400 pts, etc.) | No verificables |
| H2 «sin efecto» anterior | La manipulación no llegaba al Tribunal |
| Herencia 6,1 % → 19,8 % | Semillas de diagnóstico |
| Línea base a mano 19,4 % | No reproducible |
| «100 % agnóstico» | No cierto: el nivel 3 es específico de cada mundo |
| «Tiempo real» o «RTOS» | Solo plazo cooperativo |
| «Φ de Tononi» | Solo una métrica interna, sin relación con la teoría |

---

## 12. Matriz de mecanismos (N5)

| Mecanismo | Estado |
| --- | --- |
| Tribunal (A0–A7) | Activo y medido |
| Cortisol | Medido, nulo en logros |
| S2 y sueño | Medido (H7) |
| Φ | Solo métrica |
| Talamocortical, DMN, TD(λ), Hebb (solo actualiza en el Bosque), REM | Sin efecto medido |
| Guillotina de 100 ms | 0 disparos |
| Autopoiesis | Desactivada; 0 mutaciones en 240 episodios |
| SQLite WAL | Solo escritura |
| pgvector | No conectado |
| MCP Φ | Siempre 0 |
| Órgano LLM | Simulado |
| Lichess y visión ASCII | Inexistentes |

---

## 13. Hipótesis pendientes y situaciones por explorar

Situaciones en las que el diseño orgánico podría superar a uno tradicional y no se han medido:

- **Entornos cambiantes (H4).** Un cambio de reglas a mitad de vida podría favorecer la adaptación.
- **Presupuesto de tiempo variable (H3).** Degradación elegante con plazos recortados.
- **Información no codificable a mano (H5).** Herencia de rasgos que un diseñador no sabría escribir.
- **Experiencia entre vidas.** Modulación de candidatos existentes por la experiencia acumulada.
- **Conflictos entre objetivos.** Casos en que reglas simples de un solo criterio fallan (separar A0 de reglas simples en los latidos de desacuerdo, R3).
- **Reutilización entre mundos (H8).**

---

## 14. Plan de experimentos del laboratorio

Ordenados por valor frente a coste:

1. **Línea base tradicional de Crafter.** Una política escrita a mano con la misma información y el mismo presupuesto de afinación.
2. **Más líneas base de ajedrez:** 1, 2 y 3 ply con la misma evaluación.
3. **Diagnóstico de Snake:** por qué IdA pierde contra BFS (autoencierro, latencia, reglas de S1 y S3).
4. **R3:** separar A0 de las reglas simples en los latidos donde discrepan.
5. **H4:** cambio de entorno a mitad de vida.
6. **Herencia V5b entre vidas** y modulación de candidatos existentes por la experiencia.
7. **E6**, tal como estaba diseñado.
8. **R7:** réplicas independientes de linaje.

**Notas prácticas:**

- Usar las semillas 4000–4039 en las pruebas finales, porque las 3000–3039 ya se usaron.
- Arreglar antes el soma de Crafter (carga falsa y peligro binario; el balance ya incluía la sed).
- Una pregunta por experimento, ficha de cinco campos, veredicto escrito antes de ejecutar.

---

## 15. Amenazas a la validez y qué no se afirma

**No se afirma:**

- Consciencia ni Φ.
- Superioridad frente a PPO, Rainbow, DreamerV3 o un LLM.
- ELO de ajedrez.
- Tiempo real duro.

**Amenazas a la validez:**

- H1 se midió en un solo mundo y con un solo arquetipo (el preregistro pedía dos de tres mundos).
- Un único linaje evolutivo.
- Linter léxico, no semántico.
- Semillas 2000–2059 y 3000–3039 ya usadas.
- Ruido físico real: la reproducción es estadística, no exacta.
- Una máquina y un día en Snake, con concurrencia declarada.
- Las líneas base «tradicionales» son pocas y algunas débiles.

---

## 16. Fuentes y reproducción

**Ficheros de origen:** `RESULTADOS_Y_VERIFICACION.md`, `INFORME_FINAL.md`, `H1_H7_H2.md`, `REVISION_V13.md`, `REVISION_V14.md`, `ESTADO.md`, `GUIA_REVISION_V14.md`, informes de hitos (Crafter, Snake, Ajedrez), `experimento_factorial_heredabilidad_crafter.json/csv`, `MANIFIESTO.md` y `README.md`.

**Comandos de reproducción (según los informes):**

```
python analisis/run_experimento.py --hipotesis H1 --modo-ablacion nivel_a \
    --semillas 3000-3039 --out salidas/H1_crafter_nivel_a.csv
python -m v14.observar --out-dir ...
python -m v14.canario --referencia origin/v13
# Crafter reproducible: --semilla 108 --latidos 500 --aislar-ruido
```

**Aviso:** este dossier se compuso a partir de los informes y documentos adjuntos, no de los datos ni del código directamente. La subsección 10.2 (E5) procede de mis notas y debe verificarse. Las cifras citadas son las de los informes.
