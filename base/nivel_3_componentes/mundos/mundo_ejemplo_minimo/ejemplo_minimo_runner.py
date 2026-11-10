"""
Runner del mundo de ejemplo mínimo (tutorial).

Conecta el adaptador al core con los sistemas genéricos S1, S2 y S3 tal cual (sin componentes
de dominio) y ejecuta unos latidos. No escribe nada en disco.

    python nivel_3_componentes/mundos/mundo_ejemplo_minimo/ejemplo_minimo_runner.py --latidos 30
"""

import argparse
import asyncio
import os
import sys
from typing import Dict, List, Optional

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from nivel_1_core.contratos import Arquetipo  # noqa: E402
from nivel_1_core.gestor_onda import GestorOndaCore  # noqa: E402
from nivel_2_sistemas.ciclo_sueno_rem import GestorCicloSuenoREM  # noqa: E402
from nivel_2_sistemas.consciencia_talamo_dmn import BucleTalamocortical, RedNeuronalPorDefecto  # noqa: E402
from nivel_2_sistemas.plasticidad_td_hebbiana import MatrizHebbianaTresFactores  # noqa: E402
from nivel_2_sistemas.s1_reactivo import crear_sistema_s1  # noqa: E402
from nivel_2_sistemas.s2_limbico import crear_sistema_s2  # noqa: E402
from nivel_2_sistemas.s3_racional import crear_sistema_s3  # noqa: E402
from nivel_3_componentes.mundos.mundo_ejemplo_minimo.adaptador_ejemplo_minimo import AdaptadorEjemploMinimo  # noqa: E402


async def ejecutar(latidos: int = 30, nombres: Optional[Dict[str, str]] = None, aislar_ruido: bool = False) -> List[Dict]:
    """Ejecuta el mundo y devuelve la traza por latido (comando, objetivo, vitalidad, alimentación, posición)."""
    adaptador = AdaptadorEjemploMinimo(nombres=nombres)
    core = GestorOndaCore(
        sensor=adaptador,
        actuador=adaptador,
        arquetipo=Arquetipo(nombre="Ejemplo", linaje="Linaje_Ejemplo"),
        sistemas_cognitivos=[crear_sistema_s1(MatrizHebbianaTresFactores()), crear_sistema_s2(), crear_sistema_s3()],
        bucle_talamocortical=BucleTalamocortical(),
        dmn=RedNeuronalPorDefecto(),
        gestor_sueno_rem=GestorCicloSuenoREM(),
        cirujano_ast=None,
        frecuencia_max_ms=5000.0,  # presupuesto holgado: la guillotina no interviene en el ejemplo
        amplitud_max=150,
    )
    if aislar_ruido:
        core.cosechador.amplitud_basal = 0.0
        core.cosechador.cosechar_unidad_uniforme = lambda: 0.5

    traza = []
    for _ in range(latidos):
        onda = await core.ejecutar_latido()
        ejec = next(iter(onda.reactiva.ef.get("Ejecucion", {}).values()), None)
        traza.append({
            "latido": onda.ciclo,
            "comando": str(ejec.product.get("comando")) if ejec else "ACC_ESPERAR",
            "objetivo": str(ejec.product.get("target", "")) if ejec else "",
            "sistema": str(onda.metricas.get("sistema_ganador", "")),
            "vitalidad": round(core.soma.vitalidad, 6),
            "alimentacion": round(core.soma.alimentacion, 6),
            "posicion": adaptador.posicion,
            "frutas_comidas": adaptador.frutas_comidas,
        })
        if not core.soma.esta_vivo:
            break
    return traza


def main() -> None:
    ap = argparse.ArgumentParser(description="Mundo de ejemplo mínimo de IdA (tutorial; no escribe en disco)")
    ap.add_argument("--latidos", type=int, default=30)
    ap.add_argument("--aislar-ruido", action="store_true", help="Sustituye el ruido físico por un valor fijo (ejecución reproducible)")
    args = ap.parse_args()
    traza = asyncio.run(ejecutar(args.latidos, aislar_ruido=args.aislar_ruido))
    for t in traza:
        print(f"L{t['latido']:03d} claro={t['posicion']} {t['comando']:<13} {t['objetivo']:<10} "
              f"[{t['sistema']}] Vit={t['vitalidad']:6.2f} Ali={t['alimentacion']:6.2f}")
    print(f"Frutas comidas: {traza[-1]['frutas_comidas']} en {len(traza)} latidos")


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    main()
