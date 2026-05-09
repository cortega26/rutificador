# SECURITY-CRITICAL
import logging

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Pandas no está instalado. Instálalo con 'pip install rutificador[pandas]'"
    ) from exc

from ..rut import Rut, RigorValidacion
from ._formato_comun import aplicar_formato

logger = logging.getLogger(__name__)


@pd.api.extensions.register_series_accessor("rut")
class RutAccessor:
    """Accessor de Pandas para operaciones de RUT en Series."""

    def __init__(self, pandas_obj: pd.Series):
        self._obj = pandas_obj

    def validar(self, modo: RigorValidacion = RigorValidacion.ESTRICTO) -> pd.Series:
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
                return aplicar_formato(res, formato)
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
            norm, _, _ = Rut.normalizar(x, modo=RigorValidacion.FLEXIBLE)
            return norm

        return self._obj.apply(_norm)
