# Resultados y verificación

Versión 12.0.0 · documento del 8 de noviembre de 2026.

**Fechas reales de medición** (de los metadatos de cada ejecución): Crafter N1, 7 de noviembre de 2026, de 23:19 a 23:52, código `n1-codigo-congelado` (commit `21dff6c`) · Ajedrez N3, 7 de noviembre de 2026, de 23:27 a 23:50, commit `0301666` · Autopoiesis P-3, 7 de noviembre de 2026, hasta las 23:54 · Verificación del cortisol R1, 7 de noviembre de 2026, 23:18 · Snake N2, del 7 de noviembre de 2026 a las 23:52 al 8 de noviembre a las 03:44, commit `fb32487`.

Las cifras de este documento salen de [`RESULTADOS_TABLAS.md`](RESULTADOS_TABLAS.md), que genera `python analisis/generar_tablas.py` a partir de los CSV versionados en `analisis/resultados/`; cada tabla allí cita su CSV y su SHA-256. Si una cifra de aquí no coincide con esa tabla, manda la tabla. Decimales con coma.

## 1. Método

- **Preregistro:** [`analisis/preregistro/H1_H7_H2.md`](../analisis/preregistro/H1_H7_H2.md) (H1, H7 y H2). El diseño de las demás hipótesis está en [`H3_H9_diseno.md`](../analisis/preregistro/H3_H9_diseno.md), sin ejecutar.
- **Semillas separadas:** desarrollo 0–999 (ajustes y comprobaciones), test 2000–2999 (fase de diagnóstico) y reserva 3000–3999. **Todas las cifras públicas de Crafter usan la reserva 3000–3039 una sola vez (N1).** Los resultados de diagnóstico (semillas 2000–2059) se conservan en `analisis/resultados/diagnostico/` como evidencia del proceso, no como resultado.
- **Diseño pareado:** todas las condiciones se evalúan en las mismas 40 semillas; se compara semilla a semilla.
- **Estadística** ([`analisis/estadistica.py`](../analisis/estadistica.py)): diferencia media con IC 95 % bootstrap (10 000 remuestreos), Wilcoxon de rangos con signo, test de signos, delta de Cliff y corrección de Holm-Bonferroni dentro de cada familia de comparaciones. En ajedrez, intervalo de Wilson para la puntuación.
- **Ruido:** el ruido «físico» del core es real (`os.urandom`) y está activo en todas las mediciones públicas, como en el uso normal. Con `--aislar-ruido` las trayectorias son reproducibles exactamente.
- **Configuración publicada:** autopoiesis desactivada, sin Ollama.

### Cómo reproducir

```bash
python analisis/run_experimento.py --hipotesis H1 --modo-ablacion nivel_a --semillas 3000-3039 --out salidas/H1_crafter_nivel_a.csv   # ~16 min
python analisis/run_experimento.py --hipotesis H1 --modo-ablacion nivel_b --semillas 3000-3039 --out salidas/H1_crafter_nivel_b.csv   # ~16 min
python analisis/run_experimento.py --hipotesis H2 --semillas 3000-3039 --out salidas/H2_crafter_sweep.csv                            # ~16 min
python analisis/run_experimento.py --hipotesis H7 --max-pasos 1500 --semillas 3000-3039 --out salidas/H7_crafter_1500p.csv           # ~8 min
python nivel_3_componentes/mundos/mundo_crafter/ejecutar_estudio_factorial_crafter.py --semillas 3000-3039                           # ~16 min
python nivel_3_componentes/mundos/mundo_ajedrez/medir_ajedrez.py --partidas 50                                                       # ~23 min, necesita IDA_STOCKFISH_PATH
python analisis/medir_snake.py --episodios 30 --max-segundos 300                                                                      # horas, necesita Internet
python analisis/generar_tablas.py
```

