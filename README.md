# Laboratorio IdA

Banco de contrastación empírica para investigar **si el diseño cognitivo orgánico y bioinspirado de IdA puede superar al diseño tradicional de base en cada mundo, en qué situaciones, cuánto, y dónde no**.

El laboratorio no es un producto ni un escaparate de cara a la galería: es un entorno de prueba formal, guiado por hipótesis previas, semillas idénticas y aceptación rigurosa de resultados negativos.

---

## 1. Relación con el Framework IdA

Este laboratorio es el banco de experimentación y evaluación científica. Si lo que buscas es ver y ejecutar agentes vivos en una implementación limpia, accesible y con panel de telemetría visual, consulta el repositorio oficial del framework:

- [**Framework IdA (Identidad Artificial)**](https://github.com/diegorodriguezreija/IdA): el framework bioinspirado en Python para crear y observar agentes con cuerpo, carácter y linaje viviendo en cinco mundos.

| | **Framework IdA** | **Laboratorio IdA** (este repositorio) |
|---|---|---|
| **Propósito** | Ver y ejecutar agentes vivos | Probar variantes, medir y contrastar hipótesis |
| **Contenido** | Framework limpio, telemetría y mundos | Variantes experimentales, líneas base y mediciones |
| **Enfoque** | Directo, accesible y visual | Riguroso, formal y con hipótesis fijadas a priori |
| **Versión** | Oficial del framework | Modificaciones aisladas en `base/` y `variantes/` |

---

## 2. Estructura del Laboratorio

```
laboratorio-ida/
├── base/             # Código de referencia del organismo de IdA (inmutable para experimentos)
├── variantes/        # Modificaciones puntuales sobre la base (cada una con su CAMBIOS.md)
├── lineas-base/      # Agentes tradicionales sencillos por mundo (BFS, voraz, minimax...)
├── experimentos/     # Carpetas 001-..., con PREGUNTA.md, correr.py, datos/ y RESULTADO.md
├── herramientas/     # Observadores por latido, comparadores con misma semilla y estadísticas
├── archivo-v14/      # Archivo histórico de lecciones y preregistros de la v14
└── INDICE.md         # Historial global de preguntas, hipótesis y veredictos
```

## 3. El Método Experimental

Cada investigación se aísla en una carpeta de `experimentos/` y sigue una ficha obligatoria fijada **antes** de ejecutar:

| Campo | Regla |
|---|---|
| **Pregunta** | Una sola, binaria (sí / no). |
| **Variantes** | Dos brazos: Base vs. Variante, o Variante vs. Línea Base Tradicional. |
| **Mundo y semillas** | Mismo mundo, mismas semillas pareadas en ambos brazos (20 por defecto). |
| **Medida** | Un indicador numérico objetivo derivado de los registros. |
| **Veredicto** | Umbral de mejora fijado a priori. Si no lo alcanza, es «no mejora»; el criterio nunca se modifica a posteriori. |

El resumen de todos los veredictos se actualiza en el [ÍNDICE.md](INDICE.md).

## 4. Ejecución Rápida

```bash
# Entorno e instalación
python -m venv .venv
source .venv/bin/activate       # En Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Comprobación de arquitectura y pureza
pytest tests_arquitectura -q

# Lanzar una suite de experimento
python experimentos/001-nombre/correr.py --semillas 20
```

## 5. Licencia

Apache-2.0. El adaptador del mundo Ajedrez se distribuye bajo GPL-3.0-or-later conforme a su dependencia del motor (ver [NOTICE](NOTICE)).
