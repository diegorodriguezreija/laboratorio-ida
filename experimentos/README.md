# Experimentos del Laboratorio IdA

Cada experimento responde a **una sola pregunta** comparando dos brazos (dos variantes, o una variante frente a la línea base tradicional) con **la misma semilla**.

## Estructura de un Experimento

```
experimentos/
  001-nombre-del-experimento/
    PREGUNTA.md     # Ficha de 5 líneas fijada ANTES de ejecutar
    correr.py       # Ejecuta ambos brazos con idénticas semillas pareadas
    datos/          # Registros y resúmenes numéricos ligeros
    RESULTADO.md    # Veredicto final: una frase, gráfica o resumen numérico
```

## Reglas del Método

1. **Misma semilla en las dos variantes;** solo cambia una cosa.
2. **El veredicto se fija antes de ejecutar.** Si el resultado no cumple el umbral establecido, se califica como «no mejora»; bajo ninguna circunstancia se altera el criterio a posteriori.
3. **Resultado en una gráfica y una frase** en `RESULTADO.md`, y se añade una línea en `INDICE.md`.
4. **Los resultados negativos se archivan con el mismo rigor y valor científico.**
