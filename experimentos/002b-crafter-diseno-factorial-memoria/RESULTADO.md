# Resultado Formal: Experimento 002b (Diseño Factorial 2×2 en Crafter 2D)

**Fecha de ejecución:** 11 de noviembre de 2026  
**Commit congelado de código:** `6dc8fc2ee1c7fe035ba0d2a5031d8be0c3990622`  
**Semillas de evaluación vírgenes:** 3040 a 3099 ($N = 60$ semillas pareadas, 240 episodios en total)  
**Datos brutos:** `salidas/002b-crafter-diseno-factorial-memoria/episodios_pareados.csv`  
**Resumen estadístico:** `salidas/002b-crafter-diseno-factorial-memoria/resumen_estadistico.json`

---

## 1. Resumen Ejecutivo y Veredicto Formal

Bajo las condiciones y criterios pre-registrados en [PREGUNTA.md](PREGUNTA.md):

* **Veredicto formal de la tabla de decisión:** **CASO G — No concluyente en equivalencia estricta (en el límite por 0.03 logros frente al Caso A)**.
* **Contraste Primario (Logros por episodio: IdA Canónica B4 vs. Voraz con Memoria B3):**
  * Diferencia media pareada: **$-0.07$ logros** a favor de la línea base con memoria.
  * **IC 95 % Bootstrap percentil:** $[-1.03, +0.92]$ logros.
  * **Aplicación rigurosa de la regla:** Según la condición pre-registrada (IC 95 % enteramente contenido dentro de $[-1.0, +1.0]$), la equivalencia estricta no se alcanza formalmente por $0.03$ logros (límite inferior en $-1.03$). Con el procedimiento TOST convencional ($\alpha = 0.05$, correspondiente a un IC del 90 %), sí se concluye equivalencia práctica ($p_{\text{TOST}} = 0.0316 < 0.05$).
  * **Hallazgo empírico no ambiguo:** El límite superior del intervalo ($+0.92$ logros) **descarta con un 95 % de confianza que exista un excedente bioinspirado relevante ($\ge 1.0$ logro)** en Crafter cuando la línea base tradicional dispone de memoria espacial equivalente.
* **Efectos Factoriales ($2 \times 2$, ajuste Holm-Bonferroni):**
  * **Efecto de la Memoria Espacial:** $\Delta_{\text{Mem}} = +2.85$ logros (IC 95 % $[+2.42, +3.27]$, $p_{\text{Holm}} = 4.16 \times 10^{-10}$).
  * **Efecto de la Arquitectura Bioinspirada:** $\Delta_{\text{Arq}} = +2.37$ logros (IC 95 % $[+1.52, +3.21]$, $p_{\text{Holm}} = 6.67 \times 10^{-6}$).
  * **Interacción Arquitectura $\times$ Memoria:** $\text{Int} = -4.87$ logros (IC 95 % $[-5.75, -3.93]$, $p_{\text{Holm}} = 1.62 \times 10^{-9}$).

---

## 2. Resultados Descriptivos por Brazo Experimental

Tabla resumen de los 4 brazos pareados evaluados sobre las 60 semillas vírgenes (3040–3099):

| Brazo | Arquitectura | Memoria Alocéntrica | Logros (Media ± DE) | Mediana [IQR] | Crafter Score Poblacional | Retornos a Estación Completados |
|---|---|---|---|---|---|---|
| **Brazo 1 (Voraz Reactivo)** | Tradicional | No (Reactivo puro) | $5.58 \pm 2.56$ | $5.0$ $[4.0, 7.0]$ | $6.74 \%$ | 0 |
| **Brazo 2 (IdA Sin Memoria)** | Bioinspirado | No (Ablación alocéntrica) | $10.38 \pm 2.95$ | $11.0$ $[9.0, 13.0]$ | $19.28 \%$ | 0 |
| **Brazo 3 (Voraz con Memoria)** | Tradicional | Sí (Mapa alocéntrico + BFS) | $10.87 \pm 1.79$ | $11.0$ $[10.0, 12.0]$ | $14.05 \%$ | 135 (media 2.25/ep) |
| **Brazo 4 (IdA Canónica)** | Bioinspirado | Sí (Hominis G12 completo) | $10.80 \pm 3.06$ | $11.0$ $[9.0, 13.0]$ | $20.54 \%$ | — (en S3) |

> [!NOTE]
> El Brazo 1 ($5.58$ logros de media) reproduce de forma consistente la evaluación del agente voraz puro en el Experimento 002 ($5.65$ logros), confirmando la ausencia de sesgo o deriva procedimental en la línea base.

---

## 3. Contrastes Estadísticos Formales

