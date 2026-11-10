"""
Seguridad de ejecución (D7, sección 5.4):
- La autopoiesis AST está desactivada por defecto en todos los puntos de ensamblaje.
- El mundo Bosque solo opera dentro de un subdirectorio del temporal del sistema y no
  puede leer, borrar, truncar ni escribir nada fuera de su raíz.
- La demo de main.py no modifica nada en el árbol del repositorio.
"""

import asyncio
import inspect
import os
import pathlib
import tempfile

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def test_autopoiesis_desactivada_por_defecto_en_organismo():
    from base.organismo import construir_organismo
    from nivel_3_componentes.mundos.mundo_acompanante_humano.adaptador_acompanante import AdaptadorAcompananteHumano

    adaptador = AdaptadorAcompananteHumano()
    core = construir_organismo(sensor=adaptador, actuador=adaptador)
    assert core.cirujano is None

    core_on = construir_organismo(sensor=adaptador, actuador=adaptador, habilitar_autopoiesis=True)
    assert core_on.cirujano is not None


@pytest.mark.parametrize(
    "modulo,funcion,dependencia",
    [
        ("nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner", "ejecutar_simulacion_crafter", "crafter"),
        ("nivel_3_componentes.mundos.mundo_crafter.mundo_crafter_runner", "evaluar_individuo_en_semilla", "crafter"),
        ("nivel_3_componentes.mundos.mundo_arcade_snake.mundo_snake_runner", "ejecutar_simulacion_snake", None),
        ("nivel_3_componentes.mundos.mundo_ajedrez.mundo_ajedrez_runner", "simular_partida", "chess"),
    ],
)
def test_autopoiesis_desactivada_por_defecto_en_runners(modulo, funcion, dependencia):
    import importlib

    if dependencia:
        pytest.importorskip(dependencia)
    fn = getattr(importlib.import_module(modulo), funcion)
    param = inspect.signature(fn).parameters.get("habilitar_autopoiesis")
    assert param is not None, f"{funcion} no expone habilitar_autopoiesis"
    assert param.default is False


# --------------------------------------------------------------------------- Bosque (sandbox)

def _bosque():
    from nivel_3_componentes.mundos.mundo_bosque_archivos.adaptador_bosque import AdaptadorBosqueArchivos

    return AdaptadorBosqueArchivos


@pytest.mark.parametrize("ruta", [str(RAIZ), tempfile.gettempdir(), os.path.expanduser("~")])
def test_bosque_rechaza_raices_fuera_de_un_subdirectorio_temporal(ruta):
    with pytest.raises(ValueError):
        _bosque()(ruta_bioma_raiz=ruta)


def test_bosque_rechaza_subdirectorios_temporales_no_creados_para_el(tmp_path):
    # tmp_path cuelga del temporal del sistema pero no lleva el prefijo del sandbox
    with pytest.raises(ValueError):
        _bosque()(ruta_bioma_raiz=str(tmp_path / "bioma"))


def test_bosque_no_toca_nada_fuera_de_su_raiz():
    import shutil

    from nivel_1_core.vocabulario import V_Comando

    tmp_path = pathlib.Path(tempfile.mkdtemp(prefix=_bosque().PREFIJO_SANDBOX))
    try:
        _comprobar_confinamiento(tmp_path, V_Comando)
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def _comprobar_confinamiento(tmp_path, V_Comando):
    bioma = tmp_path / "bioma"
    bioma.mkdir()
    (bioma / "brote_dentro.brote").write_bytes(b"x" * 500)
    fuera = tmp_path / "fruto_fuera.brote"
    contenido_fuera = b"NO_TOCAR" * 50
    fuera.write_bytes(contenido_fuera)

    adaptador = _bosque()(ruta_bioma_raiz=str(bioma))
    objetivos_fuera = ["../fruto_fuera.brote", str(fuera), "nuevo/../../fruto_fuera.brote"]
    if os.name == "nt":  # en Windows la barra invertida también separa rutas
        objetivos_fuera.append(r"..\fruto_fuera.brote")
    comandos = [V_Comando.DEGLUTIR, V_Comando.CENSURAR, V_Comando.ATACAR, V_Comando.COGER, V_Comando.ASIMILAR, V_Comando.SOLTAR]
    for objetivo in objetivos_fuera:
        for cmd in comandos:
            res = adaptador.ejecutar_comando_fisico(cmd, objetivo)
            assert res.exito is False, f"{cmd} sobre {objetivo} debía fallar"
        assert adaptador.ejecutar_comando_fisico(V_Comando.MOVER, "..").exito is False

    assert fuera.read_bytes() == contenido_fuera
    assert sorted(p.name for p in tmp_path.iterdir()) == ["bioma", "fruto_fuera.brote"]

    # Dentro de la raíz el mundo sigue funcionando igual (DEGLUTIR trunca 64 bytes)
    res = adaptador.ejecutar_comando_fisico(V_Comando.DEGLUTIR, "brote_dentro.brote")
    assert res.exito is True
    assert (bioma / "brote_dentro.brote").stat().st_size == 500 - 64


def _instantanea_repositorio():
    excluir = {".git", ".venv", "salidas", "__pycache__", ".pytest_cache"}
    estado = {}
    for raiz, dirs, ficheros in os.walk(RAIZ):
        dirs[:] = [d for d in dirs if d not in excluir]
        for f in ficheros:
            p = os.path.join(raiz, f)
            st = os.stat(p)
            estado[os.path.relpath(p, RAIZ)] = (st.st_size, st.st_mtime_ns)
    return estado


def test_ejecucion_no_modifica_el_repositorio(monkeypatch, tmp_path):
    from nivel_3_componentes.mundos.mundo_ejemplo_minimo.ejemplo_minimo_runner import ejecutar

    monkeypatch.setenv("IDA_OUT_DIR", str(tmp_path / "salidas"))
    antes = _instantanea_repositorio()
    asyncio.run(ejecutar(6))
    assert _instantanea_repositorio() == antes
