"""Test suite for the RutDigitoVerificador class."""

import pytest
from chile_rut.main import RutDigitoVerificador, RutInvalidoError


class TestRutDigitoVerificador:
    """Test suite for RutDigitoVerificador class."""

    def test_calculate_digit_verifier_for_base_12345678(self):
        """Calculates digit verifier for valid base."""
        base = "12345678"
        expected = "5"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_raise_error_for_non_digit_base(self):
        """Non-digit base raises RutInvalidoError."""
        base = "1234567a"
        with pytest.raises(RutInvalidoError):
            RutDigitoVerificador(base)

    def test_calculate_digit_verifier_for_base_1(self):
        """Calculates digit verifier for base "1"."""
        base = "1"
        expected = "9"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_for_base_2(self):
        """Calculates digit verifier for base "2"."""
        base = "2"
        expected = "7"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_for_base_1234567(self):
        """Calculates digit verifier for base "1234567"."""
        base = "1234567"
        expected = "4"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_for_base_4(self):
        """Calculates digit verifier for base "4"."""
        base = "4"
        expected = "3"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_for_base_6(self):
        """Calculates digit verifier for base "6"."""
        base = "6"
        expected = "k"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_for_base_5(self):
        """Calculates digit verifier for base "5"."""
        base = "5"
        expected = "1"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_for_base_7(self):
        """Calculates digit verifier for base "7"."""
        base = "7"
        expected = "8"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_for_base_8(self):
        """Calculates digit verifier for base "8"."""
        base = "8"
        expected = "6"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_calculate_digit_verifier_for_base_9(self):
        """Calculates digit verifier for base "9"."""
        base = "9"
        expected = "4"
        rut = RutDigitoVerificador(base)
        assert str(rut) == expected

    def test_invalid_base_raises_error(self):
        """Invalid base raises RutInvalidoError."""
        base = "1234567890"
        with pytest.raises(RutInvalidoError):
            RutDigitoVerificador(base)

    def test_base_with_more_than_8_digits_raises_error(self):
        """Base with more than 8 digits raises RutInvalidoError."""
        base = "123456789"
        with pytest.raises(RutInvalidoError):
            RutDigitoVerificador(base)