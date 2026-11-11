# Laboratorio IdA

Banco de contrastación empírica formal de **IdA (Identidad Artificial)**: investiga si el diseño cognitivo bioinspirado (homeostasis afectiva, modulación somática, memoria tridimensional y arbitraje triúnico) supera al diseño tradicional de ingeniería en cada entorno simulado, en qué condiciones, en qué medida y dónde no.

El laboratorio no es un escaparate publicitario: es un entorno de verificación científica regido por hipótesis fijadas *a priori*, diseño pareado intra-semilla y aceptación rigurosa de resultados negativos.

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

| Documento | Contenido Principal |
|---|---|
| [**Índice de Experimentos**](INDICE.md) | Historial vivo de todas las evaluaciones históricas (E-01 a E-12) y experimentos del laboratorio (001 a 002b). |
| [**Metodología Experimental**](docs/METODOLOGIA.md) | Partición de semillas (desarrollo, evaluación y reserva), diseño pareado, TOST y Holm-Bonferroni. |
| [**Resultados Históricos**](docs/RESULTADOS_HISTORICOS.md) | Análisis de mediciones en Ajedrez, Snake, Crafter y diagnósticos v12/v14. |
| [**Catálogo de Hipótesis**](docs/CATALOGO_HIPOTESIS.md) | Estado formal de las hipótesis H1 a H9 y ablaciones de mecanismos. |
| [**Auditoría y Fe de Erratas**](docs/AUDITORIA_Y_ERRATAS.md) | Hallazgos de auditoría, afirmaciones retiradas formalmente y matriz de mecanismos N5. |
| [**Arquitectura de Base**](docs/ARQUITECTURA.md) | Descripción técnica del núcleo de IdA, el ciclo de latido y los tres niveles cognitivos. |

---

## 3. Resumen de Experimentos del Laboratorio

### Experimento 001: Diagnóstico de la derrota de Snake frente a BFS
- **Pregunta:** ¿Qué mecanismo intrínseco de IdA explica su desventaja frente a BFS en Snake (auto-encierro, interferencia del motor S1 u oscilación)?
- **Hallazgo:** En simulación local síncrona ($N = 50$ episodios pareados), IdA y BFS empatan (23 victorias IdA, 23 BFS, 4 tablas; diferencia media $+0.58$ puntos [IC 95 %: $-4.46, +5.62$]). No se reprodujo la desventaja de E-09 en entorno síncrono, formulándose la latencia de red/asincronía como hipótesis externa.
- [Ver ficha PREGUNTA.md](experimentos/001-snake-diagnostico-bfs/PREGUNTA.md) y [Informe RESULTADO.md](experimentos/001-snake-diagnostico-bfs/RESULTADO.md).

### Experimento 002: IdA v12.0 vs. Agente Voraz en Crafter 2D
- **Pregunta:** ¿Aporta el chasis bioinspirado de IdA una ventaja de supervivencia o progresión técnica frente a un agente voraz tradicional con vista local idéntica ($13 \times 13$)?
- **Hallazgo:** IdA superó ampliamente al agente voraz reactivo puro en Crafter Score ($22.07 \%$ frente a $6.46 \%$, $+15.61\text{ pp}$ [IC 95 %: $+12.34\text{ pp}, +18.41\text{ pp}$]) y en logros brutos ($11.53$ frente a $5.65$ logros), pero sin efecto separable en supervivencia pura ($p = 0.067$). La prueba no discriminaba si la ventaja procedía de la bioinspiración o de la memoria alocéntrica.
- [Ver ficha PREGUNTA.md](experimentos/002-crafter-ida-vs-voraz/PREGUNTA.md) y [Informe RESULTADO.md](experimentos/002-crafter-ida-vs-voraz/RESULTADO.md).

### Experimento 002b: Diseño Factorial 2×2 (Arquitectura vs. Memoria Espacial)
- **Pregunta:** ¿Aporta el diseño bioinspirado de IdA un excedente técnico frente a una línea base voraz dotada de memoria espacial alocéntrica idéntica, o la ventaja de Exp 002 se debía íntegramente a la asimetría de memoria?
- **Hallazgo:** Evaluado sobre 60 semillas vírgenes (240 episodios):
  - **Logros brutos:** IdA Canónica ($10.80 \pm 3.06$) y Voraz con Memoria ($10.87 \pm 1.79$) empatan formalmente ($\Delta = -0.07$ logros [IC 95 %: $-1.03, +0.92$]). El límite superior ($+0.92$) descarta un excedente bioinspirado $\ge 1.0$ logro.
  - **Crafter Score:** IdA mantiene $+6.49\text{ pp}$ ($20.54 \%$ vs. $14.05 %$), explicado principalmente por logros no programados en la máquina de estados de la línea base (`make_stone_sword`, `place_stone`) y la regla de huida ante esqueletos.
  - **Ablación e Interacción:** IdA sin mapa alocéntrico apenas pierde rendimiento ($10.38$ logros) frente al colapso del voraz sin memoria ($5.58$ logros), lo que apunta a la redundancia de su memoria de trabajo somática.
