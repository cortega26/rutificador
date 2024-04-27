"""Test suite for the RutBase class.

This module contains tests for the RutBase class from the chile_rut package.
The tests cover various input scenarios for the RutBase class, including
valid and invalid base strings, as well as other input conditions such as
leading zeros, dots as separators, and empty strings.
"""

import pytest
from chile_rut.main import RutBase
from chile_rut.exceptions import RutInvalidoError


class TestRutBase:
    """Test suite for the RutBase class."""

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
