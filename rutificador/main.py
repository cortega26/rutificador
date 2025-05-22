# pylint: disable=missing-module-docstring

import json
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Union, Optional, Literal

# ============================================================================
# CONSTANTS & TYPE DEFINITIONS
# ============================================================================

FACTORES_DIGITO_VERIFICADOR: List[int] = [2, 3, 4, 5, 6, 7]
MODULO_DIGITO_VERIFICADOR: int = 11
RUT_REGEX: str = r"^(\d{1,8}(?:.\d{3})*)(-([0-9kK]))?$"

FormatoOutput = Literal["csv", "xml", "json"]


# ============================================================================
# EXCEPTIONS
# ============================================================================

class RutInvalidoError(Exception):
    """Lanzada cuando el RUT ingresado es inválido."""


# ============================================================================
# CORE UTILITIES
# ============================================================================

def calcular_digito_verificador(base_numerica: str) -> str:
    """
    Calcula el dígito verificador del RUT de forma optimizada.
    
    Args:
        base_numerica (str): El número base del RUT sin puntos ni guiones.
        
    Returns:
        str: El dígito verificador del RUT.
    """
    suma_parcial: int = 0
    factor_index: int = 0

    if not base_numerica:
        raise RutInvalidoError("La base numérica no puede estar vacía.")

    # Iteramos desde el final hacia adelante sin crear string reversed
    for i in range(len(base_numerica) - 1, -1, -1):
        digito: int = int(base_numerica[i])
        suma_parcial += digito * FACTORES_DIGITO_VERIFICADOR[factor_index % 6]
        factor_index += 1

    digito_verificador: int = (
        MODULO_DIGITO_VERIFICADOR - suma_parcial % MODULO_DIGITO_VERIFICADOR
    ) % MODULO_DIGITO_VERIFICADOR

    return str(digito_verificador) if digito_verificador < 10 else "k"


def normalizar_base_rut(base: str) -> str:
    """
    Normaliza la base del RUT removiendo puntos y ceros iniciales.
    
    Args:
        base (str): La base del RUT a normalizar.
        
    Returns:
        str: La base normalizada.
    """
    base_normalizada = base.replace(".", "").lstrip("0")
    return base_normalizada if base_normalizada else "0"


# ============================================================================
# VALIDATION LAYER
# ============================================================================

class RutValidator:
    """Responsable únicamente de validar RUTs."""

    PATRON_RUT = re.compile(RUT_REGEX)
    
    @classmethod
    def validar_formato(cls, rut_string: str) -> re.Match:
        """
        Valida el formato del RUT.

        Args:
            rut_string (str): El RUT a validar.

        Returns:
            re.Match: El objeto match de la validación.

        Raises:
            RutInvalidoError: Si el formato es inválido.
        """
        if not rut_string or not isinstance(rut_string, str):
            raise RutInvalidoError(f"El RUT '{rut_string}' no es válido.")
            
        rut_string = rut_string.strip()
        match = cls.PATRON_RUT.fullmatch(rut_string)

        if not match:
            raise RutInvalidoError(f"El formato del RUT '{rut_string}' es inválido.")

        return match
    
    @classmethod
    def validar_base(cls, base: str, rut_original: str) -> str:
        """
        Valida y normaliza el número base del RUT.

        Args:
            base (str): El número base del RUT.
            rut_original (str): El RUT original para mensajes de error.

        Returns:
            str: El número base normalizado.

        Raises:
            RutInvalidoError: Si el número base es inválido.
        """
        if not base or not isinstance(base, str):
            raise RutInvalidoError(f"El número base '{base}' no es válido.")

        if not re.match(r"^\d{1,3}(?:\.\d{3})*$", base) and not base.isdigit():
            raise RutInvalidoError(f"El número base '{base}' no es válido.")

        base_normalizada = normalizar_base_rut(base)

        if len(base_normalizada) > 8:
            raise RutInvalidoError(
                f"El rut '{rut_original}' es inválido ya que contiene más de 8 dígitos."
            )

        return base_normalizada

    @classmethod
    def validar_digito_verificador(
        cls, 
        digito_input: Optional[str], 
        digito_calculado: str
    ) -> None:
        """
        Valida que el dígito verificador proporcionado coincida con el calculado.

        Args:
            digito_input: El dígito verificador proporcionado por el usuario.
            digito_calculado: El dígito verificador calculado.

        Raises:
            RutInvalidoError: Si el dígito verificador no coincide.
        """
        if digito_input and digito_input.lower() != digito_calculado:
            raise RutInvalidoError(
                f"El dígito verificador '{digito_input}' no coincide con "
                f"el dígito verificador calculado '{digito_calculado}'."
            )


