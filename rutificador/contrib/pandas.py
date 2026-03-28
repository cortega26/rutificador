# SECURITY-CRITICAL
import logging
from typing import Any, Optional, Union

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    raise ImportError(
        "Pandas no está instalado. Instálalo con 'pip install rutificador[pandas]'"
    )

from ..rut import Rut, RigorValidacion
from ..procesador import RutProcesado

logger = logging.getLogger(__name__)


@pd.api.extensions.register_series_accessor("rut")
class RutAccessor:
    """Accessor de Pandas para operaciones de RUT en Series."""

    def __init__(self, pandas_obj: pd.Series):
        self._obj = pandas_obj

    def validar(
        self, modo: RigorValidacion = RigorValidacion.ESTRICTO
    ) -> pd.Series:
        """Valida cada elemento de la serie y devuelve objetos RutProcesado."""
        def _val(x):
            try:
                # Rut.parse devuelve ValidacionResultado
                res = Rut.parse(x, modo=modo)
                return res
            except Exception:
                return None

        return self._obj.apply(_val)

    def formatear(
        self, formato: str = "base-dv", modo: RigorValidacion = RigorValidacion.ESTRICTO
    ) -> pd.Series:
        """Devuelve una serie con los RUTs formateados."""
        def _fmt(x):
            try:
                res = Rut.parse(x, modo=modo)
                if res.estado == "valido":
                    # Usamos la lógica de formateo interno
                    obj = Rut(res.normalizado)
                    # Aquí recreamos la lógica de formateo o usamos un helper
                    # Por simplicidad ahora usamos f-strings o los métodos de Rut
                    if formato == "miles":
                        base_masc = Rut.agregar_separador_miles(res.base)
                        return f"{base_masc}-{res.dv}"
                    if formato == "canonico":
                        return res.normalizado.upper()
                    if formato == "miles-con-guion":
                        base_masc = Rut.agregar_separador_miles(res.base)
                        return f"{base_masc}-{res.dv}".upper()
                    return res.normalizado
                return None
            except Exception:
                return None

        return self._obj.apply(_fmt)

    @property
    def es_valido(self) -> pd.Series:
        """Devuelve una serie booleana indicando si cada RUT es válido."""
        def _check(x):
            res = Rut.parse(x, modo=RigorValidacion.ESTRICTO)
            return res.estado == "valido"
        
        return self._obj.apply(_check)

    def normalizar(self) -> pd.Series:
        """Devuelve los RUTs normalizados (sin puntos, con guion)."""
        def _norm(x):
            norm, _, _ = Rut.normalizar(x, modo=RigorValidacion.HOLGADO)
            return norm
        
        return self._obj.apply(_norm)
