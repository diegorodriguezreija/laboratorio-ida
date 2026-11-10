import json
from typing import Dict, Any, Optional
from nivel_1_core.vocabulario import V_Modalidad, V_Relacion
from nivel_1_core.contratos import Pieza


class ServidorMCPTelemetria:
    """
    Tronco Encefalico Estandar y Servidor Model Context Protocol (MCP - JSON-RPC 2.0).
    Permite la observabilidad total de IdA preservando estrictamente la Inversion de Control:
    las herramientas JAMAS fuerzan acciones motoras ejecutivas.
    """

    def __init__(self, core_ref: Any = None):
        self.core = core_ref
        self.mensajes_oraculo_pendientes: list = []

    def despachar_jsonrpc(self, solicitud_json: str) -> str:
        try:
            req = json.loads(solicitud_json)
            metodo = req.get("method", "")
            req_id = req.get("id")
            params = req.get("params", {})

            if metodo == "resources/list":
                res = self._listar_recursos()
            elif metodo == "resources/read":
                res = self._leer_recurso(params.get("uri", ""))
            elif metodo == "tools/list":
                res = self._listar_tools()
            elif metodo == "tools/call":
                res = self._llamar_tool(params.get("name", ""), params.get("arguments", {}))
            else:
                return json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}})

            return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": res})
        except Exception as exc:
            return json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(exc)}})

    def _listar_recursos(self) -> Dict[str, Any]:
        return {
            "resources": [
                {"uri": "ida://constantes_vitales", "name": "Constantes Somaticas y Homeostasis"},
                {"uri": "ida://fenomenologia_phi", "name": "Informacion Integrada (IIT Phi) y Fenomenologia"},
                {"uri": "ida://memoria_inconsciente", "name": "Inconsciente Colectivo pgvector"},
                {"uri": "ida://topologia_grafo", "name": "Grafo Topologico de Biomas"},
                {"uri": "ida://linaje_evolutivo", "name": "Linaje, Generacion y Arquetipo"},
            ]
        }

    def _leer_recurso(self, uri: str) -> Dict[str, Any]:
        if self.core is None:
            return {"contents": [{"uri": uri, "text": "Core no instanciado"}]}

        soma = getattr(self.core, "soma", None)
        activa = getattr(self.core, "activa", None)
        pgv = getattr(self.core, "pgvector", None)
        arq = getattr(self.core, "arquetipo", None)

        if uri == "ida://constantes_vitales" and soma:
            data = {
                "vitalidad": round(soma.vitalidad, 2),
                "alimentacion": round(soma.alimentacion, 2),
                "energia": round(soma.energia, 2),
                "descanso": round(soma.descanso, 2),
                "dopamina": round(soma.dopamina, 2),
                "placer": round(soma.placer, 2),
                "cortisol": round(soma.cortisol, 3),
                "estado_afectivo": str(soma.estado_afectivo),
                "integridad": dict(soma.integridad),
            }
        elif uri == "ida://fenomenologia_phi":
            data = {
                "phi_ultimo": getattr(self.core, "ultimo_phi", 0.0),
                "estado_fenomenologico": getattr(self.core, "ultimo_estado_fenomenologico", "ZOMBI_REFLEJO"),
            }
        elif uri == "ida://memoria_inconsciente" and pgv:
            data = {
                "backend": "postgresql_pgvector" if pgv.conectado_postgres else "volatil_numpy",
                "consultas_rag": pgv.consultas_rag,
                "intuiciones_sintetizadas": pgv.intuiciones_sintetizadas,
            }
        elif uri == "ida://topologia_grafo" and activa:
            data = {"grafo_topologico": activa.grafo_topologico}
        elif uri == "ida://linaje_evolutivo" and arq:
            data = {
                "id_individuo": arq.id_individuo,
                "linaje": arq.linaje,
                "generacion": arq.generacion,
                "ancestros": arq.ancestros,
                "marcadores_epigeneticos": arq.marcadores_epigeneticos,
            }
        else:
            data = {"error": f"Recurso '{uri}' no disponible"}

        return {"contents": [{"uri": uri, "text": json.dumps(data, indent=2)}]}

    def _listar_tools(self) -> Dict[str, Any]:
        return {
            "tools": [
                {
                    "name": "revelar_dogma_s3",
                    "description": "Transmite una revelacion abstracta al Cortex S3 (IoC respetado; no fuerza motor)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "sujeto": {"type": "string"},
                            "relacion": {"type": "string"},
                            "trust": {"type": "number", "default": 0.85},
                        },
                        "required": ["sujeto", "relacion"],
                    },
                },
                {
                    "name": "consultar_inconsciente_colectivo",
                    "description": "Ejecuta busqueda semantica k-NN en el Inconsciente Colectivo pgvector",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "nodo_consulta": {"type": "string"},
                            "top_k": {"type": "integer", "default": 3},
                        },
                        "required": ["nodo_consulta"],
                    },
                },
                {
                    "name": "auditar_organismo",
                    "description": "Diagnostico integral instantaneo de la psique y el cuerpo",
                    "inputSchema": {"type": "object", "properties": {}},
                },
            ]
        }

    def _llamar_tool(self, nombre: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if nombre == "revelar_dogma_s3":
            suj = args["sujeto"]
            rel = args["relacion"]
            trust_val = float(args.get("trust", 0.85))
            if self.core and hasattr(self.core, "proactiva"):
                self.core.proactiva.cola_eurekas.append({
                    "sujeto": suj,
                    "relacion": rel,
                    "trust": trust_val,
                    "fuente": "Oraculo_MCP",
                })
            return {"content": [{"type": "text", "text": f"Dogma sobre '{suj}' transmitido a la cola latente de S3."}]}

        elif nombre == "consultar_inconsciente_colectivo":
            nodo = args["nodo_consulta"]
            k = int(args.get("top_k", 3))
            if self.core and hasattr(self.core, "pgvector") and hasattr(self.core, "arquetipo"):
                recs = self.core.pgvector.consultar_inconsciente_rag(
                    linaje_actual=self.core.arquetipo.linaje,
                    ancestros_permitidos=self.core.arquetipo.ancestros,
                    nodo_consulta=nodo,
                    top_k=k,
                )
                return {"content": [{"type": "text", "text": json.dumps(recs, indent=2)}]}
            return {"content": [{"type": "text", "text": "Almacen vectorial no disponible"}]}

        elif nombre == "auditar_organismo":
            if self.core and hasattr(self.core, "soma"):
                diag = {
                    "vitalidad": round(self.core.soma.vitalidad, 2),
                    "estado": str(self.core.soma.estado_afectivo),
                    "ciclo": getattr(self.core, "ciclo_actual", 0),
                    "autoestima": round(self.core.soma.autoestima_cognitiva, 3),
                    "esta_vivo": self.core.soma.esta_vivo,
                }
                return {"content": [{"type": "text", "text": json.dumps(diag, indent=2)}]}
            return {"content": [{"type": "text", "text": "Core no disponible"}]}

        return {"content": [{"type": "text", "text": f"Tool '{nombre}' desconocida."}]}

