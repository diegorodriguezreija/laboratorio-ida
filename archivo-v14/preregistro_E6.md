# Preregistro E6 (v14): contrafactual de la modulación, creencias del núcleo, carga falsa, curiosidad en el ejemplo mínimo y activa por modulación

9 de noviembre de 2026. Confirmado en git **antes de medir nada** de este encargo (`ENCARGO_E6.md`, repositorio de trabajo). Siguen las reglas de `preregistro_E2_E4.md` y `preregistro_E5.md`: bootstrap por partidas con 2000 remuestreos, Wilcoxon, Holm, α = 0,05, A0, arquetipo de H7, ruido aislado y hasta 500 latidos. Lo que aquí se fija no se cambia después de medir.

**Datos ya conocidos que fijan la escala** (bloque D del E5, semillas 30–49): margen A0 entre el mejor y el segundo, con mediana 0,504 en los latidos en calma (p10 0,37) y 0,477 en todos (p10 0,11).

## 1. Semillas

| Bloque | Semillas | Datos |
|---|---|---|
| I y J | 30–49, ejemplo mínimo y Bosque (una partida) | Se **repite el observador del bloque D** con dos campos que faltaban: el objetivo de cada candidato (I) y las evidencias de cada creencia (J). Las trayectorias son las mismas, porque el observador no las cambia |
| H | 290–369 (80) | Por pares: flag apagado / `corregir_carga_falsa_crafter` con `carga_pesados = []` |
| K | Ejemplo mínimo (sin semillas) | Ver K |
| L | 410–469 | Solo si la puerta I lo permite |

## 2. Bloque I: contrafactual de la modulación (observador, fuera del latido)

**Regla de decisión que se reproduce:** A0 elige la mayor puntuación. Si las dos mejores están a ≤ 0,03, gana la segunda: es la bifurcación con el ruido aislado, observada en el E5. Un **cambio** es que el ganador con la modulación sea un candidato distinto del ganador sin ella, aplicando la misma regla a los dos. Se usan los 8 candidatos de mayor puntuación que guarda el registro.

**I1. Modulación dirigida (la activa).**
- **Latidos con recuperación:** el latido **siguiente** a la apertura de un episodio en el que el observador del paso 2 recuperó un episodio parecido con coseno ≥ 0,95 (el umbral de «parecidos» del paso 0) y con un balance recordado de |balance| ≥ 0,5 puntos del juego. Es el primer latido cuya decisión podría usar ese recuerdo.
- **Acción del episodio recordado:** la orden más frecuente en sus latidos.
- **Modulación:** se suma +m a los candidatos con esa orden si el balance fue positivo, y −m si fue negativo.

**I2. Modulación de novedad (la curiosidad).** En los latidos en calma (definición del E5), se suma +m a los candidatos cuyo objetivo es una casilla (`nodo_x_y`) y es la menos visitada en la vida hasta ese latido, entre los objetivos de los candidatos (en empate, todos los empatados).

**Rejilla de m** (fijada aquí con la distribución de D): **0,01, 0,025, 0,05, 0,10, 0,126 (= 25 % del margen mediano en calma), 0,25 y 0,50.**

**Tablas.**
- Para cada m: % de latidos con cambio de ganador, sobre todos los latidos con recuperación y sobre los que están además en calma.
- De los cambios de I1: cuántos van hacia la orden del episodio recordado con balance positivo (descriptivo).

**Puerta I (sobre I1, Crafter):**

| Resultado | Condición |
|---|---|
| **«Ejercitable»** | Con alguna m ≤ 0,126, el ganador cambia en ≥ 10 % de los latidos en calma con recuperación. Se ejecuta L con la **menor** m de la rejilla que lo cumpla |
| **«No ejercitable»** | Ninguna m ≤ 0,126 llega al 10 %. Se informa de la menor m de la rejilla que llega (o de que ninguna llega) |

Si hay menos de 30 latidos en calma con recuperación, la puerta se evalúa sobre **todos** los latidos con recuperación, y se dice así.

## 3. Bloque J: ¿se contrastan las creencias del núcleo? (observador)

