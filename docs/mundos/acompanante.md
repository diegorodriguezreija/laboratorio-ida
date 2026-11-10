# Mundo Acompañante (sintético)

Estado: **experimental**.

> **No es una herramienta de apoyo, acompañamiento ni contención de personas, y no debe usarse como tal.** No interactúa con ningún humano ni procesa texto.

Dos «temas» ficticios, codificados a mano en un diccionario, se traducen a tensores 6D para comprobar que el mismo core funciona con un mundo de semántica distinta. Los nombres de nodos y comandos (escucha, límites, crisis) son etiquetas de la simulación, no capacidades. El nombre de la clase y de la carpeta se conserva para no romper imports ni tests.

Solo se ejecuta dentro del test `test_mundo_acompanante_humano_e2e`. Son 100 líneas de adaptador.
