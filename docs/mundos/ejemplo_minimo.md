# Mundo de ejemplo mínimo (tutorial)

Estado: **tutorial**. Un anillo de claros con fruta y seta que vuelven a crecer; determinista, en memoria, sin ficheros ni red.

```bash
python nivel_3_componentes/mundos/mundo_ejemplo_minimo/ejemplo_minimo_runner.py --latidos 30 --aislar-ruido
```

- Usa los sistemas genéricos S1, S2 y S3 tal cual, sin componentes de dominio.
- Tiene 73 líneas de adaptador y 65 de runner, y se añadió sin modificar los niveles 1 y 2.
- Es la base de la prueba metamórfica del aislamiento (`test_metamorfico_aislamiento.py`) y del tutorial de [`../GOBERNANZA_Y_CONTRATOS.md`](../GOBERNANZA_Y_CONTRATOS.md#4-tutorial-añade-tu-propio-mundo).
