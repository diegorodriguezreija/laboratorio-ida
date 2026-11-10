# Mundo Bosque de archivos

Estado: **experimental, solo en sandbox**.

> Aviso: las acciones de este mundo borran, truncan y escriben ficheros reales. Solo funciona dentro de un subdirectorio temporal que crea el propio programa.

## Qué es

Un directorio hace de «bosque»: cada fichero es una entidad (nutritiva, tóxica, oráculo…) según las palabras de su nombre, y su tamaño y su entropía forman el tensor 6D. DEGLUTIR trunca o borra; CENSURAR, ATACAR y COGER borran; SOLTAR escribe.

## Cómo ejecutarlo

```bash
python main.py --demo     # 10 latidos en un directorio temporal que se borra al terminar
```

Duración medida en un clon limpio (Windows, 8 de noviembre de 2026): 1 s.

## Seguridad

El adaptador rechaza cualquier raíz que no esté dentro de un directorio temporal creado para él (prefijo `ida_bosque_` bajo `tempfile.gettempdir()`; así lo crea `main.py`) y confina todas las operaciones a esa raíz. Antes, un objetivo como `../fichero` escapaba del sandbox. Tests: `tests_arquitectura/test_seguridad_ejecucion.py`.

## Conocimiento de dominio

No hay componentes de dominio: aquí deciden los sistemas genéricos del nivel 2. El adaptador (216 líneas) clasifica los ficheros por palabras de su nombre.
