# Laboratorio IdA – Documento de diseño

Nov 10, 2026 · @Diego

Borrador para revisar contigo antes de crear el repositorio `laboratorio-ida`. Sin código hasta que lo apruebes.

## Introducción: IdA y el laboratorio son cosas distintas

**IdA – Identidad Artificial** es un framework pequeño en Python, inspirado en la biología: agentes con cuerpo, carácter y linaje que viven en varios mundos (mínimo, archivos, Snake, Crafter y Ajedrez). Se ejecuta con un comando y se mira. Su filosofía, su arquitectura y su estado están en su propio repositorio (`MANIFIESTO.md`, `doc-repositorio/`); **este documento no los describe ni los sustituye**, y no entra en cómo está hecho por dentro.

**El laboratorio IdA** es otro repositorio, con otra finalidad: **probar si el diseño orgánico de IdA puede superar al diseño tradicional de base en cada mundo, y en qué situaciones**. Parte de IdA pero no se queda con él tal cual: hace muchos cambios y prueba distintas configuraciones para adaptarlo a cada situación, y compara cada variante con una línea base tradicional del mundo. **La versión que se prueba aquí no coincide con la del framework, y no tiene por qué hacerlo.**

|  | **Framework IdA** | **Laboratorio IdA** |
| --- | --- | --- |
| **Para qué sirve** | Ver y ejecutar agentes vivos | Probar variantes, medir y comparar |
| **Qué contiene** | El código, los mundos y su documentación | Variantes de IdA, líneas base tradicionales, experimentos y resultados |
| **Versión de IdA** | La oficial, la que publicas tú | Variantes modificadas, que difieren de la oficial |
| **Tono** | Sencillo y vistoso | Riguroso y honesto |
| **Relación** | No sabe que el laboratorio existe | Parte de IdA y lo cambia en su propia copia; nunca toca el original |
| **Ritmo** | Rápido: se construye y se mira | Lento: una pregunta cada vez |

## 1. Para qué existe el laboratorio

IdA (el repositorio del framework) es para **ver y ejecutar**: sencillo, vistoso, con la magia en el README. El laboratorio es para **comprobar y explorar**: en qué mundos y con qué configuración el diseño orgánico supera al diseño tradicional, cuánto, y dónde no, que quede dicho con honestidad.

**Qué es.**

- Un sitio para plantear una pregunta, ejecutarla con el mismo mundo y la misma semilla en dos variantes, y leer la diferencia.
- **Un taller de variantes:** copias modificadas de IdA (otra configuración, componentes cambiados, ajustes para un mundo concreto) para ver si el diseño orgánico rinde más.
- **Una línea base tradicional por mundo** (un agente convencional sencillo) contra la que comparar, para que «mejora» signifique algo.
- Un archivo de lo que se probó, lo que salió y lo que no salió, incluida la v14.

**Qué no es.**

- No es un producto ni se enseña como escaparate.
- No es la versión oficial de IdA: sus variantes no sustituyen al framework hasta que tú decidas llevar algo allí.
- No es un freno: IdA no espera a que el laboratorio apruebe nada para avanzar.

**Por qué separarlo.** La v14 mezcló construir y medir en un mismo sitio, y se acabó midiendo mucho sin construir lo importante. Con dos repositorios IdA se mantiene sencillo y vistoso, mientras el laboratorio puede cambiar muchas cosas, romperlas y comparar sin ensuciarlo.

## 2. Relación con el repositorio IdA

**El laboratorio parte de IdA, pero no está atado a su versión.**

- Cada variante nace de una versión concreta de IdA (tag o commit) y la modifica en la copia del laboratorio. El repositorio IdA no se toca desde aquí.
- Cada variante tiene un nombre, su versión de origen y una lista corta de cambios respecto a ella (`CAMBIOS.md`). Así siempre se sabe qué versión era y qué se cambió.
- Las variantes se comparan entre sí y con la línea base tradicional del mundo.
- Lo que gane y merezca pasar al framework viaja a IdA como una propuesta descrita en una frase, para que decidas tú. No se mezcla de oficio.
- IdA no sabe que el laboratorio existe.

## 3. Estructura del repositorio `laboratorio-ida`

