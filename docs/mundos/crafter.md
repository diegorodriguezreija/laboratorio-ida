# Mundo Crafter

Estado: **activo**. Es el mundo principal de medición. La librería Crafter tiene licencia MIT (Hafner, 2021).

## Qué es

[Crafter](https://github.com/danijar/crafter) es un entorno 2D procedural con 22 logros (recoger madera, fabricar herramientas, comer, beber, dormir, defenderse). El adaptador (`nivel_3_componentes/mundos/mundo_crafter/adaptador_crafter.py`) traduce el mapa local a piezas con tensor 6D y los `V_Comando` a acciones de Crafter.

## Cómo ejecutarlo

```bash
pip install -e ".[crafter]"
python nivel_3_componentes/mundos/mundo_crafter/mundo_crafter_runner.py --modo fast --generaciones 10 --max-latidos 500 --seed 42
```

Opciones: `--gui` (visor Tkinter/Pillow), `--guardar-gif`, `--tabula-rasa`, `--habilitar-autopoiesis` (experimental). Las salidas van a `IDA_OUT_DIR/crafter/`. Duración medida en un clon limpio (Windows, 8 de noviembre de 2026): 38 s.

## Conocimiento de dominio codificado en el nivel 3

`componentes_crafter.py` contiene casi toda la competencia en el juego:

- **S1 (`CompCrafterS1`):** reflejos (evitar lava, huir de un depredador adyacente o atacarlo, beber si hay deshidratación) y movimiento hacia el recurso más saliente.
- **S2 (`CompCrafterS2`):** proposiciones fijas («la vaca es nutritiva», «el zombi es letal») y la regla de sueño circadiano.
- **S3 (`CompCrafterS3`):** el **árbol tecnológico codificado a mano** (madera → mesa → pico → piedra…) y búsqueda en anchura sobre la memoria alocéntrica.

Por tanto, IdA **no aprende** el árbol tecnológico. Lo que se mide es cómo se arbitra entre las propuestas de S1, S2 y S3.

## Qué percibe IdA en Crafter

IdA no ve la imagen del juego. El adaptador lee el **estado interno del mundo** (`env._world`) en un radio de 6 casillas alrededor del jugador, es decir, una ventana de **13×13** (`radio_vision=6`, `adaptador_crafter.py:56` y `188-192`). Es más de lo que muestra la vista estándar del juego, de 9×7 casillas (`view=(9, 9)` menos dos filas de inventario). El actuador también consulta ese estado para decidir dónde colocar un objeto (`adaptador_crafter.py:520-575`).

No cambia ninguna comparación publicada: todas las de Crafter (H1, H2, H7 y herencia) enfrentan variantes de IdA que usan el mismo adaptador y la misma ventana. Sí impide comparar su Crafter Score con el de agentes que aprenden de la imagen del juego.

## Corrección propia del motor

El orden de iteración de un `set()` del motor de Crafter introducía deriva no determinista. El adaptador lo sustituye por `_DeterministicChunkSet` (`adaptador_crafter.py:93`).

## Resultados

H1, H2, H7 y el estudio de herencia: [`../RESULTADOS_TABLAS.md`](../RESULTADOS_TABLAS.md), con su interpretación en [`../RESULTADOS_Y_VERIFICACION.md`](../RESULTADOS_Y_VERIFICACION.md).

## Coste de adaptación

556 líneas de adaptador, 921 de componentes de dominio y 1599 de runner y herramientas, en 5 ficheros ([`coste_adaptacion.csv`](../../analisis/resultados/coste_adaptacion.csv)). No se puede reconstruir si integrar Crafter exigió cambiar los niveles 1 y 2: el repositorio original integró varios mundos en un solo commit.

## Limitaciones

- Un solo arquetipo de referencia en H1.
- 500 pasos por episodio, salvo en H7.
- La supervivencia depende mucho de la regla de sueño (H7).