Tiempos medidos el 7 de noviembre de 2026 en un portátil con Windows 10 y 4 núcleos, con tres procesos en paralelo. Con ruido activo la reproducción es **estadística**, no exacta: en el estudio factorial, dos condiciones que deberían comportarse igual (C1 y C2) coincidieron en 38 de 40 semillas.

## 2. Hipótesis

| Id | Hipótesis | Veredicto | Efecto (IC 95 %) | N | Datos |
|---|---|---|---|---|---|
| H1 | En Crafter, el Tribunal (A0) supera a jerarquías fijas | **Apoyada** | +8,85 logros frente a S1 > S2 > S3 [+7,95; +9,68]; +2,30 frente a S3 > S2 > S1 [+1,82; +2,80]; p Holm < 0,001 | 40 semillas | [`H1_crafter_nivel_a.csv`](../analisis/resultados/N1_reserva_3000-3039/H1_crafter_nivel_a.csv) |
| H1 | El Tribunal supera a «mayor arousal» o a «mayor producto arousal × confianza» | **No apoyada** (no equivale a «sin efecto») | +0,72 [+0,05; +1,52], p Holm = 0,116; +0,62 [−0,05; +1,43], p Holm = 0,147. El efecto puede ser pequeño pero real; por la colinealidad (eligen lo mismo que A0 en el 96,0 % y el 96,7 % de los latidos), este diseño no puede separarlos | 40 | ídem |
| H7 | S2 (con su regla de sueño en Crafter) cambia resultados | **Apoyada, con un coste** | +1,40 logros [+0,65; +2,23], p = 0,002; −536 pasos vividos [−731; −345]; muertes por depredador 34/40 frente a 16/40 | 40 | [`H7_crafter_1500p.csv`](../analisis/resultados/N1_reserva_3000-3039/H7_crafter_1500p.csv) |
| H2 | Fijar el cortisol (manipulación verificada) cambia los logros | **No apoyada** | Diferencias entre −0,35 y +0,12 logros frente al cortisol dinámico; ninguna significativa tras Holm (p ≥ 0,19). Sí cambia la conducta: el % de decisiones de S1 va de 32,7 (cortisol 0,05) a 38,7 (0,90) | 40 | [`H2_crafter_sweep.csv`](../analisis/resultados/N1_reserva_3000-3039/H2_crafter_sweep.csv) |
| Herencia | Un arquetipo seleccionado mejora Crafter en semillas nuevas | **Apoyada** | Crafter Score poblacional 5,74 % → 22,31 %; +5,22 logros [+4,35; +6,03], p < 0,001 | 40 | [`experimento_factorial_…csv`](../analisis/resultados/N1_reserva_3000-3039/experimento_factorial_heredabilidad_crafter.csv) |
| Herencia | Los axiomas heredados (barrera de Weismann) aportan rendimiento | **No apoyada** | Con el mismo arquetipo: +0,00 logros [−0,07; +0,07]; 38 de 40 semillas iguales. Sin arquetipo: +0,40 [−0,05; +0,88], p = 0,123 | 40 | ídem |
| H3 | El plazo acotado permite degradación elegante | Pendiente | La guillotina no se disparó en ningún episodio contado | — | diseño |
| H4 | Adaptación a entornos cambiantes | Pendiente | — | — | diseño |
| H5 | Herencia de información no codificable a mano | Pendiente | — | — | diseño |
| H6 | La plasticidad (TD(λ), Hebb) mejora el rendimiento | Pendiente | Implementada, sin efecto demostrado | — | diseño |
| H8 | Reutilización del core | Pendiente (dato previo) | El mundo de ejemplo mínimo se añadió sin tocar los niveles 1 y 2 | — | `coste_adaptacion.csv` |
| H9 | Arbitraje con presupuesto fuera de los juegos | Pendiente (opcional) | — | — | diseño |

