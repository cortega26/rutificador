"""Configuración global de pytest para el paquete rutificador."""

import multiprocessing
import sys

# Python 3.13+ depreca fork() con hilos activos (pytest + plugins).
# Usamos spawn para evitar race conditions en tests con ProcessPoolExecutor.
if sys.platform not in ("win32", "cygwin"):
    try:
        multiprocessing.set_start_method("spawn", force=True)
    except RuntimeError:
        pass  # Ya configurado por el entorno