- [Ver ficha PREGUNTA.md](experimentos/002b-crafter-diseno-factorial-memoria/PREGUNTA.md) y [Informe RESULTADO.md](experimentos/002b-crafter-diseno-factorial-memoria/RESULTADO.md).

---

## 4. Estructura del Repositorio

```
laboratorio-ida/
├── base/             # Código de referencia del organismo (Nivel 1 Core, Nivel 2 Sistemas, Nivel 3 Mundos)
├── lineas-base/      # Agentes tradicionales sencillos por mundo (crafter_voraz, crafter_voraz_memoria, snake_bfs...)
├── experimentos/     # Carpetas de experimentos formales con PREGUNTA.md, ejecutar.py, analizar.py y RESULTADO.md
│   ├── 001-snake-diagnostico-bfs/
│   ├── 002-crafter-ida-vs-voraz/
│   └── 002b-crafter-diseno-factorial-memoria/
├── salidas/          # Registros y datasets CSV de episodios pareados (abiertos y reproducibles)
├── tests_arquitectura/ # Suite formal de tests de pureza de base, licencias y contratos
├── docs/             # Metodología, resultados históricos, catálogo de hipótesis y auditoría
├── INDICE.md         # Registro vivo de todas las evaluaciones y veredictos
├── requirements.txt  # Dependencias fijadas para reproducción exacta
├── NOTICE            # Declaración de autoría, licencias de terceros y desglose legal
└── LICENSE           # Licencia Apache 2.0 y CC-BY-4.0
```

---

## 5. Instrucciones de Reproducción

El repositorio está diseñado para permitir la verificación independiente y reproducible de todos los resultados.

### 5.1 Instalación del Entorno
Se recomienda utilizar Python 3.10 o superior (verificado en Python 3.11 / 3.15):

```bash
# 1. Clonar el repositorio
git clone https://github.com/diegorodriguezreija/laboratorio-ida.git
cd laboratorio-ida

# 2. Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate       # En Windows PowerShell: .venv\Scripts\Activate.ps1

# 3. Instalar dependencias exactas
pip install -r requirements.txt
pip install -e .
```

### 5.2 Comprobación de Pureza Arquitectural
Verifica que la base cognitiva no contiene vocabulario de dominio ni fugas de dependencias:

```bash
pytest tests_arquitectura -q
```
*(Deben pasar los 82 tests sin errores).*

### 5.3 Reproducción de los Análisis Estadísticos
Los datasets brutos de cada evaluación pareada se incluyen en `salidas/`. Puedes recalcular los contrastes, intervalos bootstrap y pruebas TOST al instante:

```bash
# Análisis Experimento 001 (Snake vs BFS)
python experimentos/001-snake-diagnostico-bfs/analizar.py

# Análisis Experimento 002 (IdA vs Voraz en Crafter)
python experimentos/002-crafter-ida-vs-voraz/analizar.py

# Análisis Experimento 002b (Diseño Factorial 2x2 en Crafter)
python experimentos/002b-crafter-diseno-factorial-memoria/analizar.py
```

### 5.4 Re-ejecución Completa de un Experimento
Para re-ejecutar la simulación completa desde cero sobre las semillas registradas:

```bash
python experimentos/002b-crafter-diseno-factorial-memoria/ejecutar.py
```

---

## 6. Avisos sobre Servicios de Terceros y Aislamiento Legal

- **Aviso sobre Playsnake (E-09):** El adaptador de Snake (`AdaptadorSnakeWeb`) incluye código histórico para interactuar mediante Playwright con el sitio web público `playsnake.org`. El laboratorio desaconseja lanzar peticiones automatizadas contra dicho servidor para preservar sus recursos; todas las evaluaciones locales deben realizarse sobre el simulador síncrono local `experimentos/001-snake-diagnostico-bfs/simulador_snake.py`.
- **Aislamiento de Licencias (Ajedrez):** El módulo `base/nivel_3_componentes/mundos/mundo_ajedrez/` depende de `python-chess` y se distribuye de forma aislada bajo licencia **GPL-3.0-or-later**. El núcleo cognitivo y los mundos de Crafter y Snake son completamente independientes de esta dependencia.

---

## 7. Licencia

- **Código fuente:** Distribuido bajo licencia [Apache License 2.0](LICENSE), salvo el módulo `mundo_ajedrez/` que se distribuye bajo [GNU GPL v3.0 or later](base/nivel_3_componentes/mundos/mundo_ajedrez/LICENSE).
- **Documentación, informes y datos empíricos:** Todos los ficheros markdown (`*.md`), informes en `experimentos/` y datasets en `salidas/` se licencian bajo [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/).

Para detalles completos, consulte el archivo [NOTICE](NOTICE).