```
laboratorio-ida/
  README.md            qué es y cómo lanzar un experimento (una pantalla)
  base/                copia de trabajo de IdA, con su versión de origen anotada
  variantes/
    nombre-01/
      CAMBIOS.md       qué se cambió respecto a la base y por qué
  lineas-base/         agentes tradicionales sencillos, uno por mundo
  experimentos/
    001-nombre/
      PREGUNTA.md      la ficha (sección 4)
      correr.py        lanza las variantes con la misma semilla
      datos/           registros de ejecución (no se versionan, solo el resumen)
      RESULTADO.md     qué salió, con gráfica y una frase
  herramientas/        observadores, comparador de variantes, gráficas
  archivo-v14/         lo que se rescata de la v14 (sección 5)
  INDICE.md            tabla de experimentos: pregunta, fecha, variante, veredicto
```

- **Un experimento = una carpeta.** Se puede borrar sin romper nada.
- **Una variante = una carpeta** con su lista de cambios.
- **El ÍNDICE es el historial del laboratorio.** Una línea por experimento, con veredicto: mejora, empata, empeora o no concluyente.
- **Los datos pesados no se suben.** Se sube el resumen y la forma de regenerarlos con la semilla.

## 4. Cómo se hace un experimento

Una ficha de cinco líneas, siempre igual. Si no cabe en la ficha, la pregunta está mal planteada.

| Campo | Qué se escribe | Ejemplo |
| --- | --- | --- |
| **Pregunta** | Una sola, que se pueda responder sí o no | ¿Apagar la experiencia acorta la vida en Crafter? |
| **Variantes** | Dos, que difieren en una sola cosa: dos variantes, o una variante y la línea base tradicional del mundo | Con experiencia y `--sin-experiencia` |
| **Mundo y semillas** | Qué mundo y cuántas semillas (mismas en ambas variantes) | Crafter, 20 semillas, 500 latidos |
| **Medida** | Un número que se calcula del registro | Latidos vividos hasta la muerte |
| **Veredicto** | Qué diferencia cuenta como mejora, fijada **antes** de mirar | Mejora si la mediana sube un 10 % o más |

**Reglas del método (las únicas).**

1. Misma semilla en las dos variantes; solo cambia una cosa.
2. El veredicto se escribe antes de ejecutar. Si el resultado no encaja, se dice que no mejora; no se cambia el criterio.
3. Resultado en una gráfica y una frase en `RESULTADO.md`, y una línea en el ÍNDICE.
4. Un experimento que sale negativo es un resultado válido y se archiva igual.

Nada de preregistros largos, puertas ni estadística elaborada: con varias semillas, la mediana y el rango bastan para decidir si algo merece seguir.

## 5. Qué se traslada de la v14

La v14 fue el primer laboratorio sin saberlo. De ella se rescata lo útil y el resto queda como archivo de solo lectura.

| Se traslada a `herramientas/` | Se deja en `archivo-v14/` |
| --- | --- |
| Los observadores que leen el registro por latido (los que sigan sirviendo con la IdA actual) | Preregistros, puertas y evidencias de E1 a E5 |
| El comparador de variantes con la misma semilla | Los encargos E2 a E6 y sus prompts |
| La extracción de balance y señal de signo por episodio | Los informes `REVISION_V14` y `GUIA_REVISION_V14` |

**Lo que enseñó la v14 y se conserva como nota** (`archivo-v14/LECCIONES.md`):

1. El cuello de botella del Tribunal: la experiencia debe modular los candidatos existentes.
2. Los fallos del soma de Crafter y el peligro binario.
3. El soma simulado sigue al juego (correlación 0,90).
4. Efecto de la experiencia activa: poco dentro de una vida, más entre vidas.
5. Casi todo lo «demostrado» perdió el estado al contrastarse.

La v14 no se reescribe ni se borra: se copia a un tag o carpeta de archivo y el historial queda como está. Estas lecciones describen la v14; la IdA actual ha cambiado mucho y cada una se vuelve a comprobar antes de darla por buena.

## 6. Primeras preguntas a investigar

