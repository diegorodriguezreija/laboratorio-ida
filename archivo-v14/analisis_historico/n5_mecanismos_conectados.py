"""
N5 – ¿Qué mecanismos documentados están realmente conectados?

Envuelve con contadores los métodos de entrada de cada mecanismo (sin cambiar su resultado)
y ejecuta episodios cortos de cada mundo local con la configuración publicada (autopoiesis
desactivada, sin Ollama). Cuenta cuántas veces se invoca cada mecanismo por mundo.
"Invocado" significa conectado al flujo; no dice nada de si tiene efecto medible.

    python analisis/n5_mecanismos_conectados.py --out analisis/resultados/N5_mecanismos_conectados.csv

Snake web queda fuera porque necesita Internet; usa el mismo core y los mismos sistemas.
"""

import argparse
import asyncio
import csv
import functools
import inspect
import os
import sys
from collections import Counter

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from nivel_1_core.calculadoras_estructurales import CalculadorasEstructurales  # noqa: E402
from nivel_1_core.gestor_onda import GestorOndaCore  # noqa: E402
from nivel_1_core.persistencia.motor_pgvector import MotorPgVectorHNSW  # noqa: E402
from nivel_1_core.persistencia.motor_sqlite_wal import MotorSQLiteWAL  # noqa: E402
from nivel_1_core.tribunal_motor import TribunalMotor  # noqa: E402
from nivel_2_sistemas.autopoiesis_ast import CirujanoAST  # noqa: E402
from nivel_2_sistemas.ciclo_sueno_rem import GestorCicloSuenoREM  # noqa: E402
from nivel_2_sistemas.consciencia_talamo_dmn import BucleTalamocortical, RedNeuronalPorDefecto  # noqa: E402
from nivel_2_sistemas.plasticidad_td_hebbiana import MatrizHebbianaTresFactores  # noqa: E402
from nivel_2_sistemas.sistema_base import SistemaCognitivoTriunico  # noqa: E402
from nivel_3_componentes.organos_universales_s3.comp_imaginacion_llm import CompImaginacionLLMS3  # noqa: E402
from nivel_3_componentes.organos_universales_s3.servidor_mcp_telemetria import ServidorMCPTelemetria  # noqa: E402

CONTADOR: Counter = Counter()

# (etiqueta del mecanismo, clase, método)
SONDAS = [
    ("phi_metrica_integracion", CalculadorasEstructurales, "calcular_phi_tononi"),
    ("dmn_red_por_defecto", RedNeuronalPorDefecto, "evaluar_y_rumiar"),
    ("bucle_talamocortical", BucleTalamocortical, "procesar_reentrada_diastole"),
    ("td_lambda", SistemaCognitivoTriunico, "actualizar_plasticidad_td"),
    ("hebb_evaluar", MatrizHebbianaTresFactores, "evaluar_tensor_6d"),
    ("hebb_actualizar", MatrizHebbianaTresFactores, "actualizar_hebbiano_3_factores"),
    ("rem_transicion_circadiana", GestorCicloSuenoREM, "evaluar_transicion_circadiana"),
    ("rem_procesar_sueno", GestorCicloSuenoREM, "procesar_sueno_rem"),
    ("autopoiesis_auditar", CirujanoAST, "auditar_ciclo"),
    ("pgvector_consultar_rag", MotorPgVectorHNSW, "consultar_inconsciente_rag"),
    ("pgvector_enterrar_memoria", MotorPgVectorHNSW, "enterrar_memoria"),
    ("sqlite_escribir", MotorSQLiteWAL, "sincronizar_desde_activa"),
    ("sqlite_leer", MotorSQLiteWAL, "cargar_hacia_activa"),
    ("mcp_despachar", ServidorMCPTelemetria, "despachar_jsonrpc"),
    ("telemetria_contrafactual", TribunalMotor, "_evaluar_registro_contrafactual"),
    ("organo_imaginacion_llm_simulado", CompImaginacionLLMS3, "procesar_proactiva"),
]


