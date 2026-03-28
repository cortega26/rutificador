# SECURITY-CRITICAL
import logging
from typing import Annotated, Optional, Union

try:
    from fastapi import Depends, HTTPException, Path, Query
    from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
except ImportError:
    # Este módulo solo debe usarse si fastapi está instalado
    pass

from rutificador.rut import Rut
from rutificador.exceptions import ErrorValidacionRut

logger = logging.getLogger(__name__)

async def get_rut_param(
    rut: str,
) -> Rut:
    """Dependencia de FastAPI para validar e inyectar un objeto Rut.
    
    Uso:
        @app.get("/validar")
        def validar(rut: Rut = Depends(get_rut_param)):
            return {"rut": rut.formatear(separador_miles=True)}
    """
    try:
        return Rut(rut)
    except ErrorValidacionRut as exc:
        logger.warning(f"Error de validación en parámetro FastAPI: {exc}")
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "loc": ["query", "rut"],
                    "msg": str(exc),
                    "type": exc.error_code or "value_error.rut_invalid",
                }
            ],
        )

def RutQuery(
    default: Any = ...,
    *,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
):
    """Factory para un Query parameter que se valida como RUT."""
    return Annotated[str, Query(default, alias=alias, title=title, description=description, **kwargs), Depends(get_rut_param)]

# Alias para facilitar el descubrimiento
RutParam = get_rut_param

__all__ = ["get_rut_param", "RutParam", "RutQuery"]
