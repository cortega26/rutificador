"""Test suite for RutBase class."""

import pytest
from chile_rut.main import RutBase, RutInvalidoError


class TestRutBase:

    """Valid base string sets 'base' attribute."""
    def test_valid_base_string_sets_base_attribute(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    """Base with too many digits raises RutInvalidoError."""
    def test_base_with_too_many_digits_raises_error(self):
        base = "123.456.7890"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    """Valid base sets 'rut_original' attribute."""
    def test_valid_base_string_sets_rut_original_attribute(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.rut_original == base

    """str() returns normalized base string."""
    def test_str_method_returns_normalized_base(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert str(rut) == "12345678"

    """Normalizes base with leading zeros."""
    def test_normalize_base_with_leading_zeros(self):
        base = "000.123.456"
        rut = RutBase(base)
        assert rut.base == "123456"

    """Normalizes base with dots as separators."""
    def test_normalize_base_with_dots_as_separators(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    """Normalizes base with dots and leading zeros."""
    def test_normalize_base_with_dots_and_leading_zeros(self):
        base = "00.123.456"
        rut = RutBase(base)
        assert rut.base == "123456"

    """Base with max digits is valid."""
    def test_base_with_max_digits_is_valid(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    """Normalizes base with only digits."""
    def test_normalize_base_with_only_digits(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    """Non-digit chars other than dots raise RutInvalidoError."""
    def test_base_with_non_digit_chars_raises_error(self):
        base = "12.3a5.678"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    """Mix of digits and non-digits raises RutInvalidoError."""
    def test_base_with_mixed_chars_raises_error(self):
        base = "12.3a4.678"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    """Empty string raises RutInvalidoError."""
    def test_empty_base_string_raises_error(self):
        with pytest.raises(RutInvalidoError):
            RutBase("")

    """Base with only dots raises RutInvalidoError."""
    def test_base_with_only_dots_raises_error(self):
        base = "........"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    """Normalizes base with leading zeros and dots."""
    def test_normalize_base_with_leading_zeros_and_dots(self):
        base = "000.123.456"
        rut = RutBase(base)
        assert rut.base == "123456"

    """Normalizes single digit base."""
    def test_normalize_single_digit_base(self):
        base = "1"
        rut = RutBase(base)
        assert rut.base == "1"

    """Normalizes two-digit base."""
    def test_normalize_two_digit_base(self):
        base = "12"
        rut = RutBase(base)
        assert rut.base == "12"

    """Normalizes three-digit base."""
    def test_normalize_three_digit_base(self):
        base = "123"
        rut = RutBase(base)
        assert rut.base == "123"

    """Normalizes four-digit base."""
    def test_normalize_four_digit_base(self):
        base = "1.234"
        rut = RutBase(base)
        assert rut.base == "1234"

    """Normalizes five-digit base."""
    def test_normalize_five_digit_base(self):
        base = "12.345"
        rut = RutBase(base)
        assert rut.base == "12345"

    """Normalizes six-digit base."""
    def test_normalize_six_digit_base(self):
        base = "123.456"
        rut = RutBase(base)
        assert rut.base == "123456"

    """Normalizes seven-digit base."""
    def test_normalize_seven_digit_base(self):
        base = "1.234.567"
        rut = RutBase(base)
        assert rut.base == "1234567"

    """Normalizes eight-digit base."""
    def test_normalize_eight_digit_base(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    def test_valid_base_string(self):
        """Test RutBase instance with a valid base string.

        Checks if RutBase instance correctly normalizes valid base strings
        by removing dots.
        """
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    def test_invalid_base_string(self):
        """Test RutBase instance with an invalid base string.

        Verifies that an invalid base string raises a RutInvalidoError.
        """
        base = "123.456.7890"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    def test_str_method_returns_normalized_base_string(self):
        """Test str() method of RutBase instance.

        Confirms that str() returns the normalized base string.
        """
        base = "12.345.678"
        rut = RutBase(base)
        assert str(rut) == "12345678"

    def test_remove_leading_zeros(self):
        """Test RutBase instance with base string containing leading zeros.

        Ensures leading zeros are removed from the normalized base string.
        """
        base = "000.123.456"
        rut = RutBase(base)
        assert rut.base == "123456"

    def test_remove_dots_from_base_string(self):
        """Test RutBase instance with base string containing dots.

        Confirms dots are removed from the normalized base string.
        """
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    def test_invalid_base_string_non_digits(self):
        """Test RutBase instance with invalid base string containing non-digit characters.

        Ensures invalid base string with non-digit characters raises RutInvalidoError.
        """
        base = "12.3a5.678"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    def test_invalid_base_string_with_only_dots(self):
        """Test RutBase instance with base string containing only dots.

        Verifies RutInvalidoError is raised for base string with only dots.
        """
        base = "........"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    def test_invalid_base_string_with_dot_followed_by_less_than_3_digits(self):
        """Test RutBase instance with base string containing dot followed by less than 3 digits.

        Ensures RutInvalidoError is raised for base string with dot followed by less than 3 digits.
        """
        base = "12.34"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    def test_invalid_base_string_with_dot_followed_by_more_than_3_digits(self):
        """Test RutBase instance with base string containing dot followed by more than 3 digits.

        Confirms RutInvalidoError is raised for base string with dot followed by more than 3 digits.
        """
        base = "12.345.6789"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    def test_valid_base_string_with_dot_followed_by_3_digits(self):
        """Test RutBase instance with base string containing dot followed by exactly 3 digits.

        Checks if RutBase instance normalizes base strings with dot followed by exactly 3 digits.
        """
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    def test_empty_base_string(self):
        """Test RutBase instance with empty base string.

        Confirms RutInvalidoError is raised for empty base string.
        """
        with pytest.raises(RutInvalidoError):
            RutBase("")