# SECURITY-CRITICAL
import logging
from typing import Annotated, Any, Optional

try:
    from fastapi import Depends, HTTPException, Path, Query
    from starlette import status

    # Usar el nombre moderno si está disponible, fallback al antiguo para compatibilidad
    HTTP_422 = getattr(
        status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY
    )
except ImportError:
    # Este módulo solo debe usarse si fastapi está instalado
    HTTP_422 = 422

from rutificador.rut import Rut
from rutificador.exceptions import ErrorValidacionRut

logger = logging.getLogger(__name__)


async def obtener_param_rut(
    rut: str,
) -> Rut:
    """Dependencia de FastAPI para validar e inyectar un objeto Rut.

    Uso:
        @app.get("/validar")
        def validar(rut: Rut = Depends(obtener_param_rut)):
            return {"rut": rut.formatear(separador_miles=True)}
    """
    try:
        return Rut(rut)
    except ErrorValidacionRut as exc:
        logger.warning(f"Error de validación en parámetro FastAPI: {exc}")
        raise HTTPException(
            status_code=HTTP_422,
            detail=[
                {
                    "loc": ["query", "rut"],
                    "msg": str(exc),
                    "type": exc.codigo_error or "valor_error.rut_invalido",
                }
            ],
        )


def ConsultaRut(
    default: Any = ...,
    *,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs,
):
    """Factory para un Query parameter que se valida como RUT."""
    return Annotated[
        str,
        Query(default, alias=alias, title=title, description=description, **kwargs),
        Depends(obtener_param_rut),
    ]


# Alias para facilitar el descubrimiento
ParametroRut = obtener_param_rut

__all__ = ["obtener_param_rut", "ParametroRut", "ConsultaRut"]