**Lectura de la herencia:** la evolución redescubre parámetros que también se pueden fijar a mano. El arquetipo «mediano» de la generación 8 rinde exactamente igual que el «récord» de la 12 (22,31 %), y el arquetipo de H1, fijado a mano, da la misma media de logros (11,62). No es aprendizaje del árbol tecnológico, que está codificado en el nivel 3.

**H1 en el nivel B de ablación** (el árbitro elige directamente, sin las reglas de desesperación ni de veto): mismo patrón. Frente a jerarquías fijas +8,65 y +2,05; frente a «mayor arousal» +0,53 [−0,15; +1,27] y frente a «mayor producto» +0,42 [−0,25; +1,18], sin significación.

## 3. Resultados por mundo

### Crafter
Tablas completas, con comando, CSV y SHA-256: [`RESULTADOS_TABLAS.md`](RESULTADOS_TABLAS.md#crafter-n1-semillas-de-reserva-30003039-usadas-una-sola-vez). Incluyen el acuerdo contrafactual: «mayor arousal» y «mayor producto» habrían elegido lo mismo que A0 en el 96,0 % y el 96,7 % de los latidos. Esa colinealidad explica por qué H1 no puede separarlos.

### Ajedrez (N3)
50 partidas pareadas por rival (aperturas aleatorias de 4 medias jugadas, colores alternos), sin Ollama, frente a un baseline de 1 ply con la misma evaluación:

| Rival | IdA: puntuación (Wilson 95 %) | Baseline 1 ply | IdA − baseline (puntos/partida) |
|---|---|---|---|
| Minimax local nivel 1 | 0,97 [0,88; 0,99] | 0,51 | +0,46 [+0,39; +0,53] |
| Minimax local nivel 2 | 0,99 [0,91; 1,00] | 0,47 | +0,52 [+0,45; +0,59] |
| Minimax local nivel 3 (alfa-beta 3 ply) | 0,99 [0,91; 1,00] | 0,78 | +0,21 [+0,14; +0,28] |
| Stockfish UCI_Elo 1320 | 0,09 [0,04; 0,20] | 0,06 | +0,03 [−0,06; +0,13] |
| Stockfish UCI_Elo 1500 | 0,02 [0,00; 0,11] | 0,02 | +0,00 [−0,04; +0,05] |

Ninguna partida llegó al tope de seguridad y no hubo sustituciones de Stockfish. No se publica ningún ELO. Datos: [`N3_ajedrez.csv`](../analisis/resultados/N3_ajedrez/N3_ajedrez.csv).

### Snake web (N2)

30 episodios por dificultad del sitio (Slug, Worm, Python) y agente, 180 en total, en orden aleatorio. IdA usa el core con los componentes de Snake y un arquetipo fijo, sin axiomas heredados ni autopoiesis. El baseline BFS sigue el camino más corto a la comida y comprueba el espacio libre con *flood fill*. No hay tope de latidos; el tope de seguridad de 300 s por episodio no se alcanzó nunca y no hubo errores del sitio ni del navegador.

| Dificultad | IdA: puntuación media | BFS: puntuación media | IdA − BFS (IC 95 % bootstrap, no pareado) |
|---|---:|---:|---|
| Slug | 1669,7 | 1862,0 | −192,3 [−577,2; +217,5] |
| Worm | 1597,2 | 2014,3 | −417,2 [−745,5; −90,3] |
| Python | 1526,2 | 2141,3 | −615,2 [−972,2; −258,2] |

**IdA puntúa menos que el baseline BFS** en Worm y Python; en Slug la diferencia (−192) tiene un intervalo que incluye el 0. Causas de muerte parecidas en ambos agentes (sobre todo choques con el propio cuerpo). Tablas completas: [`RESULTADOS_TABLAS.md`](RESULTADOS_TABLAS.md#snake-web-n2). Datos: [`N2_snake.csv`](../analisis/resultados/N2_snake/N2_snake.csv).

**Concurrencia declarada:** desde el episodio de orden 61 (8 de noviembre, 01:04) coincidieron en la misma máquina las dos pruebas de arranque limpio N8, que ejecutan Crafter, Ajedrez y Snake ([`aviso_concurrencia.txt`](../analisis/resultados/N2_snake/aviso_concurrencia.txt)). Como el orden es aleatorio, afecta a los dos agentes. La diferencia es negativa en las tres dificultades tanto en los episodios 1–60 como en los 61–180, con intervalos más anchos por el menor tamaño, y el ritmo medio de latidos por segundo es parecido en ambas ventanas (IdA 10,9 y 9,9; BFS 9,8 y 10,5). No se repitió la medición.

## 4. Resultados negativos

- **No se ha demostrado que el Tribunal supere a reglas simples de un solo criterio.** Frente a «mayor arousal» y «mayor producto arousal × confianza», las diferencias son pequeñas y no significativas tras Holm. «No apoyada» no equivale a «sin efecto»: el efecto puede ser pequeño pero real, y como los tres árbitros coinciden en ~96 % de las decisiones, este diseño no tiene potencia para separarlos. Hace falta un diseño que provoque desacuerdos (por ejemplo, R3: perturbar el arousal).
- **La modulación por cortisol no cambia los logros**, ni siquiera tras verificar que el valor fijado llega al Tribunal (R1). Cambia el reparto de decisiones, no el resultado.
- **Los axiomas heredados no aportan nada** medible; un placebo de axiomas de otros mundos da el mismo resultado.
- **Contra Stockfish, IdA no se distingue de un baseline de 1 ply.**
- **En Snake, IdA puntúa menos que un baseline BFS sencillo** en dos de las tres dificultades (N2).
- **TD(λ) y Hebb:** implementados, sin efecto demostrado (H6 pendiente). En Crafter y Ajedrez, Hebb ni siquiera actualiza pesos.

## 5. Matriz mecanismo documentado ↔ conectado (N5)

Recuento real de invocaciones en episodios cortos de cada mundo ([`N5_mecanismos_conectados.csv`](../analisis/resultados/N5_mecanismos_conectados.csv), `python analisis/n5_mecanismos_conectados.py`):

| Mecanismo | Implementación | Invocado en | Efecto | Estado y acción |
|---|---|---|---|---|
| Arbitraje del Tribunal | `arbitros.py` (A0) | Todos los mundos, cada latido | Medido (H1) | Activo, efecto medido |
| Modulación por cortisol | `arbitros.py:83-100` | Todos | Medido: no cambia logros (H2) | Activo, efecto medido (nulo en logros) |
| S2 y regla de sueño | `s2_limbico.py`, `componentes_crafter.py` | Todos | Medido (H7) | Activo, efecto medido |
| Métrica de integración («Φ») | `calculadoras_estructurales.py` | Todos, tras decidir | No interviene en la decisión | Solo métrica; se renombra en la documentación como «métrica de integración inspirada en IIT» |
| Bucle talamocortical | `consciencia_talamo_dmn.py` | Todos | No medido | Activo, efecto no medido |
| DMN | `consciencia_talamo_dmn.py` | Todos | No medido | Activo, efecto no medido |
| TD(λ) | `sistema_base.py:86` | Todos (≈3 por latido) | No medido | Activo, efecto no medido (H6) |
| Hebb | `plasticidad_td_hebbiana.py` | Actualiza solo en Bosque (0 en Crafter y Ajedrez) | No medido | Activo, efecto no medido; documentado |
| Sueño REM | `ciclo_sueno_rem.py` | Crafter y Ajedrez | No medido por separado | Activo, efecto no medido |
| Guillotina | `sistema_base.py:106` | Comprobada siempre; 0 disparos | No medido | Plazo cooperativo; H3 pendiente |
| Autopoiesis AST | `autopoiesis_ast.py` | Desactivada por defecto; 0 mutaciones en 240 episodios con la configuración anterior | — | Experimental, desactivada |
| SQLite WAL | `motor_sqlite_wal.py` | Escribe en Crafter y Ajedrez; nunca se lee | — | Activo solo escritura; documentado |
| pgvector / almacén vectorial | `motor_pgvector.py`, `nivel_0_demiurgo/` | Se consulta (vacío); nunca se escribe; sin driver de PostgreSQL | — | Preparado, no conectado; documentado, no implementado |
| MCP | `servidor_mcp_telemetria.py` | Solo en la demo | — | En proceso, sin red. `ida://fenomenologia_phi` devuelve 0 siempre (lee un atributo que nunca se asigna); documentado |
| Telemetría contrafactual | `tribunal_motor.py` | Todos | Instrumentación | Activo |
| Órgano «imaginación LLM» | `comp_imaginacion_llm.py` | Solo en la demo | — | Simulado (no hay LLM) |
| Ollama | `componentes_ajedrez.py` | Opcional | No medido | Opcional; mediciones sin Ollama |
| Modo Lichess | `adaptador_ajedrez.py` | — | — | No implementado |
| Visión ASCII | — | — | — | No existe en el código; se retira de la documentación |

## 6. Pruebas, linter y entorno (N6–N8)

- **Tests (Windows, Python 3.11.9):** 86 superados y 1 omitido (necesita un Stockfish local; pasa con `IDA_STOCKFISH_PATH_TEST`). En la CI (GitHub Actions, Ubuntu y Windows con Python 3.11 y 3.12) pasan 84 y se omiten 2 en cada trabajo: el que necesita Stockfish y el del baseline BFS de Snake, porque la CI no instala Playwright. Los tests marcados `network` no se ejecutan en la CI.
- **Cobertura del linter:** detecta 14 de 23 fragmentos de evasión ([`N7_cobertura_linter.csv`](../analisis/resultados/N7_cobertura_linter.csv)); detalle en [`ARQUITECTURA.md`](ARQUITECTURA.md#5-el-linter-como-función-de-aptitud-arquitectónica).
- **Prueba metamórfica:** renombrar todos los identificadores del mundo de ejemplo con 3 vocabularios produce la misma trayectoria latido a latido (60 latidos, ruido aislado).
- **Arranque limpio desde un clon (N8):** hecho en Windows el 8 de noviembre de 2026: instalación, tests, demo, ejemplo mínimo y los tres mundos terminan con código 0 (duraciones en el README). La primera pasada destapó dos fallos (raíz del Bosque aceptada dentro de un clon en el temporal y runners que salían con código 0 ante un error crítico), corregidos antes de la segunda. En Linux, el arranque limpio lo cubre la CI (instalación y tests).

## 7. Fe de erratas

Se retiran estas cifras y afirmaciones de versiones anteriores del proyecto:

| Afirmación anterior | Motivo | Sustituida por |
|---|---|---|
| ELO estimado para el ajedrez | Derivado de 5 partidas por nivel | Ningún ELO; puntuación con Wilson sobre 50 partidas (N3) |
| Crafter Score de 3,63 % | No reproducible; coexistía con otra cifra para el mismo concepto | Una sola función, con test (N4) |
| Scores de un solo individuo como resultado | N = 1 | Crafter Score poblacional sobre 40 semillas |
| Comparaciones de un «récord» con medias publicadas de PPO, Rainbow o DreamerV3 | Comparar un máximo con medias no es válido, y los entornos no eran comparables | Ninguna comparación con agentes de RL |
| Ajedrez: 17 V / 2 T / 0 D frente al nivel 3 | Siempre con blancas y sin variar aperturas | 49 V / 1 T / 0 D con aperturas aleatorias y colores alternos (N3) |
| Ajedrez: datos G72–G81 | No existen en ningún fichero | Retirados |
| Ajedrez: 0 V / 0 T / 15 D frente a Stockfish 1320–1500 | N = 5 por nivel | 4 V / 1 T / 45 D (1320) y 1 V / 0 T / 49 D (1500), N = 50 |
| Snake: «100 % de supervivencia», récords por generación y causas de muerte | Bugs del *flood fill* y de la lectura de la causa de muerte; tope de latidos | Re-medición N2 |
| H2: «el cortisol no tiene efecto» | El valor fijado no llegaba al Tribunal (R1) | H2 re-medida con la manipulación verificada |
| Herencia: 6,1 % → 19,8 % (semillas 2000–2019) | Semillas de test ya usadas para diagnosticar | 5,74 % → 22,31 % (semillas de reserva 3000–3039) |
| Baseline fijado a mano del 19,4 % | No re-medido en esta versión | Retirado. La comparación equivalente en semillas de reserva es H1, cuyo arquetipo está fijado a mano: 11,62 logros de media con A0, igual que el arquetipo seleccionado del estudio factorial (C2, 11,62; Crafter Score 22,31 %) |
| «100 % agnóstico al dominio» | El linter es léxico | Cobertura medida (sección 6) |
| «Tiempo real» o «RTOS» | El plazo es cooperativo | «Plazo cooperativo» |
| Φ de Tononi / consciencia | Es una métrica inspirada en IIT, no la Φ de Tononi | «Métrica de integración inspirada en IIT» |

## 8. Hallazgos de la auditoría (7 de noviembre de 2026)

Encontrados al preparar esta versión, en este orden:

1. Un fichero de configuración local con un secreto estaba versionado en el repositorio de trabajo. No forma parte de este repositorio, que se publica sin historial previo.
2. Credenciales de ejemplo de PostgreSQL en claro y el puerto expuesto a todas las interfaces → variables de entorno y `127.0.0.1`.
3. La autopoiesis estaba activa en todos los runners → desactivada por defecto (no llegó a mutar nada en el protocolo H1).
4. Los runners escribían dentro de las carpetas de código y uno sobrescribía un fichero que leía un test → `IDA_OUT_DIR`.
5. `scipy` faltaba en las dependencias.
6. **Fuga del sandbox del Bosque:** un objetivo `../fichero` permitía truncar o borrar fuera del bioma (comprobado con un test que falla con el código anterior).
7. El harness terminaba sin error con mundos no implementados; el ajedrez sustituía Stockfish en silencio.
8. Dos copias de la fórmula del Crafter Score → una sola función.
9. **La manipulación de cortisol de H2 no llegaba al Tribunal** ([`R1_manipulacion_cortisol/`](../analisis/resultados/R1_manipulacion_cortisol/)).
10. Mecanismos documentados que no están conectados: memoria vectorial nunca escrita, SQLite nunca leída, Hebb inactivo en dos mundos, MCP con Φ siempre 0, órgano LLM simulado, modo Lichess y visión ASCII inexistentes.
11. El linter no detecta 9 de 23 formas de evasión.
12. Todo lo que importa python-chess se aisló en su carpeta GPL, con un test.

## 9. Limitaciones

- H1 está medida en un solo mundo (Crafter) y con un solo arquetipo.
- El conocimiento de los juegos está codificado en el nivel 3; IdA no aprende Crafter, Snake ni Ajedrez desde cero.
- Un solo linaje evolutivo; no hay réplicas independientes (R7 no realizado).
- El linter es léxico.
- Las semillas 2000–2059 se usaron para diagnosticar; las 3000–3039 ya se han usado y no deben reutilizarse para afirmaciones nuevas.
- Ruido físico activo: los resultados se reproducen estadísticamente, no exactamente.

## 10. Qué no se afirma

Consciencia ni «Φ de Tononi» · emergencia de inteligencia · récords o superioridad frente a agentes de aprendizaje por refuerzo o cualquier especialista · un ELO · que IdA aprenda el árbol tecnológico de Crafter · ventaja sobre los LLM (no se ha comparado) · tiempo real duro · «100 % agnóstico» sin el alcance del linter · adaptación a entornos cambiantes (H4 no medida).
