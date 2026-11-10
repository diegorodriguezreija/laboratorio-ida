# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versionado semántico (ver `docs/GOBERNANZA_Y_CONTRATOS.md`).

## [13.0.0] – sin fecha (preparada en la rama `v13`, sin etiquetar)

Todo lo nuevo está en `escaparate/` y `docs/episodios/`; el núcleo no cambia (`git diff main` vacío fuera de esas carpetas, el README, el CHANGELOG, `docs/img/`, la CI y los metadatos de versión; en `main.py` solo cambia el número que imprime el banner, que pasa a 13.0.0). Los niveles conservan su versión: `nivel_1_core` 12.0.0 y `nivel_2_sistemas` 12.1.0. La versión del proyecto pasa a 13.0.0 en `pyproject.toml` y `CITATION.cff`; el escaparate declara la suya en `escaparate/__init__.py`.

### Añadido
- **Registro de latidos** (`escaparate/registro_latido.py`, observador, apagado por defecto): JSONL con eventos tipados, se activa con `--grabar`.
- **Visor de repeticiones** en un único HTML autocontenido, sin red: Tribunal, cuerpo, mundo, registro de vida, lo que sabe el individuo, representación y linaje.
- **Biografía** en tercera persona al final de cada episodio grabado.
- **Modo `--demo-guillotina`** en el ejemplo mínimo: modificador, apagado por defecto.
- **Episodios publicados** (`docs/episodios/`): el mejor, el peor y uno típico de Crafter, con una regla de selección escrita antes de ejecutar; un episodio reproducible del ejemplo mínimo y otro del Bosque; y un linaje de seis generaciones.
- Tests de no regresión (misma trayectoria con y sin registro) y del visor, en la CI.

## [Sin publicar] – 12.0.1 (solo textos)

Sin cambios de código, configuración, cifras, figuras ni tablas de resultados, salvo el número de versión: lo que imprime `main.py` y los metadatos de `pyproject.toml` y `CITATION.cff` pasan de 12.0.0 a 12.0.1.

### Cambiado
- **README reescrito**, también su resumen en inglés. Incluye:
  - apertura y «pruébalo en un minuto», con un fragmento real de la demo;
  - «Qué hay dentro»: ondas, sistema triuno, cuarteto en tres barridos, lenguaje interno formal y modularidad;
  - mundos, hitos y resultados en corto;
  - enlaces a los documentos de detalle y una única sección de alcance y límites.
- **Manifiesto reescrito** como texto de motivación del autor, con el porqué del nombre: IdA – Identidad Artificial se aleja del término «inteligencia artificial» y busca la diversidad y la identidad dentro de cada especie. El texto fundacional v11.7 se conserva sin cambios en `docs/manifiesto_fundacional_v11.7.txt`, y se mantienen las notas de contraste con el código.
- **Glosario bilingüe** (es/en), con una nota sobre `consciencia_talamo_dmn.py`: conserva su nombre por la historia del proyecto.

### Añadido
- `docs/ARQUITECTURA.md` §12: clasificación del lenguaje interno formal (qué caminos deciden, cuáles son estructura y cuáles solo se ejercitan en tests), con rutas y líneas. En los límites conocidos (§11) se añaden el barrido activo vacío y la cuota de frecuencia declarada pero sin uso.
- `docs/mundos/crafter.md`: «Qué percibe IdA en Crafter». El adaptador lee el estado interno del juego en una ventana de 13×13, mayor que la vista de 9×7 del jugador; las comparaciones publicadas no cambian, porque todas usan el mismo adaptador. También se añade en «Alcance y límites» del README.

## [12.0.0] – 2026-11-07

Primera versión pública. El repositorio se publica sin historial previo; las versiones anteriores (v7–v11.7 y v12 de trabajo) quedan en el laboratorio privado del autor.

### Nombre
- **IdA significa «Identidad Artificial»**, con la misma expansión en todo el repositorio.

### Añadido
- Árbitros intercambiables (A0–A7), modos de ablación y telemetría contrafactual del Tribunal.
- Harness de experimentos (`analisis/run_experimento.py`), módulo estadístico y generador único de tablas (`analisis/generar_tablas.py`).
- Re-medición N1 de Crafter con semillas de reserva 3000–3039, medición N3 (Ajedrez) con baseline; medición N2 (Snake, 180 episodios) frente a un baseline BFS.
- Mundo de ejemplo mínimo (tutorial) y prueba metamórfica del aislamiento.
- Sondeo reproducible de la cobertura del linter; recuento de mecanismos conectados (N5).
- Tests de seguridad (sandbox del Bosque, autopoiesis desactivada), de salidas fuera del código y de separación de licencias.
- Documentación pública: README (es/en), arquitectura, stack, resultados, gobernanza, mundos, glosario, archivos de comunidad.

### Cambiado
- **Autopoiesis AST desactivada por defecto** (`--habilitar-autopoiesis`). Las cifras anteriores se midieron con ella activa.
- **El mundo Bosque solo opera en un subdirectorio temporal** y confina todas sus operaciones (antes, un objetivo `../fichero` escapaba del sandbox).
- Todas las salidas van a `IDA_OUT_DIR` (por defecto `./salidas/`); antes se escribían en las carpetas de código.
- Una sola función de Crafter Score.
- Licencias: Apache-2.0 en general y GPL-3.0-or-later en `mundo_ajedrez/` (todo lo que importa python-chess está allí).

### Corregido
- **Manipulación de cortisol de H2:** el valor fijado no llegaba al Tribunal (el core lo reescribía dentro del latido). Corregido y re-medido.
- El harness terminaba sin error con mundos u opciones no implementados.
- El ajedrez sustituía Stockfish por el rival local en silencio si no arrancaba.
- Fallo al redirigir la salida en Windows (`UnicodeEncodeError`).
- `scipy` faltaba en las dependencias.

### Eliminado
- Mundo de ciberseguridad (excluido del repositorio público).
- Binario de Stockfish, bases de datos, logs y linajes grandes (quedan en el laboratorio).

### Cifras retiradas
Ver la fe de erratas en `docs/RESULTADOS_Y_VERIFICACION.md`. En resumen: el ELO estimado con 5 partidas, el Crafter Score de 3,63 % no reproducible, scores de un solo individuo, comparaciones de «récord» con medias de RL, causas de muerte de Snake mal clasificadas y todas las cifras medidas antes de las correcciones de esta versión.
