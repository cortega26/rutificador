"""
Este módulo proporciona clases y funciones para validar, formatear y manipular RUTs chilenos.

Clases:
- RutBase: Representa el número base de un RUT chileno.
- RutDigitoVerificador: Calcula y representa el dígito verificador de un RUT chileno.
- Rut: Representa un RUT chileno completo y proporciona métodos para validarlo y formatearlo.

Funciones:
- calcular_digito_verificador: Calcula el dígito verificador de un RUT.
- validar_lista_ruts(ruts): Valida una lista de RUTs.
- formatear_lista_ruts(ruts, separador_miles=False, mayusculas=False, formato=None):
    Formatea una lista de RUTs chilenos según las opciones especificadas.

Excepciones:
- RutInvalidoError: Excepción lanzada cuando se encuentra un RUT inválido.
"""

import re

FACTORES_DIGITO_VERIFICADOR = [2, 3, 4, 5, 6, 7]
MODULO_DIGITO_VERIFICADOR = 11
RUT_REGEX = r"^(\d{1,8}(?:.\d{3})*)(-([0-9kK]))?$"


class RutInvalidoError(Exception):
    """Lanzada cuando el formato del RUT ingresado es inválido."""


class RutBase:
    """Representa el número base de un RUT chileno."""

    def __init__(self, base):
        self.rut_original = base
        self.base = self.validar_y_normalizar_base(base)

    def validar_y_normalizar_base(self, base):
        """Valida y normaliza el número base."""
        if not re.match(r"^\d{1,3}(?:\.\d{3})*$", base) and not base.isdigit():
            raise RutInvalidoError(f"El número base '{base}' no es válido.")

        base_normalizada = base.replace(".", "").lstrip("0")
        if len(base_normalizada) > 8:
            raise RutInvalidoError(
                f"El rut '{self.rut_original}' es inválido ya que contiene más de 8 dígitos."
            )

        return base_normalizada

    def __str__(self):
        return self.base


class RutDigitoVerificador(RutBase):
    """Calcula y representa el dígito verificador de un RUT chileno."""

    def __init__(self, base):
        super().__init__(base)
        self.digito_verificador = self.calcular_digito_verificador()

    def calcular_digito_verificador(self):
        """Calcula el dígito verificador del RUT."""
        suma_parcial = sum(
            int(digito) * FACTORES_DIGITO_VERIFICADOR[i % 6]
            for i, digito in enumerate(reversed(str(self.base)))
        )
        digito_verificador = (
            MODULO_DIGITO_VERIFICADOR - suma_parcial % MODULO_DIGITO_VERIFICADOR
        ) % MODULO_DIGITO_VERIFICADOR
        return str(digito_verificador) if digito_verificador < 10 else "k"

    def __str__(self):
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
        validar_lista_ruts: Valida una lista de RUTs.
        formatear_lista_ruts: Formatea una lista de RUTs según las opciones especificadas.
    """

    PATRON_RUT = re.compile(RUT_REGEX)

    def __init__(self, rut: str):
        """
        Inicializa un objeto Rut.

        Args:
            rut (str): El RUT en formato string o numérico.

        Raises:
            RutInvalidoError: Si el formato del RUT ingresado es inválido.
        """
        self.rut_string = str(rut).strip()
        self._validar_formato_rut()
        self.base = RutBase(self.base_string)
        self.digito_verificador = RutDigitoVerificador(self.base_string)

    def _validar_formato_rut(self):
        """Valida el formato del RUT ingresado."""
        match = Rut.PATRON_RUT.fullmatch(self.rut_string)
        if not match:
            raise RutInvalidoError(
                f"El formato del RUT '{self.rut_string}' es inválido."
            )

        self.base_string = match.group(1)
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

    def __str__(self):
        return f"{self.base}-{self.digito_verificador}"

    def formatear(self, separador_miles=False, mayusculas=False):
        """
        Formatea el RUT según las opciones especificadas.

        Args:
            separador_miles (bool, opcional): Si se deben agregar separadores de miles (puntos).
            mayusculas (bool, opcional): Si el D.V. debe ser mayúscula cuando este sea 'k'.

        Returns:
            str: El RUT formateado según las opciones especificadas.
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
    def _agregar_separador_miles(numero):
        """Agrega separadores de miles (puntos) a un número."""
        return f"{int(numero):,}".replace(",", ".")

    @staticmethod
    def validar_lista_ruts(ruts):
        """
        Valida una lista de RUTs.

        Args:
            ruts (List[str]): Una lista de RUTs en formato string o numérico.

        Returns:
            dict: Un diccionario con dos claves: 'validos' y 'invalidos',
                  cada una conteniendo una lista de RUTs válidos e inválidos respectivamente.

        Raises:
            RutInvalidoError: Si alguno de los RUTs en la lista es inválido.
        """
        validos = []
        invalidos = []
        for rut in ruts:
            try:
                rut_valido = str(Rut(rut))
                validos.append(rut_valido)
            except RutInvalidoError as e:
                invalidos.append((rut, str(e)))
        return {'validos': validos, 'invalidos': invalidos}

    @staticmethod
    def _formatear_csv(ruts_formateados):
        cadena_ruts = "\n".join(ruts_formateados)
        return f"rut\n{cadena_ruts}"

    @staticmethod
    def _formatear_xml(ruts_formateados):
        xml_lines = ["<root>"]
        for rut in ruts_formateados:
            xml_lines.append(f"    <rut>{rut}</rut>")
        xml_lines.append("</root>")
        return "\n".join(xml_lines)

    @staticmethod
    def _formatear_json(ruts_formateados):
        ruts_json = [{"rut": rut} for rut in ruts_formateados]
        return str(ruts_json)

    @staticmethod
    def formatear_lista_ruts(
        ruts,
        separador_miles=False,
        mayusculas=False,
        formato=None,
    ):
        """
        Formatea una lista de RUTs según las opciones especificadas.
        
        Args:
        ruts (List[str]): Una lista de RUTs en formato string o numérico.
        separador_miles (bool): Si se deben agregar separadores de miles (puntos).
        mayusculas (bool): Si los RUTs deben estar en mayúsculas.
        formato (str, opcional): El formato de salida deseado (csv, json, xml, etc.).

        Returns:
            str: Una cadena con los RUTs válidos e inválidos formateados según las opciones
                especificadas.

        Raises:
            RutInvalidoError: Si alguno de los RUTs en la lista es inválido.
            ValueError: Si se especifica un formato no válido.
        """
        formato_salida = {
            "csv": Rut._formatear_csv,
            "xml": Rut._formatear_xml,
            "json": Rut._formatear_json,
        }
        ruts_validos_invalidos = Rut.validar_lista_ruts(ruts)
        ruts_validos = ruts_validos_invalidos['validos']
        ruts_invalidos = ruts_validos_invalidos['invalidos']

        resultado = ''
        if ruts_validos:
            ruts_validos_formateados = [Rut(rut).formatear(separador_miles, mayusculas)
                                        for rut in ruts_validos]
            resultado += 'RUTs válidos:\n'
            if formato in ('csv', 'xml', 'json'):
                resultado += formato_salida[formato](ruts_validos_formateados)
            else:
                resultado += '\n'.join(ruts_validos_formateados)
            resultado += '\n\n'

        if ruts_invalidos:
            resultado += 'RUTs inválidos:\n'
            for rut, error in ruts_invalidos:
                resultado += f'{rut} - {error}\n'

        return resultado