# pylint: disable=missing-module-docstring

import re
from typing import List, Tuple, Dict, Union
from collections import deque

FACTORES_DIGITO_VERIFICADOR: List[int] = [2, 3, 4, 5, 6, 7]
MODULO_DIGITO_VERIFICADOR: int = 11
RUT_REGEX: str = r"^(\d{1,8}(?:.\d{3})*)(-([0-9kK]))?$"


class RutInvalidoError(Exception):
    """Lanzada cuando el RUT ingresado es inválido."""


class RutBase:
    """Representa el número base de un RUT chileno."""

    def __init__(self, base: str):
        self.rut_original: str = base
        self.base: str = self._validar_y_normalizar_base(base)

    def _validar_y_normalizar_base(self, base: str) -> str:
        """
        Valida y normaliza el número base.

        Args:
            base (str): El número base del RUT.

        Returns:
            str: El número base normalizado.

        Raises:
            RutInvalidoError: Si el número base es inválido.
        """
        if not re.match(r"^\d{1,3}(?:\.\d{3})*$", base) and not base.isdigit():
            raise RutInvalidoError(f"El número base '{base}' no es válido.")

        base_normalizada: str = base.replace(".", "").lstrip("0")
        if len(base_normalizada) > 8:
            raise RutInvalidoError(
                f"El rut '{self.rut_original}' es inválido ya que contiene más de 8 dígitos."
            )

        return base_normalizada

    def __str__(self) -> str:
        return self.base


class RutDigitoVerificador(RutBase):
    """Calcula y representa el dígito verificador de un RUT chileno."""

    def __init__(self, base: str):
        super().__init__(base)
        self.digito_verificador: str = self._calcular_digito_verificador()

    def _calcular_digito_verificador(self) -> str:
        """
        Calcula el dígito verificador del RUT.

        Returns:
            str: El dígito verificador del RUT.
        """
        factores = deque(FACTORES_DIGITO_VERIFICADOR)
        suma_parcial: int = sum(
            int(digito) * factores[0] for digito in reversed(str(self.base))
        )
        factores.rotate(-1)
        digito_verificador: int = (
            MODULO_DIGITO_VERIFICADOR - suma_parcial % MODULO_DIGITO_VERIFICADOR
        ) % MODULO_DIGITO_VERIFICADOR
        return str(digito_verificador) if digito_verificador < 10 else "k"

    def __str__(self) -> str:
        return self.digito_verificador


class RutValidador:
    """Valida un RUT chileno."""

    @staticmethod
    def validar_formato(rut: str) -> Tuple[bool, str]:
        """Valida el formato del RUT."""
        match = re.fullmatch(RUT_REGEX, rut)
        if not match:
            return False, f"El formato del RUT '{rut}' es inválido."
        return True, match.group(1)

    @staticmethod
    def validar_digito_verificador(base: str, digito: str) -> bool:
        """Valida el dígito verificador del RUT."""
        digito_calculado = RutDigitoVerificador(base).digito_verificador
        return digito.lower() == digito_calculado


