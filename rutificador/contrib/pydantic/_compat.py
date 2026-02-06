# SECURITY-CRITICAL
"""Compatibilidad y guardrails para extras.

Este archivo NO debe importar Pydantic al importarse. Se usa como punto unico de
verificacion para mantener un mensaje determinista cuando el extra no esta instalado.
"""

from __future__ import annotations


PYDANTIC_IMPORT_ERROR_MESSAGE = "Instala rutificador[pydantic] para usar RutStr"


def _require_pydantic() -> None:
    try:
        import pydantic  # noqa: F401
        import pydantic_core  # noqa: F401
    except (ImportError, ModuleNotFoundError) as exc:  # pragma: no cover
        raise ImportError(PYDANTIC_IMPORT_ERROR_MESSAGE) from exc
