# Gobernanza y contratos

Versión 12.0.0 · 7 de noviembre de 2026.

Cómo se protege la separación entre el core (niveles 1 y 2) y los mundos (nivel 3), cómo se versionan los contratos y cómo se añade un mundo nuevo.

## 1. Protocolo de aislamiento

1. **Los niveles 1 y 2 no conocen ningún mundo.** No contienen vocabulario de dominio (nombres de juegos, piezas, objetos), no importan librerías de E/S, red, interfaz o mundo, y no importan nada del nivel 3. La excepción acotada son los motores de persistencia y entropía del nivel 1 (`motor_sqlite_wal.py`, `motor_pgvector.py`, `cosechador_termodinamico.py`), que pueden importar módulos del sistema.
2. **El nivel 3 inyecta, el core no pide.** Los mundos se conectan por los protocolos `ISensorEntorno` e `IActuadorEntorno` y, si lo necesitan, inyectan componentes en las estaciones de S1, S2 y S3. El core nunca importa un mundo (inversión de control).
3. **Lo hace cumplir un test, no la buena voluntad.** [`test_linter_pureza.py`](../tests_arquitectura/test_linter_pureza.py) falla si se rompe la regla 1 en los términos que es capaz de detectar. Su cobertura exacta (qué detecta y qué no) está en [`ARQUITECTURA.md`](ARQUITECTURA.md#5-el-linter-como-función-de-aptitud-arquitectónica). La prueba metamórfica ([`test_metamorfico_aislamiento.py`](../tests_arquitectura/test_metamorfico_aislamiento.py)) comprueba la conducta, no solo el texto.
4. **El linter no se relaja para que pase un cambio.** Si un cambio en los niveles 1 o 2 necesita vocabulario de dominio, el cambio va en el nivel 3. Ampliar la lista de términos prohibidos sí está permitido.
5. **Lo que el linter no ve también cuenta.** Construir cadenas en tiempo de ejecución, imports dinámicos o umbrales afinados para un mundo concreto violan el protocolo aunque el test pase.

## 2. Versionado de los contratos

Cada nivel declara su versión en su `__init__.py` (`nivel_1_core` 12.0.0; `nivel_2_sistemas` 12.1.0). Se sigue el versionado semántico:

| Tipo de versión | Qué puede cambiar | Ejemplos |
|---|---|---|
| Parche (x.y.**Z**) | Correcciones internas sin cambiar firmas ni significado | Arreglar un cálculo dentro de un árbitro |
| Menor (x.**Y**.0) | Añadidos compatibles hacia atrás | Nuevo árbitro registrado; nuevo parámetro opcional con valor por defecto que conserva la conducta anterior (así entraron `arbitro` y `modo_ablacion` en `GestorOndaCore`) |
| Mayor (**X**.0.0) | Cambios incompatibles | Cambiar la firma de `percibir_mundo`, quitar un `V_Comando`, cambiar la dimensión del tensor sensorial |

Superficie pública que se versiona: `Pieza`, `Onda`, `DimensionReactiva`, `ISensorEntorno`, `IActuadorEntorno`, `ResultadoEfectoEntorno`, `Arquetipo` (`contratos.py`); los enumerados de `vocabulario.py`; los constructores de `GestorOndaCore` y `TribunalMotor`, y `crear_sistema_s1/s2/s3`.

## 3. Reglas de contribución que protegen la arquitectura

- Un commit por cambio, con mensaje descriptivo. Los cambios de conducta van en su propio commit y, si alteran resultados, detrás de un flag.
- No se modifican tests, linter ni umbrales para que algo pase.
- Toda cifra pública sale de un CSV versionado y de un script que la regenera (`analisis/generar_tablas.py`).
- Las reglas para agentes de IA están en [`AGENTS.md`](../AGENTS.md).

## 4. Tutorial: añade tu propio mundo

El mundo de ejemplo mínimo ([`nivel_3_componentes/mundos/mundo_ejemplo_minimo/`](../nivel_3_componentes/mundos/mundo_ejemplo_minimo/)) tiene 73 líneas de código de adaptador y 65 de runner (sin contar comentarios ni líneas en blanco; [`coste_adaptacion.csv`](../analisis/resultados/coste_adaptacion.csv)) y se añadió sin modificar los niveles 1 y 2. Sigue los mismos pasos para tu mundo.

### Paso 1 · Crea la carpeta

`nivel_3_componentes/mundos/mundo_<nombre>/` con `adaptador_<nombre>.py` y un runner. Todo lo que sepa de tu dominio vive aquí.

### Paso 2 · Implementa el sensor

```python
def percibir_mundo(self) -> Tuple[str, List[Pieza], List[str]]:
    piezas = [Pieza(
        id="fruta_2",                      # identificador libre: el core no lo interpreta
        tipo_componente="Escena",
        arousal=0.75, trust=0.90,          # urgencia y fiabilidad en [0, 1]
        tensor_sensorial=np.array([1.0, 0.4, 0.5, 0.3, 0.95, 0.05]),
        product={"es_nutritivo": True, "es_letal": False},
    )]
    return "claro_2", piezas, ["claro_1", "claro_3"]   # nodo actual, piezas, vecinos
```

Las 6 dimensiones del tensor son proximidad, magnitud, movimiento, entropía, afinidad nutricional y nocicepción. El core decide a partir de ellas y de las banderas de `product`, nunca a partir del nombre.

### Paso 3 · Implementa el actuador

```python
def ejecutar_comando_fisico(self, comando, target, factor_fauces=1.0, payload_extra=None):
    if comando == V_Comando.MOVER and target in self._vecinos():
        self.posicion = ...
        return ResultadoEfectoEntorno(exito=True, comando=comando, target=target, nueva_ubicacion=target)
    if comando == V_Comando.DEGLUTIR and ...:
        return ResultadoEfectoEntorno(exito=True, comando=comando, target=target, delta_alimentacion=12.0)
    return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)
```

Devuelve `exito=False` cuando la acción no tiene efecto. Un «éxito» sin cambio en el mundo puede dejar al agente repitiendo la misma acción; le pasó al primer borrador del ejemplo mínimo con `COGER`.

### Paso 4 · Conecta el core

```python
core = GestorOndaCore(
    sensor=adaptador, actuador=adaptador, arquetipo=Arquetipo(nombre="Ejemplo"),
    sistemas_cognitivos=[crear_sistema_s1(MatrizHebbianaTresFactores()), crear_sistema_s2(), crear_sistema_s3()],
    bucle_talamocortical=BucleTalamocortical(), dmn=RedNeuronalPorDefecto(),
    gestor_sueno_rem=GestorCicloSuenoREM(), cirujano_ast=None,
)
onda = await core.ejecutar_latido()
```

Si tu mundo necesita conocimiento táctico que los sistemas genéricos no tienen, escribe un componente de dominio que herede de `ComponenteCognitivoBase` (`nivel_2_sistemas/sistema_base.py`) e inyéctalo en la estación correspondiente, como hacen Crafter, Snake y Ajedrez.

### Paso 5 · Comprueba que no tocaste el core

```bash
python -m pytest tests_arquitectura/test_linter_pureza.py     # el linter sigue en verde
git diff --stat main -- nivel_1_core nivel_2_sistemas          # debe estar vacío
python analisis/coste_adaptacion.py --out salidas/coste.csv   # líneas y ficheros de tu mundo
```

### Paso 6 · Mídelo

Añade un test que ejecute unos latidos con el ruido aislado (`core.cosechador.cosechar_unidad_uniforme = lambda: 0.5`) y compruebe algo observable. Si quieres afirmar que el core aporta algo en tu mundo, compáralo con un baseline sencillo y con árbitros alternativos, como en H1, usando semillas que no hayas usado para ajustar.
