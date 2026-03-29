# SECURITY-CRITICAL
import logging
from typing import Annotated, Any, Optional

try:
    from fastapi import Depends, HTTPException, Query
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
        logger.warning("Error de validación en parámetro FastAPI: %s", exc)
        raise HTTPException(
            status_code=HTTP_422,
            detail=[
                {
                    "loc": ["query", "rut"],
                    "msg": str(exc),
                    "type": exc.codigo_error or "valor_error.rut_invalido",
                }
            ],
        ) from exc


def consulta_rut(
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


# Alias para compatibilidad retroactiva
ConsultaRut = consulta_rut  # pylint: disable=invalid-name


# Alias para facilitar el descubrimiento
parametro_rut = obtener_param_rut
ParametroRut = parametro_rut  # pylint: disable=invalid-name

__all__ = [
    "obtener_param_rut",
    "parametro_rut",
    "ParametroRut",
    "consulta_rut",
    "ConsultaRut",
]
