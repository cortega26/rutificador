"""Test suite for RutBase class.

This module contains tests for the RutBase class from the chile_rut package.
The tests cover a variety of scenarios including valid and invalid base strings,
as well as various input conditions such as leading zeros, thousands separators,
and non-digit characters. The tests use parametrization to efficiently test
multiple input scenarios for the RutBase class.
"""

import pytest
from chile_rut.main import RutBase
from chile_rut.exceptions import RutInvalidoError

class TestRutBase:

    # Creating a new instance of RutBase with a valid base string should set the 'base' attribute to the normalized base string.
    def test_valid_base_string(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    # Creating a new instance of RutBase with a base string containing more than the maximum allowed number of digits should raise a RutInvalidoError.
    def test_invalid_base_string(self):
        base = "123.456.7890"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    # Creating a new instance of RutBase with a valid base string should set the 'rut_original' attribute to the original base string.
    def test_valid_base_string(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.rut_original == base

    # Calling str() on a RutBase instance should return the normalized base string.
    def test_str_method_returns_normalized_base_string(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert str(rut) == "12345678"

    # Creating a new instance of RutBase with a base string containing leading zeros should normalize the base string correctly.
    def test_normalize_base_string(self):
        base = "000.123.456"
        rut = RutBase(base)
        assert rut.base == "123456"

    # Creating a new instance of RutBase with a base string containing dots as thousands separators should normalize the base string correctly.
    def test_normalize_base_string(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    # Creating a new instance of RutBase with a base string containing both dots and leading zeros should normalize the base string correctly.
    def test_normalize_base_string(self):
        base = "00.123.456"
        rut = RutBase(base)
        assert rut.base == "123456"

    # Creating a new instance of RutBase with a base string containing the maximum allowed number of digits should not raise an exception.
    def test_valid_base_string(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    # Creating a new instance of RutBase with a base string containing only digits should normalize the base string correctly.
    def test_normalize_base_string(self):
        base = "12.345.678"
        rut = RutBase(base)
        assert rut.base == "12345678"

    # Creating a new instance of RutBase with a base string containing non-digit characters other than dots should raise a RutInvalidoError.
    def test_invalid_base_string(self):
        base = "12.3a5.678"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    # Creating a new instance of RutBase with a base string containing a mix of digit and non-digit characters should raise a RutInvalidoError.
    def test_invalid_base_string(self):
        base = "12.3a4.678"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    # Creating a new instance of RutBase with an empty string should raise a RutInvalidoError.
    def test_empty_base_string(self):
        with pytest.raises(RutInvalidoError):
            RutBase("")

    # Creating a new instance of RutBase with a base string consisting only of dots should raise a RutInvalidoError.
    def test_invalid_base_string(self):
        base = "........"
        with pytest.raises(RutInvalidoError):
            RutBase(base)

    # Creating a new instance of RutBase with a base string consisting only of leading zeros should normalize the base string correctly.
    def test_normalize_base_string(self):
        base = "000.123.456"
        rut = RutBase(base)
        assert rut.base == "123456"

    # Creating a new instance of RutBase with a base string containing a single digit should normalize the base string correctly.
    def test_normalize_base_string(self):
        base = "1"
        rut = RutBase(base)
        assert rut.base == "1"

    # Creating a new instance of RutBase with a base string containing two digits should normalize the base string correctly.
    def test_normalize_base_string_with_two_digits(self):
        base = "12"
        rut = RutBase(base)
        assert rut.base == "12"

    # Creating a new instance of RutBase with a base string containing three digits should normalize the base string correctly.
    def test_normalize_base_string(self):
        base = "123"
        rut = RutBase(base)
        assert rut.base == "123"

    # Creating a new instance of RutBase with a base string containing five digits should normalize the base string correctly.
    def test_normalize_base_string(self):
        base = "12.345"
        rut = RutBase(base)
        assert rut.base == "12345"

    # Creating a new instance of RutBase with a base string containing four digits should normalize the base string correctly.
    def test_normalize_base_string(self):
        base = "1.234"
        rut = RutBase(base)
        assert rut.base == "1234"