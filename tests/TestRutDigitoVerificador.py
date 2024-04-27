"""Test suite for the RutDigitoVerificador class.

This file contains tests for the RutDigitoVerificador class from the chile_rut package.
The tests focus on validating the behavior of the digit verifier calculation for a valid
RUT base, as well as ensuring that invalid base strings raise appropriate exceptions.

The tests cover various scenarios, including:
- Calculating the correct digit verifier for different valid RUT bases.
- Raising a RutInvalidoError for invalid RUT base strings, such as non-digit characters.
- Testing RUT bases with different lengths and compositions to verify the correct handling.

These tests help ensure the accuracy and robustness of the RutDigitoVerificador class.
"""

from chile_rut.main import RutDigitoVerificador
from chile_rut.exceptions import RutInvalidoError
import pytest

class TestRutDigitoVerificador:
    """Test suite for RutDigitoVerificador class."""

    def test_calculate_digit_verifier_valid_base(self):
        """Test RutDigitoVerificador with a valid base.

        Verifies the correct digit verifier is calculated for valid base "12345678".
        """
        base = "12345678"
        expected = "5"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_raise_rut_invalido_error_non_digit_base(self):
        """Test RutDigitoVerificador with non-digit base.

        Confirms that non-digit base "1234567a" raises RutInvalidoError.
        """
        base = "1234567a"
        with pytest.raises(RutInvalidoError):
            RutDigitoVerificador(base)

    def test_calculate_digit_verifier_valid_base(self):
        """Test RutDigitoVerificador with base "1".

        Confirms digit verifier "9" is calculated for base "1".
        """
        base = "1"
        expected = "9"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_valid_base(self):
        """Test RutDigitoVerificador with base "2".

        Confirms digit verifier "7" is calculated for base "2".
        """
        base = "2"
        expected = "7"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_valid_base_with_less_than_8_digits(self):
        """Test RutDigitoVerificador with base "1234567".

        Verifies digit verifier "4" is calculated for base "1234567".
        """
        base = "1234567"
        expected = "4"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_valid_base(self):
        """Test RutDigitoVerificador with base "4".

        Confirms digit verifier "3" is calculated for base "4".
        """
        base = "4"
        expected = "3"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_valid_base(self):
        """Test RutDigitoVerificador with base "6".

        Checks that the digit verifier "k" is calculated for base "6".
        """
        base = "6"
        expected = "k"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_valid_base(self):
        """Test RutDigitoVerificador with base "5".

        Verifies digit verifier "1" is calculated for base "5".
        """
        base = "5"
        expected = "1"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_valid_base(self):
        """Test RutDigitoVerificador with base "7".

        Confirms digit verifier "8" is calculated for base "7".
        """
        base = "7"
        expected = "8"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_valid_base(self):
        """Test RutDigitoVerificador with base "8".

        Verifies digit verifier "6" is calculated for base "8".
        """
        base = "8"
        expected = "6"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_valid_base(self):
        """Test RutDigitoVerificador with base "9".

        Confirms digit verifier "4" is calculated for base "9".
        """
        base = "9"
        expected = "4"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_invalid_base(self):
        """Test RutDigitoVerificador with invalid base.

        Ensures RutInvalidoError is raised for invalid base "1234567890".
        """
        base = "1234567890"
        with pytest.raises(RutInvalidoError):
            RutDigitoVerificador(base)

    def test_raise_rut_invalido_error_with_more_than_8_digits(self):
        """Test RutDigitoVerificador with base "123456789".

        Confirms RutInvalidoError is raised for base with more than 8 digits.
        """
        base = "123456789"
        with pytest.raises(RutInvalidoError):
            RutDigitoVerificador(base)