### 3.1 Contraste Primario: $H_1$ (Brazo 4 vs. Brazo 3)
* **Variable primaria:** Total de logros desbloqueados por episodio.
* **Estimación puntual:** $-0.07$ logros.
* **IC 95 % Bootstrap percentil (10 000 réplicas):** $[-1.03, +0.92]$ logros.
* **Test pareado de Wilcoxon:** $W = 700.5$, $p = 0.8940$ (dos colas).
* **Test de Equivalencia TOST ($\Delta_0 = \pm 1.0$ logro):**
  * $H_{01} (\mu \le -1.0)$: $t_1 = +1.894, p_1 = 0.0316$.
  * $H_{02} (\mu \ge +1.0)$: $t_2 = -2.164, p_2 = 0.0172$.
  * $p_{\text{TOST}} = \max(p_1, p_2) = 0.0316 < 0.05$.
* **Conclusión formal del contraste:** El límite inferior del IC 95 % rebasa el margen por $0.03$ logros, situando formalmente el caso en G según la regla pre-registrada, aunque TOST convencional alcanza equivalencia al $90 \%$. No se observa excedente bioinspirado relevante ($\ge 1.0$ logro).

### 3.2 Contrastes Secundarios Factoriales (Corrección Holm-Bonferroni)
1. **Efecto Principal de Memoria ($\Delta_{\text{Mem}}$):**
   * $\frac{1}{2} [(\text{B4} - \text{B2}) + (\text{B3} - \text{B1})] = +2.85$ logros (IC 95 % $[+2.42, +3.27]$).
   * $p_{\text{crudo}} = 1.39 \times 10^{-10}$, $p_{\text{Holm}} = 4.16 \times 10^{-10}$ ($\alpha_1 = 0.0167$). **Significativo**.
2. **Efecto Principal de Arquitectura ($\Delta_{\text{Arq}}$):**
   * $\frac{1}{2} [(\text{B4} - \text{B3}) + (\text{B2} - \text{B1})] = +2.37$ logros (IC 95 % $[+1.52, +3.21]$).
   * $p_{\text{crudo}} = 6.67 \times 10^{-6}$, $p_{\text{Holm}} = 6.67 \times 10^{-6}$ ($\alpha_2 = 0.05$). **Significativo**.
3. **Interacción Arquitectura $\times$ Memoria ($\text{Int}$):**
   * $(\text{B4} - \text{B3}) - (\text{B2} - \text{B1}) = -4.87$ logros (IC 95 % $[-5.75, -3.93]$).
   * $p_{\text{crudo}} = 8.12 \times 10^{-10}$, $p_{\text{Holm}} = 1.62 \times 10^{-9}$ ($\alpha_3 = 0.025$). **Significativo**.

### 3.3 Métrica Secundaria: Crafter Score Poblacional
* Brazo 4 (IdA Canónica): $20.54 \%$
* Brazo 3 (Voraz con Memoria): $14.05 \%$
* Diferencia puntual: **$+6.49$ puntos porcentuales (pp)**
* IC 95 % Bootstrap percentil pareado: $[+3.90\text{ pp}, +8.56\text{ pp}]$

---

## 4. Desglose de Tasas de Éxito por Logro (60 Episodios por Brazo)

| Logro | Brazo 1 (Voraz Reactivo) | Brazo 2 (IdA Sin Memoria) | Brazo 3 (Voraz Memoria) | Brazo 4 (IdA Canónica) |
|---|---|---|---|---|
| `collect_wood` | $100.0 \%$ (60) | $100.0 \%$ (60) | $100.0 \%$ (60) | $100.0 \%$ (60) |
| `place_table` | $100.0 \%$ (60) | $96.7 \%$ (58) | $100.0 \%$ (60) | $96.7 \%$ (58) |
| `make_wood_pickaxe` | $26.7 \%$ (16) | $96.7 \%$ (58) | $100.0 \%$ (60) | $96.7 \%$ (58) |
| `make_wood_sword` | $15.0 \%$ (9) | $96.7 \%$ (58) | $98.3 \%$ (59) | $96.7 \%$ (58) |
| `collect_stone` | $25.0 \%$ (15) | $78.3 \%$ (47) | $96.7 \%$ (58) | $80.0 \%$ (48) |
| `make_stone_pickaxe` | $13.3 \%$ (8) | $66.7 \%$ (40) | $93.3 \%$ (56) | $70.0 \%$ (42) |
| `place_furnace` | $11.7 \%$ (7) | $33.3 \%$ (20) | $91.7 \%$ (55) | $36.7 \%$ (22) |
| `collect_coal` | $8.3 \%$ (5) | $43.3 \%$ (26) | $60.0 \%$ (36) | $50.0 \%$ (30) |
| `collect_iron` | $5.0 \%$ (3) | $16.7 \%$ (10) | $48.3 \%$ (29) | $16.7 \%$ (10) |
| `make_iron_pickaxe` | $0.0 \%$ (0) | $1.7 \%$ (1) | $0.0 \%$ (0) | $3.3 \%$ (2) |
| `make_stone_sword` | $0.0 \%$ (0) | $50.0 \%$ (30) | $0.0 \%$ (0) | $56.7 \%$ (34) |
| `eat_cow` | $80.0 \%$ (48) | $68.3 \%$ (41) | $83.3 \%$ (50) | $68.3 \%$ (41) |
| `collect_drink` | $80.0 \%$ (48) | $90.0 \%$ (54) | $91.7 \%$ (55) | $91.7 \%$ (55) |
| `defeat_zombie` | $80.0 \%$ (48) | $76.7 \%$ (46) | $81.7 \%$ (49) | $78.3 \%$ (47) |
| `defeat_skeleton` | $5.0 \%$ (3) | $55.0 \%$ (33) | $20.0 \%$ (12) | $56.7 \%$ (34) |
| `wake_up` | $8.3 \%$ (5) | $23.3 \%$ (14) | $21.7 \%$ (13) | $28.3 \%$ (17) |
| `place_stone` | $0.0 \%$ (0) | $45.0 \%$ (27) | $0.0 \%$ (0) | $53.3 \%$ (32) |
| `collect_diamond` | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) |
| `collect_sapling` | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) |
| `eat_plant` | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 %$ (0) |
| `make_iron_sword` | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 %$ (0) |
| `place_plant` | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 %$ (0) |