El objetivo es saber **dónde y cómo el diseño orgánico supera al tradicional**. Solo se pasa a la siguiente cuando la anterior tiene veredicto. Todas se responden con la ficha de la sección 4.

| # | Pregunta | Variantes | Medida |
| --- | --- | --- | --- |
| 1 | ¿En qué mundos supera IdA a una línea base tradicional? | Una variante de IdA frente a la línea base de ese mundo | La medida propia de cada mundo (a definir con él) |
| 2 | ¿Qué situaciones favorecen al diseño orgánico (recursos escasos, peligros nuevos, mundo cambiante)? | La misma variante en el mundo normal y en uno alterado | Ventaja sobre la línea base en cada caso |
| 3 | ¿Qué configuración funciona mejor en cada mundo? | Varias configuraciones de una misma variante | La medida del mundo |
| 4 | ¿La experiencia aporta algo? | Con y con `--sin-experiencia` | Latidos vividos o la medida del mundo |
| 5 | ¿Se vive mejor a lo largo de las generaciones? | Con linaje y con `--tabula-rasa` | Última generación frente a la primera |
| 6 | ¿La diversidad de arquetipos rinde más que un arquetipo único? | Arquetipo único y variados | Media y dispersión entre individuos |

La 1 es la pregunta de fondo del laboratorio y necesita antes una línea base por mundo. El manifiesto de IdA reconoce que el efecto de la experiencia solo está indicado y que el de los arquetipos no se ha medido, así que 4 y 6 tienen mucho margen. Las preguntas se confirman contra la variante concreta antes de lanzarlas.

## 7. Reglas de trabajo y decisiones abiertas

**Reglas.**

- Repositorio privado. Solo tú publicas, etiquetas o fusionas.
- Sin claves ni `.env`. Autor de git: Diego Rodriguez Reija, solo en local.
- No se reescribe el historial.
- Las variantes se modifican solo en la copia del laboratorio; el repositorio IdA no se toca desde aquí.
- No se escribe código hasta que apruebes este documento. Después, un experimento cada vez.
- La gente que lea el repositorio debe entender en una pantalla qué se mide y qué salió.

**Decisiones abiertas** (mi propuesta entre paréntesis):

| # | Decisión | Propuesta |
| --- | --- | --- |
| 1 | Cómo se parte de IdA | Copia de trabajo en base/ con la versión de origen anotada en cada variante |
| 2 | Qué se hace con el repositorio actual (`ida-release`) | Convertirlo en el laboratorio o archivarlo, y crear `laboratorio-ida` limpio con solo lo rescatado |
| 3 | Visibilidad del laboratorio | Privado al inicio; público cuando haya índice con varios veredictos |
| 4 | Qué observadores de la v14 se mantienen | Solo los que alimenten las preguntas de la sección 6 |
| 5 | Cuántas semillas por experimento | 20 por defecto |
| 6 | Quién implementa | Un agente por experimento, con la ficha como encargo (máximo una interacción cada uno) |
| 7 | Cómo se guardan las variantes | Carpetas con CAMBIOS.md; ramas de git si crecen mucho |

## 8. Puesta en marcha: repositorio limpio desde la v14

Decisiones ya tomadas:

1. **Repositorio nuevo y de cero** (`laboratorio-ida`), sin ramas ni versiones anteriores.
2. **Foto limpia, sin historial.** Se copian los ficheros de la v14 con un primer commit nuevo.
3. **Antes de copiar, se termina E6** (contrafactual del arbitraje, repetición de la carga, curiosidad en el ejemplo mínimo y activa por modulación) y se deja todo en verde.
4. **Se conserva:** el código de la v14 como `base/`, los observadores y herramientas de medida que sirvan a la sección 6, y los resultados E1 a E5 en `archivo-v14/`.
5. **Se elimina:** documentación histórica (v8 a v12, `docs_old`), preregistros, puertas, prompts de encargos, nombres de ramas y versiones anteriores en cualquier fichero, y todo lo que narre la historia del proyecto.
6. **Licencia:** Apache-2.0, con la carpeta del mundo Ajedrez en GPL-3.0-or-later y archivo NOTICE.
7. **El agente trabaja solo en local.** Tú creas el repositorio vacío en GitHub y autorizas el push cuando quieras.
