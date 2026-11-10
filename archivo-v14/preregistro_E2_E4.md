# Preregistro E2–E4 (v14): calibración del cuerpo de Crafter, curiosidad intrínseca y tres observadores

9 de noviembre de 2026. Escrito y confirmado en git **antes de medir nada** con las semillas de este encargo. Encargo: `ENCARGO_E2_E4.md` (repositorio de trabajo). Lo que aquí se fija no se cambia después de medir. Si algo se concreta más tarde (las combinaciones de A2), se hace en un **anexo** con su propio commit, anterior a la medición correspondiente.

**Base del diseño.** Solo he usado la lectura del código y datos ya medidos en los pasos 0 a 3 (semillas 0–29), no datos nuevos:
- En el paso 0 (semillas 0–9), el miedo ocupa el 77,6 % de los latidos en vigilia: el 60,1 % con peligro ≥ 0,75 (un depredador o lava a la vista) y el 17,4 % solo por inanición.
- El adaptador de Crafter compensa el desgaste del soma (+0,8) solo cuando se ejecuta una acción (`adaptador_crafter.py:642`).
- Cada resultado lleva un `objeto_cargado`, que el soma guarda como carga tras cualquier COGER (`estado_somatico.py:200-201`), y la carga añade 0,5 de desgaste por latido (`estado_somatico.py:120`).

## 1. Diseño común

| Aspecto | Valor |
|---|---|
| Mundo y configuración | Crafter, `evaluar_individuo_en_semilla`, árbitro A0, arquetipo de H7 (responsabilidad 0,72; umbral de miedo 0,58; neuroticismo 0,30; apertura 0,60), sin axiomas, ruido aislado, hasta 500 latidos |
| Unidad independiente | La partida (una semilla = una vida) |
| Comparación de modificadores | Por pares: la misma semilla con el flag apagado y encendido |
| Intervalos | Bootstrap por partidas, 2000 remuestreos, percentil del 95 % (semilla del remuestreo 0) |
| Contraste | Wilcoxon de rangos con signo sobre las diferencias por pares (con la cola indicada); corrección de Holm dentro de cada familia confirmatoria; α = 0,05 |
| Observadores | Encendidos en todos los brazos, con `parametros_observacion.json`. No cambian la trayectoria (test de la CI) |
| Logros | Logros únicos de Crafter desbloqueados en la vida (`total_logros`) |
| Duración de la vida | Latidos vividos |

**Semillas** (todas de desarrollo):

| Uso | Semillas |
|---|---|
| A1, diagnóstico | 30–49 |
| A2, exploración | 50–89 |
| A3, confirmación y repetición de los pasos 2 y 3 | 130–169 |
| B, exploración | 90–129 |
| B, confirmación | 170–209 |
| C, observadores | 30–49 y 130–169, sobre los brazos con todo apagado |

No se usan las particiones de test ni de reserva.

**Señal de peligro de los observadores en Crafter (cautela del encargo).** El parámetro de peligro del bloque A (abajo) cambia la percepción de S1. Para que los observadores no cambien lo que leen, en todas las mediciones de este encargo el observador de Crafter usa el **peligro del juego**: 1 si hay un Zombie, un Skeleton, una flecha o lava en la ventana de 13 × 13 casillas que lee el adaptador, y 0 en otro caso (ajuste `peligro_crafter: "juego"`). Con el flag apagado se comprueba que coincide con el peligro de S1 (≥ 0,55) que se usó en los pasos 2 y 3, y se informa del porcentaje de coincidencia. El valor por defecto sigue siendo `"s1"`.

## 2. Bloque A: calibración del cuerpo simulado de Crafter

### A1. Diagnóstico (observador; semillas 30–49; flag apagado)

**Métricas.** Para alimentación, vitalidad, urgencia de S1, peligro de S1 y miedo (estado MIEDO o PÁNICO), en vigilia:
- la distribución;
- el porcentaje de latidos en el 10 % extremo de su rango: alimentación y vitalidad ≤ 10 o ≥ 90; urgencia y peligro ≤ 0,1 o ≥ 0,9; miedo es binario y se usa su porcentaje.

Para la alimentación y la vitalidad, además, la correlación de Pearson por vida con la señal del juego (comida + bebida; salud) y el desfase de −20 a +20 latidos que maximiza la correlación cruzada (mediana entre vidas).

**Causas.**
- Atribución del descenso de la alimentación simulada a tres fuentes, por latido, con las constantes del código: lastre de la carga (0,5 por latido con carga), desgaste no compensado (0,8 en los latidos sin acción ejecutada) y caídas de comida y bebida del juego.
- Atribución del miedo: peligro ≥ 0,75 frente a inanición sola.
- Recuento de qué entidades disparan el peligro de S1.

**Distinguibilidad.** Número de combinaciones distintas del vector de indicadores por franjas (peligro, tensión y calma; baja/media/alta: < 0,35, < 0,75, ≥ 0,75) y su entropía de Shannon (bits), para comparar antes y después.

