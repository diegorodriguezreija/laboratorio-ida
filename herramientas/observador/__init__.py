"""
Observadores de la v14: experiencia activa (paso 2) y proactiva (paso 3), solo observadas.

Regla de oro: observar no es decidir. Todo lo de esta carpeta lee el núcleo **después** de cada
latido y lo copia a su propio almacén; nunca escribe en la Onda, en el soma ni en la memoria del
núcleo (`DimensionActiva`, `DimensionProactiva`). Con el observador encendido, la trayectoria es
idéntica a la de sin observador (`v14/tests/test_observador.py`).
"""
