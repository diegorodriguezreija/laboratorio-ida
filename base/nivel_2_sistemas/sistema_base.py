import asyncio
from abc import ABC
from typing import Dict, List, Any, Set
from nivel_1_core.contratos import Pieza, Onda, LatidoAgotadoException
from nivel_2_sistemas.plasticidad_td_hebbiana import MotorTDLambda


class ComponenteCognitivoBase(ABC):
    """
    Clase base para todos los Componentes Cognitivos de Nivel 2 y Nivel 3.
    Opera en tres barridos opcionales por estacion:
    1. procesar_reactiva (percepcion e interpretacion en la Onda).
    2. procesar_activa (evocacion y consolidacion en DimensionActiva).
    3. procesar_proactiva (proyeccion de expectativas y rutas en DimensionProactiva).
    """

    def __init__(self, id_componente: str, sistema: str, peso_sinaptico: float = 1.0):
        self.id_componente = id_componente
        self.sistema = sistema
        self.peso_sinaptico = peso_sinaptico

    def emitir_reactiva(
        self,
        onda: Onda,
        nombre_canal: str,
        pieza: Pieza,
        proyectar_ev: bool = True,
        coste_amplitud: int = 1,
    ) -> None:
        pieza.sistemas_participantes.add(self.sistema)
        if self.id_componente not in pieza.inputs:
            pieza.inputs.append(self.id_componente)
        onda.reactiva.registrar_ef_universal(nombre_canal, pieza)
        if proyectar_ev:
            onda.reactiva.proyectar_atencion_ev(nombre_canal, pieza, onda, coste_amplitud=coste_amplitud)

    def emitir_impulso(
        self,
        onda: Onda,
        pieza: Pieza,
        canal_acc: str = "Impulso",
        coste_amplitud: int = 1,
    ) -> None:
        pieza.sistemas_participantes.add(self.sistema)
        if self.id_componente not in pieza.inputs:
            pieza.inputs.append(self.id_componente)
        pieza.product.setdefault("id_componente", self.id_componente)
        pieza.product["peso_sinaptico"] = round(float(self.peso_sinaptico), 4)
        onda.reactiva.converger_impulso_acc(canal_acc, pieza, onda, coste_amplitud=coste_amplitud)

    async def procesar_reactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        return False

    async def procesar_activa(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        return False

    async def procesar_proactiva(self, onda: Onda, ctx: Dict[str, Any]) -> bool:
        return False


class SistemaCognitivoTriunico:
    """
    Tuberia estandarizada Sentir -> Interpretar -> Reaccionar -> Actuar
    con ejecucion en tres barridos (Reactivo, Activo, Proactivo) bajo Guillotina Asincrona.
    """

    ORDEN_ESTACIONES = ("SENTIR", "INTERPRETAR", "REACCIONAR", "ACTUAR")

    def __init__(self, nombre: str, cuota_frecuencia_ratio: float = 0.33):
        self.nombre = nombre
        self.cuota_frecuencia_ratio = cuota_frecuencia_ratio
        self.estaciones: Dict[str, List[ComponenteCognitivoBase]] = {m: [] for m in self.ORDEN_ESTACIONES}
        self.motor_td = MotorTDLambda()

    def inyectar_componente(self, estacion: str, componente: ComponenteCognitivoBase) -> None:
        if estacion not in self.estaciones:
            raise ValueError(f"Estacion invalida '{estacion}'. Use {self.ORDEN_ESTACIONES}")
        self.estaciones[estacion].append(componente)

    def todos_los_componentes(self) -> List[ComponenteCognitivoBase]:
        lista: List[ComponenteCognitivoBase] = []
        for est in self.ORDEN_ESTACIONES:
            lista.extend(self.estaciones[est])
        return lista

    def actualizar_plasticidad_td(self, recompensa: float, ids_activados: Set[str]) -> float:
        """Actualiza los pesos sinapticos de los componentes mediante TD(lambda) y trazas de elegibilidad."""
        componentes = self.todos_los_componentes()
        if not componentes:
            return 0.0
        return self.motor_td.actualizar_pesos_componentes(recompensa, componentes, ids_activados)

    async def procesar_onda(self, onda: Onda, ctx: Dict[str, Any]) -> None:
        for est in self.ORDEN_ESTACIONES:
            componentes = self.estaciones[est]
            if not componentes:
                continue
            onda.verificar_guillotina_frecuencia(contexto=f"{self.nombre}.{est}")

            for comp in componentes:
                ms_disp = onda.ms_restantes()
                if ms_disp <= 0.0:
                    raise LatidoAgotadoException(f"Tiempo agotado antes de {comp.id_componente}")
                timeout_s = ms_disp / 1000.0
                try:
                    await asyncio.wait_for(self._ejecutar_tres_barridos(comp, onda, ctx), timeout=timeout_s)
                except asyncio.TimeoutError as exc:
                    raise LatidoAgotadoException(
                        f"GUILLOTINA en {self.nombre}.{est} -> {comp.id_componente} excedio {ms_disp:.2f} ms."
                    ) from exc

    @staticmethod
    async def _ejecutar_tres_barridos(comp: ComponenteCognitivoBase, onda: Onda, ctx: Dict[str, Any]) -> None:
        await comp.procesar_reactiva(onda, ctx)
        await comp.procesar_activa(onda, ctx)
        await comp.procesar_proactiva(onda, ctx)
