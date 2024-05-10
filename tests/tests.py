# pylint: disable=missing-module-docstring

import pytest
from rutificador.main import Rut, RutDigitoVerificador, RutBase, RutInvalidoError

# Datos de prueba para RutDigitoVerificador
cadenas_test_digito_verificador = [
    ("12345678", "5"),
    ("1", "9"),
    ("999", "7"),
    ("999999", "k"),
    ("22.791.914", "0"),
    ("8.670.089", "1"),
    ("10.535.006", "6"),
    ("84.920.968", "k"),
    ("123-", RutInvalidoError),  # Con guión pero sin dígito verificador
    ("1234567-1", RutInvalidoError),  # Con dígito verificador erróneo
]

# Datos de prueba para RutBase
cadenas_base_validas = [
    ("000.123.456", "123456"),
    ("12345678", "12345678"),
    ("1", "1"),
    ("12", "12"),
    ("123", "123"),
    ("1.234", "1234"),
    ("12.345", "12345"),
    ("123.456", "123456"),
    ("1.234.567", "1234567"),
    ("12.345.678", "12345678"),
]

cadenas_base_invalidas = [
    "123456789",  # Más de 8 dígitos
    "123.4567",  # Más de 3 dígitos luego del punto
    "12.32",  # Menos de 3 dígitos luego del punto
    "12.3a5.678",  # Letras en el RUT base
    "",  # RUT base vacío
    " ",  # RUT base sin dígitos
    "-1",  # RUT base negativo o dígito verificador sin base
]

# Datos de prueba para Rut
cadenas_rut_validas = [
    "12345678-5",  # Formato convencional
    " 12345678",  # Con espacio delante
    "12345679 ",  # Con espacio detrás
    " 12345680 ",  # Con espacio a ambos lados del RUT
    " 1-9 ",  # Con D.V. y espacio a ambos lados
    " 000000001 ",  # Con ceros delante y espacios
    " 00.000.001",  # Con ceros delante, puntos y espacios
    " 25.005.183-2 "  # Con puntos, espacios y D.V.
]
cadenas_rut_invalidas = ["12345678-9", "98765432-1", "12345.67", "123456789"]

# Datos de prueba para formatear_lista_ruts
datos_test_formato = [
    ("csv", "RUTs válidos:\nrut\n12345678-5\n98765432-5\n1-9\n\n"),
    (
        "xml",
        "RUTs válidos:\n<root>\n    <rut>12345678-5</rut>\n"
        "    <rut>98765432-5</rut>\n    <rut>1-9</rut>\n</root>\n\n"
    ),
    (
        "json",
        "RUTs válidos:\n[{'rut': '12345678-5'}, {'rut': '98765432-5'}, "
        "{'rut': '1-9'}]\n\n"
    ),
]

datos_test_formatear_lista_ruts = [
    (
        ["12345678-5", "98765432-5", "1-9"],
        None,
        "RUTs válidos:\n12345678-5\n98765432-5\n1-9\n\n"
    ),
    (
        ["12345678-5", "98765432-1", "123456789", "1-9"],
        None,
        "RUTs válidos:\n12345678-5\n1-9\n\nRUTs inválidos:\n"
        "98765432-1 - El dígito verificador '1' no coincide con "
        "el dígito verificador calculado '5'.\n"
        "123456789 - El rut '123456789' es inválido ya que contiene "
        "más de 8 dígitos.\n"
    ),
]


# pylint: disable=R0903
class TestsRutDigitoVerificador:
    """
    Suite de pruebas para la clase RutDigitoVerificador.
    """

    @pytest.mark.parametrize("base, esperado", cadenas_test_digito_verificador)
    def test_calcular_digito_verificador(self, base, esperado):
        """
        Prueba el cálculo del dígito verificador para valores de base válidos e inválidos.
        """
        if isinstance(esperado, type) and issubclass(esperado, Exception):
            with pytest.raises(esperado):
                RutDigitoVerificador(base)
        else:
            rut = RutDigitoVerificador(base)
            assert str(rut) == esperado


class TestsRutBase:
    """
    Suite de pruebas para la clase RutBase.
    """

    @pytest.mark.parametrize("base, esperado", cadenas_base_validas)
    def test_cadenas_base_validas(self, base, esperado):
        """
        Prueba que las cadenas base válidas se normalizan correctamente.
        """
        rut = RutBase(base)
        assert rut.base == esperado
        assert str(rut) == esperado

    @pytest.mark.parametrize("base", cadenas_base_invalidas)
    def test_cadenas_base_invalidas(self, base):
        """
        Prueba que las cadenas base inválidas generen un RutInvalidoError.
        """
        with pytest.raises(RutInvalidoError):
            RutBase(base)


class TestsRut:
    """
    Suite de pruebas para la clase Rut.
    """

    @pytest.fixture(scope="class")
    def rut_valido(self):
        """Fixture para crear una instancia de Rut válida."""
        return Rut("12345678-5")

    @pytest.mark.parametrize("cadena_rut", cadenas_rut_validas)
    def test_cadenas_rut_validas(self, cadena_rut):
        """
        Prueba que las cadenas RUT válidas se manejen correctamente.
        """
        rut = Rut(cadena_rut)
        assert rut.rut_string == cadena_rut.strip()

    @pytest.mark.parametrize("cadena_rut", cadenas_rut_invalidas)
    def test_cadenas_rut_invalidas(self, cadena_rut):
        """
        Prueba que las cadenas RUT inválidas generen un RutInvalidoError.
        """
        with pytest.raises(RutInvalidoError):
            Rut(cadena_rut)

    @pytest.mark.parametrize("formato, esperado", datos_test_formato)
    def test_formatear_lista_ruts(self, formato, esperado):
        """
        Prueba que el método formatear_lista_ruts formatee correctamente una lista de cadenas RUT.
        """
        ruts = ["12345678-5", "98765432-5", "1-9"]
        resultado = Rut.formatear_lista_ruts(ruts, formato=formato)
        assert resultado == esperado

    # pylint: disable=C0301
    @pytest.mark.parametrize("ruts, formato, esperado", datos_test_formatear_lista_ruts)
    def test_formatear_lista_ruts_sin_formato(self, ruts, formato, esperado):
        """
        Prueba que el método formatear_lista_ruts formatee correctamente una lista de RUTs sin un formato específico.
        """
        resultado = Rut.formatear_lista_ruts(ruts, formato=formato)
        assert resultado == esperado

    # pylint: disable=C0301
    def test_formatear_rut_con_separador_miles(self, rut_valido):
        """
        Prueba que el método formatear formatee correctamente una cadena RUT con separador_miles=True.
        """
        rut_formateado = rut_valido.formatear(separador_miles=True)
        assert rut_formateado == "12.345.678-5"

    def test_formatear_rut_con_mayusculas(self, rut_valido):
        """
        Prueba que el método formatear formatee correctamente una cadena RUT con mayusculas=False.
        """
        rut_formateado = rut_valido.formatear(mayusculas=False)
        assert rut_formateado == "12345678-5"

    # pylint: disable=C0301
    def test_formatear_rut_con_separador_miles_y_mayusculas(self, rut_valido):
        """
        Prueba que el método formatear formatee correctamente una cadena RUT con separador_miles=True y mayusculas=True.
        """
        rut_formateado = rut_valido.formatear(separador_miles=True, mayusculas=True)
        assert rut_formateado == "12.345.678-5"