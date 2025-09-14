import logging
import re
from typing import Optional, Protocol, runtime_checkable, Match

from .config import CONFIGURACION_POR_DEFECTO, ConfiguracionRut, RigorValidacion
from .exceptions import ErrorFormatoRut, ErrorDigitoRut, ErrorLongitudRut, ErrorValidacionRut
from .utils import normalizar_base_rut, asegurar_cadena_no_vacia

logger = logging.getLogger(__name__)

# Expresiones regulares compiladas una vez
RUT_REGEX = re.compile(r"^(\d{1,8}(?:\.\d{3})*)(-([0-9kK]))?$")
BASE_WITH_DOTS_REGEX = re.compile(r"^\d{1,3}(?:\.\d{3})*$")
BASE_DIGITS_ONLY_REGEX = re.compile(r"^\d+$")


@runtime_checkable
class Validador(Protocol):  # pylint: disable=too-few-public-methods
    """Protocolo para validadores de RUT."""

    def validate(self, cadena_rut: str) -> bool:  # pragma: no cover - protocolo
        """Valida una cadena de RUT."""
        raise NotImplementedError


class ValidadorRut:
    """Validador de RUT con niveles de rigurosidad configurables."""

    def __init__(
        self,
        configuracion: ConfiguracionRut = CONFIGURACION_POR_DEFECTO,
        modo: RigorValidacion = RigorValidacion.ESTRICTO,
    ) -> None:
        self.configuracion = configuracion
        self.modo = modo
        logger.debug("ValidadorRut inicializado con modo: %s", modo.value)

    def validar_formato(self, cadena_rut: str) -> Match[str]:
        """Valida el formato del RUT."""
        cadena_rut = asegurar_cadena_no_vacia(cadena_rut, "RUT")

        if self.modo == RigorValidacion.FLEXIBLE:
            cadena_rut = self._normalizar_entrada(cadena_rut)

        match = RUT_REGEX.fullmatch(cadena_rut)
        if not match:
            raise ErrorFormatoRut(
                cadena_rut,
                "XXXXXXXX-X o XX.XXX.XXX-X donde X son dígitos y el último puede ser 'k'",
            )
        logger.debug("Formato de RUT validado correctamente: %s", cadena_rut)
        return match

    def validar_base(self, base: str, rut_original: str) -> str:
        """Valida y normaliza el número base del RUT."""
        base = asegurar_cadena_no_vacia(base, "base")

        if not (
            BASE_WITH_DOTS_REGEX.match(base)
            or BASE_DIGITS_ONLY_REGEX.match(base)
        ):
            raise ErrorFormatoRut(
                base, "cadena numérica con separadores de miles opcionales"
            )

        base_normalizada = normalizar_base_rut(base)
        if len(base_normalizada) > self.configuracion.max_digitos:
            raise ErrorLongitudRut(
                rut_original, len(base_normalizada), self.configuracion.max_digitos
            )
        logger.debug("Base validada y normalizada: %s -> %s", base, base_normalizada)
        return base_normalizada

    def validar_digito_verificador(
        self, digito_ingresado: Optional[str], digito_calculado: str
    ) -> None:
        """Valida el dígito verificador del RUT."""
        if digito_ingresado is None:
            return
        if not isinstance(digito_ingresado, str):
            raise ErrorValidacionRut(
                "El dígito verificador debe ser una cadena", error_code="TYPE_ERROR"
            )
        if digito_ingresado.lower() != digito_calculado.lower():
            raise ErrorDigitoRut(digito_ingresado, digito_calculado)
        logger.debug(
            "Dígito verificador validado: %s == %s", digito_ingresado, digito_calculado
        )

    def _normalizar_entrada(self, cadena_rut: str) -> str:
        """Normaliza la entrada en modo de validación flexible."""
        normalizado = re.sub(r"\s+", "", cadena_rut)
        normalizado = normalizado.replace("_", "-").replace("–", "-")
        return normalizado


# Alias para compatibilidad retroactiva
RutValidator = ValidadorRut

__all__ = [
    "Validador",
    "ValidadorRut",
    "RutValidator",
]
