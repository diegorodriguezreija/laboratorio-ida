# Experimento 002b: Diseño Factorial 2×2 — Desacoplamiento de Arquitectura Bioinspirada vs. Memoria Espacial en Crafter 2D

## 1. Pregunta Experimental

> **¿Aporta el diseño bioinspirado de IdA v12.0 (homeostasis afectiva, modulación somática y arbitraje triúnico) un excedente medible en progresión técnica frente a una línea base tradicional dotada de memoria espacial equivalente, o la ventaja observada en el Experimento 002 se debía íntegramente a la asimetría de memoria?**

---

## 2. Hipótesis Formales y Diseño Factorial 2×2 (Medidas Repetidas Intra-Semilla)

Se define un diseño factorial equilibrado de dos factores con medidas repetidas donde cada semilla procedural se evalúa bajo los 4 brazos ($2 \times 2$):
* **Factor A (Arquitectura Cognitiva):** `IdA Bioinspirado` vs. `Línea Base Tradicional (Voraz)`.
* **Factor B (Memoria Espacial):** `Con Memoria Alocéntrica` vs. `Sin Memoria (Reactivo puro al tick)`.

### Matriz Experimental (4 Brazos Pareados Intra-Semilla)

| Factor B \ Factor A | A1: Tradicional (Voraz) | A2: Bioinspirado (IdA v12.0) |
|---|---|---|
| **B1: Sin Memoria (Reactivo)** | **Brazo 1:** `Voraz Reactivo` (sin memoria, idéntico a Exp 002) | **Brazo 2:** `IdA sin memoria alocéntrica` (Ablación limpia: $S_3$ despojado de consulta a `hitos_alocentricos`, operando únicamente sobre la fóvea visual local actual; conserva memoria de trabajo y soma básico) |
| **B2: Con Memoria Espacial** | **Brazo 3:** `Voraz con Memoria` (`crafter_voraz_memoria.py`: extensión aditiva pura sobre Voraz base con mapa alocéntrico idéntico, limpieza de recursos modificados y retorno A\*) | **Brazo 4:** `IdA Canónico Completo` (`Hominis_G12` con mapa alocéntrico activo y memoria hipocampal) |

### Contrastes Estadísticos y Jerarquía de Hipótesis

1. **Contraste Primario ($H_{1}$):**
   - Comparación pareada intra-semilla entre **Brazo 4 (IdA Completo)** y **Brazo 3 (Voraz con Memoria)**.
   - Variable: Número total de logros desbloqueados por episodio.
   - $H_{1,0}$: La diferencia pareada es igual a cero ($\Delta_{\text{primario}} = \text{Logros}_{B4} - \text{Logros}_{B3} = 0$).
   - $H_{1,1}$: $\Delta_{\text{primario}} \ne 0$ (bilateral, $\alpha = 0.05$).
2. **Efecto Principal de la Arquitectura ($H_{\text{Arq}}$):**
   - $\Delta_{\text{Arq}} = \frac{1}{2} [(\text{Logros}_{B4} - \text{Logros}_{B3}) + (\text{Logros}_{B2} - \text{Logros}_{B1})]$.
   - Mide el excedente organísmico promedio a través de ambos niveles de memoria.
3. **Efecto Principal de la Memoria ($H_{\text{Mem}}$):**
   - $\Delta_{\text{Mem}} = \frac{1}{2} [(\text{Logros}_{B4} - \text{Logros}_{B2}) + (\text{Logros}_{B3} - \text{Logros}_{B1})]$.
   - Mide el impacto neto de disponer de memoria espacial en ambas arquitecturas.
4. **Interacción Arquitectura $\times$ Memoria ($H_{\text{Int}}$):**
   - $\text{Int} = (\text{Logros}_{B4} - \text{Logros}_{B3}) - (\text{Logros}_{B2} - \text{Logros}_{B1})$.
   - Evalúa si IdA aprovecha la memoria con mayor o menor eficacia que el voraz (estimado mediante IC Bootstrap al 95 %).
5. **Control de Comparaciones Múltiples:**
   - El contraste primario se evalúa a $\alpha = 0.05$. Los tres contrastes secundarios ($\Delta_{\text{Arq}}$, $\Delta_{\text{Mem}}$, $\text{Int}$) se ajustan mediante el procedimiento secuencial de Holm-Bonferroni.

---

## 3. Matriz de Decisión y Criterios de Falsación A Priori (TOST)

Se fija a priori un margen de equivalencia práctica de **$\delta_{\text{equiv}} = \pm 1.0$ logro por episodio**. La interpretación de los resultados se regirá por la siguiente tabla exhaustiva:

