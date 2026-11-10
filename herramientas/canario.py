"""
Canario de la v14 contra la v13 (encargo v14, secciÃ³n 1.2).

Con todos los flags de la v14 apagados, el CSV de H7 (Crafter, A0, semillas 0â€“9, 300 pasos,
ruido aislado) del Ã¡rbol actual debe ser idÃ©ntico byte a byte al de una referencia (por defecto
`origin/v13`). La referencia se ejecuta en un `git worktree` temporal fuera del repositorio,
con el mismo intÃ©rprete, y se borra al terminar.

    python -m v14.canario                         # contra origin/v13
    python -m v14.canario --referencia v13        # contra la rama local

Sale con 0 si los dos CSV son idÃ©nticos, 1 si difieren y 2 si no se puede comparar
(un flag encendido, la referencia no existe o el worktree importarÃ­a cÃ³digo ajeno).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from herramientas.parametros import encendidos  # noqa: E402

# SHA-256 del CSV de H7 de la v13 medido en Windows con Python 3.11 (evidencias de la v13).
# Solo informativo: el canario compara siempre contra la referencia ejecutada en la misma mÃ¡quina.
SHA_V13_CONOCIDO = "46856cb3756feb81fb3271524e2566b3f1356a3409d5c8199c12028fa0c250e9"


def sha256(ruta: str) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 16), b""):
            h.update(bloque)
    return h.hexdigest()


def _git(*args: str, cwd: str = RAIZ) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def _entorno(out_dir: str) -> dict:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["IDA_OUT_DIR"] = out_dir
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def _ejecutar_h7(raiz: str, csv: str, semillas: str, max_pasos: int, env: dict) -> None:
    cmd = [sys.executable, os.path.join(raiz, "analisis", "run_experimento.py"), "--hipotesis", "H7",
           "--semillas", semillas, "--max-pasos", str(max_pasos), "--aislar-ruido", "--out", csv]
    res = subprocess.run(cmd, cwd=raiz, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        sys.stderr.write(res.stdout[-2000:] + res.stderr[-4000:])
        raise RuntimeError(f"H7 fallÃ³ en {raiz} (cÃ³digo {res.returncode})")


def _comprobar_resolucion(raiz: str, env: dict) -> None:
    """El worktree debe importar su propio cÃ³digo, no el del Ã¡rbol actual (instalaciÃ³n editable)."""
    sonda = ("import sys, os; sys.path.insert(0, os.getcwd()); "
             "import nivel_1_core.gestor_onda as g, nivel_2_sistemas.s1_reactivo as s, analisis.estadistica as a; "
             "print('\\n'.join(os.path.abspath(m.__file__) for m in (g, s, a)))")
    res = subprocess.run([sys.executable, "-c", sonda], cwd=raiz, env=env, capture_output=True, text=True, check=True)
    ajenos = [r for r in res.stdout.split() if not os.path.normcase(r).startswith(os.path.normcase(os.path.abspath(raiz)))]
    if ajenos:
        raise RuntimeError(f"el worktree importarÃ­a cÃ³digo de fuera: {ajenos}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--referencia", default="origin/v13")
    ap.add_argument("--semillas", default="0-9")
    ap.add_argument("--max-pasos", type=int, default=300)
    ap.add_argument("--out-dir", default=None, help="por defecto, <IDA_OUT_DIR>/v14_canario")
    args = ap.parse_args(argv)

    flags = encendidos()
    if flags:
        print(f"[canario] NO SE COMPARA: hay flags de la v14 encendidos: {flags}")
        return 2

    base = os.environ.get("IDA_OUT_DIR") or os.path.join(RAIZ, "salidas")
    out_dir = os.path.abspath(args.out_dir or os.path.join(base, "v14_canario"))
    os.makedirs(out_dir, exist_ok=True)

    try:
        sha_ref_commit = _git("rev-parse", "--verify", f"{args.referencia}^{{commit}}")
    except subprocess.CalledProcessError:
        print(f"[canario] NO SE COMPARA: la referencia {args.referencia!r} no existe (Â¿falta git fetch?)")
        return 2
    sha_actual_commit = _git("rev-parse", "HEAD")

    csv_actual = os.path.join(out_dir, "actual_H7.csv")
    csv_ref = os.path.join(out_dir, "referencia_H7.csv")
    tmp = tempfile.mkdtemp(prefix="ida_v14_canario_")
    wt = os.path.join(tmp, "referencia")
    try:
        _git("worktree", "add", "--detach", wt, sha_ref_commit)
        env_ref = _entorno(os.path.join(out_dir, "salidas_referencia"))
        _comprobar_resolucion(wt, env_ref)
        print(f"[canario] referencia {args.referencia} ({sha_ref_commit[:7]}): H7 {args.semillas}, {args.max_pasos} pasos")
        _ejecutar_h7(wt, csv_ref, args.semillas, args.max_pasos, env_ref)
    except RuntimeError as exc:
        print(f"[canario] NO SE COMPARA: {exc}")
        return 2
    finally:
        try:
            _git("worktree", "remove", "--force", wt)
        except subprocess.CalledProcessError:
            pass
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"[canario] actual HEAD ({sha_actual_commit[:7]}): H7 {args.semillas}, {args.max_pasos} pasos")
    _ejecutar_h7(RAIZ, csv_actual, args.semillas, args.max_pasos, _entorno(os.path.join(out_dir, "salidas_actual")))

    h_act, h_ref = sha256(csv_actual), sha256(csv_ref)
    print(f"[canario] SHA-256 actual     {h_act}")
    print(f"[canario] SHA-256 referencia {h_ref}")
    print(f"[canario] coincide con el valor conocido de la v13: {'sÃ­' if h_ref == SHA_V13_CONOCIDO else 'no (informativo)'}")
    if h_act != h_ref:
        print("[canario] DISTINTOS: con los flags apagados, la v14 no reproduce la v13.")
        return 1
    print("[canario] IDÃ‰NTICOS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

