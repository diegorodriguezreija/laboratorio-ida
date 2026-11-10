# Tablas de resultados (generadas)

Generado por `python analisis/generar_tablas.py` en el commit `85ca454`. No editar a mano: cualquier cambio se hace en el script o en los datos y se regenera. Decimales con coma.

## Crafter (N1: semillas de reserva 3000–3039, usadas una sola vez)

### H1 · Crafter · ablación nivel a

Fuente: [`analisis/resultados/N1_reserva_3000-3039/H1_crafter_nivel_a.csv`](../analisis/resultados/N1_reserva_3000-3039/H1_crafter_nivel_a.csv) · SHA-256 `fcc0ef4c39024baa…`

| Árbitro | N | Logros (media) | Crafter Score poblacional (%) | Pasos (mediana) |
|---|---:|---:|---:|---:|
| A0 Tribunal (ponderación arousal-confianza modulada por estrés) | 40 | 11,62 | 22,31 | 246 |
| A1 Mayor arousal | 40 | 10,90 | 20,86 | 250 |
| A2 Prioridad fija S1 > S2 > S3 | 40 | 2,77 | 1,42 | 283 |
| A3 Prioridad fija S3 > S2 > S1 | 40 | 9,32 | 16,66 | 210 |
| A4 Muestreo aleatorio ponderado por arousal | 40 | 9,62 | 15,48 | 240 |
| A7 Mayor producto arousal × confianza | 40 | 11,00 | 21,05 | 232 |

Comparación pareada por semilla del total de logros: A0 menos el árbitro alternativo.

| A0 frente a | N | Δ logros (A0 − alt.) | IC 95 % bootstrap | Wilcoxon p | p Holm | V/E/D (A0) | δ de Cliff |
|---|---:|---:|---|---:|---:|---|---:|
| A1 Mayor arousal | 40 | +0,72 | [+0,05, +1,52] | 0,058 | 0,116 | 19/11/10 | 0,17 |
| A2 Prioridad fija S1 > S2 > S3 | 40 | +8,85 | [+7,95, +9,68] | < 0,001 | < 0,001 | 39/0/1 | 0,98 |
| A3 Prioridad fija S3 > S2 > S1 | 40 | +2,30 | [+1,82, +2,80] | < 0,001 | < 0,001 | 32/8/0 | 0,50 |
| A4 Muestreo aleatorio ponderado por arousal | 40 | +2,00 | [+1,07, +2,92] | < 0,001 | < 0,001 | 27/2/11 | 0,47 |
| A7 Mayor producto arousal × confianza | 40 | +0,62 | [-0,05, +1,43] | 0,147 | 0,147 | 17/14/9 | 0,14 |

Acuerdo contrafactual (telemetría de los episodios A0): porcentaje de latidos en que el árbitro alternativo habría elegido el mismo comando que A0 ante los mismos candidatos.

Fuente: [`analisis/resultados/N1_reserva_3000-3039/H1_crafter_nivel_a_telemetria.csv.gz`](../analisis/resultados/N1_reserva_3000-3039/H1_crafter_nivel_a_telemetria.csv.gz) · SHA-256 `d57639c3657d900a…`

| Árbitro | Latidos | Acuerdo con A0 |
|---|---:|---:|
| A1 | 10935 | 96,0 % |
| A2 | 10935 | 73,7 % |
| A3 | 10935 | 92,9 % |
| A4 | 10935 | 86,2 % |
| A5 | 10935 | 73,7 % |
| A6 | 10935 | 67,5 % |
| A7 | 10935 | 96,7 % |

### H1 · Crafter · ablación nivel b

Fuente: [`analisis/resultados/N1_reserva_3000-3039/H1_crafter_nivel_b.csv`](../analisis/resultados/N1_reserva_3000-3039/H1_crafter_nivel_b.csv) · SHA-256 `a6bed21b3b77272a…`

