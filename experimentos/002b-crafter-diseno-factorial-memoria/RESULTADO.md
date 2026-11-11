# Resultado Formal: Experimento 002b (Diseño Factorial 2×2 en Crafter 2D)

**Fecha de ejecución:** 11 de noviembre de 2026  
**Commit congelado de código:** `6dc8fc2ee1c7fe035ba0d2a5031d8be0c3990622`  
**Semillas de evaluación vírgenes:** 3040 a 3099 ($N = 60$ semillas pareadas, 240 episodios en total)  
**Datos brutos:** `salidas/002b-crafter-diseno-factorial-memoria/episodios_pareados.csv`  
**Resumen estadístico:** `salidas/002b-crafter-diseno-factorial-memoria/resumen_estadistico.json`

---

## 1. Resumen Ejecutivo y Veredicto Formal

Bajo las condiciones pre-registradas en [PREGUNTA.md](file:///f:/laboratorio-ida/experimentos/002b-crafter-diseno-factorial-memoria/PREGUNTA.md):
- **Veredicto formal:** **CASO A — Solo Memoria (Equivalencia Demostrada en Métrica Primaria)**.
- **Contraste Primario (Logros/episodio entre IdA Canónica B4 y Voraz con Memoria B3):**
  - Diferencia media pareada: **$-0.07$ logros** (IC 95 % bootstrap percentil $[-1.03, +0.92]$ logros).
  - Wilcoxon signed-rank: $W = 700.5$, $p = 0.8940$ (sin diferencia estadísticamente detectable).
  - TOST (Two One-Sided Tests, margen $\pm 1.0$ logro): $t_1 = 1.894$ ($p_1 = 0.0316$), $t_2 = -2.164$ ($p_2 = 0.0172$), $p_{\text{TOST}} = 0.0316 < 0.05$. **Equivalencia práctica demostrada**.
- **Efecto de la Memoria Espacial:**
  - $\Delta_{\text{Mem}} = +2.85$ logros (IC 95 % $[+2.42, +3.27]$ logros, $p_{\text{Holm}} = 4.16 \times 10^{-10}$).
- **Efecto de la Arquitectura Bioinspirada:**
  - $\Delta_{\text{Arq}} = +2.37$ logros (IC 95 % $[+1.52, +3.21]$ logros, $p_{\text{Holm}} = 6.67 \times 10^{-6}$).
- **Interacción Arquitectura $\times$ Memoria:**
  - $\text{Int} = -4.87$ logros (IC 95 % $[-5.75, -3.93]$ logros, $p_{\text{Holm}} = 1.62 \times 10^{-9}$).

---

## 2. Resultados Descriptivos por Brazo Experimental

Tabla resumen de los 4 brazos pareados evaluados sobre las mismas 60 semillas vírgenes (3040–3099):

| Brazo | Arquitectura | Memoria Alocéntrica | Logros (Media ± DE) | Logros (Mediana [IQR]) | Crafter Score Poblacional | Retornos a Estación Completados |
|---|---|---|---|---|---|---|
| **Brazo 1 (Voraz Reactivo)** | Tradicional | No (Reactivo puro) | $5.58 \pm 2.56$ | $5.0$ $[4.0, 7.0]$ | $6.74 \%$ | 0 |
| **Brazo 2 (IdA Sin Memoria)** | Bioinspirado | No (Ablación alocéntrica) | $10.38 \pm 2.95$ | $11.0$ $[9.0, 13.0]$ | $19.28 \%$ | 0 |
| **Brazo 3 (Voraz con Memoria)** | Tradicional | Sí (Mapa alocéntrico + BFS) | $10.87 \pm 1.79$ | $11.0$ $[10.0, 12.0]$ | $14.05 \%$ | 135 (media 2.25/ep) |
| **Brazo 4 (IdA Canónica)** | Bioinspirado | Sí (Hominis G12 completo) | $10.80 \pm 3.06$ | $11.0$ $[9.0, 13.0]$ | $20.54 \%$ | — (implícito en S3) |

---

## 3. Contrastes Estadísticos Pre-registrados

### 3.1 Contraste Primario: $H_1$ (Brazo 4 vs. Brazo 3)
- **Variable primaria pre-registrada:** Total de logros desbloqueados por episodio (métrica con soporte por semilla).
- **Estimación puntual:** $-0.07$ logros a favor de la línea base con memoria.
- **IC 95 % Bootstrap (10 000 réplicas):** $[-1.03, +0.92]$ logros.
- **Test de Equivalencia TOST:** Margen de equivalencia a priori fijado en $\Delta_0 = \pm 1.0$ logro.
  - Rechazo de $H_{01} (\mu \le -1.0)$: $t = +1.894, p = 0.0316$.
  - Rechazo de $H_{02} (\mu \ge +1.0)$: $t = -2.164, p = 0.0172$.
  - $p_{\text{TOST}} = \max(p_1, p_2) = 0.0316 < 0.05$. Se concluye equivalencia estadística práctica entre ambas arquitecturas cuando ambas disponen de memoria alocéntrica.

### 3.2 Contrastes Secundarios Factoriales (Corrección Holm-Bonferroni)
Para controlar la tasa de error por familia (FWER $\alpha = 0.05$):

1. **Efecto Principal de Memoria ($\Delta_{\text{Mem}}$):**
   - Media: $+2.85$ logros (IC 95 % $[+2.42, +3.27]$).
   - $p_{\text{crudo}} = 1.39 \times 10^{-10}$, $p_{\text{Holm}} = 4.16 \times 10^{-10}$ ($\alpha_1 = 0.0167$). **Significativo**.
2. **Efecto Principal de Arquitectura ($\Delta_{\text{Arq}}$):**
   - Media: $+2.37$ logros (IC 95 % $[+1.52, +3.21]$).
   - $p_{\text{crudo}} = 6.67 \times 10^{-6}$, $p_{\text{Holm}} = 6.67 \times 10^{-6}$ ($\alpha_2 = 0.05$). **Significativo**.
3. **Interacción Arquitectura $\times$ Memoria ($\text{Int}$):**
   - Media: $-4.87$ logros (IC 95 % $[-5.75, -3.93]$).
   - $p_{\text{crudo}} = 8.12 \times 10^{-10}$, $p_{\text{Holm}} = 1.62 \times 10^{-9}$ ($\alpha_3 = 0.025$). **Significativo**.

### 3.3 Métrica Secundaria: Crafter Score Poblacional
El Crafter Score mide la media geométrica exponencial de las tasas de éxito de los 22 logros.
- Brazo 4 (IdA Canónica): $20.54 \%$
- Brazo 3 (Voraz con Memoria): $14.05 \%$
- Diferencia puntual: **$+6.49$ puntos porcentuales (pp)**
- IC 95 % Bootstrap percentil pareado: $[+3.90\text{ pp}, +8.56\text{ pp}]$

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
| `collect_iron` | $5.0 \%$ (3) | $16.7 \%$ (10) | $48.3 \%$ (29) | $16.7 Fak% (10) |
| `make_iron_pickaxe` | $0.0 \%$ (0) | $1.7 \%$ (1) | $0.0 \%$ (0) | $3.3 \%$ (2) |
| `make_stone_sword` | $0.0 \%$ (0) | $50.0 \%$ (30) | $0.0 \%$ (0) | $56.7 \%$ (34) |
| `eat_cow` | $80.0 \%$ (48) | $68.3 \%$ (41) | $83.3 \%$ (50) | $68.3 \%$ (41) |
| `collect_drink` | $80.0 \%$ (48) | $90.0 \%$ (54) | $91.7 \%$ (55) | $91.7 \%$ (55) |
| `defeat_zombie` | $80.0 \%$ (48) | $76.7% $ (46) | $81.7 \%$ (49) | $78.3 \%$ (47) |
| `defeat_skeleton` | $5.0 \%$ (3) | $55.0 \%$ (33) | $20.0 \%$ (12) | $56.7 \%$ (34) |
| `wake_up` | $8.3 \%$ (5) | $23.3 \%$ (14) | $21.7 \%$ (13) | $28.3 \%$ (17) |
| `place_stone` | $0.0 \%$ (0) | $45.0 \%$ (27) | $0.0 \%$ (0) | $53.3 \%$ (32) |
| `collect_diamond` | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) |
| `collect_sapling` | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) |
| `eat_plant` | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) |
| `make_iron_sword` | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) |
| `place_plant` | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) | $0.0 \%$ (0) |