class Rut:
    """
    Representa un RUT chileno.

    Atributos:
        rut_string (str): El RUT en formato string.
        base (RutBase): El número base del RUT.
        digito_verificador (RutDigitoVerificador): El dígito verificador del RUT.

    Métodos:
        formatear: Formatea el RUT según las opciones especificadas.
        formatear_lista_ruts: Formatea una lista de RUTs según las opciones especificadas.
    """

    def __init__(self, rut: str):
        self.rut_string: str = str(rut).strip()
        self._validar_rut()
        self.base = RutBase(self.base_string)
        self.digito_verificador = RutDigitoVerificador(self.base_string)

    def _validar_rut(self) -> None:
        """Valida el formato y el dígito verificador del RUT."""
        es_valido, resultado = RutValidador.validar_formato(self.rut_string)
        if not es_valido:
            raise RutInvalidoError(resultado)
        
        self.base_string = resultado
        match = re.fullmatch(RUT_REGEX, self.rut_string)
        digito_verificador_input = match.group(3).lower() if match.group(3) else None
        
        if digito_verificador_input and not RutValidador.validar_digito_verificador(self.base_string, digito_verificador_input):
            raise RutInvalidoError(
                f"El dígito verificador '{digito_verificador_input}' no coincide con "
                f"el dígito verificador calculado '{self.digito_verificador}'."
            )

    def __str__(self) -> str:
        return f"{self.base}-{self.digito_verificador}"

    def formatear(self, separador_miles: bool = False, mayusculas: bool = False) -> str:
        """
        Formatea el RUT según las opciones especificadas.

        Args:
            separador_miles (bool, optional): Si se deben agregar separadores de miles (puntos).
            mayusculas (bool, optional): Si los RUTs deben estar en mayúsculas.

        Returns:
            str: El RUT formateado.
        """
        rut = str(self)
        if separador_miles:
            rut = (
                self._agregar_separador_miles(rut.split("-", maxsplit=1)[0])
                + "-"
                + rut.split("-")[1]
            )

        return rut.upper() if mayusculas else rut

    @staticmethod
    def _agregar_separador_miles(numero: str) -> str:
        return f"{int(numero):,}".replace(",", ".")

    @staticmethod
    def _validar_lista_ruts(ruts: List[str]) -> Dict[str, List[Union[str, Tuple[str, str]]]]:
        validos: List[str] = []
        invalidos: List[Tuple[str, str]] = []
        for rut in ruts:
            try:
                rut_valido: str = str(Rut(rut))
                validos.append(rut_valido)
            except RutInvalidoError as e:
                invalidos.append((rut, str(e)))
        return {"validos": validos, "invalidos": invalidos}

    @staticmethod
    def _formatear_csv(ruts_formateados: List[str]) -> str:
        return f"rut\n{chr(10).join(ruts_formateados)}"

    @staticmethod
    def _formatear_xml(ruts_formateados: List[str]) -> str:
        return "\n".join(["<root>"] + [f"    <rut>{rut}</rut>" for rut in ruts_formateados] + ["</root>"])

    @staticmethod
    def _formatear_json(ruts_formateados: List[str]) -> str:
        return str([{"rut": rut} for rut in ruts_formateados])

    @staticmethod
    def formatear_lista_ruts(
        ruts: List[str],
        separador_miles: bool = False,
        mayusculas: bool = False,
        formato: Union[str, None] = None,
    ) -> str:
        """
        Formatea una lista de RUTs según las opciones especificadas.

        Args:
            ruts (List[str]): Una lista de RUTs en formato string o numérico.
            separador_miles (bool, opcional): Si se deben agregar separadores de miles (puntos).
            mayusculas (bool, opcional): Si los RUTs deben estar en mayúsculas.
            formato (str, opcional): El formato de salida deseado (csv, json, xml, None).

        Returns:
            str: Una cadena con los RUTs válidos e inválidos formateados según las opciones
                especificadas.
        """
        formato_salida: Dict[str, callable] = {
            "csv": Rut._formatear_csv,
            "xml": Rut._formatear_xml,
            "json": Rut._formatear_json,
        }
        ruts_validos_invalidos: Dict[str, List[Union[str, Tuple[str, str]]]] = Rut._validar_lista_ruts(ruts)
        ruts_validos: List[str] = ruts_validos_invalidos["validos"]
        ruts_invalidos: List[Tuple[str, str]] = ruts_validos_invalidos["invalidos"]

        resultado: List[str] = []
        if ruts_validos:
            ruts_validos_formateados: List[str] = [
                Rut(rut).formatear(separador_miles, mayusculas) for rut in ruts_validos
            ]
            resultado.append("RUTs válidos:")
            if formato in formato_salida:
                resultado.append(formato_salida[formato](ruts_validos_formateados))
            else:
                resultado.extend(ruts_validos_formateados)

        if ruts_invalidos:
            resultado.append("\nRUTs inválidos:")
            resultado.extend(f"{rut} - {error}" for rut, error in ruts_invalidos)

        return "\n".join(resultado)
