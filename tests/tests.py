"""
Comprehensive test suite for the RutDigitoVerificador, RutBase, and Rut classes.

This file contains a comprehensive set of tests for the RutDigitoVerificador, RutBase,
and Rut classes, which are part of the chile_rut library. The tests cover various scenarios,
including valid and invalid inputs, edge cases, and expected outputs. The tests are designed
to ensure the robustness and correctness of the classes and their methods.
"""

import pytest
from rutificador.main import Rut, RutDigitoVerificador, RutBase, RutInvalidoError


# pylint: disable=R0904
class TestRutDigitoVerificador:
    """
    Test suite for the RutDigitoVerificador class.
    This class contains tests to verify the correct calculation of the digit verifier for
    various base values, as well as tests for handling invalid inputs.
    """

    def test_calculate_digit_verifier_for_valid_base(self):
        """
        Test that the digit verifier is correctly calculated for a valid base value.
        """
        base = "12345678"
        expected = "5"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_raise_error_for_non_digit_base(self):
        """
        Test that a RutInvalidoError is raised when the base contains non-digit characters.
        """
        base = "1234567a"
        with pytest.raises(RutInvalidoError):
            RutDigitoVerificador(base)

    def test_calculate_digit_verifier_for_single_digit_base(self):
        """
        Test that the digit verifier is correctly calculated for a single-digit base value.
        """
        base = "1"
        expected = "9"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_invalid_base_raises_error(self):
        """
        Test that a RutInvalidoError is raised when the base value is invalid (eg. +8 digits)
        """
        base = "123456789"
        with pytest.raises(RutInvalidoError):
            RutDigitoVerificador(base)


class TestRutBase:
    """
    Test suite for the RutBase class.

    This class contains tests to verify the normalization of base strings, handling of
    valid and invalid inputs, and expected outputs.
    """

    def test_valid_base_string_sets_base_attribute(self):
        """
        Test that a valid base string correctly sets the 'base' attribute.
        """
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    def test_base_with_too_many_digits_raises_error(self):
        """
        Test that a RutInvalidoError is raised when the base string contains more than 8 digits.
        """
        base = "123.456.7890"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    def test_valid_base_string_sets_rut_original_attribute(self):
        """
        Test that a valid base string correctly sets the 'rut_original' attribute.
        """
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.rut_original == base

    def test_str_method_returns_normalized_base(self):
        """
        Test that the str() method returns the normalized base string.
        """
        base = "12.345.678"
        rut = RutBase(base)
        assert str(rut) == "12345678"

    def test_normalize_base_with_leading_zeros(self):
        """
        Test that the base string is correctly normalized when it contains leading zeros.
        """
        base = "000.123.456"
        rut = RutBase(base)
        assert rut.base == "123456"

    def test_normalize_base_with_dots_as_separators(self):
        """
        Test that the base string is correctly normalized when it contains dots as separators.
        """
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    def test_normalize_base_with_dots_and_leading_zeros(self):
        """
        Test that the base string is correctly normalized when it contains dots as separators
        and leading zeros.
        """
        base = "00.123.456"
        rut = RutBase(base)
        assert rut.base == "123456"

    def test_base_with_max_digits_is_valid(self):
        """
        Test that a base string with the maximum allowed number of digits (8) is valid.
        """
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    def test_normalize_base_with_only_digits(self):
        """
        Test that the base string is correctly normalized when it contains only digits.
        """
        base = "12345678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    def test_base_with_non_digit_chars_raises_error(self):
        """
        Test that a RutInvalidoError is raised when the base string contains non-digit
        characters other than dots.
        """
        base = "12.3a5.678"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    def test_base_with_mixed_chars_raises_error(self):
        """
        Test that a RutInvalidoError is raised when the base string contains a mix of
        digits and non-digit characters.
        """
        base = "12.3a4.678"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    def test_empty_base_string_raises_error(self):
        """
        Test that a RutInvalidoError is raised when the base string is empty.
        """
        with pytest.raises(RutInvalidoError):
            RutBase("")

    def test_base_with_only_dots_raises_error(self):
        """
        Test that a RutInvalidoError is raised when the base string contains only dots.
        """
        base = "........"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    def test_normalize_base_with_leading_zeros_and_dots(self):
        """
        Test that the base string is correctly normalized when it contains leading zeros
        and dots.
        """
        base = "000.123.456"
        rut = RutBase(base)
        assert rut.base == "123456"

    def test_normalize_single_digit_base(self):
        """
        Test that a single-digit base string is correctly normalized.
        """
        base = "1"
        rut = RutBase(base)
        assert rut.base == "1"

    def test_normalize_two_digit_base(self):
        """
        Test that a two-digit base string is correctly normalized.
        """
        base = "12"
        rut = RutBase(base)
        assert rut.base == "12"

    def test_normalize_three_digit_base(self):
        """
        Test that a three-digit base string is correctly normalized.
        """
        base = "123"
        rut = RutBase(base)
        assert rut.base == "123"

    def test_normalize_four_digit_base(self):
        """
        Test that a four-digit base string is correctly normalized.
        """
        base = "1.234"
        rut = RutBase(base)
        assert rut.base == "1234"

    def test_normalize_five_digit_base(self):
        """
        Test that a five-digit base string is correctly normalized.
        """
        base = "12.345"
        rut = RutBase(base)
        assert rut.base == "12345"

    def test_normalize_six_digit_base(self):
        """
        Test that a six-digit base string is correctly normalized.
        """
        base = "123.456"
        rut = RutBase(base)
        assert rut.base == "123456"

    def test_normalize_seven_digit_base(self):
        """
        Test that a seven-digit base string is correctly normalized.
        """
        base = "1.234.567"
        rut = RutBase(base)
        assert rut.base == "1234567"

    def test_normalize_eight_digit_base(self):
        """
        Test that an eight-digit base string is correctly normalized.
        """
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"


