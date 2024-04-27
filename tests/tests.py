import pytest
from chile_rut.exceptions import RutInvalidoError, RutDigitoVerificadorInvalidoError
from chile_rut.main import Rut, RutBase, RutDigitoVerificador

# Tests for the RutBase class.
class TestRutBase:
    """Tests for the RutBase class."""

    # Test cases for valid base strings
    valid_base_strings = [
        ("12345678", "12345678"),  # string
        ("int(12345)", "12345"),  # integer
        ("12.345", "12345"),  # one dot followed by 3 digits
        ("12.345.678", "12345678"),  # two dots followed by 3 digits each
        ("00123456", "123456"),  # leading zeros
        (" 123 ", "123"),  # leading and trailing whitespace
    ]

    @pytest.mark.parametrize("base_string, expected_base", valid_base_strings)
    def test_valid_base_string(self, base_string, expected_base):
        """Test that valid base strings are properly handled."""
        rut = RutBase(base_string)
        assert rut.base == expected_base

    # Test cases for invalid base strings
    invalid_base_strings = [
        "12.3a5.678",  # non-digit characters
        "123.456.789",  # more than 8 digits
        "123.456.",  # dot at the end
        ".123.456",  # dot at the beginning
        "12.34",  # dot followed by less than 3 digits
        "345.6789",  # dot followed by more than 3 digits
        "12..345.678",  # multiple dots in a row
        "0",  # single digit
        ("12345678-", "12345678"),  # dash
    ]

    @pytest.mark.parametrize("base_string", invalid_base_strings)
    def test_invalid_base_string(self, base_string):
        """Test that invalid base strings raise an exception."""
        with pytest.raises(RutInvalidoError):
            RutBase(base_string)

    # Test for empty string
    def test_empty_string(self):
        """Test that empty string raises an exception."""
        base = ""
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    # Test for the __str__ method
    def test_str_method_returns_base_attribute_as_string(self):
        """Test the __str__ method of RutBase class."""
        base = "12.345.678"
        rut = RutBase(base)
        assert str(rut) == rut.base


# TestRutDigitoVerificador
class TestRutDigitoVerificador:
    """Tests for the RutDigitoVerificador class."""

    # Test cases for valid RUT bases
    valid_rut_bases = [
        ("12345678", "5"),
        ("11111111", "1"),
        ("00.111.111", "6"),
        ("12.345.678", "9"),
        ("22.222.222", "2"),
        ("1", "9"),
        ("99", "k"),
    ]

    @pytest.mark.parametrize("rut_base, expected_digit", valid_rut_bases)
    def test_valid_rut_base(self, rut_base, expected_digit):
        """Test that valid RUT bases are properly handled."""
        rut = RutDigitoVerificador(rut_base)
        assert str(rut) == expected_digit

    # Test cases for invalid RUT bases
    invalid_rut_bases = ["abc", "123.456.789"]

    @pytest.mark.parametrize("rut_base", invalid_rut_bases)
    def test_invalid_rut_base(self, rut_base):
        """Test that invalid RUT bases raise an exception."""
        with pytest.raises(RutDigitoVerificadorInvalidoError):
            RutDigitoVerificador(rut_base)


# TestRut
class TestRut:
    """Tests for the Rut class."""

    # Test cases for valid RUTs
    valid_ruts = [
        ("12345678-5", "12345678-5", "12345678", "5"),
        (" 12345678-5 ", "12345678-5", "12345678", "5"),
        ("012.345.678-5", "012.345.678-5", "12345678", "5"),
        ("12.345.678-5", "12.345.678-5", "12345678", "5"),
    ]

    @pytest.mark.parametrize(
        "input_rut, expected_rut_string, expected_base, expected_digit", valid_ruts
    )
    def test_initialize_valid_rut(
        self, input_rut, expected_rut_string, expected_base, expected_digit
    ):
        """Test initialization of valid RUTs."""
        rut = Rut(input_rut)
        assert rut.rut_string == expected_rut_string
        assert rut.base.base == expected_base
        assert rut.digito_verificador.digito_verificador == expected_digit

    # Test case for invalid verification digit
    def test_initialize_invalid_verification_digit(self):
        """Test initialization of RUTs with invalid verification digit."""
        with pytest.raises(RutInvalidoError):
            Rut("12345678-0")

    # Test case for RUT with more than 8 digits
    def test_initialize_invalid_rut(self):
        """Test initialization of RUTs with more than 8 digits."""
        with pytest.raises(RutInvalidoError):
            Rut("1234567890-1")

    # Test cases for formatting RUTs
    formatting_cases = [
        (
            ["12345678-5", "11111111-1", "22222222-2"],
            False,
            False,
            "12345678-5,11111111-1,22222222-2",
        ),
        (
            ["12345678-5", "11111111-1", "22222222-2"],
            True,
            False,
            "12.345.678-5,11.111.111-1,22.222.222-2",
        ),
        (
            ["12345678-5", "11111111-1", "22222222-2"],
            False,
            True,
            "12345678-5,11111111-1,22222222-2",
        ),
        (
            ["12345678-5", "11111111-1", "22222222-2"],
            True,
            True,
            "12.345.678-5,11.111.111-1,22.222.222-2",
        ),
    ]

    @pytest.mark.parametrize(
        "ruts, separador_miles, mayusculas, expected_output", formatting_cases
    )
    def test_format_list_ruts(self, ruts, separador_miles, mayusculas, expected_output):
        """Test formatting a list of RUTs."""
        formatted_ruts = Rut.formatear_lista_ruts(
            ruts, separador_miles=separador_miles, mayusculas=mayusculas
        )
        assert formatted_ruts == expected_output

    # Test case for formatting a single RUT
    def test_format_rut(self):
        """Test formatting a single RUT."""
        rut = Rut("12345678-5")
        assert rut.formatear() == "12345678-5"
        assert rut.formatear(separador_miles=True) == "12.345.678-5"
        assert rut.formatear(mayusculas=True) == "12345678-5"
        assert rut.formatear(separador_miles=True, mayusculas=True) == "12.345.678-5"

    # Test case for formatting a RUT with lowercase verification digit
    def test_format_rut_with_thousands_separators_and_lowercase_verification_digit(
        self,
    ):
        """Test formatting a RUT with lowercase verification digit."""
        rut = Rut("12345670-k")
        formatted_rut = rut.formatear(separador_miles=True, mayusculas=False)
        assert formatted_rut == "12.345.670-k"

    # Test case for validating and formatting a list of RUTs
    def test_validate_and_format_ruts(self):
        """Test validating and formatting a list of RUTs."""
        ruts = ["12345678-9", "98765432-1", "11111111-1"]
        expected_result = ["12.345.678-5", "98.765.432-k", "11.111.111-k"]

        result = Rut.validar_lista_ruts(ruts)

        assert result == expected_result
