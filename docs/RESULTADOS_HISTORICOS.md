# Compendio de Resultados Históricos y Evidencia Empírica

Este documento consolida la totalidad de las mediciones, contrastes cuantitativos y evaluaciones realizadas hasta la fecha en el proyecto (versiones 12, 13 y 14), depurado tras las auditorías de publicación.

---

## 1. Respuesta Global Honesta

A la pregunta central: ***¿Supera el diseño cognitivo orgánico de IdA al diseño tradicional en cada mundo?***, la respuesta basada estrictamente en los datos empíricos es:

1. **Existe ventaja táctica sobre agentes tradicionales muy débiles:** En Ajedrez, IdA supera de forma contundente a un minimax clásico de 1 nivel (1-ply) con evaluación pura de material.
2. **Empate ante motores tradicionales consolidados:** Contra Stockfish (UCI_Elo 1320 y 1500), IdA empata con la línea base de 1-ply: no muestra ninguna superioridad medible.
3. **El diseño tradicional supera a IdA en problemas de rutas bajo presión temporal:** En Snake, un buscador clásico de rutas (BFS) supera ampliamente a IdA en cuanto aumenta la velocidad del juego (Worm y Python).
4. **En Crafter, la superioridad depende de contra qué se compare:** El Tribunal supera con claridad a jerarquías fijas rígidas (S1>S2>S3), pero empata estadísticamente contra reglas simples de un solo criterio («mayor arousal» o «mayor producto»), debido a una colinealidad del 96 %.
5. **Muchos mecanismos bioinspirados no aportan rendimiento:** La herencia epigenética de axiomas, la modulación por cortisol, la plasticidad TD-hebbiana en Crafter, el ciclo REM y el bucle talamocortical no han demostrado impacto positivo medible sobre los logros o la supervivencia.

---

## 2. Tabla Maestra de Contrastes Empíricos

| # | Mundo | Comparación Evaluada | Resultado Numérico | Veredicto |
|---|---|---|---|---|
| **1** | **Ajedrez** | IdA vs. Línea base 1-ply (misma evaluación), contra Minimax local niveles 1, 2 y 3 | +0,46, +0,52 y +0,21 puntos por partida (puntuaciones torneo: 0,97, 0,99 y 0,99) | **Mejora clara** sobre 1-ply |
| **2** | **Ajedrez** | IdA vs. Línea base 1-ply, contra Stockfish UCI_Elo 1320 y 1500 | +0,03 [−0,06; +0,13] y +0,00 [−0,04; +0,05] puntos por partida | **Empate** (sin ventaja) |
| **3** | **Crafter** | Tribunal (A0) vs. Jerarquías fijas (S1>S2>S3 y S3>S2>S1) | +8,85 y +2,30 logros por vida (p Holm < 0,001) | **Mejora clara** sobre jerarquías |
| **4** | **Crafter** | Tribunal (A0) vs. Reglas simples («mayor arousal» y «mayor producto») | +0,72 [+0,05; +1,52] (p = 0,116) y +0,62 [−0,05; +1,43] (p = 0,147) | **Empate** (colinealidad 96 %) |
| **5** | **Crafter** | S2 activo (H7) vs. S2 neutro | +1,40 logros [+0,65; +2,23] (p = 0,002), pero −536 pasos de vida [−731; −345] | **Mejora con coste** |
| **6** | **Crafter** | Arquetipo seleccionado (G12/G8) vs. Arquetipo fundador | Crafter Score poblacional: 5,74 % → 22,31 %; +5,22 logros [4,35; 6,03] (p < 0,001) | **Mejora clara** (parámetros) |
| **7** | **Crafter** | Axiomas Weismann heredados vs. Memoria vacía (mismo arquetipo) | +0,00 logros [−0,07; +0,07]; 38 de 40 semillas idénticas | **Sin efecto** |
| **8** | **Crafter** | Cortisol dinámico acoplado a score vs. Cortisol fijo (H2) | Diferencia entre −0,35 y +0,12 logros (p Holm ≥ 0,19). | **Sin efecto en logros** |
| **9** | **Snake** | IdA vs. Agente tradicional BFS (búsqueda en anchura + flood-fill) | Diferencia media: Slug −192,3 [−577; +218]; Worm −417,2 [−746; −90]; Python −615,2 [−972; −258] | **Peor** en Worm y Python |
| **10** | **Mínimo** | Experiencia activa vs. Sin experiencia | Mayor longevidad y menor consumo de setas venenosas (4 vidas por grupo) | **Indicado** (señal preliminar) |
| **11** | **v14 (Crafter)** | Recuperación episódica parecida vs. Predicción basal | +6,3 puntos porcentuales de acierto de signo [+1,5; +11,2] (578 episodios, 20 vidas) | **Mejora pequeña** (predicción) |
| **12** | **v14 (Crafter)** | Expectativas proactivas vs. Predicción por frecuencia modal | −5,8 puntos porcentuales [−9,0; −3,1] (42,0 % vs 47,8 %) | **Peor** |