class TestRut:
    """
    Test suite for the Rut class.

    This class contains tests to verify the correct creation of Rut objects, validation
    of RUT strings, formatting of RUTs, and handling of invalid inputs.
    """

    def test_valid_rut_string(self):
        """
        Test that a Rut object is correctly created with a valid RUT string.
        """
        rut = Rut("12345678-5")
        assert rut.rut_string == "12345678-5"
        assert rut.base.base == "12345678"
        assert rut.digito_verificador.digito_verificador == "5"

    def test_format_rut_with_separador_miles(self):
        """
        Test that the formatear() method correctly formats a RUT string with
        separador_miles=True.
        """
        rut = Rut("12345678-5")
        formatted_rut = rut.formatear(separador_miles=True)
        assert formatted_rut == "12.345.678-5"

    def test_format_rut_with_mayusculas(self):
        """
        Test that the formatear() method correctly formats a RUT string with mayusculas=True.
        """
        rut = Rut("999999-k")
        formatted_rut = rut.formatear(mayusculas=True)
        assert formatted_rut == "999999-K"

    def test_format_rut_with_separador_miles_and_mayusculas(self):
        """
        Test that the formatear() method correctly formats a RUT string with
        separador_miles=True and mayusculas=True.
        """
        rut = Rut("999999-k")
        formatted_rut = rut.formatear(separador_miles=True, mayusculas=True)
        assert formatted_rut == "999.999-K"

    def test_validate_list_of_valid_rut_strings(self):
        """
        Test that the validar_lista_ruts() method correctly validates a list of valid
        RUT strings.
        """
        ruts = ["12345678-5", "98765432-5", "11111111-1"]
        result = Rut.validar_lista_ruts(ruts)
        assert result["validos"] == ["12345678-5", "98765432-5", "11111111-1"]

    # pylint: disable=C0301
    def test_validate_list_of_ruts(self):
        """
        Test that the validar_lista_ruts() method correctly validates a list of valid and
        invalid RUT strings.
        """
        ruts = ["12345678-9", "98765432-1", "11111111-1", "22222222-2", "33333333-3"]
        expected_valid = ["11111111-1", "22222222-2", "33333333-3"]
        expected_invalid = [
            (
                "12345678-9",
                "El dígito verificador '9' no coincide con el dígito verificador calculado '5'.",
            ),
            (
                "98765432-1",
                "El dígito verificador '1' no coincide con el dígito verificador calculado '5'.",
            ),
        ]
        result = Rut.validar_lista_ruts(ruts)
        assert result["validos"] == expected_valid
        assert result["invalidos"] == expected_invalid

    def test_invalid_rut_string_with_invalid_format(self):
        """
        Test that a RutInvalidoError is raised when attempting to create a Rut object
        with an invalid RUT string format.
        """
        with pytest.raises(RutInvalidoError):
            Rut("12345.67")

    def test_invalid_rut_string_with_invalid_base(self):
        """
        Test that a RutInvalidoError is raised when attempting to create a Rut object
        with an invalid base value.
        """
        with pytest.raises(RutInvalidoError):
            Rut("123456789")

    # pylint: disable=C0301
    def test_format_rut_csv(self):
        """
        Test that the formatear_lista_ruts() method correctly formats a list of RUT strings
        as a CSV string.
        """
        ruts = ["12345678-5", "98765432-5", "1-9"]
        expected_output = "RUTs válidos:\nrut\n12345678-5\n98765432-5\n1-9\n\n"
        result = Rut.formatear_lista_ruts(ruts, formato="csv")
        assert result == expected_output

    # pylint: disable=C0301
    def test_format_rut_xml(self):
        """
        Test that the formatear_lista_ruts() method correctly formats a list of RUT strings
        as an XML string.
        """
        ruts = ["12345678-5", "98765432-5", "1-9"]
        expected_output = "RUTs válidos:\n<root>\n    <rut>12345678-5</rut>\n    <rut>98765432-5</rut>\n    <rut>1-9</rut>\n</root>\n\n"
        result = Rut.formatear_lista_ruts(ruts, formato="xml")
        assert result == expected_output

    # pylint: disable=C0301
    def test_format_rut_json(self):
        """
        Test that the formatear_lista_ruts() method correctly formats a list of RUT strings
        as a JSON string.
        """
        ruts = ["12345678-5", "98765432-5", "11111111-1"]
        expected_output = 'RUTs válidos:\n[{"rut": "12345678-5"}, {"rut": "98765432-5"}, {"rut": "11111111-1"}]\n\n'
        result = Rut.formatear_lista_ruts(ruts, formato="json")
        assert result == expected_output.replace('"', "'")
