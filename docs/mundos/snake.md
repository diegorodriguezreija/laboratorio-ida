# Mundo Snake web

Estado: **experimental**. Depende de un sitio de terceros (https://playsnake.org/) y de sus condiciones de uso. Si el sitio cambia o desaparece, este mundo deja de funcionar. No hay versión local (decisión D5).

## Qué es

El adaptador (`nivel_3_componentes/mundos/mundo_arcade_snake/adaptador_snake.py`) abre Chromium con Playwright en un hilo aparte, lee el DOM del tablero (21 × 15) y pulsa las flechas del teclado.

## Cómo ejecutarlo

```bash
pip install -e ".[snake]"
python -m playwright install chromium
python nivel_3_componentes/mundos/mundo_arcade_snake/mundo_snake_runner.py --generaciones 3 --dificultad gusano
```

Necesita Internet. Los tests que lo usen llevan la marca `network` y no forman parte de la CI obligatoria. Duración medida en un clon limpio (Windows, 8 de noviembre de 2026): 207 s para 3 generaciones (depende de cuánto viva la serpiente).

## Conocimiento de dominio codificado en el nivel 3

- **S1 (`CompSupervivenciaSnakeS1`):** no chocar en el siguiente tick, seguir el gradiente hacia la comida y no girar 180 grados.
- **S3 (`CompEstrategiaSnakeS3`):** *flood fill* del espacio libre desde cada dirección y veto de los caminos que llevan a un bolsillo cerrado. Un error anterior (el *flood fill* ignoraba el cuerpo) queda fijado por `test_snake_s3_flood_fill_cuerpo_y_veto_area`.

## Resultados

N2 (IdA frente a un baseline BFS): [`../RESULTADOS_TABLAS.md`](../RESULTADOS_TABLAS.md#snake-web-n2). Las cifras de versiones anteriores se retiraron (ver la fe de erratas).

## Coste de adaptación

375 líneas de adaptador, 374 de componentes y 431 de runner y herramientas ([`coste_adaptacion.csv`](../../analisis/resultados/coste_adaptacion.csv)).

## Limitaciones

- El tiempo real pasa por un navegador: la latencia de la página afecta al resultado.
- La causa de muerte se infiere de la última posición de la cabeza (borde del tablero = muro).
