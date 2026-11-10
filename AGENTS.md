# Reglas para agentes de IA que contribuyan al Laboratorio IdA

El Laboratorio IdA es un entorno de investigación formal. Su fin es verificar si el diseño bioinspirado supera al tradicional mediante contrastes empíricos rigurosos. Estas reglas son de obligado cumplimiento para cualquier agente o persona.

## No negociables

1. **No debilites el linter ni los tests.** No quites términos de `TERMINOS_DOMINIO_PROHIBIDOS`, no añadas excepciones en `test_linter_pureza.py`, no relajes aserciones ni umbrales para que algo pase. Si un test falla, informa de qué falla y por qué.
2. **Pureza de la base cognitiva:** No introduzcas vocabulario de dominio en los niveles 1 y 2 (`base/nivel_1_core/`, `base/nivel_2_sistemas/`), ni directamente ni mediante artilugios que el linter no detecte (cadenas dinámicas, f-strings partidas, umbrales ajustados para un mundo específico). El conocimiento de dominio pertenece exclusivamente a los adaptadores de mundo (`base/nivel_3_componentes/`).
3. **El método experimental es innegociable:**
   - Un experimento = una carpeta en `experimentos/XXX-nombre/`.
   - La ficha `PREGUNTA.md` fija la hipótesis y el umbral de veredicto **antes** de lanzar la ejecución.
   - Mismas semillas pareadas en ambos brazos.
   - Si los datos no superan el criterio prefijado, el veredicto es «no mejora» o «empeora». Está terminantemente prohibido reajustar los umbrales o cambiar la métrica a posteriori para forzar un resultado positivo.
4. **Variantes aisladas:** Las modificaciones sobre el organismo se crean en `variantes/<nombre>/` con su correspondiente `CAMBIOS.md` documentando la versión base de origen, las diferencias exactas y la justificación.
5. **No inventes cifras, referencias ni mecanismos.** Cada cifra debe provenir de registros generados y reproducibles. Todo resultado negativo es valioso y debe registrarse en `RESULTADO.md` y en `INDICE.md`.
6. **Sin lenguaje enfático ni publicitario.** Prohibido el tono de marketing o venta. Describe con precisión numérica: N, mediana, dispersión o IC, fecha y condiciones de prueba.
7. **Seguridad y limpieza de salidas:** No ejecutes mundos fuera de sus entornos controlados ni actives autopoiesis salvo prueba aislada expresa. Ninguna ejecución debe escribir en carpetas de código; las salidas van a `IDA_OUT_DIR` o a directorios temporales del sistema.
8. **Aislamiento de licencias:** No añadas dependencias de `chess` fuera de `base/nivel_3_componentes/mundos/mundo_ajedrez/` (GPL-3.0-or-later, ver `NOTICE`).

## Verificación antes de proponer cambios

```bash
pytest tests_arquitectura -q                       # suite de arquitectura y pureza
pytest base/nivel_3_componentes/mundos/mundo_ajedrez/tests -q # tests de ajedrez
git diff --stat -- base/nivel_1_core base/nivel_2_sistemas   # justificación si se toca la base
```
