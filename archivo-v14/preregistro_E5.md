# Preregistro E5 (v14): arbitraje, carga falsa, curiosidad y observadores

9 de noviembre de 2026. Confirmado en git **antes de medir nada** de este encargo (`ENCARGO_E5.md`, repositorio de trabajo). Las reglas de E2–E4 siguen vigentes (`v14/preregistro_E2_E4.md`, sección 1: diseño común, bootstrap por partidas con 2000 remuestreos, Wilcoxon, Holm, α = 0,05). Lo que aquí se fija no se cambia después de medir.

**Origen de las ideas:**
- El bloque E nace del diagnóstico A1 (semillas 30–49): el lastre de la carga falsa explica el 40,5 % del descenso de la alimentación simulada. Se confirma en semillas nuevas (210–249).
- La regla de F se apoya en la definición de «relleno» de D, fijada aquí antes de ver ningún dato del arbitraje.

## 1. Semillas (solo desarrollo)

| Bloque | Semillas | Brazos |
|---|---|---|
| D, diagnóstico del arbitraje | 30–49 (Crafter); ejemplo mínimo y Bosque, una partida | Todo apagado, con el registro del arbitraje |
| E, carga falsa | 210–249 | Apagado / `corregir_carga_falsa_crafter` / exploratorio P2 |
| F, curiosidad con regla nueva | 250–289 | Apagado / `curiosidad_intrinseca` (peso 0,3) |
| G1, franja de peligro en la clave | 130–169 | Registros ya existentes de E2–E4 (todo apagado), sin ejecutar nada |
| G2 y G3 | 30–49 | Los registros de D (G2 y G3) y los de A1 (G3) |

## 2. Bloque D: diagnóstico del arbitraje (observador)

**Registro (ajuste `registrar_arbitraje`, apagado por defecto).** Por latido, leyendo `acc["Impulso"]` después del latido sin alterarlo:
- de cada candidato: Sistema de origen (`identificar_sistema_origen`), orden, clase (abajo) y puntuación A0;
- el ganador: la pieza que cita la Ejecución;
- el margen: puntuación del mejor menos la del segundo;
- si hubo acecho: el Tribunal retiene la acción;
- las órdenes de los árbitros A0 a A7 y cuáles discrepan de A0. Ya las calcula el Tribunal en `metricas["contrafactual"]`.

**Puntuación A0** (`arbitros.py:83-100`): `((arousal_ef × estrés) + (confianza × (1 − estrés))) × mod`, con:
- `mod = clip(0,85 + 0,15 × peso_sináptico, 0,80, 1,25)`;
- `arousal_ef = máx(arousal, arousal_s1_crudo)` en desesperación (alimentación ≤ 15).

Se informa también de la bifurcación de Prigogine:
- si los dos mejores están a ≤ 0,03, A0 puede elegir al segundo;
- con el ruido aislado (`cosechar_unidad_uniforme = 0,5`), lo elige siempre.

**Clase de un candidato** (genérica, también vale en Crafter):

| Clase | Regla |
|---|---|
| **Supervivencia** | `es_supervivencia_pag`, `flash_supervivencia` o la marca de soltar lastre de S1 (`soltar_lastre_*`); o la orden ATACAR o DEGLUTIR; o `motivo = evasion_amenaza` |
| **Relleno** | Orden ESPERAR (sin `dormir` y sin objetivo DORMIR), ACECHAR o MOVER, **sin** ninguna clave de propósito (`meta_teleologica`, `meta_estrategica`, `meta_tecnologica`, `objetivo`, `motivo`, `curiosidad`), y con todas sus entradas no causales: identificadores de componentes, `Propiocepcion*`, `Alarma_Supervivencia` o `Simulacion_Ruta` |
| **Con propósito** | El resto (S3 con meta, ir hacia agua o comida, dormir, coger…) |

Si no hay candidatos, el latido cuenta como «sin candidatos» (relleno).