- **Ajuste `creencias`:** además, guarda de cada creencia sus evidencias, que son las entradas `Agencia_<latido>` y `Evidencia_<latido>` que `verificar_hipotesis_empirica` añade al confirmar (`memoria_tridimensional.py:167-168`).
- **Para cada creencia demostrada al morir:**
  - **confirmaciones:** el número de evidencias;
  - **última confirmación:** la evidencia de latido más alto;
  - **oportunidades de desmentirla:** los latidos posteriores a demostrarse en los que la acción del individuo tuvo como objetivo el sujeto de la creencia;
  - **oportunidades contrarias** (para «es nutritivo»): de esas oportunidades, en las que la comida + bebida del juego **no subió** en el latido siguiente;
  - **camino de desmentido en el código:** por clase.
    - `Proposicion_*` y `Predicado_*`: la única rama que baja la confianza (`memoria_tridimensional.py:178-180`) exige `balance_positivo = False`, y todos los llamadores pasan `True` (`s1_reactivo.py:45-61`, `s3_racional.py:176-181`). Por tanto, **sin camino**.
    - `Logica_CAUSAL` vicaria: puede bajar por extinción (`s3_racional.py:193-217`).
- **Resumen por mundo:**
  - % de demostradas sin ningún contraste tras demostrarse (sin confirmaciones ni oportunidades posteriores);
  - mediana de contrastes (confirmaciones + oportunidades) por creencia;
  - % sin camino de desmentido;
  - % de oportunidades contrarias.
- **Diez ejemplos legibles** en tercera persona.

## 4. Bloque H: carga falsa con lista vacía (modificador)

- **Cambio:** `corregir_carga_falsa_crafter` con `carga_pesados = []`. El soma de Crafter no lleva carga nunca.
- **Medición:** semillas 290–369, por pares (80 partidas).
- **H-H1:** lo no explicado por el juego es < 10 % del descenso, con el límite superior del IC por partidas < 0,10.
- **H-H2 (Holm, 2 hipótesis):** el límite inferior del IC de logros es ≥ −0,5 y el de latidos ≥ −10 % de la mediana original. Wilcoxon se informa como contraste.
- **Resultado:**
  - «recomendado»: H-H1 y H-H2;
  - «indeterminado» (la tercera categoría del encargo, cuando los intervalos son demasiado anchos para decidir): H-H1, pero algún límite de H-H2 por debajo de su margen con un IC que contiene el 0;
  - «no recomendado»: en otro caso.
- **Secundarias:** miedo, urgencia de S1, entropía de los indicadores y logros.

## 5. Bloque K: curiosidad en el ejemplo mínimo (prueba de mecanismo)

- **Configuración:** `curiosidad_intrinseca` con `regla = "relleno"` y peso 0,3.
- **Por qué una sola partida:** el ejemplo mínimo no tiene semillas, y con el ruido aislado es determinista, así que 40 repeticiones darían 40 copias idénticas. Se ejecuta **una partida por pares de 400 latidos**, flag apagado y encendido. Sin IC: con n = 1 no tiene sentido.
- **Medidas:**
  - % de arbitrajes que gana la curiosidad;
  - si cambia la trayectoria;
  - exploración: claros distintos visitados y entropía (bits) de las visitas por claro;
  - frutas comidas.
- **Resultado:** «ejercitado y cambia la exploración» si gana algún arbitraje y los claros distintos o la entropía suben; «ejercitado sin efecto» si gana pero no suben; «no ejercitado» si nunca gana.
- **No ruptura en el Bosque:** sin errores y dentro de los topes.
- **Si la modulación de novedad de I2 resulta ejercitable en Crafter,** se anota como opción, sin construirla.

## 6. Bloque L: activa por modulación (solo si I es «ejercitable»)

- **Flag `activa_modulacion`,** apagado. Un componente al final de la estación ACTUAR de S3, que es el último en ejecutarse antes del Tribunal (punto de entrada 2 de D2). Modifica la confianza y el arousal de los candidatos existentes para cambiar su puntuación A0 en ±m, sin añadir candidatos. Usa el almacén del observador: el episodio recuperado en la última apertura y su balance.
- **Compuerta:** coseno ≥ 0,95, |balance| ≥ 0,5 y peligro del juego en franja baja o media.
- **Medición:** semillas 410–469, por pares.
  - **Holm con 2 hipótesis:** L-H1 (logros aumentan; Wilcoxon unilateral; IC que excluye 0) y L-H2 (latidos > −10 % de la mediana).
  - **Ejercicio:** % de latidos en que la modulación cambia el ganador.
  - **Secundarias:** acierto del signo del episodio parecido y latidos hasta el primer logro.
- **Resultado:** «recomendado», «no recomendado» o «no ejercitada».

## 7. Coste

- Topes: mediana ≤ 0,5 ms y p99 ≤ 5 ms por latido; 1 % del plazo en el p99; mantenimiento ≤ 25 ms.
- Con todo apagado no se ejecuta código de la v14.
- Los registros nuevos se miden en secuencial.

## 8. Qué se publica

Todo, se cumpla o no. Ningún flag se enciende por defecto.
