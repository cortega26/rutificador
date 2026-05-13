# SECURITY-CRITICAL
"""Namespace de polars para validar y formatear RUTs en ``Expr``.

Registra ``RutNamespace`` como extensión de polars (``Expr.rut``) con los
métodos ``validar``, ``formatear``, ``es_valido`` y ``normalizar``.
"""

import logging

# No additional imports needed from typing for now

try:
    import polars as pl
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Polars no está instalado. Instálalo con 'pip install rutificador[polars]'"
    ) from exc

from ..rut import Rut, RigorValidacion
from ._formato_comun import aplicar_formato

logger = logging.getLogger(__name__)


@pl.api.register_series_namespace("rut")
class RutNamespace:
    """Namespace de Polars para operaciones de RUT en Series."""

    def __init__(self, s: pl.Series):
        self._s = s

    def validar(self, modo: RigorValidacion = RigorValidacion.ESTRICTO) -> pl.Series:
        """Parsea los RUTs delegando en Rut.parse."""

        def _val(x):
            try:
                return Rut.parse(x, modo=modo)
            except Exception:
                return None

        return self._s.map_elements(_val, return_dtype=pl.Object)

    def formatear(
        self, formato: str = "base-dv", modo: RigorValidacion = RigorValidacion.ESTRICTO
    ) -> pl.Series:
        """Formatea los RUTs de la serie."""

        def _fmt(x):
            try:
                res = Rut.parse(x, modo=modo)
                return aplicar_formato(res, formato)
            except Exception:
                return None

        return self._s.map_elements(_fmt, return_dtype=pl.String)

    @property
    def es_valido(self) -> pl.Series:
        """Determina la validez de los RUTs de la serie."""

        def _check(x):
            try:
                res = Rut.parse(x, modo=RigorValidacion.ESTRICTO)
                return res.estado == "valido"
            except Exception:
                return False

        return self._s.map_elements(_check, return_dtype=pl.Boolean)

    def normalizar(self) -> pl.Series:
        """Normaliza los RUTs de la serie."""

        def _norm(x):
            try:
                norm, _, _ = Rut.normalizar(x, modo=RigorValidacion.FLEXIBLE)
                return norm
            except Exception:
                return None

        return self._s.map_elements(_norm, return_dtype=pl.String)