def _instrumentar(etiqueta, cls, nombre):
    estatico = inspect.getattr_static(cls, nombre)
    # Función subyacente sin enlazar (para staticmethod/classmethod se usa __func__)
    original = estatico.__func__ if isinstance(estatico, (staticmethod, classmethod)) else estatico
    if inspect.iscoroutinefunction(original):
        @functools.wraps(original)
        async def envoltura(*a, **k):
            CONTADOR[etiqueta] += 1
            return await original(*a, **k)
    else:
        @functools.wraps(original)
        def envoltura(*a, **k):
            CONTADOR[etiqueta] += 1
            return original(*a, **k)
    if isinstance(estatico, staticmethod):
        envoltura = staticmethod(envoltura)
    elif isinstance(estatico, classmethod):
        envoltura = classmethod(envoltura)
    setattr(cls, nombre, envoltura)


def _instrumentar_latido():
    original = GestorOndaCore.ejecutar_latido

    async def latido(self, *a, **k):
        onda = await original(self, *a, **k)
        CONTADOR["latidos"] += 1
        if onda.guillotina_disparada:
            CONTADOR["guillotina_disparada"] += 1
        return onda

    GestorOndaCore.ejecutar_latido = latido


async def mundo_ejemplo():
    from nivel_3_componentes.mundos.mundo_ejemplo_minimo.ejemplo_minimo_runner import ejecutar
    await ejecutar(60)


async def mundo_bosque():
    import main as demo
    await demo.ejecutar_demostracion_holistica(num_latidos=10)


async def mundo_crafter():
    from nivel_1_core.contratos import Arquetipo
    from nivel_3_componentes.mundos.mundo_crafter.adaptador_crafter import AdaptadorCrafter
    from nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner import evaluar_individuo_en_semilla
    ad = AdaptadorCrafter(max_pasos=300)
    ad.conectar()
    arq = Arquetipo(nombre="N5", responsabilidad=0.72, umbral_miedo=0.58, neuroticismo=0.30, apertura=0.60)
    for semilla in (7, 8):  # semillas de desarrollo
        await evaluar_individuo_en_semilla(adaptador=ad, arquetipo=arq, axiomas_heredados=[], seed_mapa=semilla, max_latidos=300)


async def mundo_ajedrez():
    from nivel_1_core.contratos import Arquetipo
    from nivel_3_componentes.mundos.mundo_ajedrez.mundo_ajedrez_runner import simular_partida
    arq = Arquetipo(nombre="N5", apertura=0.75, responsabilidad=0.80, neuroticismo=0.35, umbral_miedo=0.60)
    for color in ("blancas", "negras"):
        await simular_partida(gen=1, arquetipo=arq, axiomas_previos=[], color_ida=color, dificultad_rival=1, usar_ollama=False)


MUNDOS = [("ejemplo_minimo", mundo_ejemplo), ("bosque_demo", mundo_bosque), ("crafter", mundo_crafter), ("ajedrez", mundo_ajedrez)]


def main():
    ap = argparse.ArgumentParser(description="N5: cuenta invocaciones reales de cada mecanismo por mundo")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    for etiqueta, cls, nombre in SONDAS:
        _instrumentar(etiqueta, cls, nombre)
    _instrumentar_latido()

    resultados = {}
    for nombre_mundo, fn in MUNDOS:
        CONTADOR.clear()
        asyncio.run(fn())
        resultados[nombre_mundo] = dict(CONTADOR)

    etiquetas = ["latidos", "guillotina_disparada"] + [e for e, _, _ in SONDAS]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mecanismo"] + [m for m, _ in MUNDOS])
        for e in etiquetas:
            w.writerow([e] + [resultados[m].get(e, 0) for m, _ in MUNDOS])
    with open(args.out, encoding="utf-8") as f:
        print(f.read())


if __name__ == "__main__":
    from nivel_3_componentes.consola import configurar_salida_utf8

    configurar_salida_utf8()
    main()
