# pylint: disable=missing-module-docstring

import pytest
from rutificador.main import Rut, RutDigitoVerificador, RutBase, RutInvalidoError

# Test data for RutDigitoVerificador
rut_digito_verificador_test_data = [
    ("12345678", "5"),
    ("1", "9"),
    ("999", "7"),
    ("999999", "k"),
    ("123-", RutInvalidoError),  # Con guión pero sin dígito verificador
    ("1234567-1", RutInvalidoError),  # Con dígito verificador erróneo
]

# Test data for RutBase
valid_base_strings = [
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

invalid_base_strings = [
    "123456789",  # Más de 8 digitos
    "123.4567",  # Más de 3 dígitos luego del punto
    "12.32",  # Menos de 3 dígitos luego del punto
    "12.3a5.678",  # Letras en el RUT base
    "",  # RUT base vacío
    " ",  # RUT base sin número
    "-1",  # RUT base negativo
]

# Test data for Rut
valid_rut_strings = ["12345678-5", "98765432-5", "11111111-1"]
invalid_rut_strings = ["12345678-9", "98765432-1", "12345.67", "123456789"]

# pylint: disable=C0301
# Test data for formatear_lista_ruts
format_test_data = [
    ("csv", "RUTs válidos:\nrut\n12345678-5\n98765432-5\n1-9\n\n"),
    (
        "xml",
        "RUTs válidos:\n<root>\n    <rut>12345678-5</rut>\n    <rut>98765432-5</rut>\n    <rut>1-9</rut>\n</root>\n\n",
    ),
    (
        "json",
        "RUTs válidos:\n[{'rut': '12345678-5'}, {'rut': '98765432-5'}, {'rut': '1-9'}]\n\n",
    ),
]


# pylint: disable=too-few-public-methods
class TestRutDigitoVerificador:
    """
    Test suite for the RutDigitoVerificador class.
    """

    @pytest.mark.parametrize("base, expected", rut_digito_verificador_test_data)
    def test_calculate_digit_verifier(self, base, expected):
        """
        Test the calculation of the digit verifier for valid and invalid base values.
        """
        if isinstance(expected, type) and issubclass(expected, Exception):
            with pytest.raises(expected):
                RutDigitoVerificador(base)
        else:
            rut = RutDigitoVerificador(base)
            assert str(rut) == expected


class TestRutBase:
    """
    Test suite for the RutBase class.
    """

    @pytest.mark.parametrize("base, expected", valid_base_strings)
    def test_valid_base_strings(self, base, expected):
        """
        Test that valid base strings are correctly normalized.
        """
        rut = RutBase(base)
        assert rut.base == expected
        assert str(rut) == expected

    @pytest.mark.parametrize("base", invalid_base_strings)
    def test_invalid_base_strings(self, base):
        """
        Test that invalid base strings raise a RutInvalidoError.
        """
        with pytest.raises(RutInvalidoError):
            RutBase(base)


class TestRut:
    """
    Test suite for the Rut class.
    """

    @pytest.mark.parametrize("rut_string", valid_rut_strings)
    def test_valid_rut_strings(self, rut_string):
        """
        Test that valid RUT strings are correctly handled.
        """
        rut = Rut(rut_string)
        assert rut.rut_string == rut_string

    @pytest.mark.parametrize("rut_string", invalid_rut_strings)
    def test_invalid_rut_strings(self, rut_string):
        """
        Test that invalid RUT strings raise a RutInvalidoError.
        """
        with pytest.raises(RutInvalidoError):
            Rut(rut_string)

    @pytest.mark.parametrize("formato, expected", format_test_data)
    def test_format_rut_lista(self, formato, expected):
        """
        Test that the formatear_lista_ruts() method correctly formats a list of RUT strings.
        """
        ruts = ["12345678-5", "98765432-5", "1-9"]
        result = Rut.formatear_lista_ruts(ruts, formato=formato)
        assert result == expected