**Saturación:** alguna variable pasa más del 50 % de los latidos en su extremo.

**Parámetros candidatos** (como mucho dos; A1 decide con la atribución):

| Parámetro | Qué es | Valor original |
|---|---|---|
| **P1, factor del lastre de la carga en Crafter** (`factor_lastre_carga`) | Multiplica los 0,5 por latido que el soma resta cuando cree llevar carga | 1,0 |
| **P2, alcance del peligro** (`alcance_peligro`, en casillas de Manhattan) | Los depredadores, flechas y lava más lejos que ese alcance llegan a la percepción con la nocicepción a 0 y el arousal limitado a 0,5. No cambia la lista de depredadores que usan los componentes de Crafter (que van por tipo, no por nocicepción) | Sin límite (toda la ventana) |
| P1', alternativo a P1 si A1 lo indica (`factor_desgaste_basal`) | Multiplica el desgaste basal de 0,8 por latido en vigilia | 1,0 |

**Puerta A1.** Se cierra el bloque sin implementar si:
- no hay saturación;
- o los dos parámetros con mayor atribución no explican juntos al menos el 60 % del descenso de la alimentación **y** al menos el 60 % de los latidos de miedo;
- o hace falta un cambio estructural.

### A2. Exploración (modificador `calibracion_cuerpo_crafter`; semillas 50–89)

