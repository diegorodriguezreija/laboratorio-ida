# Experimento 002: Contraste Empírico de Rendimiento en Crafter 2D — IdA vs. Agente Voraz

## 1. Pregunta Experimental

> **¿Supera el organismo bioinspirado IdA v12.0 a un agente voraz tradicional basado en reglas y a un agente aleatorio uniforme en el entorno de supervivencia procedural Crafter 2D bajo paridad estricta de observación y acción?**

---

## 2. Hipótesis Formal

### Hipótesis Principal ($H_1$, Bilateral)
* **$H_0$**: La mediana de la diferencia pareada en el Crafter Score poblacional (Hafner, 2021) entre IdA y el Agente Voraz en las mismas semillas de Crafter es igual a cero:
  $$\Delta_{\text{CrafterScore}} = \text{CrafterScore}_{\text{IdA}} - \text{CrafterScore}_{\text{Voraz}} = 0$$
* **$H_1$**: La diferencia pareada en el Crafter Score entre IdA y el Agente Voraz difiere significativamente de cero ($\Delta_{\text{CrafterScore}} \ne 0$).

### Hipótesis Secundaria ($H_2$, Unilateral)
* **Supervivencia (Pasos de vida)**:
  - $H_{2,0}$: $\text{Pasos}_{\text{IdA}} \le \text{Pasos}_{\text{Voraz}}$
  - $H_{2,1}$: $\text{Pasos}_{\text{IdA}} > \text{Pasos}_{\text{Voraz}}$ (IdA sobrevive sistemáticamente más pasos debido a la modulación homeostática triúnica).

---

## 3. Protocolo Experimental y Brazos de Comparación

Se evalúan 3 brazos empíricos sobre exactamente las mismas **40 semillas pareadas** extraídas de la partición de evaluación reservada (`semillas 3000 a 3039`):

1. **Brazo IdA (Organismo Bioinspirado)**:
   - Configuración canónica de IdA v12.0 con arquitectura triúnica ($S_1$ reactivo, $S_2$ límbico, $S_3$ deliberativo).
   - Arquetipo seleccionado del linaje (`Hominis_G12`) con su acervo de axiomas ancestrales weismannianos consolidados.
   - Presupuesto de vida: máximo 10.000 pasos por episodio (estándar de Crafter) o muerte biológica.
2. **Brazo Voraz (Línea Base Tradicional, `crafter_voraz.py`)**:
   - Sistema experto determinista con jerarquía fija de prioridades a priori:
     1. Autodefensa/huida táctica frente a depredadores adyacentes.
     2. Hidratación crítica ($\text{bebida} \le 4$).
     3. Nutrición crítica ($\text{comida} \le 4$).
     4. Sueño restaurador ($\text{energía} \le 2$ o nocturno).
     5. Hidratación/nutrición preventiva si hay recurso adyacente.
     6. Progresión en árbol tecnológico (madera $\to$ mesa de trabajo $\to$ pico de madera $\to$ espada $\to$ piedra $\to$ horno $\to$ hierro).
     7. Recolección de recursos visibles.
     8. Exploración heurística para evitar ciclos locales.
   - **Garantía de Paridad (Fair Play)**: Restricción estricta a la vista local observable (radio 6, $9 \times 9$ celdas) e inventario propiocepctivo. Prohibido el acceso al mapa global $64 \times 64$.
3. **Brazo Aleatorio (Control Suelo)**:
   - Agente que selecciona en cada paso de tiempo una acción uniforme aleatoria del espacio de acciones legales de Crafter (17 acciones). Ancla el cero de la escala de capacidad.

---

## 4. Métricas Predefinidas y Regla de Veredicto

### Métrica Primaria: Crafter Score Canónico
$$\text{Crafter Score} = \exp\left( \frac{1}{22} \sum_{i=1}^{22} \ln(1 + s_i) \right) - 1$$
Donde $s_i \in [0, 100]$ es el porcentaje de episodios en los que se desbloqueó el logro $i$ de los 22 logros oficiales de Crafter.

### Métricas Secundarias: Desglose por Logro y Supervivencia
1. **Pasos de vida**: Duración en ticks del episodio antes de morir por inanición, deshidratación o daño por depredador.
2. **Tasa de Logros Básicos de Supervivencia**:
   - `collect_sapling`, `collect_wood`, `drink_water`, `eat_plant`, `eat_cow`.
3. **Tasa de Logros de Combate y Nocicepción**:
   - `defeat_zombie`, `defeat_skeleton`.
4. **Tasa de Logros de Progresión Técnica**:
   - `place_table`, `make_wood_pickaxe`, `make_wood_sword`, `collect_stone`, `place_furnace`, `make_stone_pickaxe`, `make_stone_sword`, `collect_coal`, `collect_iron`, `make_iron_pickaxe`.

### Criterio de Falsación y Veredicto (Fijado A Priori)
* **Supera al tradicional**:
  - Test de Wilcoxon pareado sobre el Crafter Score con $p < 0.05$ (bilateral).
  - Intervalo de confianza Bootstrap al 95% de la diferencia pareada estrictamente superior a cero ($\text{IC}_{95\%} > 0$).
  - O bien, si el Crafter Score global es equivalente, ventaja estadísticamente significativa en pasos de supervivencia ($p < 0.05$, unilateral) o en la tasa de logros técnicos avanzados.
* **No supera / Equivalente**:
  - Si el $p$-valor de Wilcoxon es $\ge 0.05$ o el IC al 95% cruza el cero.
* **Empeora**:
  - Si el Agente Voraz supera significativamente a IdA en Crafter Score ($p < 0.05$ a favor de la línea base).

---

## 5. Condiciones de Reproducibilidad
* Semillas pareadas: `3000` a `3039` ($N = 40$).
* Salidas crudas: `salidas/002-crafter-ida-vs-voraz/episodios_pareados.csv`.
* Prohibición absoluta de reajustar los umbrales o la jerarquía de `crafter_voraz.py` tras observar los resultados de la corrida.