**Latido en calma:** peligro y urgencia en franja baja (< 0,35).
- En Crafter, con señales del juego: el peligro del juego y la urgencia metabólica del juego, 1 − mín(comida, bebida)/9.
- En el ejemplo mínimo y el Bosque: el peligro de S1 y la urgencia metabólica del soma.

**Umbral de margen: 0,05.**
- **Por qué:** las puntuaciones A0 están en [0; 1,25] y las dominan la confianza y el estrés bajo. 0,05 queda justo por encima del margen de bifurcación (0,03), que ya es un empate de hecho.
- Se informará de la distribución completa del margen.
- **Revisión antes de calcular la puerta:** si la mediana del margen en calma fuera < 0,005 o > 0,6 (escala no comparable), se reescribe el umbral como el percentil 10 de esa distribución, en un anexo con commit propio. En otro caso, 0,05 queda fijo.

**D2.** Tabla de puntos de entrada, por lectura del código (no se implementa ninguno).

**Puerta D3:**

| Resultado | Condición |
|---|---|
| «Hay margen» | ≥ 20 % de los latidos en calma de Crafter tienen ganador de relleno o margen < 0,05, **y** existe un punto de entrada sin tocar el núcleo. Se ejecuta F |
| «Margen solo con cambio del núcleo» | Hay margen, pero ningún punto de entrada lo evita. F se cierra sin implementar |
| «No hay margen» | < 20 %. F se cierra |

**No regresión:** con `registrar_arbitraje` encendido, la trayectoria es idéntica (test).

## 3. Bloque E: corregir la carga falsa (modificador `corregir_carga_falsa_crafter`)

- **Cambio, un solo parámetro:** `carga_pesados`, la lista de objetos del inventario del juego que cuentan como carga física. Valor preregistrado: **`["iron", "diamond"]`** (los únicos minerales metálicos o raros; en Crafter todo lo demás va al inventario sin ocupar las manos).
- **Cómo:** al empezar cada latido, antes del metabolismo, el soma lleva carga solo si el inventario tiene al menos uno de esos objetos; en otro caso, `objeto_cargado = None`. Se aplica desde `v14/` envolviendo el metabolismo del soma de la partida.
- **E-H1:** con el flag encendido, la parte del descenso de la alimentación **no explicada por el juego** (lastre de la carga + desgaste no compensado) es < 10 % del descenso total. Mismo método de atribución que A1. Se contrasta con un bootstrap por partidas del cociente agregado: el límite superior del 95 % debe quedar < 0,10.
- **E-H2 (no inferioridad, Holm con 2 hipótesis):** el límite inferior del IC del cambio en logros es ≥ −0,5 (Wilcoxon sobre la diferencia + 0,5) y el de los latidos vividos es ≥ −10 % de la mediana original.
- **Secundarias** (con IC, sin criterio): miedo, urgencia de S1, entropía de los indicadores por franjas, logros.
- **Resultado:** «recomendado» si E-H1 y E-H2 se cumplen.
- **P2 exploratorio:** el flag ya existente `calibracion_cuerpo_crafter` con `alcance_peligro = 4` (los factores en 1,0), en las mismas semillas. Solo descriptivo, sin criterio.

## 4. Bloque F: curiosidad con una regla nueva (solo si D3 dice «hay margen»)

Se mantienen la compuerta (peligro de S1 < 0,35, alimentación del soma > 45, ≥ 50 % de amplitud libre), la novedad por visitas y el peso **0,3** sin explorar.

**Regla nueva.** La curiosidad puede ganar **solo** si no hay ningún candidato de supervivencia de S1 **y** el mejor candidato presente es de relleno (o no hay ninguno):
- en ese caso, su puntuación A0 = (la del mejor candidato presente, o 0) + 0,3 × novedad;
- en cualquier otro caso, la regla anterior: por debajo de la menor puntuación de S1 menos 0,05 y por debajo de la del mejor candidato menos 0,05.

