# pylint: disable=missing-module-docstring

import re

FACTORES_DIGITO_VERIFICADOR: list[int] = [2, 3, 4, 5, 6, 7]
MODULO_DIGITO_VERIFICADOR: int = 11
RUT_REGEX: str = r"^(\d{1,8}(?:.\d{3})*)(-([0-9kK]))?$"


class RutInvalidoError(Exception):
    """Lanzada cuando el RUT ingresado es inválido."""


class RutBase:
    """Representa el número base de un RUT chileno."""

    def __init__(self, base: str):
        self.rut_original: str = base
        self.base: str = self.validar_y_normalizar_base(base)

    def validar_y_normalizar_base(self, base: str) -> str:
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
        self.digito_verificador: str = self.calcular_digito_verificador()

    def calcular_digito_verificador(self) -> str:
        """
        Calcula el dígito verificador del RUT.

        Returns:
            str: El dígito verificador del RUT.
        """
        suma_parcial: int = sum(
            int(digito) * FACTORES_DIGITO_VERIFICADOR[i % 6]
            for i, digito in enumerate(reversed(str(self.base)))
        )
        digito_verificador: int = (
            MODULO_DIGITO_VERIFICADOR - suma_parcial % MODULO_DIGITO_VERIFICADOR
        ) % MODULO_DIGITO_VERIFICADOR
        return str(digito_verificador) if digito_verificador < 10 else "k"

    def __str__(self) -> str:
        return self.digito_verificador


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

    PATRON_RUT = re.compile(RUT_REGEX)

    def __init__(self, rut: str):
        self.rut_string: str = str(rut).strip()
        self._validar_formato_rut()
        self._validar_digito_verificador()
        self.base = RutBase(self.base_string)
        self.digito_verificador = RutDigitoVerificador(self.base_string)

    def _validar_formato_rut(self) -> None:
        match = Rut.PATRON_RUT.fullmatch(self.rut_string)
        if not match:
            raise RutInvalidoError(
                f"El formato del RUT '{self.rut_string}' es inválido."
            )
        self.base_string: str = match.group(1)

    def _validar_digito_verificador(self) -> None:
        match = Rut.PATRON_RUT.fullmatch(self.rut_string)
        digito_verificador_input = match.group(3).lower() if match.group(3) else None
        digito_verificador_calculado = RutDigitoVerificador(
            self.base_string
        ).digito_verificador

        if (
            digito_verificador_input
            and digito_verificador_input != digito_verificador_calculado
        ):
            raise RutInvalidoError(
                f"El dígito verificador '{digito_verificador_input}' no coincide con "
                f"el dígito verificador calculado '{digito_verificador_calculado}'."
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

        if mayusculas:
            rut = rut.upper()

        return rut

    @staticmethod
    def _agregar_separador_miles(numero: str) -> str:
        return f"{int(numero):,}".replace(",", ".")

    @staticmethod
    def _validar_lista_ruts(ruts: list[str]) -> dict[str, list[str]]:
        validos: list[str] = []
        invalidos: list[tuple[str, str]] = []
        for rut in ruts:
            try:
                rut_valido: str = str(Rut(rut))
                validos.append(rut_valido)
            except RutInvalidoError as e:
                invalidos.append((rut, str(e)))
        return {"validos": validos, "invalidos": invalidos}

    @staticmethod
    def _formatear_csv(ruts_formateados: list[str]) -> str:
        cadena_ruts: str = "\n".join(ruts_formateados)
        return f"rut\n{cadena_ruts}"

    @staticmethod
    def _formatear_xml(ruts_formateados: list[str]) -> str:
        xml_lines: list[str] = ["<root>"]
        for rut in ruts_formateados:
            xml_lines.append(f"    <rut>{rut}</rut>")
        xml_lines.append("</root>")
        return "\n".join(xml_lines)

    @staticmethod
    def _formatear_json(ruts_formateados: list[str]) -> str:
        ruts_json: list[dict[str, str]] = [{"rut": rut} for rut in ruts_formateados]
        return str(ruts_json)

    @staticmethod
    def formatear_lista_ruts(
        ruts: list[str],
        separador_miles: bool = False,
        mayusculas: bool = False,
        formato=None,
    ) -> str:
        """
        Formatea una lista de RUTs según las opciones especificadas.

        Args:
            ruts (list[str]): Una lista de RUTs en formato string o numérico.
            separador_miles (bool, opcional): Si se deben agregar separadores de miles (puntos).
            mayusculas (bool, opcional): Si los RUTs deben estar en mayúsculas.
            formato (str, opcional): El formato de salida deseado (csv, json, xml, None).

        Returns:
            str: Una cadena con los RUTs válidos e inválidos formateados según las opciones
                especificadas.
        """
        formato_salida: dict[str, callable] = {
            "csv": Rut._formatear_csv,
            "xml": Rut._formatear_xml,
            "json": Rut._formatear_json,
        }
        ruts_validos_invalidos: dict[str, list[str]] = Rut._validar_lista_ruts(ruts)
        ruts_validos: list[str] = ruts_validos_invalidos["validos"]
        ruts_invalidos: list[tuple[str, str]] = ruts_validos_invalidos["invalidos"]

        resultado: str = ""
        if ruts_validos:
            ruts_validos_formateados: list[str] = [
                Rut(rut).formatear(separador_miles, mayusculas) for rut in ruts_validos
            ]
            resultado += "RUTs válidos:\n"
            if formato in ("csv", "xml", "json"):
                resultado += formato_salida[formato](ruts_validos_formateados)
            else:
                resultado += "\n".join(ruts_validos_formateados)
            resultado += "\n\n"

        if ruts_invalidos:
            resultado += "RUTs inválidos:\n"
            for rut, error in ruts_invalidos:
                resultado += f"{rut} - {error}\n"

        return resultado