# ============================================================================
# FORMATTING LAYER
# ============================================================================

class RutFormatter(ABC):
    """Interfaz abstracta para formateadores de RUT."""
    
    @abstractmethod
    def format(self, ruts: List[str]) -> str:
        """Formatea una lista de RUTs."""
        pass


class CSVFormatter(RutFormatter):
    """Formateador CSV para RUTs."""
    
    def format(self, ruts: List[str]) -> str:
        cadena_ruts = "\n".join(ruts)
        return f"rut\n{cadena_ruts}"


class XMLFormatter(RutFormatter):
    """Formateador XML para RUTs."""
    
    def format(self, ruts: List[str]) -> str:
        xml_lines = ["<root>"]
        for rut in ruts:
            xml_lines.append(f"    <rut>{rut}</rut>")
        xml_lines.append("</root>")
        return "\n".join(xml_lines)


class JSONFormatter(RutFormatter):
    """Formateador JSON para RUTs."""
    
    def format(self, ruts: List[str]) -> str:
        ruts_json = [{"rut": rut} for rut in ruts]
        return json.dumps(ruts_json, indent=2, ensure_ascii=False)


class RutFormatterFactory:
    """Factory para crear formateadores de RUT."""
    
    _formatters: Dict[str, RutFormatter] = {
        "csv": CSVFormatter(),
        "xml": XMLFormatter(),
        "json": JSONFormatter(),
    }
    
    @classmethod
    def get_formatter(cls, formato: str) -> Optional[RutFormatter]:
        """Obtiene un formateador por su nombre."""
        return cls._formatters.get(formato.lower())
    
    @classmethod
    def get_available_formats(cls) -> List[str]:
        """Obtiene la lista de formatos disponibles."""
        return list(cls._formatters.keys())


# ============================================================================
# CORE DOMAIN MODELS
# ============================================================================

class RutBase:
    """Representa el número base de un RUT chileno."""

    def __init__(self, base: str, rut_original: str):
        self.rut_original = rut_original
        self.base = RutValidator.validar_base(base, rut_original)

    def __str__(self) -> str:
        return self.base

    def __eq__(self, other) -> bool:
        if not isinstance(other, RutBase):
            return False
        return self.base == other.base

    def __hash__(self) -> int:
        return hash(self.base)


class Rut:
    """
    Representa un RUT chileno completo.
    
    Esta clase se enfoca únicamente en representar un RUT individual,
    delegando validación a RutValidator y formateo a RutFormatter.
    """

    def __init__(self, rut: str):
        self.rut_string = str(rut).strip()

        # Validar formato y extraer componentes
        match_result = RutValidator.validar_formato(self.rut_string)
        self.base_string = match_result.group(1)
        digito_input = match_result.group(3)

        # Crear base y calcular dígito verificador
        self.base = RutBase(self.base_string, self.rut_string)
        self.digito_verificador = calcular_digito_verificador(
            normalizar_base_rut(self.base_string)
        )

        # Validar dígito verificador si fue proporcionado
        RutValidator.validar_digito_verificador(digito_input, self.digito_verificador)

    def __str__(self) -> str:
        return f"{self.base}-{self.digito_verificador}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Rut):
            return False
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def formatear(self, separador_miles: bool = False, mayusculas: bool = False) -> str:
        """
        Formatea el RUT según las opciones especificadas.

        Args:
            separador_miles: Si se deben agregar separadores de miles (puntos).
            mayusculas: Si el RUT debe estar en mayúsculas.

        Returns:
            str: El RUT formateado.
        """
        rut_str = str(self)

        if separador_miles:
            base_formateada = self._agregar_separador_miles(str(self.base))
            rut_str = f"{base_formateada}-{self.digito_verificador}"

        if mayusculas:
            rut_str = rut_str.upper()

        return rut_str

    @staticmethod
    def _agregar_separador_miles(numero: str) -> str:
        """Agrega separadores de miles a un número."""
        return f"{int(numero):,}".replace(",", ".")


