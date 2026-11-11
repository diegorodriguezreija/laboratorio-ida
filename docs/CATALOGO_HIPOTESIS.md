# Catálogo de Hipótesis de Investigación

Este documento recopila el estado formal de todas las hipótesis planteadas en IdA, distinguiendo entre aquellas contrastadas con datos en la reserva y aquellas diseñadas y pendientes de experimentación en el laboratorio.

---

## 1. Hipótesis Evaluadas Formalmente

### Hipótesis H1: Superioridad del Tribunal Motor (A0)
- **Enunciado:** El arbitraje dinámico del Tribunal (`arousal \cdot estrés + confianza \cdot (1 - estrés)`) supera a árbitros más simples con los mismos órganos sensoriales.
- **Predicción a priori:** Apoyada con probabilidad subjetiva 0,25; refutada por A1 o A3 con 0,75.
- **Mundo y muestra:** Crafter, 40 semillas de reserva no vistas (3000–3039).
- **Resultados:**
  - Frente a jerarquías fijas S1>S2>S3: **+8,85 logros** [+7,95; +9,68] (\(p < 0,001\)).
  - Frente a jerarquías fijas S3>S2>S1: **+2,30 logros** [+1,82; +2,80] (\(p < 0,001\)).
  - Frente a «mayor arousal» (A1): +0,72 logros [+0,05; +1,52] (\(p = 0,116\) tras Holm).
  - Frente a «mayor producto» (A3): +0,62 logros [−0,05; +1,43] (\(p = 0,147\) tras Holm).
- **Veredicto:** **Apoyada frente a jerarquías fijas; No apoyada frente a reglas de un solo criterio** debido al 96 % de acuerdo contrafactual.

---

### Hipótesis H7: Contribución del Sistema Límbico (S2)
- **Enunciado:** La presencia de un sistema de valor afectivo (S2) y su ciclo de descanso periódico aporta al rendimiento del organismo.
- **Predicción a priori:** Apoyada 0,05.
- **Mundo y muestra:** Crafter, 40 semillas de reserva (3000–3039).
- **Resultados:**
  - Logros desbloqueados: **+1,40 logros** [+0,65; +2,23] (\(p = 0,002\)).
  - Supervivencia en pasos: **−536 pasos** [−731; −345].
  - Causa de muerte por depredador: 34 de 40 individuos con S2 activo vs. 16 de 40 con S2 neutro.
- **Veredicto:** **Apoyada con coste vital** (mayor asunción de riesgos eleva los logros pero acelera la muerte).

---

### Hipótesis H2: Regulación por Cortisol Somático
- **Enunciado:** Modular dinámicamente la función de arbitraje con la variable somática de cortisol (estrés) mejora el rendimiento global.
- **Predicción a priori:** Apoyada 0,35.
- **Mundo y muestra:** Crafter, 40 semillas de reserva (3000–3039).
- **Resultados:**
  - Diferencia en logros entre cortisol dinámico y fijo: entre −0,35 y +0,12 logros (ninguna comparación significativa tras Holm, \(p \ge 0,19\)).
  - Efecto en la conducta: cuando el cortisol sube de 0,05 a 0,90, las decisiones de S1 aumentan del 32,7 % al 38,7 %.
- **Veredicto:** **No apoyada en rendimiento** (modifica la conducta defensiva pero no incrementa los logros).

---

### Hipótesis de Herencia y Barrera de Weismann
- **Enunciado:** La selección de linaje transmite ventajas adaptativas mediante el ajuste de arquetipos y la herencia de axiomas cognitivos.
- **Mundo y muestra:** Crafter, estudio factorial 2×2 (N=20 en diagnóstico 2000–2019) y réplica en reserva (3000–3039).
- **Resultados:**
  - Arquetipo seleccionado vs. fundador: Crafter Score **5,74 % → 22,31 %**; **+5,22 logros** [+4,35; +6,03] (\(p < 0,001\)).
  - Axiomas heredados (con mismo arquetipo): **+0,00 logros** [−0,07; +0,07] (38 de 40 semillas idénticas).
  - Placebo de 33 axiomas ajenos: rendimiento idéntico a axiomas legítimos.
- **Veredicto:** **Arquetipo apoyado; Axiomas refutados** (el beneficio reside enteramente en los pesos del carácter; la memoria cognitiva aislada no tiene efecto).

---

## 2. Hipótesis Diseñadas y Pendientes de Evaluación

| Id | Hipótesis | Pregunta de Investigación | Estado |
|---|---|---|---|
| **H3** | **Degradación Elegante bajo Guillotina** | ¿Mantiene IdA un comportamiento seguro cuando se recorta el presupuesto temporal a la mitad? | Diseñada. En condiciones normales la guillotina nunca se disparó. Requiere forzar plazos extremos (< 5 ms). |
| **H4** | **Adaptación a Entornos Cambiantes** | ¿Supera IdA a una línea base tradicional cuando las reglas del mundo cambian a mitad de vida? | Diseñada. Pendiente de implementar perturbaciones en el generador de Crafter o reglas invertidas en Snake. |
| **H5** | **Herencia No Codificable a Mano** | ¿Puede la evolución descubrir configuraciones bio-somáticas que un diseñador humano no anticiparía? | Diseñada. Los arquetipos actuales coinciden con los ajustados manualmente. |
| **H6** | **Plasticidad Sináptica TD-Hebbiana** | ¿Mejora el aprendizaje asociativo de 3 factores (dopamina) el desempeño acumulativo? | Diseñada e implementada. Sin efecto demostrado en Crafter. |
| **H8** | **Reutilización Agnóstica del Core** | ¿Puede el núcleo transferirse a un nuevo mundo sin alterar los niveles 1 y 2? | Apoyada cualitativamente (el mundo Mínimo y Snake se añadieron sin tocar el core). |
| **H9** | **Arbitraje Somático Fuera de Juegos** | ¿Aporta el balance vital ventajas en asignación de tareas cooperativas? | Opcional / teórica. |

---

## 3. Réplicas y Diseños Ampliados Planificados

- **R3 (Aislamiento de latidos en desacuerdo):** Evaluar exclusivamente los latidos donde A0 discrepa de A1 y A3 (el 3–4 % de las decisiones) para medir si en esas bifurcaciones críticas A0 salva la vida del individuo.
- **R7 (Réplicas independientes de linaje):** Lanzar 5 linajes evolutivos en paralelo desde distintas semillas para verificar si la convergencia del arquetipo es universal o un artefacto de una sola estirpe.
