# SECURITY-CRITICAL
"""Integracion opt-in con Pydantic v2.

Este modulo es un *extra* opcional. Importar ``rutificador`` no debe requerir Pydantic.
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
    # Import tardio: evita dependencia implicita en la instalacion base.
    rutstr_type = importlib.import_module(".rutstr", __name__).RutStr

    globals()["RutStr"] = rutstr_type
    return rutstr_type


def __dir__() -> list[str]:  # pragma: no cover - trivial
    return sorted([*globals().keys(), "RutStr"])


__all__ = ["RutStr", "PYDANTIC_IMPORT_ERROR_MESSAGE"]