---

## 5. Interpretación Científica y Discusión

### 5.1 No se Observa Excedente Bioinspirado en Logros Brutos
La aparente superioridad de IdA v12.0 en número de logros por episodio reportada en el Experimento 002 ($11.53$ vs. $5.65$) no se sostiene cuando la línea base tradicional se dota de memoria espacial alocéntrica equivalente ($10.80$ vs. $10.87$, diferencia de $-0.07$ logros). El límite superior del IC 95 % ($+0.92$) descarta una ventaja bioinspirada de $1.0$ logro o más. La asimetría de memoria fue el factor causal determinante de la brecha observada en el Exp 002.

### 5.2 La Interacción Negativa: ¿Resiliencia Homeostática o Ablación Incompleta?
La interacción estadística negativa ($\text{Int} = -4.87$ logros) refleja que el impacto de retirar la memoria alocéntrica es radicalmente asimétrico:
- El voraz colapsa de $10.87$ a $5.58$ logros ($-5.29$ logros).
- IdA apenas varía de $10.80$ a $10.38$ logros ($-0.42$ logros).

Sin embargo, esta diferencia **no puede atribuirse de forma concluyente a la modulación somático-homeostática**. Existe una explicación metodológica alternativa y más parsimoniosa:
- El Brazo 2 anuló la consulta al mapa alocéntrico (`consultar_hitos_alocentricos`), pero **mantuvo intacta la memoria de trabajo somática y los perceptos activos en el core**.
- El Brazo 1, en cambio, carece por completo de cualquier retención entre ticks.
- Por tanto, la memoria residual de trabajo de IdA podría retener ubicaciones o recursos recientes, amortiguando la pérdida del mapa alocéntrico. La modulación homeostática es solo una hipótesis entre otras; discernir ambas requiere un experimento futuro con ablación explícita de la memoria de trabajo espacial.

### 5.3 Origen de la Brecha en Crafter Score: Reglas de Dominio de la Línea Base
Aunque ambos agentes alcanzan un volumen idéntico de logros brutos (~11 logros), IdA mantiene una ventaja de $+6.49\text{ pp}$ en Crafter Score poblacional ($20.54 \%$ frente a $14.05 \%$). Este excedente no demuestra una propiedad emergente de la arquitectura bioinspirada, sino que se explica en gran medida por la especificación de las reglas de dominio del agente voraz:
1. **Logros no programados en la línea base:** `make_stone_sword` ($56.7 \%$ en IdA vs. $0.0 \%$ en Voraz) y `place_stone` ($53.3 \%$ en IdA vs. $0.0 \%$ en Voraz). La máquina de estados de `crafter_voraz.py` no incluye transiciones hacia estos dos logros, por lo que el voraz nunca los intenta. Al calcular la media geométrica exponencial del Crafter Score, los ceros penalizan drásticamente la puntuación.
2. **Combate contra esqueletos:** La tasa de victoria frente a esqueletos ($56.7 \%$ en IdA vs. $20.0 \%$ en Voraz) refleja principalmente la regla de huida reactiva del voraz (mantenida intacta respecto al Exp 002), frente a la modulación de arousal/miedo de IdA que permite enfrentar a distancia corta con espada.

---

## 6. Conclusión en una Frase

> **Con memoria espacial equiparada, IdA no supera a la línea base tradicional en logros (se descarta un excedente $\ge 1.0$ logro, con equivalencia en el límite por $0.03$ logros); las diferencias en Crafter Score reflejan principalmente logros no programados en el voraz, y la menor sensibilidad de IdA a la falta de mapa alocéntrico puede obedecer a la persistencia de su memoria de trabajo.**
