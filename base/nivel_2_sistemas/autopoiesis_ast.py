import ast
import inspect
import time
from typing import Dict, Any, List, Optional


class InmunomaSomatico:
    """Protege el Chasis Somatico y efectores del Core contra cirugias sintacticas."""
    COMPONENTES_INTOCABLES = {
        "TribunalMotor",
        "EstadoSomatico",
        "CosechadorTermodinamico",
        "GestorOndaCore",
        "MotorSQLiteWAL",
        "MotorPgVectorHNSW",
    }

    @classmethod
    def es_mutable(cls, componente: Any) -> bool:
        nombre = getattr(componente, "__class__", type(componente)).__name__
        id_comp = getattr(componente, "id_componente", "")
        if nombre in cls.COMPONENTES_INTOCABLES or id_comp in cls.COMPONENTES_INTOCABLES:
            return False
        return True


class DetectorDisonancia:
    """Diagnostica patologias cronicas que justifican cirugia genetica en RAM."""

    @staticmethod
    def diagnosticar(soma: Any, ciclo: int) -> Optional[Dict[str, Any]]:
        # 1. Culpa psicosomatica cronica (amenaza de necrosis por toxina)
        if getattr(soma, "estado_afectivo", None) == "CULPA":
            return {
                "tipo": "DISONANCIA_CULPA_CRONICA",
                "diana_componente": "Comp_Deontologia",
                "motivo": "Relajar prescripcion moral para evitar muerte por culpa",
            }
        # 2. Panico repetitivo por inanicion saboteando al organismo
        if getattr(soma, "ciclos_panico", 0) >= 4 and getattr(soma, "alimentacion", 100.0) <= 15.0:
            return {
                "tipo": "DISONANCIA_PANICO_INANICION",
                "diana_componente": "Comp_ImpulsoS1",
                "motivo": "Ampliar ventana de tolerancia de hambre reactiva",
            }
        return None


class TransformadorCognitivoAST:
    """Opera mutaciones sobre el AST de componentes cognitivos en caliente."""

    @staticmethod
    def mutar_componente(clase_original: type, tipo_disonancia: str) -> Optional[type]:
        try:
            codigo = inspect.getsource(clase_original)
            arbol = ast.parse(codigo)
        except Exception:
            return None

        class ModificadorLiterales(ast.NodeTransformer):
            def visit_Constant(self, node: ast.Constant) -> ast.AST:
                if tipo_disonancia == "DISONANCIA_CULPA_CRONICA":
                    if isinstance(node.value, (int, float)) and node.value == 0.0:
                        return ast.copy_location(ast.Constant(value=0.05), node)
                elif tipo_disonancia == "DISONANCIA_PANICO_INANICION":
                    if isinstance(node.value, (int, float)) and node.value == 15.0:
                        return ast.copy_location(ast.Constant(value=8.0), node)
                return node

        modificador = ModificadorLiterales()
        arbol_mutado = modificador.visit(arbol)
        ast.fix_missing_locations(arbol_mutado)

        # Sandbox inmunologico de compilacion efimera (< 5 ms)
        t0 = time.perf_counter()
        namespace_sandbox: Dict[str, Any] = {}
        try:
            modulo_orig = inspect.getmodule(clase_original)
            if modulo_orig:
                namespace_sandbox.update(modulo_orig.__dict__)
            codigo_compilado = compile(arbol_mutado, filename="<autopoiesis_sandbox>", mode="exec")
            exec(codigo_compilado, namespace_sandbox)
            t_ms = (time.perf_counter() - t0) * 1000.0
            if t_ms > 5.0:
                return None
            nueva_clase = namespace_sandbox.get(clase_original.__name__)
            return nueva_clase if isinstance(nueva_clase, type) else None
        except Exception:
            return None


class CirujanoAST:
    """
    Gestiona la cirugia en caliente de componentes y audita la Ventana Clinica de 25 latidos.
    Rollback Epigenetico automatico si Delta(Vit) <= -25 o Vitalidad <= 20.0.
    """

    VENTANA_CLINICA_LATIDOS = 25

    def __init__(self):
        self.total_mutaciones: int = 0
        self.rechazos_epigeneticos: int = 0
        self.observacion_clinica: Optional[Dict[str, Any]] = None

    def auditar_ciclo(self, onda: Any, soma: Any, sistemas: List[Any]) -> None:
        vit_actual = getattr(soma, "vitalidad", 100.0)

        # 1. Gestionar Ventana Clinica de 25 latidos si hay mutacion bajo observacion
        if self.observacion_clinica is not None:
            latidos_transcurridos = onda.ciclo - self.observacion_clinica["ciclo_inicio"]
            delta_vit = vit_actual - self.observacion_clinica["vit_inicio"]

            # Rollback Epigenetico atómico si hay colapso somatico
            if delta_vit <= -25.0 or vit_actual <= 20.0:
                componente = self.observacion_clinica["componente_ref"]
                clase_previa = self.observacion_clinica["clase_original"]
                componente.__class__ = clase_previa
                self.rechazos_epigeneticos += 1
                self.observacion_clinica = None
                return

            if latidos_transcurridos >= self.VENTANA_CLINICA_LATIDOS:
                # Mutacion consolidada definitivamente con exito
                self.observacion_clinica = None

        # 2. Si no hay cirugia activa, buscar necesidad de intervencion autopoietica
        diag = DetectorDisonancia.diagnosticar(soma, onda.ciclo)
        if diag is None:
            return

        nombre_diana = diag["diana_componente"]
        for sis in sistemas:
            for comp in getattr(sis, "todos_los_componentes", lambda: [])():
                if comp.id_componente == nombre_diana and InmunomaSomatico.es_mutable(comp):
                    clase_orig = comp.__class__
                    nueva_clase = TransformadorCognitivoAST.mutar_componente(clase_orig, diag["tipo"])
                    if nueva_clase is not None:
                        comp.__class__ = nueva_clase
                        self.total_mutaciones += 1
                        self.observacion_clinica = {
                            "componente_ref": comp,
                            "clase_original": clase_orig,
                            "ciclo_inicio": onda.ciclo,
                            "vit_inicio": vit_actual,
                        }
                        return