---

## 5. Interpretación Científica y Conclusiones

1. **Falsación de la Hipótesis del Excedente Bioinspirado en Cantidad Bruta de Logros:**
   La ventaja en número de logros por episodio reportada en el Experimento 002 ($10.70$ vs. $5.65$) desaparece cuando la línea base tradicional incorpora memoria espacial alocéntrica idéntica ($10.80$ vs. $10.87$, diferencia de $-0.07$ logros, equivalencia demostrada por TOST).
2. **Naturaleza de la Asimetría Observada en el Exp 002:**
   El factor explicativo dominante de la diferencia en el Experimento 002 fue la asimetría de memoria. Un agente de ingeniería voraz dotado de un mapa de casillas transitables y BFS alcanza la misma cantidad de logros brutos que el organismo bioinspirado.
3. **Resiliencia de la Arquitectura Bioinspirada ante la Ausencia de Memoria:**
   La interacción estadística altamente negativa ($\text{Int} = -4.87$ logros, $p = 1.62 \times 10^{-9}$) ilustra que la arquitectura bioinspirada es notablemente más resiliente ante la falta de memoria que la línea base tradicional:
   - Al quitarle la memoria al voraz, este colapsa de $10.87$ a $5.58$ logros ($-5.29$ logros) debido a que no puede reencontrar la mesa de trabajo ni las fuentes de agua fuera de vista.
   - Al quitarle la memoria alocéntrica a IdA, su rendimiento apenas desciende de $10.80$ a $10.38$ logros ($-0.42$ logros), amortiguado por la modulación homeostática de necesidades y la memoria de trabajo basal.
4. **Discrepancia Cualitativa en el Crafter Score:**
   Aunque ambos agentes empatan en el número bruto de logros (~11 logros por episodio), su perfil técnico es cualitativamente distinto:
   - El voraz con memoria concentra sus logros en la rama extractiva-industrial (`collect_stone` $96.7 \%$, `place_furnace` $91.7 \%$, `collect_iron` $48.3 %$).
   - IdA diversifica hacia la rama de supervivencia y combate (`defeat_skeleton` $56.7 \%$ vs $20.0 \%$, `make_stone_sword` $56.7 \%$ vs $0.0 %$, `place_stone` $53.3 \%$ vs $0.0 %$), lo que le confiere un Crafter Score poblacional superior en $+6.49\text{ pp}$.
