"""
ParÃ¡metros de la v14: todo apagado por defecto, esquema cerrado y aislamiento de la carpeta.
"""

import json
import pathlib
import re

import pytest

from herramientas import parametros as P

RAIZ = pathlib.Path(__file__).resolve().parents[2]


def test_todos_los_flags_apagados_por_defecto():
    assert P.encendidos() == {}
    assert P.todos_apagados()


def test_cada_mundo_declara_todos_los_flags():
    datos = P.cargar()  # solo los flags
    assert set(datos) == set(P.MUNDOS)
    for flags in datos.values():
        assert set(flags) == set(P.FLAGS)


def _escribir(tmp_path, mutar):
    datos = json.loads(pathlib.Path(P.RUTA).read_text(encoding="utf-8"))
    mutar(datos)
    ruta = tmp_path / "p.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return str(ruta)


def test_un_flag_encendido_se_detecta(tmp_path):
    ruta = _escribir(tmp_path, lambda d: d["mundos"]["crafter"]["flags"].update(observar_activa=True))
    assert P.encendidos(ruta) == {"crafter": {"observar_activa": True}}
    assert not P.todos_apagados(ruta)


def test_los_ajustes_no_encienden_nada():
    assert P.todos_apagados()
    assert P.ajustes("crafter")["senales_episodio"] == "mundo_crafter"
    assert P.ajustes("bosque")["senales_episodio"] == "soma"
    assert P.ajustes("crafter")["olvido"]["horizonte_latidos"] == P.AJUSTES_BASE["olvido"]["horizonte_latidos"]


def test_la_configuracion_de_observacion_solo_enciende_observadores():
    enc = P.encendidos(P.RUTA_OBSERVACION)
    assert set(enc) == {"crafter", "ejemplo_minimo", "bosque"}
    for flags in enc.values():
        assert set(flags) <= {"memoria_experiencia", "observar_activa", "observar_proactiva", "indicadores_generales"}


@pytest.mark.parametrize("mutar", [
    lambda d: d["mundos"]["crafter"]["flags"].update(flag_inventado=False),
    lambda d: d["mundos"]["crafter"]["flags"].pop("paso1_alerta"),
    lambda d: d["mundos"]["crafter"]["flags"].update(paso1_alerta=0),
    lambda d: d["mundos"]["crafter"]["flags"].update(memoria_experiencia="maxima"),
    lambda d: d["mundos"].pop("snake"),
    lambda d: d.update(esquema="otro"),
    lambda d: d["mundos"]["crafter"]["ajustes"].update(ajuste_inventado=1),
    lambda d: d["mundos"]["crafter"]["ajustes"]["episodio"].update(sorpresa_abre=1),
    lambda d: d["mundos"]["crafter"]["ajustes"].update(senales_episodio="otra"),
    lambda d: d["mundos"]["crafter"]["ajustes"].update(k_piezas="tres"),
], ids=["flag_desconocido", "flag_ausente", "tipo_incorrecto", "perfil_invalido", "mundo_ausente", "esquema",
        "ajuste_desconocido", "ajuste_tipo", "senales_invalidas", "k_no_numerico"])
def test_esquema_cerrado(tmp_path, mutar):
    with pytest.raises(P.ErrorParametros):
        P.cargar(_escribir(tmp_path, mutar))


def test_nada_fuera_de_v14_importa_v14():
    patron = re.compile(r"^\s*(from\s+v14\b|import\s+v14\b)", re.MULTILINE)
    culpables = [
        str(f.relative_to(RAIZ))
        for f in RAIZ.rglob("*.py")
        if "v14" not in f.relative_to(RAIZ).parts[:1]
        and not any(p in (".venv", "venv", "build", "archivo-v14") for p in f.relative_to(RAIZ).parts)
        and patron.search(f.read_text(encoding="utf-8", errors="ignore"))
    ]
    assert culpables == []

