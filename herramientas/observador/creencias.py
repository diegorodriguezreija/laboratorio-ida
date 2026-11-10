"""
Conocimiento formal legible (preregistro E5, bloque G2). Observador: lee las piezas formales de la memoria
activa del núcleo en cada mantenimiento y al morir, sin escribir en ellas, y al morir deja un `.md` en
tercera persona y un `.json` con todo.

Categorías: demostrada (modalidad DEMOSTRADO* y confianza ≥ 0,85, sin `falsado`), falsada (`falsado`) y
dudosa (el resto). La resolución temporal es la del mantenimiento.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

PREFIJOS = ("Proposicion", "Predicado", "Logica")
RELACION = {"ES_NUTRITIVO": "es nutritivo", "ES_LETAL": "es letal", "ES_SEGURO": "es seguro",
            "ES_TERRORIFICO": "da miedo", "ES_AGRADABLE": "es agradable", "ES_REPULSIVO": "le repele",
            "ES_ARMONICO": "es armónico", "ES_DISONANTE": "es disonante", "ES_FIABLE": "es fiable",
            "ES_FALIBLE": "es falible", "ES_DESCONOCIDO": "es desconocido", "ES_ALIADO": "es aliado",
            "ES_ENEMIGO": "es enemigo", "ES_TABU": "es tabú", "ES_PARASITARIO": "es parásito"}
TITULO = {"demostrada": "Lo que tenía por demostrado", "falsada": "Lo que la experiencia le desmintió",
          "dudosa": "De lo que seguía dudando"}


def categoria(p: Any) -> str:
    if p.product.get("falsado"):
        return "falsada"
    if str(p.product.get("modalidad", "")).startswith("DEMOSTRADO") and float(p.trust) >= 0.85:
        return "demostrada"
    return "dudosa"


def texto(sujeto: str, p: Any) -> str:
    rel = str(p.product.get("relacion") or p.product.get("consecuente") or "")
    return f"«{sujeto}» {RELACION.get(rel, rel.lower().replace('_', ' ') or 'sin relación')}"


class Creencias:
    def __init__(self, salida: str):
        self.base = salida[: -len(".jsonl.gz")] if salida.endswith(".jsonl.gz") else salida
        self.estado: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def leer(self, core: Any, n: int) -> None:
        vistos = set()
        for suj, cajon in core.activa.indice_identidad.items():
            for tipo, p in cajon.items():
                if not str(tipo).startswith(PREFIJOS):
                    continue
                k = (str(suj), str(tipo))
                vistos.add(k)
                cat = categoria(p)
                r = self.estado.get(k)
                if r is None:
                    r = self.estado[k] = {"sujeto": k[0], "tipo": k[1], "historial": []}
                if not r["historial"] or r["historial"][-1][1] != cat:
                    r["historial"].append([n, cat])
                r.update({"categoria": cat, "confianza": round(float(p.trust), 3), "texto": texto(k[0], p),
                          "visto": n, "vivo": True, "relacion": str(p.product.get("relacion") or p.product.get("consecuente") or ""),
                          "fuente": str(p.product.get("fuente", "")),
                          # E6, bloque J: evidencias que añade verificar_hipotesis_empirica al confirmar
                          "evidencias": [str(i) for i in p.inputs if str(i).startswith(("Agencia_", "Evidencia_"))]})
        for k, r in self.estado.items():
            if k not in vistos and r.get("vivo"):
                r["vivo"] = False
                r["historial"].append([n, "olvidada"])

    @staticmethod
    def duraciones(r: Dict[str, Any], fin: int) -> List[int]:
        """Latidos que duró cada tramo demostrada."""
        h, out = r["historial"], []
        for i, (n, cat) in enumerate(h):
            if cat == "demostrada":
                out.append((h[i + 1][0] if i + 1 < len(h) else fin) - n)
        return out

    def resumen(self, fin: int) -> Dict[str, Any]:
        al_morir = [r for r in self.estado.values() if r.get("vivo")]
        durs = [d for r in self.estado.values() for d in self.duraciones(r, fin)]
        return {"al_morir": {c: sum(1 for r in al_morir if r["categoria"] == c) for c in ("demostrada", "falsada", "dudosa")},
                "demostraciones": len(durs), "demostraciones_>=20_latidos": sum(1 for d in durs if d >= 20),
                "duraciones": sorted(durs)}

    def escribir(self, partida: str, fin: int) -> None:
        res = self.resumen(fin)
        with open(self.base + ".creencias.json", "w", encoding="utf-8") as f:
            json.dump({"partida": partida, "latido_final": fin, **res, "creencias": list(self.estado.values())}, f,
                      ensure_ascii=False, indent=1)
        lineas = [f"# Lo que creía el individuo {partida} al morir (latido {fin})", ""]
        for cat in ("demostrada", "falsada", "dudosa"):
            rs = sorted((r for r in self.estado.values() if r.get("vivo") and r["categoria"] == cat),
                        key=lambda r: (-r["confianza"], r["sujeto"]))
            lineas += [f"## {TITULO[cat]} ({len(rs)})", ""]
            for r in rs[:10]:
                desde = next((n for n, c in reversed(r["historial"]) if c == cat), r["historial"][-1][0])
                lineas.append(f"- Creía que {r['texto']} (confianza {r['confianza']:.2f}; así desde el latido {desde}).")
            if len(rs) > 10:
                lineas.append(f"- … y {len(rs) - 10} más en el `.json`.")
            lineas.append("")
        lineas.append(f"Demostraciones en toda la vida: {res['demostraciones']}; duraron ≥ 20 latidos: "
                      f"{res['demostraciones_>=20_latidos']}. Son lecturas del observador de la v14: no cambiaron ninguna decisión.")
        with open(self.base + ".creencias.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lineas) + "\n")
