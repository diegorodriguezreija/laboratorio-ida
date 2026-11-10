# Glosario · Glossary

Términos tal como se usan en IdA. Varios vienen de la biología o la neurociencia: denotan **inspiración**, no equivalencia. · *Terms as used in IdA. Several come from biology or neuroscience: they denote **inspiration**, not equivalence.*

> **Nota sobre los nombres de algunos ficheros.** `nivel_2_sistemas/consciencia_talamo_dmn.py` y `tests_arquitectura/test_funcional_sueno_y_consciencia.py` conservan su nombre por la historia del proyecto (y para no romper imports ni tests); no afirman que IdA tenga consciencia. El primero contiene el bucle talamocortical y la red por defecto descritos abajo.
>
> *Note on some file names. The two files above keep their names for historical reasons (and to avoid breaking imports and tests); they make no claim that IdA is conscious. The first one holds the thalamocortical loop and the default-mode network described below.*

| Término | Term | Significado en IdA · *Meaning in IdA* |
|---|---|---|
| Latido | Tick (heartbeat) | Un paso de decisión del core (`GestorOndaCore.ejecutar_latido`) |
| Onda | Wave | El objeto que acompaña a un latido: pizarra, presupuesto y métricas (`contratos.py`) |
| `ei`, `ev`, `acc`, `ef` | `ei`, `ev`, `acc`, `ef` | Canales de la pizarra: estado inicial (solo lectura), atención, impulsos motores y registro final. El «cuarteto de la experiencia» |
| Amplitud | Amplitude | Presupuesto de escrituras en la pizarra por latido |
| Frecuencia | Frequency | Plazo por latido (100 ms por defecto) |
| Guillotina | Guillotine | Corte del latido cuando se agota el plazo, con `asyncio.wait_for`. Es **cooperativo**: solo corta en puntos `await`; no es tiempo real |
| Barridos reactivo, activo y proactivo | Reactive, active and proactive passes | Las tres llamadas que recibe cada componente en cada latido (`procesar_reactiva`, `procesar_activa`, `procesar_proactiva`). Ningún componente implementa hoy el barrido activo |
| Estaciones | Stations | Sentir, interpretar, reaccionar y actuar: el orden en que un sistema ejecuta sus componentes |
| Pieza | Piece | Unidad de información en la pizarra: identificador, tipo, `arousal`, `trust`, tensor 6D y `product` |
| Predicado, proposición, sentencia, lógica | Predicate, proposition, sentence, logic rule | Tipos de pieza del lenguaje interno formal, con modalidad (hipótesis, demostrado, deducido…) y vínculos (implica, causa, contradice…). Dónde deciden: [ARQUITECTURA §12](ARQUITECTURA.md#12-lenguaje-interno-formal) |
| Tensor 6D | 6D tensor | Vector de percepción: proximidad, magnitud, movimiento, entropía, afinidad nutricional y nocicepción |
| Arousal | Arousal | Urgencia o saliencia de una pieza, en [0, 1] |
| Trust (confianza) | Trust | Fiabilidad de una pieza, en [0, 1] |
| S1, S2, S3 | S1, S2, S3 | Sistemas reactivo, límbico y racional del nivel 2; cada uno ejecuta componentes en estaciones |
| Sistema triuno | Triune system | Los tres sistemas juntos, inspirados en el cerebro triúnico de MacLean |
| Tribunal | Tribunal | `TribunalMotor`: elige qué impulso de `acc` se ejecuta mediante un árbitro |
| Árbitro (A0–A7) | Arbiter (A0–A7) | Regla de decisión intercambiable; A0 es la del Tribunal por defecto |
| Soma | Soma (body state) | `EstadoSomatico`: alimentación, energía, vitalidad, dopamina, cortisol… |
| Cortisol | Cortisol | Variable de estrés del soma; en A0 pondera arousal frente a confianza |
| Arquetipo | Archetype | Rasgos de un individuo (apertura, responsabilidad, neuroticismo, umbral de miedo) |
| Linaje | Lineage | Sucesión de arquetipos y axiomas guardada en JSON entre generaciones |
| Axioma heredado / barrera de Weismann | Inherited axiom / Weismann barrier | Piezas que pasan de un individuo a sus descendientes; la «barrera» filtra por linaje |
| Métrica de integración («Φ») | Integration metric ("Φ") | Métrica inspirada en IIT que se calcula tras cada latido. **No es** la Φ de Tononi ni mide consciencia |
| DMN | DMN (default-mode network) | «Red por defecto»: rebaja el arousal sensorial y repasa la memoria cuando no hay urgencia |
| Bucle talamocortical | Thalamocortical loop | Reentrada al final del latido que deja *priors* para el siguiente |
| Sueño REM | REM sleep | Fase en la que el core consolida reglas y no actúa |
| Autopoiesis AST | AST autopoiesis | Mutación experimental de clases en memoria con `ast` y `exec`; desactivada por defecto |
| Componente de dominio | Domain component | Clase de nivel 3 con conocimiento de un mundo, inyectada en S1, S2 o S3 |
| Membrana | Membrane | Los contratos `ISensorEntorno` e `IActuadorEntorno` |
| Crafter Score | Crafter Score | exp(media de ln(1 + s_i)) − 1, con s_i el % de episodios que desbloquean el logro i de los 22 (Hafner, 2021); se calcula por población |
| Semillas de desarrollo, test y reserva | Development, test and held-out seeds | 0–999 para ajustar; 2000–2999 para medir; 3000–3999 para la medición final, una sola vez |
| Diseño pareado | Paired design | Todas las condiciones se evalúan en las mismas semillas y se comparan semilla a semilla |
| Delta de Cliff | Cliff's delta | Tamaño de efecto no paramétrico en [−1, 1] |
| Holm-Bonferroni | Holm–Bonferroni | Corrección de p-valores por comparaciones múltiples |
| Intervalo de Wilson | Wilson interval | Intervalo de confianza para una proporción |
| Acuerdo contrafactual | Counterfactual agreement | % de latidos en que un árbitro alternativo habría elegido lo mismo que A0 |