| Árbitro | N | Logros (media) | Crafter Score poblacional (%) | Pasos (mediana) |
|---|---:|---:|---:|---:|
| A0 Tribunal (ponderación arousal-confianza modulada por estrés) | 40 | 11,43 | 21,85 | 249 |
| A1 Mayor arousal | 40 | 10,90 | 20,86 | 250 |
| A2 Prioridad fija S1 > S2 > S3 | 40 | 2,77 | 1,42 | 212 |
| A3 Prioridad fija S3 > S2 > S1 | 40 | 9,38 | 16,76 | 209 |
| A4 Muestreo aleatorio ponderado por arousal | 40 | 9,70 | 15,48 | 222 |
| A7 Mayor producto arousal × confianza | 40 | 11,00 | 21,05 | 230 |

Comparación pareada por semilla del total de logros: A0 menos el árbitro alternativo.

| A0 frente a | N | Δ logros (A0 − alt.) | IC 95 % bootstrap | Wilcoxon p | p Holm | V/E/D (A0) | δ de Cliff |
|---|---:|---:|---|---:|---:|---|---:|
| A1 Mayor arousal | 40 | +0,53 | [-0,15, +1,27] | 0,240 | 0,479 | 16/14/10 | 0,12 |
| A2 Prioridad fija S1 > S2 > S3 | 40 | +8,65 | [+7,75, +9,47] | < 0,001 | < 0,001 | 39/0/1 | 0,98 |
| A3 Prioridad fija S3 > S2 > S1 | 40 | +2,05 | [+1,60, +2,52] | < 0,001 | < 0,001 | 31/9/0 | 0,44 |
| A4 Muestreo aleatorio ponderado por arousal | 40 | +1,73 | [+0,60, +2,88] | 0,007 | 0,022 | 24/4/12 | 0,39 |
| A7 Mayor producto arousal × confianza | 40 | +0,42 | [-0,25, +1,18] | 0,451 | 0,479 | 14/16/10 | 0,09 |

Acuerdo contrafactual (telemetría de los episodios A0): porcentaje de latidos en que el árbitro alternativo habría elegido el mismo comando que A0 ante los mismos candidatos.

Fuente: [`analisis/resultados/N1_reserva_3000-3039/H1_crafter_nivel_b_telemetria.csv.gz`](../analisis/resultados/N1_reserva_3000-3039/H1_crafter_nivel_b_telemetria.csv.gz) · SHA-256 `0b2c9b08c517b08c…`

| Árbitro | Latidos | Acuerdo con A0 |
|---|---:|---:|
| A1 | 10860 | 96,7 % |
| A2 | 10860 | 73,3 % |
| A3 | 10860 | 93,9 % |
| A4 | 10860 | 86,3 % |
| A5 | 10860 | 73,3 % |
| A6 | 10860 | 69,3 % |
| A7 | 10860 | 97,0 % |

### H7 · Crafter · S2 activo frente a S2 neutralizado (tope 1500 pasos)

Fuente: [`analisis/resultados/N1_reserva_3000-3039/H7_crafter_1500p.csv`](../analisis/resultados/N1_reserva_3000-3039/H7_crafter_1500p.csv) · SHA-256 `17d8dd99d7641d1a…`

| Condición | N | Logros (media) | Pasos (mediana) | Muertes por depredador | Llegan al tope | Crafter Score poblacional (%) |
|---|---:|---:|---:|---:|---:|---:|
| S2 activo | 40 | 11,57 | 244 | 34/40 | 0/40 | 22,12 |
| S2 neutralizado | 40 | 10,18 | 393 | 16/40 | 18/40 | 16,70 |

| Variable (S2 activo − S2 neutralizado) | N | Δ media | IC 95 % bootstrap | Wilcoxon p | V/E/D |
|---|---:|---:|---|---:|---|
| Logros | 40 | +1,40 | [+0,65, +2,23] | 0,002 | 25/9/6 |
| Pasos vividos | 40 | -535,90 | [-731,00, -345,18] | < 0,001 | 12/1/27 |

### H2 · Crafter · cortisol fijo frente a dinámico (manipulación verificada, R1)

Fuente: [`analisis/resultados/N1_reserva_3000-3039/H2_crafter_sweep.csv`](../analisis/resultados/N1_reserva_3000-3039/H2_crafter_sweep.csv) · SHA-256 `3962fa925e1e57aa…`

