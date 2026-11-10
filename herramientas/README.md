# Herramientas del Laboratorio

Conjunto de observadores, comparadores de variantes, utilidades estadísticas y generadores de datos empíricos para soportar las investigaciones.

## Componentes

- `observador/`: Observador analítico desacoplado del latido. Extrae señales vitales, activación de creencias, episodios y balance somático por latido.
- `observar.py`: Hook de inyección de telemetría pasiva sobre el ciclo vital del organismo.
- `experimento.py`: Lanzador de variantes con control pareado de semillas e iteraciones.
- `estadistica.py`: Métricas no paramétricas (Wilcoxon, remuestreo bootstrap con remuestreos por pares, corrección Holm para hipótesis múltiples).
- `generar_tablas.py`: Generador de tablas Markdown y resúmenes a partir de ficheros CSV y registros.
- `arbitraje.py`: Utilidades para auditar las decisiones del Tribunal Motor.
- `canario.py`: Pruebas de sanidad y no ruptura antes de tandas de experimentación prolongadas.
