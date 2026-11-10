# Mundo Ajedrez

Estado: **activo** en modo local. Licencia de esta carpeta: **GPL-3.0-or-later**, porque importa python-chess (ver [`NOTICE`](../../NOTICE)). El modo «lichess» está declarado pero **no implementado**.

## Qué es

Partidas locales contra un rival minimax propio (niveles 0–3; el 3 es alfa-beta a 3 ply) o contra Stockfish con fuerza limitada (`--elo`). Las reglas las aplica python-chess.

## Cómo ejecutarlo

```bash
pip install -e ".[ajedrez]"
python nivel_3_componentes/mundos/mundo_ajedrez/mundo_ajedrez_runner.py --modo fast --partidas 5 --dificultad 3 --sin-ollama
```

Stockfish no se distribuye: descárgalo y define `IDA_STOCKFISH_PATH`. Si pides `--elo` y no lo encuentra, el programa falla con un mensaje claro; antes usaba el rival local sin avisar. Ollama es opcional (`localhost:11434`). Duración medida en un clon limpio (Windows, 8 de noviembre de 2026): 11 s.

## Conocimiento de dominio codificado en el nivel 3

- **S1 (`CompAjedrezS1`):** responder a los jaques, no dejar piezas colgadas y capturar piezas indefensas.
- **S2 (`CompAjedrezS2`):** amenazas, defensas y clavadas como proposiciones, y «ansiedad» ante una clavada.
- **S3 (`CompAjedrezS3`):** heurísticas de centro y de seguridad del rey, búsqueda corta, penalización de posiciones repetidas (`_fens_visitados`) y, si está disponible, una hipótesis de Ollama validada contra las reglas.

## Resultados

N3 (50 partidas pareadas por rival, colores alternos y aperturas aleatorias, frente a un baseline de 1 ply): [`../RESULTADOS_TABLAS.md`](../RESULTADOS_TABLAS.md#ajedrez-n3). Medido sin Ollama. No se publica ningún ELO.

## Coste de adaptación

391 líneas de adaptador, 444 de componentes y 511 de runner y herramientas, incluido el script de medición ([`coste_adaptacion.csv`](../../analisis/resultados/coste_adaptacion.csv)).
