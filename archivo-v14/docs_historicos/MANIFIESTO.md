# Manifiesto

*Por qué existe IdA y por qué se llama así. Es la voz del autor: opiniones e intuiciones, no resultados. El texto fundacional completo de la v11.7 se conserva sin cambios en [`manifiesto_fundacional_v11.7.txt`](manifiesto_fundacional_v11.7.txt).*

## Aprender del maestro

IdA empezó como un intento de entender, a pequeña escala, cómo resuelve la vida el problema de seguir viva. No pretende superar a la naturaleza, sino aprender de ella: mirar al maestro milenario de la evolución como un aprendiz e intentar traducir algunos de sus gestos a estructuras de datos, interfaces y flujos de ejecución.

Por eso el proyecto es tanto un ejercicio de introspección como de ingeniería. Hay que observar la duda, el miedo o el apego, preguntarse qué papel cumplen y tratar de escribirlos de forma que un programa pueda usarlos. Muchas veces sale mal; lo interesante está en averiguar por qué.

## Un cuerpo que mantener vivo

La intuición de partida es sencilla: la inteligencia de los seres vivos no nació para procesar texto, sino para mantener vivo un cuerpo vulnerable con una energía que se acaba. Razonar, desde esta mirada, es lo que hace un organismo cuando su entorno le afecta y no tiene tiempo ni fuerzas infinitas.

De ahí salen las piezas de IdA:

- **Un cuerpo simulado** con alimentación, energía, dopamina, placer y estrés.
- **Un latido con límites**: un presupuesto de atención (la amplitud) y un plazo (la frecuencia).
- **Tres sistemas con metas distintas**: S1 busca sobrevivir, S2 da valor y vínculo a lo que ve y S3 busca la verdad. Ninguno manda sobre los otros: proponen y un tribunal decide, según cómo esté el cuerpo.
- **El cuarteto de la experiencia**, `ei → ev → acc → ef`: lo que había, lo que atiende, lo que quiere hacer y lo que queda. De contrastar el resultado de la acción anterior con el presente nace su historia.

## Identidad, no inteligencia

**IdA significa Identidad Artificial.** El nombre se aleja a propósito de «inteligencia artificial», que suele imaginarse como una sola inteligencia, cada vez mayor, optimizada para una puntuación o para complacer a quien la usa.

La vida no funciona así. Lo que hace fuerte a una especie no es un individuo óptimo, sino la diversidad y la identidad dentro de ella: individuos con temperamento y linaje propios que responden de forma distinta al mismo mundo. La fricción entre ellos también es un motor. Por eso en IdA cada individuo nace con un **arquetipo** (apertura, responsabilidad, neuroticismo, umbral de miedo) y pertenece a un **linaje** que le transmite axiomas a través de una barrera, como la que separa en biología lo heredable de lo vivido.

## La historia del nombre

El proyecto se llama **IdA – Identidad Artificial**. El nombre se aleja a propósito del término «inteligencia artificial» y pone en el centro otra búsqueda: la diversidad y la identidad dentro de cada especie, individuos que responden de forma distinta al mismo mundo, en lugar de una sola inteligencia cada vez mayor.

## Una voz entre otras

Los modelos de lenguaje actuales tienen una capacidad enorme. La opinión del autor es que, al no tener un cuerpo que perder, se parecen a un cerebro en una cubeta. Cree también que centrar toda la inteligencia artificial en ellos deja fuera ideas valiosas de la biología. IdA no compite con ellos: es una forma de explorar esas otras ideas con las manos.

## Más arte que tecnología

IdA es un banco de pruebas personal para aprender ingeniería de software con algo que importe: puertos y adaptadores, análisis estático, concurrencia, persistencia, diseño experimental y estadística, y trabajo con agentes de IA bajo reglas claras. Lo que se mide se publica tal como salió, también cuando sale mal, porque la verdad es una de las tres metas del sistema y debería serlo también del proyecto.

## Lo que este texto no afirma

- **La crítica a los modelos de lenguaje es una opinión.** IdA no se ha comparado empíricamente con ningún modelo de lenguaje.
- **Los nombres biológicos son inspiración, no equivalencia.** Ni el sistema triuno ni la teoría de la mente ni los ficheros `consciencia_*` afirman que IdA tenga mente, creencias o experiencia más allá de lo funcional.
- **La diversidad de arquetipos no ha demostrado rendir más.** En Crafter, un arquetipo fijado a mano rinde igual que uno seleccionado, y los axiomas heredados no aportan nada medible ([resultados](RESULTADOS_Y_VERIFICACION.md)).
- **Sobre cifras y afirmaciones técnicas mandan [`RESULTADOS_Y_VERIFICACION.md`](RESULTADOS_Y_VERIFICACION.md) y [`ARQUITECTURA.md`](ARQUITECTURA.md).**

El texto v11.7 describe una arquitectura anterior (v7.0) con ficheros que ya no existen. Estas son las diferencias con el código actual:

1. **«Sin condicionales if/else despóticos».** El arbitraje del núcleo es una ponderación sobre un canal común (`nivel_1_core/arbitros.py`), pero los componentes de dominio de Crafter, Snake y Ajedrez sí son árboles de reglas escritos a mano (por ejemplo, `nivel_3_componentes/mundos/mundo_crafter/componentes_crafter.py`).
2. **«El sistema de archivos, los procesos y las constantes del hardware constituyen un bioma real».** El mundo de archivos solo opera dentro de un directorio temporal propio, por seguridad, y el mundo de procesos (ciberseguridad) no se publica.
3. **«Pensamiento latente asíncrono (LLM)».** El órgano de imaginación del S3 genérico está simulado: no llama a ningún modelo. Solo el mundo de ajedrez puede consultar un LLM local opcional (Ollama), y su efecto no se ha medido.
4. **«Teoría de la Mente».** Existe un órgano con ese nombre (`comp_teoria_mente.py`), usado en la demo y en un test; no se activó en las comprobaciones ni se ha evaluado en ningún mundo de medición ([ARQUITECTURA §12](ARQUITECTURA.md#12-lenguaje-interno-formal)).
5. **Arquetipo «que modula sus umbrales de miedo y tasas de olvido».** Existen esos parámetros (`nivel_1_core/contratos.py`), pero en el estudio factorial de Crafter el arquetipo de la generación 8 y el de la 12 dieron exactamente el mismo resultado.
6. **Filtro retiniano y habituación.** La habituación ante estímulos repetidos existe en el S1 genérico (`nivel_2_sistemas/s1_reactivo.py`); no tiene efecto medido.