# ============================================================================
# BATCH PROCESSING SERVICE
# ============================================================================

class RutBatchProcessor:
    """
    Servicio para procesamiento por lotes de RUTs.

    Separada de la clase Rut principal para seguir el principio de responsabilidad única.
    """
    
    @staticmethod
    def validar_lista_ruts(ruts: List[str]) -> Dict[str, List[Union[str, Tuple[str, str]]]]:
        """
        Valida una lista de RUTs y separa válidos de inválidos.

        Args:
            ruts: Lista de RUTs en formato string.

        Returns:
            Dict con listas de RUTs válidos e inválidos.
        """
        validos: List[str] = []
        invalidos: List[Tuple[str, str]] = []

        for rut_string in ruts:
            try:
                rut_obj = Rut(rut_string)
                validos.append(str(rut_obj))
            except RutInvalidoError as e:
                invalidos.append((rut_string, str(e)))

        return {"validos": validos, "invalidos": invalidos}
    
    @staticmethod
    def formatear_lista_ruts(
        ruts: List[str],
        separador_miles: bool = False,
        mayusculas: bool = False,
        formato: Optional[FormatoOutput] = None,
    ) -> str:
        """
        Formatea una lista de RUTs según las opciones especificadas.

        Args:
            ruts: Una lista de RUTs en formato string.
            separador_miles: Si se deben agregar separadores de miles (puntos).
            mayusculas: Si los RUTs deben estar en mayúsculas.
            formato: El formato de salida deseado (csv, json, xml, None).

        Returns:
            str: Una cadena con los RUTs válidos e inválidos formateados.
        """
        # Validar RUTs
        resultado_validacion = RutBatchProcessor.validar_lista_ruts(ruts)
        ruts_validos = resultado_validacion["validos"]
        ruts_invalidos = resultado_validacion["invalidos"]

        resultado = ""
        
        # Procesar RUTs válidos
        if ruts_validos:
            ruts_validos_formateados = []
            for rut_string in ruts_validos:
                try:
                    rut_obj = Rut(rut_string)
                    ruts_validos_formateados.append(
                        rut_obj.formatear(separador_miles, mayusculas)
                    )
                except RutInvalidoError:
                    # Este caso no debería ocurrir ya que los RUTs ya fueron validados
                    continue

            resultado += "RUTs válidos:\n"
            
            # Aplicar formato específico si se solicita
            if formato:
                formatter = RutFormatterFactory.get_formatter(formato)
                if formatter:
                    resultado += formatter.format(ruts_validos_formateados)
                else:
                    raise ValueError(f"Formato '{formato}' no soportado. "
                                    f"Formatos disponibles: {RutFormatterFactory.get_available_formats()}")
            else:
                resultado += "\n".join(ruts_validos_formateados)

            resultado += "\n\n"

        # Procesar RUTs inválidos
        if ruts_invalidos:
            resultado += "RUTs inválidos:\n"
            for rut, error in ruts_invalidos:
                resultado += f"{rut} - {error}\n"

        return resultado


# ============================================================================
# BACKWARDS COMPATIBILITY
# ============================================================================

# Mantener compatibilidad con la API original
def formatear_lista_ruts(
    ruts: List[str],
    separador_miles: bool = False,
    mayusculas: bool = False,
    formato: Optional[str] = None,
) -> str:
    """
    Función de compatibilidad con la API original.

    Delegada al nuevo RutBatchProcessor.
    """
    return RutBatchProcessor.formatear_lista_ruts(
        ruts, separador_miles, mayusculas, formato
    )