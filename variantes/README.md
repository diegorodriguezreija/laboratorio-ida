# Variantes de IdA

Un taller de variantes: modificaciones controladas sobre el código de `base/` (cambios en configuración, ajuste de pesos, poda de componentes, o mecanismos específicos para un mundo).

## Reglas de las Variantes

1. Cada variante vive en su propia subcarpeta dentro de `variantes/` (ej. `variantes/01-sin-experiencia/`).
2. Cada variante **debe** incluir un archivo `CAMBIOS.md` que detalle:
   - **Versión de origen en `base/`** (tag o commit de partida).
   - **Lista corta y exacta de cambios** respecto a la base.
   - **Motivación o hipótesis** que justifica la modificación.
3. El repositorio base nunca se toca directamente por una variante.
4. Las variantes se comparan entre sí y contra la línea base tradicional de cada mundo con semillas idénticas.
