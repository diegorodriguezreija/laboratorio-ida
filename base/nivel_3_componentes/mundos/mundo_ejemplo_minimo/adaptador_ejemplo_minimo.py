"""
Mundo de ejemplo mínimo (tutorial, D12/R8).

Un anillo de N claros. Cada claro puede tener una fruta (nutritiva), una seta (tóxica) o nada;
lo comido o retirado vuelve a crecer al cabo de unos latidos. Todo es determinista y en memoria:
no lee ni escribe ficheros ni usa la red.

Sirve para dos cosas:
1. Enseñar qué hace falta para conectar un mundo al core: implementar percibir_mundo
   (ISensorEntorno) y ejecutar_comando_fisico (IActuadorEntorno).
2. Prueba metamórfica del aislamiento (N7): el parámetro `nombres` cambia todos los
   identificadores visibles para el core sin cambiar la dinámica del mundo.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from nivel_1_core.contratos import IActuadorEntorno, ISensorEntorno, Pieza, ResultadoEfectoEntorno
from nivel_1_core.vocabulario import V_Comando

NOMBRES_POR_DEFECTO = {"claro": "claro", "fruta": "fruta", "seta": "seta"}


class AdaptadorEjemploMinimo(ISensorEntorno, IActuadorEntorno):
    def __init__(self, num_claros: int = 6, latidos_rebrote: int = 5, nombres: Optional[Dict[str, str]] = None):
        self.nombres = {**NOMBRES_POR_DEFECTO, **(nombres or {})}
        self.num_claros = num_claros
        self.latidos_rebrote = latidos_rebrote
        self.posicion = 0
        self.latido = 0
        # Disposición fija: fruta en claros pares, seta en el claro 3
        self.contenido: Dict[int, Optional[str]] = {
            i: ("seta" if i == 3 else ("fruta" if i % 2 == 0 else None)) for i in range(num_claros)
        }
        self.original = dict(self.contenido)
        self.rebrote: Dict[int, int] = {}
        self.frutas_comidas = 0

    # ------------------------------------------------------------------ nombres
    def _nodo(self, i: int) -> str:
        return f"{self.nombres['claro']}_{i}"

    def _entidad(self, i: int) -> str:
        return f"{self.nombres[self.contenido[i]]}_{i}"

    # ------------------------------------------------------------------ ISensorEntorno
    def percibir_mundo(self) -> Tuple[str, List[Pieza], List[str]]:
        self.latido += 1
        for i, t in list(self.rebrote.items()):
            if self.latido >= t:
                self.contenido[i] = self.original[i]
                del self.rebrote[i]

        piezas: List[Pieza] = []
        tipo = self.contenido[self.posicion]
        if tipo is not None:
            letal = tipo == "seta"
            piezas.append(Pieza(
                id=self._entidad(self.posicion),
                tipo_componente="Escena",
                arousal=0.85 if letal else 0.75,
                trust=0.90,
                # x0 proximidad, x1 magnitud, x2 movimiento, x3 entropía, x4 afinidad nutricional, x5 nocicepción
                tensor_sensorial=np.array([1.0, 0.4, 0.5, 0.3, 0.10 if letal else 0.95, 0.98 if letal else 0.05]),
                product={"es_nutritivo": not letal, "es_letal": letal},
                inputs=["AdaptadorEjemploMinimo"],
            ))
        vecinos = [self._nodo((self.posicion - 1) % self.num_claros), self._nodo((self.posicion + 1) % self.num_claros)]
        return self._nodo(self.posicion), piezas, vecinos

    # ------------------------------------------------------------------ IActuadorEntorno
    def ejecutar_comando_fisico(
        self, comando: V_Comando, target: str, factor_fauces: float = 1.0, payload_extra: Optional[Dict[str, Any]] = None
    ) -> ResultadoEfectoEntorno:
        if comando == V_Comando.MOVER:
            vecinos = {self._nodo((self.posicion + d) % self.num_claros): (self.posicion + d) % self.num_claros for d in (-1, 1)}
            if target in vecinos:
                self.posicion = vecinos[target]
                return ResultadoEfectoEntorno(exito=True, comando=comando, target=target, nueva_ubicacion=target)
            return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        tipo = self.contenido[self.posicion]
        if tipo is None or target != self._entidad(self.posicion):
            return ResultadoEfectoEntorno(exito=False, comando=comando, target=target)

        if comando == V_Comando.DEGLUTIR:
            self._retirar()
            if tipo == "seta":
                return ResultadoEfectoEntorno(exito=True, comando=comando, target=target, intoxicacion_aguda=True,
                                              dano_subsistemas={"core": -14.0}, delta_alimentacion=-8.0)
            self.frutas_comidas += 1
            return ResultadoEfectoEntorno(exito=True, comando=comando, target=target, delta_alimentacion=12.0, delta_energia=2.0)

        if comando in (V_Comando.CENSURAR, V_Comando.ATACAR) and tipo == "seta":
            self._retirar()
            return ResultadoEfectoEntorno(exito=True, comando=comando, target=target, delta_energia=-1.0)

        if comando == V_Comando.COGER:
            self._retirar()
            return ResultadoEfectoEntorno(exito=True, comando=comando, target=target,
                                          objeto_cargado={"id": target, "es_nutritivo": tipo == "fruta"})

        return ResultadoEfectoEntorno(exito=True, comando=comando, target=target)

    def _retirar(self) -> None:
        self.contenido[self.posicion] = None
        self.rebrote[self.posicion] = self.latido + self.latidos_rebrote
