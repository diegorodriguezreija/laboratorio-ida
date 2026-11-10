"""
Almacén de experiencia propio de la v14 (plan, secciones 4.3, 4.5 y 4.7). No toca la memoria del núcleo.

- Experiencia reactiva: `reactiva[Clase][id]` → lista de registros (varias relaciones de la misma
  clase sobre una entidad no chocan). Cada registro lleva el latido de creación, el Sistema y el
  Componente de origen, el arousal, la confianza, los rasgos y la referencia al Episodio.
- Experiencia activa: `activa[(Clase, id)]` → lista de recuerdos (qué se recuperó y con qué relevancia).
- Índice por clase y rasgos (y uno de episodios por huella de apertura), reconstruido en cada
  mantenimiento: lo guardado en un latido entra en un búfer y solo se puede recuperar tras consolidarse.
- Olvido en el mantenimiento: lo que no se usa en `horizonte_latidos` y tiene poco arousal acumulado
  se olvida. Nunca se olvidan las proposiciones demostradas, lo heredado ni los episodios de balance
  extremo. Las marcas son de latido, no de reloj (ARQUITECTURA §13).
- Relevancia: similitud coseno × (1 + 0,85 × arousal), la misma fórmula del núcleo
  (`CalculadorasEstructurales.score_gravitacional_arousal`), aquí vectorizada.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

PESO_AROUSAL = 0.85  # calculadoras_estructurales.py:104


def relevancia(cos: np.ndarray, arousal: np.ndarray) -> np.ndarray:
    return cos * (1.0 + PESO_AROUSAL * np.clip(arousal, 0.0, 1.0))


def _normalizar(m: np.ndarray) -> np.ndarray:
    return m / np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-12)


@dataclass
class Registro:
    clase: str
    id: str
    latido: int
    arousal: float
    confianza: float
    rasgos: np.ndarray
    sistema: str
    componente: str
    episodio: Optional[str]
    protegido: bool = False


@dataclass
class Uso:
    ultimo: int
    acumulado: float = 0.0


@dataclass
class Almacen:
    olvido: Dict[str, float]
    reactiva: Dict[str, Dict[str, List[Registro]]] = field(default_factory=dict)
    activa: Dict[Tuple[str, str], List[Dict[str, Any]]] = field(default_factory=dict)
    uso: Dict[Tuple[str, str], Uso] = field(default_factory=dict)
    episodios: List[Dict[str, Any]] = field(default_factory=list)
    uso_ep: Dict[str, int] = field(default_factory=dict)
    _bufer: List[Registro] = field(default_factory=list)
    _bufer_ep: List[Dict[str, Any]] = field(default_factory=list)
    _indice: Dict[str, Tuple[np.ndarray, np.ndarray, List[Registro]]] = field(default_factory=dict)
    _indice_ep: Optional[Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]]]] = None
    olvidados: int = 0
    olvidados_ep: int = 0

    # -- camino rápido (cada latido) -------------------------------------------------------------
    def guardar(self, r: Registro) -> None:
        self._bufer.append(r)

    def guardar_episodio(self, ep: Dict[str, Any]) -> None:
        self._bufer_ep.append(ep)

    def recuperar(self, clase: str, rasgos: np.ndarray, latido: int) -> Optional[Dict[str, Any]]:
        """El registro consolidado más relevante de la misma clase (sin el propio latido)."""
        ind = self._indice.get(clase)
        if ind is None:
            return None
        mat, aro, regs = ind
        q = rasgos / max(float(np.linalg.norm(rasgos)), 1e-12)
        rel = relevancia(mat @ q, aro)
        i = int(np.argmax(rel))
        r = regs[i]
        self._usar((r.clase, r.id), latido, r.arousal)
        return {"clase": r.clase, "id": r.id, "latido": r.latido, "episodio": r.episodio, "sistema": r.sistema,
                "coseno": float(mat[i] @ q), "relevancia": float(rel[i])}

    def recuperar_episodio(self, huella: List[float], latido: int) -> Optional[Dict[str, Any]]:
        if self._indice_ep is None:
            return None
        mat, aro, eps = self._indice_ep
        q = np.asarray(huella, dtype=float)
        q = q / max(float(np.linalg.norm(q)), 1e-12)
        rel = relevancia(mat @ q, aro)
        i = int(np.argmax(rel))
        ep = eps[i]
        self.uso_ep[ep["id"]] = latido
        return {"id": ep["id"], "signo": ep["signo"], "balance": ep["balance"], "coseno": float(mat[i] @ q),
                "relevancia": float(rel[i]), "desde": ep["desde"]}

    def anotar_recuerdo(self, clave: Tuple[str, str], recuerdo: Dict[str, Any]) -> None:
        self.activa.setdefault(clave, []).append(recuerdo)

    def _usar(self, clave: Tuple[str, str], latido: int, arousal: float) -> None:
        u = self.uso.setdefault(clave, Uso(ultimo=latido))
        u.ultimo = latido
        u.acumulado += arousal

    # -- camino lento (mantenimiento: REM, periódico o al morir) --------------------------------
    def mantenimiento(self, latido: int) -> Dict[str, Any]:
        t0 = time.perf_counter()
        n_bufer, n_bufer_ep = len(self._bufer), len(self._bufer_ep)
        for r in self._bufer:
            self.reactiva.setdefault(r.clase, {}).setdefault(r.id, []).append(r)
            self._usar((r.clase, r.id), r.latido, r.arousal)
        self._bufer.clear()
        for ep in self._bufer_ep:
            self.episodios.append(ep)
            self.uso_ep.setdefault(ep["id"], ep["hasta"])
        self._bufer_ep.clear()
        self._olvidar(latido)
        self._reindexar()
        return {"consolidados": n_bufer, "episodios_consolidados": n_bufer_ep,
                "olvidados_total": self.olvidados, "episodios_olvidados_total": self.olvidados_ep,
                "registros": self.tamano(), "episodios": len(self.episodios),
                "ms": (time.perf_counter() - t0) * 1000.0}

    def _olvidar(self, latido: int) -> None:
        horizonte = self.olvido["horizonte_latidos"]
        minimo = self.olvido["arousal_acumulado_min"]
        for clase in list(self.reactiva):
            for id_ in list(self.reactiva[clase]):
                u = self.uso.get((clase, id_))
                if u is None or latido - u.ultimo <= horizonte or u.acumulado >= minimo:
                    continue
                antes = self.reactiva[clase][id_]
                quedan = [r for r in antes if r.protegido]
                self.olvidados += len(antes) - len(quedan)
                if quedan:
                    self.reactiva[clase][id_] = quedan
                else:
                    del self.reactiva[clase][id_]
                    self.uso.pop((clase, id_), None)
            if not self.reactiva[clase]:
                del self.reactiva[clase]
        extremo = self.olvido["balance_extremo"]
        quedan_ep = [ep for ep in self.episodios
                     if abs(ep["balance"]) >= extremo or latido - self.uso_ep.get(ep["id"], ep["hasta"]) <= horizonte]
        self.olvidados_ep += len(self.episodios) - len(quedan_ep)
        self.episodios = quedan_ep

    def _reindexar(self) -> None:
        self._indice = {}
        for clase, por_id in self.reactiva.items():
            regs = [r for lista in por_id.values() for r in lista]
            if regs:
                mat = _normalizar(np.vstack([r.rasgos for r in regs]))
                self._indice[clase] = (mat, np.array([r.arousal for r in regs]), regs)
        if self.episodios:
            mat = _normalizar(np.array([ep["huella"] for ep in self.episodios], dtype=float))
            self._indice_ep = (mat, np.array([ep["max_arousal"] for ep in self.episodios]), list(self.episodios))
        else:
            self._indice_ep = None

    def tamano(self) -> int:
        return sum(len(lista) for por_id in self.reactiva.values() for lista in por_id.values())
