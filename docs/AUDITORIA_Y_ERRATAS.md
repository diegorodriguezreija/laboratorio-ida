# Auditoría, Fe de Erratas y Matriz de Mecanismos

La credibilidad del Laboratorio IdA se fundamenta en la transparencia radical: declarar abiertamente qué falló en versiones anteriores, qué afirmaciones se han retirado formalmente y cuál es el estado técnico real de cada mecanismo.

---

## 1. Fe de Erratas: Afirmaciones y Cifras Retiradas

Las siguientes métricas y conclusiones formaron parte de versiones tempranas (v8 a v12) y **han sido revocadas formalmente** tras auditoría:

| Afirmación o Cifra Retirada | Causa de la Retirada | Corrección en el Laboratorio |
|---|---|---|
| **Cálculo de ELO en Ajedrez** | Muestra insuficiente y falta de calibración con oponentes oficiales. | Se mide exclusivamente puntuación de torneo (0, 0.5, 1) con intervalo de Wilson frente a rivales específicos. |
| **Crafter Score de 3,63 % o 7,15 % (G24/G15)** | Comparación del mejor individuo aislado (máximo) frente a medias poblacionales (\(N = 1\)), y fórmulas inconsistentes de Crafter Score. | Se utiliza exclusivamente la fórmula poblacional oficial (\(N \ge 20\) semillas en reserva) con media geométrica ajustada. |
| **Comparación con PPO, Rainbow o DreamerV3** | Protocolos incompatibles: el adaptador de IdA utiliza visión simbólica en cuadrícula 13×13, no los píxeles estándar 64×64 del benchmark oficial. | Retirada toda comparación con algoritmos externos de RL. Las comparaciones son solo frente a líneas base tradicionales o variantes internas. |
| **Ajedrez 17V / 2T / 0D (G72–G81)** | Registros de desarrollo no reproducibles bajo condiciones de control. | Sustituido por el torneo pareado N3 de 50 partidas por rival. |
| **Snake «100 % de supervivencia» y 1400 pts** | Datos anecdóticos no controlados estadísticamente. | Sustituido por el estudio N2 de 180 episodios pareados frente a BFS. |
| **«Herencia multiplica por 3 el rendimiento (6,1 % → 19,8 %)»** | Obtenido sobre semillas de diagnóstico (2000–2019) ya vistas durante el ajuste. | Sustituido por la evaluación en reserva 3000–3039 (5,74 % → 22,31 %). |
| **«El cortisol no tiene efecto (H2)» en v12** | La variable de cortisol calculada no se inyectaba en la función de ponderación del Tribunal por un error en el arnés. | Se corrigió el flujo de inyección y se volvió a medir en reserva (confirmando que no altera logros pero sí eleva decisiones de S1). |
| **«Totalmente agnóstico del mundo»** | El nivel 3 contiene código altamente especializado para cada entorno. | La pureza agnóstica se restringe formalmente a los niveles 1 y 2 (`base/nivel_1_core`, `base/nivel_2_sistemas`). |
| **«Tiempo real duro / RTOS»** | La guillotina de latido solo interrumpe en puntos `await` cooperativos de Python. | Se documenta como plazo cooperativo acotado, no tiempo real estricto. |
| **«Métrica de consciencia Φ de Tononi»** | El cálculo interno es una métrica heurística de integración de canales, sin respaldo formal de la teoría IIT. | Descartada cualquier pretensión de evaluar consciencia sintética. |

---

## 2. Los 12 Hallazgos de la Auditoría v12

Durante la auditoría formal previa a la reestructuración se identificaron y solventaron doce fallos críticos:

1. **Credenciales en histórico:** Detección de claves de prueba locales ya revocadas.
2. **Dependencia oculta de bases de datos:** Credenciales de PostgreSQL en scripts de desarrollo (eliminadas; el laboratorio no usa servicios externos).
3. **Autopoiesis no aislada:** La cirugía de código AST estaba activa por defecto en un runner (ahora desactivada de forma estricta).
4. **Fuga de sandbox en Bosque:** Escape posible mediante secuencias `../` en el árbol de archivos (bloqueado y comprobado por test).
5. **Fallos silenciosos en Stockfish:** Si el ejecutable del motor fallaba, la partida continuaba con movimientos nulos en lugar de abortar.
6. **Discrepancia en fórmulas de Crafter:** Existencia de dos funciones distintas para calcular el Crafter Score (unificada en una sola con test de equivalencia).
7. **Manipulación de cortisol rota en H2:** 0 % de los arbitrajes reflejaban el estrés forzado (corregido al 100 %).
8. **Mecanismos desconectados:** Varios componentes declarados en la arquitectura no participaban en el ciclo vital.
9. **Evasiones del linter de pureza:** El linter estático inicial pasaba por alto 9 de 23 formas de ofuscación de vocabulario de dominio (resuelto con análisis sobre el AST).
10. **Salidas en directorios de código:** Runners escribiendo logs en carpetas versionadas (redirigido a `IDA_OUT_DIR`).
11. **Aislamiento de licencia GPL:** Asegurar que `python-chess` no contamine componentes fuera de `base/nivel_3_componentes/mundos/mundo_ajedrez/`.
12. **Sobreajuste a semillas de prueba:** Uso indebido de semillas reservadas para afinar heurísticas.

---

## 3. Matriz de Estado Técnico de Mecanismos (N5)

| Mecanismo / Componente | Estado Real en el Código | Efecto Empírico Demostrado |
|---|---|---|
| **Tribunal Motor (A0–A7)** | Activo en el latido | Supera a jerarquías fijas (+8,85 logros); indistinguible de reglas simples (96 % colineal). |
| **Sistema Límbico S2** | Activo en el latido | Mejora logros (+1,40) a costa de menor supervivencia (−536 pasos). |
| **Regulación por Cortisol** | Activo en el latido | Altera la distribución de impulsos defensivos (+6 % en S1); nulo en logros. |
| **Memoria Activa (Episodios)** | Activo | +6,3 % de acierto en signo somático intra-vida; +24 % entre vidas. Nulo en logros directos. |
| **Memoria Proactiva (Expectativas)**| Activo | **Negativo**: −5,8 % de acierto frente a predecir la categoría modal más frecuente. |
| **Arquetipo y Carácter** | Activo | Fuerte: explica el salto de 5,74 % a 22,31 % en Crafter Score. |
| **Axiomas Weismann (Epigenética)** | Activo | **Nulo**: +0,00 logros frente a memoria vacía o placebo. |
| **Guillotina de 100 ms** | Activo (cooperativo) | Neutro: 0 disparos en condiciones normales (latidos entre 1,5 y 8 ms). |
| **Plasticidad TD(λ) / Hebbiana** | Activo | Sin efecto medido en supervivencia o rendimiento en juegos. |
| **Bucle Talamocortical y DMN** | Activo | Modula saliencia sensorial; sin efecto medido en desempeño de tareas. |
| **Ciclo de Sueño REM** | Activo | Consolida reglas simbólicas; sin impacto medido en el score. |
| **Autopoiesis por Cirugía AST** | Desactivado por defecto | 0 mutaciones en 240 episodios de prueba controlada. |
| **Persistencia SQLite WAL** | Activo | Operativo solo en modo escritura/auditoría. |
| **Almacén PgVector HNSW** | Desconectado | Preparado en el core, sin uso real en los experimentos. |

---

## 4. Qué NO se Afirma en este Repositorio

Para evitar cualquier tergiversación, el Laboratorio IdA declara formalmente que:
- **No se afirma consciencia sintética ni experiencia subjetiva.**
- **No se afirma equivalencia neurobiológica:** los términos anatómicos son metáforas de diseño bioinspirado.
- **No se afirma superioridad generalizada sobre el Aprendizaje por Refuerzo (RL) moderno ni sobre LLMs.**
- **No se afirma tiempo real estricto:** la ejecución se basa en asincronía cooperativa sobre Python.