| Condición | N | Logros (media) | % decisiones de S1 (media) | Pasos (mediana) |
|---|---:|---:|---:|---:|
| Soma_Dinamico | 40 | 11,53 | 34,6 | 243 |
| Soma_Cortisol_0.05 | 40 | 11,38 | 32,7 | 238 |
| Soma_Cortisol_0.30 | 40 | 11,18 | 34,9 | 233 |
| Soma_Cortisol_0.60 | 40 | 11,65 | 37,4 | 240 |
| Soma_Cortisol_0.90 | 40 | 11,55 | 38,7 | 246 |
| Soma_Invertido | 40 | 11,32 | 34,0 | 240 |

| Condición − dinámico (logros) | N | Δ media | IC 95 % bootstrap | Wilcoxon p | p Holm |
|---|---:|---:|---|---:|---:|
| Soma_Cortisol_0.05 | 40 | -0,15 | [-0,45, +0,12] | 0,304 | 0,911 |
| Soma_Cortisol_0.30 | 40 | -0,35 | [-0,68, -0,03] | 0,038 | 0,190 |
| Soma_Cortisol_0.60 | 40 | +0,12 | [-0,17, +0,42] | 0,400 | 0,911 |
| Soma_Cortisol_0.90 | 40 | +0,03 | [-0,30, +0,35] | 0,923 | 0,923 |
| Soma_Invertido | 40 | -0,20 | [-0,45, +0,03] | 0,118 | 0,470 |

### Herencia · Crafter · estudio factorial arquetipo × axiomas

Fuente: [`analisis/resultados/N1_reserva_3000-3039/experimento_factorial_heredabilidad_crafter.csv`](../analisis/resultados/N1_reserva_3000-3039/experimento_factorial_heredabilidad_crafter.csv) · SHA-256 `915b321d6b50de5f…`

| Condición | N | Logros (media) | Crafter Score poblacional (%) |
|---|---:|---:|---:|
| C1: Arq Récord + Axiomas Récord (2x2 Récord) | 40 | 11,62 | 22,32 |
| C2: Arq Récord + Axiomas Vacíos (Ablación Axiomas) | 40 | 11,62 | 22,31 |
| C3: Arq Fundador + Axiomas Récord (Ablación Arquetipo) | 40 | 6,80 | 7,60 |
| C4: Arq Fundador + Axiomas Vacíos (Control Negativo Base) | 40 | 6,40 | 5,74 |
| C5: Arq Récord + 33 Axiomas Placebo (Control Sham) | 40 | 11,62 | 22,31 |
| C6: Arq Mediano G8 + 23 Axiomas G8 (Control Mediano) | 40 | 11,62 | 22,31 |

| Condición − C4 control vacío (logros) | N | Δ media | IC 95 % bootstrap | Wilcoxon p | p Holm |
|---|---:|---:|---|---:|---:|
| C1_Record_Completo | 40 | +5,22 | [+4,35, +6,03] | < 0,001 | < 0,001 |
| C2_Solo_Arquetipo | 40 | +5,22 | [+4,35, +6,03] | < 0,001 | < 0,001 |
| C3_Solo_Axiomas | 40 | +0,40 | [-0,05, +0,88] | 0,123 | 0,123 |
| C5_Placebo_Sham | 40 | +5,22 | [+4,35, +6,03] | < 0,001 | < 0,001 |
| C6_Linaje_Mediano | 40 | +5,22 | [+4,35, +6,03] | < 0,001 | < 0,001 |

Axiomas con el mismo arquetipo (C1 − C2): Δ = +0,00 logros, IC 95 % [-0,07, +0,07], Wilcoxon p = 1,000; 38 de 40 semillas con el mismo número de logros.

### Autopoiesis en la configuración previa (P-3)

Fuente: [`analisis/resultados/P3_autopoiesis/P3_mutaciones_autopoiesis.csv`](../analisis/resultados/P3_autopoiesis/P3_mutaciones_autopoiesis.csv) · SHA-256 `456bbfa950e3a4cb…`

Protocolo H1 nivel A con la autopoiesis activa, semillas 2020–2059: 240 episodios; 0 con al menos una mutación; 0 mutaciones en total; 0 rollbacks.

## Snake web (N2)

### N2 · Snake web · IdA frente a baseline BFS

Fuente: [`analisis/resultados/N2_snake/N2_snake.csv`](../analisis/resultados/N2_snake/N2_snake.csv) · SHA-256 `7995539064b4256e…`

