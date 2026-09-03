"""Configuración global de pytest para el paquete rutificador."""

import multiprocessing
import sys
import warnings

# anyio 4.x deprecates anyio.abc.BlockingPortal (usado por starlette<1.6).
# Con `pytest -W error::DeprecationWarning` ese warning rompe la colección
# de tests/contrib/test_fastapi.py. Lo ignoramos aquí para que el gate
# siga detectando deprecations propias pero no las de dependencias.
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=".*BlockingPortal.*",
)

# Python 3.13+ depreca fork() con hilos activos (pytest + plugins).
# Usamos spawn para evitar race conditions en tests con ProcessPoolExecutor.
if sys.platform not in ("win32", "cygwin"):
    try:
        multiprocessing.set_start_method("spawn", force=True)
    except RuntimeError:
        pass  # Ya configurado por el entorno
