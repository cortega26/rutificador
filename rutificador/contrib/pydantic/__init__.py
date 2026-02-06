# SECURITY-CRITICAL
"""Integración opcional (se instala explícitamente) con Pydantic v2.

Este módulo es un *extra* opcional. Importar ``rutificador`` no debe requerir Pydantic.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from ._compat import PYDANTIC_IMPORT_ERROR_MESSAGE, _require_pydantic

if TYPE_CHECKING:  # pragma: no cover
    from .rutstr import RutStr


def __getattr__(name: str) -> Any:
    if name != "RutStr":
        raise AttributeError(name)
    _require_pydantic()
    # Importación tardía: evita dependencia implícita en la instalación base.
    tipo_rutstr = importlib.import_module(".rutstr", __name__).RutStr

    globals()["RutStr"] = tipo_rutstr
    return tipo_rutstr


def __dir__() -> list[str]:  # pragma: no cover - trivial
    return sorted([*globals().keys(), "RutStr"])


__all__ = ["RutStr", "PYDANTIC_IMPORT_ERROR_MESSAGE"]
