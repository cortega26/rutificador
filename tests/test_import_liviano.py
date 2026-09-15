"""Prueba de importación liviana sin multiprocessing.

Garantiza que ``from rutificador import Rut`` y ``Rut.parse`` funcionan
aunque ``multiprocessing``, ``_multiprocessing`` y
``concurrent.futures.process`` sean inimportables (caso Pyodide en el
navegador, donde el playground solo usa ``Rut`` y nunca los ejecutores
paralelos de ``rutificador.procesador``).
"""

import subprocess
import sys
import textwrap

PROGRAMA = textwrap.dedent(
    """\
    import importlib.abc
    import sys

    BLOQUEADOS = frozenset(
        {"multiprocessing", "_multiprocessing", "concurrent.futures.process"}
    )


    class Bloqueador(importlib.abc.MetaPathFinder):
        def find_spec(self, nombre, ruta=None, objetivo=None):
            if nombre in BLOQUEADOS or nombre.startswith(
                tuple(b + "." for b in BLOQUEADOS)
            ):
                raise ImportError(f"bloqueado para prueba: {nombre}")
            return None


    sys.meta_path.insert(0, Bloqueador())

    from rutificador import Rut

    valido = Rut.parse("12.345.678-5")
    assert str(valido.estado) == "valido", valido
    invalido = Rut.parse("12.345.678-9")
    assert str(invalido.estado) == "invalido", invalido
    print("ok")
    """
)


def test_import_sin_multiprocessing() -> None:
    resultado = subprocess.run(
        [sys.executable, "-c", PROGRAMA],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,  # Anti-cuelgue
    )
    assert resultado.returncode == 0, (
        f"stdout={resultado.stdout!r} stderr={resultado.stderr!r}"
    )
    assert "ok" in resultado.stdout
