# Cómo contribuir

Gracias por el interés. IdA es un proyecto de aprendizaje y experimentación; las contribuciones son bienvenidas si respetan la arquitectura y la disciplina de medición.

## Entorno

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    ·    Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q
```

Los tests que necesitan Internet llevan la marca `network` y no forman parte de la CI obligatoria: `python -m pytest -m "not network"`.

## Qué no se puede relajar

- El linter arquitectónico (`tests_arquitectura/test_linter_pureza.py`) y los tests en general. No se borran ni se debilitan aserciones para que un cambio pase.
- La separación de niveles: nada de vocabulario de dominio ni imports de mundo en `nivel_1_core/` y `nivel_2_sistemas/` (ver [`docs/GOBERNANZA_Y_CONTRATOS.md`](docs/GOBERNANZA_Y_CONTRATOS.md)).
- La separación de licencias: `chess` solo se importa dentro de `nivel_3_componentes/mundos/mundo_ajedrez/` (ver [`NOTICE`](NOTICE)).
- Las particiones de semillas: desarrollo 0–999, test 2000–2999, reserva 3000–3999.

## Lista de comprobación del pull request

- [ ] `python -m pytest -q` en verde.
- [ ] Un commit por cambio, con mensaje descriptivo.
- [ ] Si cambia la conducta, va en su propio commit y está explicado (y detrás de un flag si altera resultados medidos).
- [ ] Ningún programa escribe en las carpetas de código; las salidas van a `IDA_OUT_DIR`.
- [ ] Si se publican cifras nuevas: CSV versionado, preregistro y tablas regeneradas con `python analisis/generar_tablas.py`.
- [ ] Sin rutas absolutas, secretos ni datos personales.
- [ ] Documentación actualizada (y la versión inglesa si cambia algo que aparece en `README.en.md`).

## Cómo informar de un problema

Abre un *issue* con la plantilla correspondiente. Para problemas de seguridad, sigue [`SECURITY.md`](SECURITY.md).
