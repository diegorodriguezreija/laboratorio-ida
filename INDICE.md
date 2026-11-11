# Índice General de Experimentos y Evaluaciones

Historial oficial de contrastes empíricos realizados en el marco de IdA. Cada entrada cuenta con su hipótesis prefijada, condiciones pareadas y veredicto científico contrastado.

---

## 1. Definición de Veredictos
- **Mejora clara:** La variante bioinspirada supera a la línea base o condición de control con significación estadística tras corrección múltiple (\(p < 0,05\)) y tamaño de efecto relevante.
- **Mejora con coste:** Incremento en la métrica primaria pero con penalización severa en otra dimensión crítica (ej. más logros a costa de menor supervivencia).
- **Empate:** Intervalo de confianza de la diferencia centrado en cero o solapamiento contrafactual casi total (colinealidad).
- **Sin efecto:** Diferencia absoluta nula (\(\approx 0,00\)) o idéntica a una condición de control placebo.
- **Peor:** La línea base tradicional supera con significación estadística a la variante bioinspirada.
- **Indicado:** Señal observacional positiva pero en muestra reducida (\(N \le 5\)), pendiente de confirmación formal.

---

## 2. Registro Histórico Consolidado (v12, v13, v14)

| # | Fecha | Mundo | Condición de Prueba | Línea Base / Control | Métrica Primaria | Veredicto | Detalle |
|---|---|---|---|---|---|---|---|
| **E-01** | 2026-11 | **Ajedrez** | IdA (Sensor táctico S3) | Minimax tradicional 1-ply | Puntos de torneo vs. Minimax nivel 1, 2 y 3 (50 partidas) | **Mejora clara** | [+0,46, +0,52, +0,21 pts/partida](docs/RESULTADOS_HISTORICOS.md#31-ajedrez-evaluación-n3-50-partidas-pareadas-por-rival) |
| **E-02** | 2026-11 | **Ajedrez** | IdA (Sensor táctico S3) | Minimax tradicional 1-ply | Puntos de torneo vs. Stockfish 1320 y 1500 (50 partidas) | **Empate** | [+0,03 y +0,00 pts/partida](docs/RESULTADOS_HISTORICOS.md#31-ajedrez-evaluación-n3-50-partidas-pareadas-por-rival) |
| **E-03** | 2026-11 | **Crafter** | Tribunal Motor (A0) | Jerarquías fijas (S1>S2>S3 y S3>S2>S1) | Logros desbloqueados por vida (40 semillas reserva) | **Mejora clara** | [+8,85 y +2,30 logros, p < 0,001](docs/CATALOGO_HIPOTESIS.md#hipótesis-h1-superioridad-del-tribunal-motor-a0) |
| **E-04** | 2026-11 | **Crafter** | Tribunal Motor (A0) | Reglas simples (Mayor arousal A1, Mayor producto A3) | Logros desbloqueados por vida (40 semillas reserva) | **Empate** | [Acuerdo contrafactual del 96 %](docs/CATALOGO_HIPOTESIS.md#hipótesis-h1-superioridad-del-tribunal-motor-a0) |
| **E-05** | 2026-11 | **Crafter** | Sistema Límbico S2 activo (H7) | S2 neutro (Ablación afectiva) | Logros y pasos de vida (40 semillas reserva) | **Mejora con coste** | [+1,40 logros, pero −536 pasos](docs/CATALOGO_HIPOTESIS.md#hipótesis-h7-contribución-del-sistema-límbico-s2) |
| **E-06** | 2026-11 | **Crafter** | Arquetipo seleccionado (G12/G8) | Arquetipo fundador (G1) | Crafter Score poblacional (40 semillas reserva) | **Mejora clara** | [5,74 % → 22,31 % (+5,22 logros)](docs/CATALOGO_HIPOTESIS.md#hipótesis-de-herencia-y-barrera-de-weismann) |
| **E-07** | 2026-11 | **Crafter** | Axiomas cognitivos Weismann | Memoria vacía (mismo arquetipo) | Logros desbloqueados por vida (40 semillas) | **Sin efecto** | [+0,00 logros [−0,07; +0,07]](docs/CATALOGO_HIPOTESIS.md#hipótesis-de-herencia-y-barrera-de-weismann) |
| **E-08** | 2026-11 | **Crafter** | Cortisol dinámico acoplado a score | Cortisol fijo en valores extremos | Logros desbloqueados por vida (40 semillas reserva) | **Sin efecto** | [Diferencia entre −0,35 y +0,12 logros](docs/CATALOGO_HIPOTESIS.md#hipótesis-h2-regulación-por-cortisol-somático) |
| **E-09** | 2026-11 | **Snake** | IdA (Reactivo + Deliberativo) | Agente tradicional BFS (búsqueda rutas + flood-fill) | Puntuación media en playsnake.org (180 episodios) | **Peor** | [Worm −417 pts, Python −615 pts](docs/RESULTADOS_HISTORICOS.md#32-snake-web-evaluación-n2-180-episodios-en-playsnakeorg) |
| **E-10** | 2026-11 | **Mínimo** | Individuos con experiencia | Individuos sin experiencia (tabula rasa) | Supervivencia y consumo de toxinas (4 vidas) | **Indicado** | [Mayor vida y menos setas tóxicas](docs/RESULTADOS_HISTORICOS.md#34-mundo-mínimo-y-mundo-de-archivos-bosque) |
| **E-11** | 2026-11 | **Crafter** | Recuperación episódica parecida (v14) | Predicción basal sin memoria | Acierto de signo somático (578 episodios, 20 vidas) | **Mejora pequeña** | [+6,3 puntos porcentuales de acierto](docs/RESULTADOS_HISTORICOS.md#34-v14-diagnóstico-de-la-experiencia-activa-y-proactiva) |
| **E-12** | 2026-11 | **Crafter** | Expectativas proactivas S3 (v14) | Predicción basal por frecuencia modal | Acierto en validación de expectativas cognitivas | **Peor** | [−5,8 puntos porcentuales de acierto](docs/RESULTADOS_HISTORICOS.md#34-v14-diagnóstico-de-la-experiencia-activa-y-proactiva) |

---

## 3. Experimentos Nuevos del Laboratorio (En Curso y Planificados)

| # | Experimento | Estado | Mundo | Pregunta de Investigación | Veredicto |
|---|---|---|---|---|---|
| **001** | `001-snake-diagnostico-bfs` | **Completado** | Snake | ¿Qué mecanismo intrínseco de IdA explica su desventaja frente a BFS (auto-encierro, interferencia S1, u oscilación)? | **Empate (23-23-4)**. Sin latencia web, IdA empata con BFS (71,8 vs 71,2); la brecha de E-09 era por reloj de red. 0 % interferencia S1. [Ver RESULTADO.md](experimentos/001-snake-diagnostico-bfs/RESULTADO.md) |
| **002** | `002-crafter-ida-vs-voraz` | Planificado | Crafter | ¿Aporta el chasis bioinspirado de IdA una ventaja de supervivencia o progreso frente a un agente tradicional voraz con vista local idéntica? | *(Pendiente)* |
| **003** | `003-ajedrez-coste-afectivo` | Planificado | Ajedrez | Experimento de control: ¿cuál es el coste en centipeones (Stockfish) de la modulación afectiva en un entorno determinista sin homeostasis frente a Minimax puro (1-ply / 2-ply)? | *(Pendiente)* |
| **004** | `004-desacuerdos-tribunal-r3` | Planificado | Crafter | ¿Salva vidas el Tribunal A0 en el 4 % de bifurcaciones donde discrepa de A1 y A3? | *(Pendiente)* |