---

## 3. Desglose Detallado por Entorno

### 3.1. Ajedrez (Evaluación N3: 50 partidas pareadas por rival)
- **Condiciones:** IdA utiliza un sensor táctico en el nivel 3 que detecta jaques, capturas favorables, control central y enroque. Se enfrenta a 5 rivales con colores alternos y 4 medias jugadas aleatorias.
- **Rendimiento táctico:** Contra el oponente minimax de nivel 3 (alfa-beta a profundidad 3), IdA logró **49 victorias, 1 tabla y 0 derrotas**. La línea base tradicional de 1-ply obtuvo solo 0,78 puntos por partida, otorgando a IdA una ventaja neta de **+0,21 puntos/partida**.
- **Límite contra motores avanzados:** Contra Stockfish 1320 (4 V, 1 T, 45 D) y Stockfish 1500 (1 V, 0 T, 49 D), IdA no supera al jugador de 1-ply. 
- **Conclusión científica:** El diseño orgánico añade valor heurístico sobre una evaluación estática plana, pero no sustituye la profundidad de cálculo en el árbol de variantes.

### 3.2. Snake Web (Evaluación N2: 180 episodios en playsnake.org)

> [!NOTE]
> **Aviso ético y metodológico sobre E-09:** Los 180 episodios de E-09 se ejecutaron contra el servicio web público `playsnake.org` mediante automatización con Playwright. Por motivos éticos y de preservación de recursos de terceros, el laboratorio desaconseja lanzar ejecuciones automáticas masivas contra servidores públicos. Para cualquier réplica o contraste mecánico sobre el juego de Snake, debe emplearse el simulador local síncrono disponible en `experimentos/001-snake-diagnostico-bfs/simulador_snake.py`.

- **Condiciones:** 30 episodios por dificultad (Slug, Worm, Python) para IdA y para el agente tradicional BFS.
- **Resultados de puntuación:**
  - *Slug (baja velocidad):* IdA −192,3 pts (no concluyente, el IC del 95 % cruza el cero).
  - *Worm (media velocidad):* IdA **−417,2 pts** (pérdida significativa).
  - *Python (alta velocidad):* IdA **−615,2 pts** (pérdida severa).
- **Diagnóstico:** A mayor velocidad, la sobrecarga deliberativa de IdA (evaluación somática y arbitraje) y la tendencia al autoencierro por falta de horizonte espacial penalizan al organismo frente a un algoritmo determinista directo de inundación (flood-fill).

### 3.3. Crafter (Evaluación N1: 40 semillas de reserva 3000–3039)
- **Fidelidad somática:** Las constantes somáticas internas correlacionan estrechamente con la realidad del juego: alimentación simulada con comida + bebida (\(r = 0,90\)) y vitalidad con salud (\(r = 0,80\)).
- **Ablación del Tribunal (H1):** Supera con contundencia a una jerarquía ciega S1>S2>S3 (+8,85 logros), demostrando que la modulación por urgencia somática es vital para sobrevivir en un mundo multifactorial. Sin embargo, frente a reglas simples («mayor arousal» y «mayor producto»), el acuerdo contrafactual es del **96,0 %** y **96,7 %**, haciendo imposible distinguir estadísticamente sus decisiones.
- **El coste del sistema límbico (H7):** Activar el sistema límbico S2 y la pulsión exploratoria añade +1,40 logros desbloqueados por vida, pero reduce la vida en 536 pasos y duplica las muertes por depredador (34 frente a 16 sobre 40). **Es una compensación biológica real: mayor ambición conlleva menor supervivencia.**
- **Selección de Arquetipos vs. Axiomas:** La selección natural entre linajes eleva el Crafter Score de 5,74 % a 22,31 %. Sin embargo, el estudio factorial 2×2 demostró que **el 100 % del beneficio procede de los parámetros del arquetipo** (pesos de apertura, responsabilidad, neuroticismo y umbral de miedo). Los axiomas cognitivos heredados dieron exactamente \(+0,00\) logros de diferencia.

### 3.4. v14: Diagnóstico de la Experiencia Activa y Proactiva
- **Experiencia activa (paso 2):** En 578 episodios, recordar un episodio pasado parecido incrementó el acierto del signo somático en +6,3 puntos porcentuales. Sin embargo, dentro de una sola vida, el impacto en logros fue indetectable.
- **Cuello de botella del arbitraje:** El análisis de v14 reveló que en estados de calma somática, el sistema racional S3 gana el **96 %** de los arbitrajes con márgenes de ventaja inalcanzables para los otros sistemas. Cualquier mecanismo que introduzca candidatos nuevos (como curiosidad o recuerdos) es sistemáticamente ignorado por el Tribunal a menos que module directamente las puntuaciones de los candidatos existentes.
