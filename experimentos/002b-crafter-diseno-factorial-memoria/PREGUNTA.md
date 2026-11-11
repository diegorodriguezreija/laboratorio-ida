# Experimento 002b: Diseño Factorial 2×2 — Desacoplamiento de Arquitectura Bioinspirada vs. Memoria Espacial en Crafter 2D

## 1. Pregunta Experimental

> **¿Proviene la ventaja observada de IdA v12.0 en Crafter 2D del diseño bioinspirado (homeostasis afectiva, modulación somática y arbitraje triúnico) o meramente de la disponibilidad de un mapa de memoria espacial que retiene la ubicación de las estaciones de trabajo y recursos?**

---

## 2. Hipótesis Formales y Diseño Factorial 2×2

Se define un diseño factorial equilibrado de dos factores entre sujetos pareados por semilla ($2 \times 2$):
* **Factor A (Arquitectura Cognitiva):** `IdA Bioinspirado` vs. `Línea Base Tradicional (Voraz)`.
* **Factor B (Memoria Espacial):** `Con Memoria Alocéntrica` vs. `Sin Memoria (Reactivo puro al tick)`.

### Matriz Experimental (4 Brazos Pareados)

| Factor B \ Factor A | A1: Tradicional (Voraz) | A2: Bioinspirado (IdA v12.0) |
|---|---|---|
| **B1: Sin Memoria (Reactivo)** | **Brazo 1:** `Voraz Reactivo` (sin memoria, idéntico a Exp 002) | **Brazo 2:** `IdA con Ablación de Memoria` ($S_3$ despojado de consulta a hitos alocéntricos de $S_2$, operando solo sobre fóvea local) |
| **B2: Con Memoria Espacial** | **Brazo 3:** `Voraz con Memoria` (`crafter_voraz_memoria.py`: mapa idéntico de hitos alocéntricos + retorno A\*) | **Brazo 4:** `IdA Canónico Completo` (`Hominis_G12` con mapa alocéntrico activo) |

### Contrastes Estadísticos y Jerarquía de Hipótesis

1. **Contraste Primario ($H_{1}$):**
   - Comparación pareada entre **Brazo 4 (IdA Completo)** y **Brazo 3 (Voraz con Memoria)**.
   - $H_{1,0}$: La diferencia en logros por episodio es igual a cero ($\Delta_{\text{primario}} = \text{Logros}_{B4} - \text{Logros}_{B3} = 0$).
   - $H_{1,1}$: $\Delta_{\text{primario}} \ne 0$ (bilateral, $\alpha = 0.05$).
2. **Efecto Principal de la Arquitectura ($H_{\text{Arq}}$):**
   - $\Delta_{\text{Arq}} = \frac{1}{2} [(\text{Logros}_{B4} - \text{Logros}_{B3}) + (\text{Logros}_{B2} - \text{Logros}_{B1})]$.
   - Mide si IdA supera al Voraz independientemente del estado de la memoria.
3. **Efecto Principal de la Memoria ($H_{\text{Mem}}$):**
   - $\Delta_{\text{Mem}} = \frac{1}{2} [(\text{Logros}_{B4} - \text{Logros}_{B2}) + (\text{Logros}_{B3} - \text{Logros}_{B1})]$.
   - Mide el impacto neto de añadir memoria espacial a ambos sistemas.
4. **Interacción ($H_{\text{Int}}$):**
   - $\text{Int} = (\text{Logros}_{B4} - \text{Logros}_{B3}) - (\text{Logros}_{B2} - \text{Logros}_{B1})$.
   - Evalúa si el beneficio de la memoria es asimétrico entre ambas arquitecturas (estimado con IC Bootstrap al 95 %).

---

## 3. Matriz de Decisión y Criterios de Falsación A Priori

Para evitar ambigüedades sobre qué significa «igualdad» o «equivalencia», se fija a priori un margen de equivalencia clínica/práctica de **$\delta_{\text{equiv}} = \pm 1.0$ logro por episodio**:

| Escenario | Condición Empírica | Interpretación Científica Formal |
|---|---|---|
| **Caso A: Solo Memoria** | $\Delta_{\text{primario}} \in [-1.0, +1.0]$ (equivalencia demostrada por TOST) y $\Delta_{\text{Mem}} > 0$ significativo. | **Falsación del excedente bioinspirado:** La superioridad observada en Exp 002 se debía íntegramente a la asimetría de memoria; un agente clásico con memoria equipara a IdA. |
| **Caso B: Excedente Bioinspirado Demostrado** | $\Delta_{\text{primario}} > +1.0$ logro ($p < 0.05$) y $\Delta_{\text{Arq}} > 0$ significativo. | **Confirmación de superioridad bioinspirada:** El chasis organísmico aporta una ventaja neta de progresión técnica incluso frente a una línea base dotada de memoria espacial idéntica. |
| **Caso C: Interacción Sinérgica** | $\text{Int} > 0$ con $\text{IC}_{95\%}$ estrictamente superior a cero. | IdA aprovecha la memoria espacial de forma cualitativamente más eficaz que el sistema voraz gracias a la modulación homeostática. |
| **Caso D: Avería de Ablación** | $\text{Logros}_{B2} < \text{Logros}_{B1} - 1.0$ logro ($p < 0.05$). | La ablación de memoria en IdA introdujo una avería mecánica colateral en lugar de aislar el factor memoria. Requiere invalidar y revisar la ablación. |
| **Caso E: No Concluyente** | $\Delta_{\text{primario}}$ no alcanza significación ($p \ge 0.05$) pero su IC 95 % excede el margen $[-1.0, +1.0]$. | Muestra insuficiente para discernir entre diferencia pequeña y equivalencia. Se reporta con honestidad como no concluyente. |

---

## 4. Paridad Estricta de la Memoria y Restricción de Factores

Para garantizar que el Factor B represente exactamente el mismo mecanismo en ambos brazos:
1. **Módulo de Memoria Compartido:** El agente voraz con memoria (`crafter_voraz_memoria.py`) implementa la misma estructura de memoria alocéntrica que IdA:
   - Registro alocéntrico de estaciones (`table`, `furnace`), fuentes de agua y yacimientos (`stone`, `iron`, `coal`) observados en el campo local ($9 \times 9$).
   - Regla de persistencia y capacidad idéntica (permanencia $1.0$ para mesas, retención de coordenadas absolutas observadas).
2. **Prohibición de Manipulaciones Cruzadas:**
   - **Combate con esqueletos idéntico:** La regla de autodefensa frente a esqueletos permanece inalterada respecto a `crafter_voraz.py` (huida evasiva si salud baja), para no confundir el efecto de combate con el factor memoria.
   - **Vista local:** Ambos brazos operan estrictamente bajo radio 6 ($9 \times 9$ casillas).
3. **Definición de la Ablación de IdA (Brazo 2):**
   - En `CompCrafterS3`, se anula la llamada a `activa.consultar_hitos_alocentricos` (retornando lista vacía `[]`) forzando a que $S_3$ planifique exclusivamente con las piezas presentes en la fóvea visual actual (`escena`), exactamente igual que el voraz reactivo.

---

## 5. Muestra, Semillas y Potencia Estadística

* **Rango de Semillas Vírgenes:** Se evalúan **60 semillas pareadas estrictamente nuevas** de la partición de evaluación:
  $$\text{Semillas } 3040 \text{ a } 3099 \quad (N = 60 \text{ por brazo}, \text{Total } 240 \text{ episodios})$$
  *(Las semillas 3000–3039 quedan excluidas para evitar sobreajuste retrospectivo).*
* **Efecto Mínimo Detectable (MDE):** Con $N = 60$ semillas pareadas y una $\sigma_{\text{diff}} \approx 2.5$ logros, el diseño alcanza una potencia estadística del $80 \%$ ($\beta = 0.20, \alpha = 0.05$) para detectar diferencias pareadas $\ge 0.91$ logros por episodio.
* **Presupuesto y Hash Congelado:**
  - Commit base congelado para la ejecución: `629acd1` (o el commit inmediato tras registrar este archivo).
  - Presupuesto de prueba de humo previo en entrenamiento: 5 episodios en semillas 2000–2004 para verificar que IdA con ablación no arroja excepciones ni bucles infinitos.