- Como mucho 4 combinaciones de (P1 o P1', P2). Se fijan en un **anexo** a este preregistro, con su commit, después de A1 y antes de medir A2.
- Se registran todas, aunque no se elijan.

**Objetivo**, sobre todos los latidos de vigilia de la exploración:
- miedo ≤ 40 %;
- alimentación simulada no pegada a un extremo: < 50 % de los latidos en ≤ 10 o ≥ 90.

**No inferioridad**, por pares con IC 95 %:
- límite inferior del cambio en logros por vida ≥ −0,5;
- límite inferior del cambio en latidos vividos ≥ −10 % de la mediana con el flag apagado.

**Elección:** entre las que cumplen objetivo y no inferioridad, la más cercana al original (primero, P1 más cercano a 1; después, P2 mayor).

**Puerta A2:** si ninguna cumple, se cierra el bloque con las 4 combinaciones y no se repiten los pasos 2 y 3.

### A3. Confirmación (semillas 130–169; elegida frente a flag apagado, por pares)

**Familia confirmatoria (Holm, 4 hipótesis, unilaterales):**

| Hipótesis | Criterio |
|---|---|
| A-H1 | Fracción de miedo por vida (media entre vidas) < 0,40. Bootstrap unilateral |
| A-H2 | Fracción de latidos con la alimentación en un extremo, por vida (media) < 0,50 |
| A-H3 | Cambio en logros > −0,5 (no inferioridad; Wilcoxon sobre diferencia + 0,5) |
| A-H4 | Cambio en latidos > −10 % de la mediana con el flag apagado (Wilcoxon sobre diferencia + margen) |

**Resultado:** «recomendado» si las cuatro se cumplen tras Holm; si no, «no recomendado».

**Repetición de los pasos 2 y 3** (descriptiva, con IC por partidas, flag encendido frente a apagado en 130–169):
- acierto del signo del episodio parecido frente a la base de la misma vida;
- acierto de las expectativas frente a predecir lo más frecuente;
- demostradas y las que dejan de serlo.

**Hipótesis adicional única (A-H5, α = 0,05, unilateral, fuera de la familia):** con el flag encendido, la clave de la expectativa (acción, clase del objetivo, franja de peligro del juego) acierta más que predecir lo más frecuente.
- Se calcula **fuera del latido**, reproduciendo la proactiva sobre los registros, con la misma lógica y los mismos ajustes; solo cambia la clave.
- Si no supera la base, el paso 3 se cierra como negativo y no se prueban más variantes.

## 3. Bloque B: curiosidad intrínseca (`curiosidad_intrinseca`)

### B1. Diseño (antes de implementar)

- **Componente** `Comp_CuriosidadIntrinseca`, del Sistema S2, en la estación REACCIONAR. Se añade al construir el mundo desde `v14/`, con la interfaz de componentes existente (`ComponenteCognitivoBase`). No toca el núcleo.
- **Novedad (la opción más simple):** la de cada nodo adyacente es 1 / (1 + veces que se ha entrado en ese nodo). Las veces salen del grafo topológico del individuo, que el núcleo ya mantiene (`veces_transitado`), leído sin escribir.
  - Es el caso más simple de «distancia a lo ya registrado» (distancia 0 si ya se estuvo allí).
  - Usar la huella del almacén del observador obligaría a meter el observador dentro del latido, y el error de las expectativas es negativo en el paso 3.
  - Queda anotado como decisión.
- **Salida:** un impulso MOVER hacia el nodo adyacente más novedoso (en empate, el primero en el orden de la percepción). Confianza y arousal = `peso` × novedad.
- **Nunca por encima de S1:** si hay impulsos de S1, su puntuación A0 se limita a la menor puntuación A0 de esos impulsos menos 0,05, por debajo del margen de bifurcación de 0,03.
- **Compuerta:** solo propone si:
  - el peligro de S1 < 0,35;
  - la alimentación del soma > 45 (el umbral de hambre moderada del soma);
  - queda al menos el 50 % de la amplitud del latido.

  En otro caso calla.
- **Un solo parámetro libre: el peso.** Valores de la exploración: 0,3, 0,5 y 0,7.
- **Coste:** sin cargo extra de amplitud (1 unidad, como cualquier impulso). Se mide su tiempo aparte.

### B2. Medición

- **Exploración (90–129):** los 3 pesos, por pares. Elección: el peso con mayor cambio medio de logros cuya duración de vida tenga una estimación puntual ≥ −10 % de la mediana; en empate, el menor.
- **Confirmación (170–209), Holm con 2 hipótesis:**
  - B-H1: los logros aumentan (Wilcoxon unilateral; IC que excluye 0);
  - B-H2: no inferioridad de la duración de la vida (> −10 % de la mediana).
- **Secundarias** (descriptivas, con IC): cobertura (celdas distintas visitadas; pares (acción, clase) distintos) y mediana de latidos hasta el primer logro.
- **No ruptura:** en el ejemplo mínimo (200 latidos) y el Bosque (100), con el flag encendido, sin errores y con el coste dentro de los topes.
- **Si A es «recomendado»:** se repite la confirmación con la calibración encendida en los dos brazos, como análisis secundario.
- **Resultado:** «recomendado» si B-H1 y B-H2 se cumplen tras Holm; si no, «no recomendado». «No recomendado por coste» si el componente supera la mediana de 0,5 ms o el p99 de 5 ms.

## 4. Bloque C: tres observadores (fuera del latido, sobre los registros)

### C1. Identidad medida (V4)

El repositorio no define V4, así que se usa la definición del encargo.

- **Perfil por vida y por mitad de vida:**
  - reparto de órdenes (8);
  - victorias de S1, S2 y S3;
  - media y desviación de la urgencia de S1;
  - riesgo (% de latidos con el peligro del juego en franja alta).
- **Estabilidad:** correlación de Pearson entre el perfil de la primera mitad y el de la segunda de la misma vida (media e IC por partidas), comparada con la de mitades de vidas distintas.
- **Distintividad:** CCI(1) por rasgo, tomando las dos mitades como medidas repetidas; se informa de la mediana entre rasgos.
- **Interpretación fijada:** «se diferencian de forma estable» si la correlación dentro de la vida supera a la de entre vidas con un IC que excluye 0 **y** la mediana del CCI es ≥ 0,40. En otro caso, «todos se parecen». Todas las vidas comparten arquetipo, así que es lo esperable, y se publica tal cual.

### C2. Vocabulario del lenguaje formal (8a)

- **Inventario:** recuento por latido de las piezas de la Onda cuyas clases empiezan por `Sujeto`, `Predicado`, `Proposicion`, `Sentencia` y `Logica`, en los tres mundos.
- **Uso real:** cuántas veces una pieza de esa clase fue guardada o recuperada por el observador del paso 2.
- **Lagunas** (como mucho 10):
  - pares (acción, clase del objetivo) con ≥ 20 resultados y un resultado dominante (mejora, sigue igual o empeora) en ≥ 70 %, que ninguna relación del vocabulario (`V_Relacion`) nombra;
  - situaciones de apertura (franja de peligro, orden) que preceden a un episodio negativo en ≥ 70 % de ≥ 20 casos.

  Ordenadas por frecuencia × estabilidad. No se crea ningún predicado.

### C3. Lugar seguro, fase a (6a)

- **Zona en Crafter:** la casilla del jugador agrupada en bloques de 4 × 4 (coordenadas del juego divididas entre 4). **En el Bosque:** la ubicación (carpeta).
- **Candidata:** una zona donde un episodio cierra por calma, con balance ≥ 0 y sin pérdida de salud. Se registra en el latido del cierre (sin mirar al futuro).
- **Medidas por vida:**
  - número de candidatas;
  - cuántas se repiten (≥ 2 cierres);
  - % de latidos en zonas que ya eran candidatas;
  - balance de los episodios que **empiezan** en una zona candidata (ya establecida antes) o adyacente (bloques vecinos), frente al resto: diferencia de medias por partidas con IC.
- No se hace volver al individuo a ningún sitio.

## 5. Coste

Se mide con y sin cada flag frente a los topes aceptados:
- mediana ≤ 0,5 ms y p99 ≤ 5 ms por latido del observador o el componente;
- el 1 % del plazo en el p99;
- mantenimiento ≤ 25 ms.

La calibración solo añade dos envolturas aritméticas.

## 6. Qué se publica

Todo, se cumpla o no. Ningún flag se enciende por defecto.