Nunca supera a un candidato de supervivencia ni a uno con propósito.

| Hipótesis | Criterio |
|---|---|
| **F-H1** | Los logros únicos por vida aumentan (Wilcoxon unilateral; IC por partidas que excluye 0) |
| **F-H2** | Latidos vividos > −10 % de la mediana original |

Holm con F-H1 y F-H2. Además:
- **Secundarias:** celdas distintas, pares (acción, clase) distintos y latidos hasta el primer logro.
- **Prueba de que la regla se usa:** porcentaje de arbitrajes que gana la curiosidad. Si es 0, el resultado es «no ejercitada».
- **No ruptura:** ejemplo mínimo y Bosque.
- **Resultado:** «recomendado» (F-H1 y F-H2), «no recomendado» (se ejercitó y no mejora) o «no ejercitada».

## 5. Bloque G: tres observadores (fuera del latido)

**G1, franja de peligro en la clave (130–169).**
- Se reproduce la proactiva sobre los registros (la reproducción con la clave antigua es idéntica a la ejecución en línea, comprobado en E2–E4) con la clave (acción, clase del objetivo, franja de peligro del juego).
- **G1-H1 (única, unilateral):** el acierto supera al de predecir lo más frecuente, con un bootstrap por partidas cuyo límite inferior del 95 % sea > 0.
- **Se informa también de:** el acierto con la clave antigua, la calibración por franjas de la frecuencia predicha, y las demostradas y las que dejan de serlo.
- **Si G1-H1 no se cumple,** el paso 3 se cierra como negativo y no se prueban más variantes.

**G2, conocimiento formal legible (30–49, ejemplo mínimo y Bosque).**
- **Ajuste `creencias`, apagado por defecto.** En cada mantenimiento y al morir, el observador lee (sin escribir) las piezas formales de la memoria activa del núcleo: las clases `Proposicion*`, `Predicado*` y `Logica*` de `indice_identidad`.
- **Clasificación:**
  - **demostrada:** modalidad DEMOSTRADO* y confianza ≥ 0,85, sin `falsado`;
  - **falsada:** `falsado` es verdadero;
  - **dudosa:** el resto.
- **Al morir:** un `.md` en tercera persona (como mucho 10 líneas por categoría) y un `.json` con todo. Cada línea lleva la confianza, el latido en que se observó la categoría por primera vez y un texto en castellano.
- **Tabla:** demostradas al morir, cuántas se mantuvieron ≥ 20 latidos y la distribución de la duración de una demostración. La resolución es la del mantenimiento: cada 25 latidos y en el sueño.

**G3, balance y sed (30–49; registros de A1 y de D).**
- El soma no tiene sed; el juego sí (bebida), y el balance publicado del observador de Crafter **ya incluye** la bebida, con peso 0,5 (Δsalud + 0,5 × Δ(comida + bebida)).
- **Recálculos, fijados aquí:**
  - (a) bebida con peso 1,0: Δsalud + 0,5 × Δcomida + 1,0 × Δbebida;
  - (b) efecto inmediato: el balance publicado, 1 latido después de la acción en lugar del cierre o el horizonte.
- **Se informa:** el porcentaje de resultados positivos (> 0,25) para DEGLUTIR (agua) y para el resto de acciones, con la definición publicada, (a) y (b). No se cambia la definición publicada.

## 6. Coste

Topes: mediana ≤ 0,5 ms y p99 ≤ 5 ms por latido; 1 % del plazo en el p99; mantenimiento ≤ 25 ms.
- **Con todo apagado** no se ejecuta código de la v14.
- **Registros nuevos** (arbitraje, creencias): su coste se mide en secuencial.
- **Modificadores:** su coste se mide aparte.

## 7. Qué se publica

Todo, se cumpla o no. Ningún flag se enciende por defecto.