Episodios registrados: 180; con error del sitio o del navegador: 0.

| Dificultad | Agente | N | Puntuación media | Mediana | Muerte muro / cuerpo / censurado |
|---|---|---:|---:|---:|---|
| python | bfs | 30 | 2141,3 | 2052 | 8 / 22 / 0 |
| python | ida | 30 | 1526,2 | 1498 | 9 / 21 / 0 |
| slug | bfs | 30 | 1862,0 | 1858 | 10 / 20 / 0 |
| slug | ida | 30 | 1669,7 | 1738 | 11 / 19 / 0 |
| worm | bfs | 30 | 2014,3 | 2045 | 8 / 22 / 0 |
| worm | ida | 30 | 1597,2 | 1608 | 8 / 22 / 0 |

| Dificultad | Δ puntuación media (IdA − BFS) | IC 95 % bootstrap (no pareado) |
|---|---:|---|
| python | -615,2 | [-972,2, -258,2] |
| slug | -192,3 | [-577,2, +217,5] |
| worm | -417,2 | [-745,5, -90,3] |

## Ajedrez (N3)

### N3 · Ajedrez · IdA frente a baseline de 1 ply

Fuente: [`analisis/resultados/N3_ajedrez/N3_ajedrez.csv`](../analisis/resultados/N3_ajedrez/N3_ajedrez.csv) · SHA-256 `505ecedd083dec1c…`

Puntuación = (victorias + tablas/2) / partidas terminadas, con intervalo de Wilson al 95 %. Las partidas que llegan al tope de seguridad se cuentan aparte y no entran en la puntuación.

| Rival | Agente | Partidas | V / T / D | Tope | Puntuación | IC 95 % Wilson | Tablas por repetición | Sustituciones de Stockfish |
|---|---|---:|---|---:|---:|---|---:|---:|
| minimax_n1 | ida | 50 | 47 / 3 / 0 | 0 | 0,970 | [0,880, 0,993] | 3 | 0 |
| minimax_n1 | baseline_1ply | 50 | 6 / 39 / 5 | 0 | 0,510 | [0,376, 0,643] | 38 | 0 |
| minimax_n2 | ida | 50 | 49 / 1 / 0 | 0 | 0,990 | [0,911, 0,999] | 1 | 0 |
| minimax_n2 | baseline_1ply | 50 | 5 / 37 / 8 | 0 | 0,470 | [0,339, 0,605] | 33 | 0 |
| minimax_n3 | ida | 50 | 49 / 1 / 0 | 0 | 0,990 | [0,911, 0,999] | 1 | 0 |
| minimax_n3 | baseline_1ply | 50 | 28 / 22 / 0 | 0 | 0,780 | [0,648, 0,872] | 22 | 0 |
| stockfish_1320 | ida | 50 | 4 / 1 / 45 | 0 | 0,090 | [0,037, 0,201] | 1 | 0 |
| stockfish_1320 | baseline_1ply | 50 | 1 / 4 / 45 | 0 | 0,060 | [0,021, 0,162] | 4 | 0 |
| stockfish_1500 | ida | 50 | 1 / 0 / 49 | 0 | 0,020 | [0,004, 0,105] | 0 | 0 |
| stockfish_1500 | baseline_1ply | 50 | 0 / 2 / 48 | 0 | 0,020 | [0,004, 0,105] | 2 | 0 |

Comparación pareada por partida (misma apertura, color y semilla del rival): puntos de IdA menos puntos del baseline (1 victoria, ½ tablas, 0 derrota; tope = ½).

| Rival | N | Δ puntos medios | IC 95 % bootstrap | Wilcoxon p |
|---|---:|---:|---|---:|
| minimax_n1 | 50 | +0,460 | [+0,390, +0,530] | < 0,001 |
| minimax_n2 | 50 | +0,520 | [+0,450, +0,590] | < 0,001 |
| minimax_n3 | 50 | +0,210 | [+0,140, +0,280] | < 0,001 |
| stockfish_1320 | 50 | +0,030 | [-0,060, +0,130] | 0,432 |
| stockfish_1500 | 50 | +0,000 | [-0,040, +0,050] | 1,000 |