| Escenario | Condición Empírica Formal | Interpretación Científica Formal |
|---|---|---|
| **Caso A: Solo Memoria (Equivalencia)** | El IC 95 % de $\Delta_{\text{primario}}$ queda contenido enteramente dentro de $[-1.0, +1.0]$ logros (equivalencia demostrada por TOST) y $\Delta_{\text{Mem}} > 0$ ($p_{\text{Holm}} < 0.05$). | **Falsación del excedente bioinspirado:** La ventaja observada en el Exp 002 se debía a la falta de memoria del voraz; una memoria clásica de ingeniería equipara el rendimiento de IdA. |
| **Caso B: Excedente Bioinspirado Demostrado** | Límite inferior del IC 95 % de $\Delta_{\text{primario}} > +1.0$ logro y $p < 0.05$. | **Confirmación de superioridad bioinspirada:** El chasis organísmico aporta una ventaja neta de progresión técnica estadísticamente separable y de relevancia práctica ($\ge 1.0$ logro) frente a la línea base con memoria idéntica. |
| **Caso C: Diferencia Pequeña / Sub-clínica** | $\Delta_{\text{primario}} > 0$ estadísticamente significativo ($p < 0.05$), pero su IC 95 % no supera $+1.0$ logro o cruza $+1.0$. | Existe una ventaja medible pero por debajo del margen de relevancia práctica predefinido ($\le 1.0$ logro). |
| **Caso D: Interacción Sinérgica** | Límite inferior del IC 95 % de $\text{Int} > 0$ ($p_{\text{Holm}} < 0.05$). | IdA aprovecha la memoria espacial de forma sinérgica frente a la heurística voraz gracias a la modulación homeostática. |
| **Caso E: Avería de la Ablación** | $\text{Logros}_{B2} < \text{Logros}_{B1} - 1.0$ logro ($p_{\text{Holm}} < 0.05$). | La ablación de memoria alocéntrica en IdA introdujo una avería mecánica colateral en lugar de aislar el factor memoria. Requiere invalidar y revisar la ablación. |
| **Caso F: Ineficacia de la Memoria** | El IC 95 % de $\Delta_{\text{primario}} \in [-1.0, +1.0]$, pero $\Delta_{\text{Mem}}$ no es significativo ($p_{\text{Holm}} \ge 0.05$). | La memoria espacial implementada no tuvo efecto medible en ninguna de las dos arquitecturas. |
| **Caso G: No Concluyente** | $\Delta_{\text{primario}}$ no alcanza significación ($p \ge 0.05$) pero su IC 95 % desborda el margen $[-1.0, +1.0]$. | Muestra insuficiente para discernir entre diferencia pequeña y equivalencia. |

---

## 4. Paridad Estricta y Prueba de Identidad Automática

1. **Extensión Aditiva Pura:** `crafter_voraz_memoria.py` hereda de `crafter_voraz.py` sin reescribir la jerarquía de decisiones, ni alterar los umbrales de recolección ni la regla de huida ante esqueletos.
2. **Prueba de Identidad Demostrada:** Se ejecutó la verificación automática comparando la secuencia completa de acciones entre `crafter_voraz.py` y `crafter_voraz_memoria.py(memoria_activa=False)` sobre episodios completos hasta muerte o tope (1.409 pasos totales) en las semillas de entrenamiento 2000–2004 bajo chunks deterministas: **5 de 5 semillas fueron 100 % idénticas (0 discrepancias en 1.409 ticks)**.
3. **Mapeo Alocéntrico Idéntico:** Registra estaciones (`table`, `furnace`), fuentes de agua y yacimientos. Elimina dinámicamente las entradas si la casilla visible cambia (ej. mineral picado).
4. **Navegación Fuera de Vista Auditada:** El agente voraz con memoria utiliza BFS global sobre casillas transitables recordadas si el hito está fuera de vista, contabilizando viajes completos (iniciados fuera de vista y concluidos al alcanzar la adyacencia), con 1 a 3 retornos completos efectivos por episodio verificado en semillas de entrenamiento.
5. **Recetas Oficiales Verificadas:** El horno requiere piedra $\ge 4$; el pico de hierro requiere mesa y horno adyacentes y 1 de madera, 1 de carbón y 1 de hierro (`crafter.constants.make`).

---

## 5. Muestra, Semillas y Potencia Estadística

* **Rango de Semillas Vírgenes:** Se evalúan **60 semillas pareadas estrictamente nuevas** de la partición de evaluación:
  $$\text{Semillas } 3040 \text{ a } 3099 \quad (N = 60 \text{ por brazo}, \text{Total } 240 \text{ episodios})$$
  *(Las semillas 3000–3039 quedan excluidas para evitar sobreajuste retrospectivo).*
* **Potencia Estadística:** Con $N = 60$ semillas pareadas y una $\sigma_{\text{diff}} \approx 2.5$ logros, el diseño alcanza una potencia estadística del $80 \%$ ($\beta = 0.20, \alpha = 0.05$) para detectar diferencias pareadas $\ge 0.91$ logros por episodio.
* **Comprobación Previa de los 4 Brazos en Entrenamiento (Semillas 2000–2004):**
  - Brazo 1 (Voraz sin memoria): Mediana 10.0 logros (rango 3–12).
  - Brazo 2 (IdA sin memoria alocéntrica): Mediana 9.0 logros (rango 9–12), 0 excepciones mecánicas.
  - Brazo 3 (Voraz con memoria): Mediana 11.0 logros (rango 8–11), retornos a mesa verificados (1 a 3 completados).
  - Brazo 4 (IdA completo): Mediana 12.0 logros (rango 10–12).
* **Hash Congelado Definitivo:** Se congela el commit previo exacto a la ejecución del código: `6dc8fc2ee1c7fe035ba0d2a5031d8be0c3990622`.
