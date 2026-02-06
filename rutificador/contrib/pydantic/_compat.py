# SECURITY-CRITICAL
"""Compatibilidad y salvaguardas para extras.

Este archivo NO debe importar Pydantic al importarse. Se usa como punto único de
verificación para mantener un mensaje determinista cuando el extra no está instalado.
"""

from __future__ import annotations

import importlib


PYDANTIC_IMPORT_ERROR_MESSAGE = "Instala rutificador[pydantic] para usar RutStr"


def _require_pydantic() -> None:
    try:
        # Usamos importlib para evitar falsos positivos de Pylint cuando el paquete
        # `rutificador.contrib.pydantic` se infiere como el módulo top-level `pydantic`.
        importlib.import_module("pydantic")
        importlib.import_module("pydantic_core")
    except (ImportError, ModuleNotFoundError) as exc:  # pragma: no cover
        raise ImportError(PYDANTIC_IMPORT_ERROR_MESSAGE) from exc
