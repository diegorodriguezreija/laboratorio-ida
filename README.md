# Laboratorio IdA

Banco de contrastación empírica formal: investiga **si el diseño cognitivo orgánico y bioinspirado de IdA puede superar al diseño tradicional de base en cada mundo, en qué situaciones, cuánto, y dónde no**.

El laboratorio no es un producto ni un escaparate para lucir agentes: es un entorno de prueba formal regido por hipótesis fijadas *a priori*, diseño pareado con semillas idénticas y aceptación rigurosa de resultados negativos.

---

## 1. Relación con el Framework IdA

Este repositorio alberga la investigación científica y la contrastación empírica. Si buscas ver, ejecutar y estudiar agentes vivos con panel de telemetría y visualizador interactivo, consulta el framework oficial:

- [**Framework IdA (Identidad Artificial)**](https://github.com/diegorodriguezreija/IdA): framework bioinspirado en Python para crear agentes con cuerpo, carácter y linaje viviendo en cinco mundos.

| Dimensión | **Framework IdA** | **Laboratorio IdA** (este repositorio) |
|---|---|---|
| **Propósito** | Ver y ejecutar agentes vivos en mundos simulados | Probar variantes, medir con rigor y contrastar hipótesis |
| **Contenido** | Framework limpio, telemetría y adaptadores | Variantes experimentales, líneas base y registros de datos |
| **Tono** | Sencillo, accesible y visual | Formal, empírico y honesto ante resultados negativos |
| **Ritmo** | Rápido: se construye y se observa | Lento y metódico: una pregunta cada vez |
| **Versión** | Oficial y publicable | Modificaciones aisladas en `base/` y `variantes/` |

---

## 2. Mapa Documental del Laboratorio

La investigación cuenta con documentación exhaustiva y estructurada:

| Documento | Contenido Principal |
|---|---|
| [**Dossier de Investigación**](Laboratorio_IdA_Dossier_de_investigacion.md) | Recopilación completa de hallazgos, mediciones v12/v14, balance y respuestas honestas. |
| [**Índice de Experimentos**](INDICE.md) | Historial de las 12 evaluaciones realizadas (E-01 a E-12) y experimentos en curso. |
| [**Metodología Experimental**](docs/METODOLOGIA.md) | Reglas de semillas (desarrollo, test, reserva), diseño pareado, estadística bootstrap y Holm. |
| [**Resultados Históricos**](docs/RESULTADOS_HISTORICOS.md) | Análisis detallado de mediciones en Ajedrez, Snake, Crafter y v14. |
| [**Catálogo de Hipótesis**](docs/CATALOGO_HIPOTESIS.md) | Estado de H1 a H9, estudio factorial 2×2 y réplicas planificadas (R3, R7). |
| [**Auditoría y Fe de Erratas**](docs/AUDITORIA_Y_ERRATAS.md) | 12 hallazgos de auditoría, afirmaciones retiradas formalmente y matriz de mecanismos N5. |
| [**Arquitectura de Base**](docs/ARQUITECTURA.md) | Descripción técnica del núcleo de IdA, el ciclo de latido y los tres niveles. |

---

## 3. Resumen Ejecutivo de Hallazgos Empíricos

1. **Ajedrez (+0,21 a +0,52 pts/partida vs 1-ply):** IdA supera ampliamente a un jugador tradicional de 1-ply con la misma evaluación frente a rivales minimax locales (49V, 1T, 0D contra nivel 3). Frente a Stockfish 1320 y 1500, empata con la línea base.
2. **Snake (−417 a −615 pts vs BFS):** El algoritmo tradicional de búsqueda de rutas (BFS) supera con rotundidad a IdA en cuanto aumenta la velocidad del juego.
3. **Crafter (+8,85 logros vs jerarquías; colinealidad del 96 % vs reglas simples):** El Tribunal dinámico A0 supera a jerarquías fijas, pero empata estadísticamente contra «mayor arousal» y «mayor producto» por colinealidad de decisiones.
4. **Sistema Límbico S2 (+1,40 logros, −536 pasos de vida):** El valor afectivo impulsa la consecución de logros pero duplica las muertes prematuras por depredador (compromiso biológico).
5. **Herencia (5,74 % → 22,31 % en Crafter Score):** La ventaja selectiva procede al 100 % de los pesos del arquetipo; la herencia de axiomas cognitivos aislados aporta \(+0,00\) logros.
6. **Módulos sin impacto en rendimiento:** Cortisol dinámico, plasticidad TD-hebbiana en Crafter, ciclo de sueño REM y bucle talamocortical no han demostrado beneficio estadístico en logros o supervivencia.

---

## 4. Estructura del Repositorio

```
laboratorio-ida/
├── base/             # Código de referencia del organismo (IdA v14) con su VERSION.md
├── variantes/        # Taller de modificaciones aisladas (cada una con su CAMBIOS.md)
├── lineas-base/      # Agentes tradicionales sencillos por mundo (BFS, voraz, minimax...)
├── experimentos/     # Carpetas 001-..., con PREGUNTA.md, correr.py, datos/ y RESULTADO.md
├── herramientas/     # Observadores de latido, comparadores pareados y herramientas estadísticas
├── archivo-v14/      # Archivo histórico formal (LECCIONES.md, preregistros y análisis)
├── docs/             # Metodología, resultados históricos, catálogo de hipótesis y auditoría
└── INDICE.md         # Historial vivo de experimentos, hipótesis y veredictos
```

---

## 5. El Método Experimental

Cada experimento se aísla en una carpeta de `experimentos/` y sigue una ficha obligatoria fijada **antes** de ejecutar:

| Campo | Regla |
|---|---|
| **Pregunta** | Una sola, binaria (sí / no). |
| **Variantes** | Dos brazos: Base vs. Variante, o Variante vs. Línea Base Tradicional. |
| **Mundo y semillas** | Mismo mundo, mismas semillas pareadas en ambos brazos (20 por defecto). |
| **Medida** | Un indicador numérico objetivo derivado de los registros. |
| **Veredicto** | Umbral de mejora fijado a priori. Si no lo alcanza, es «no mejora»; el criterio nunca se modifica a posteriori. |

---

## 6. Ejecución Rápida

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

---

## 7. Licencia

Apache-2.0. El adaptador del mundo Ajedrez se distribuye bajo GPL-3.0-or-later conforme a su dependencia de `python-chess` (ver [NOTICE](NOTICE)).
