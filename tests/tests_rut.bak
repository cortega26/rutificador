from chile_rut.main import Rut
from chile_rut.main import RutInvalidoError


import pytest

class TestRut:

    # create Rut object with valid RUT string
    def test_valid_rut_string(self):
        rut = Rut("12345678-5")
        assert rut.rut_string == "12345678-5"
        assert rut.base.base == "12345678"
        assert rut.digito_verificador.digito_verificador == "5"

    # create Rut object with valid RUT string with leading zeros
    def test_valid_rut_string_with_leading_zeros(self):
        rut = Rut("00001234-3")
        assert rut.rut_string == "00001234-3"
        assert rut.base.base == "1234"
        assert rut.digito_verificador.digito_verificador == "3"

    # format RUT with default options
    def test_format_rut_with_default_options(self):
        rut = Rut("12345678-5")
        formatted_rut = rut.formatear()
        assert formatted_rut == "12345678-5"

    # format RUT with valid RUT
    def test_format_rut_with_valid_rut(self):
        rut = Rut("12345678-5")
        formatted_rut = rut.formatear(separador_miles=True)
        assert formatted_rut == "12.345.678-5"

    # format RUT with mayusculas=True
    def test_format_rut_with_mayusculas_true(self):
        rut = Rut("999999-k")
        formatted_rut = rut.formatear(mayusculas=True)
        assert formatted_rut == "999999-K"

    # format RUT with separador_miles=True and mayusculas=True
    def test_format_rut_with_separador_miles_and_mayusculas(self):
        rut = Rut("999999-k")
        formatted_rut = rut.formatear(separador_miles=True, mayusculas=True)
        assert formatted_rut == "999.999-K"

    # validate a list of valid RUT strings
    def test_validate_list_of_valid_rut_strings(self):
        ruts = ["12345678-5", "98765432-5", "11111111-1"]
        result = Rut.validar_lista_ruts(ruts)
        assert result['validos'] == ["12345678-5", "98765432-5", "11111111-1"]

    # validate a list of valid and invalid RUT strings
    def test_validate_list_of_ruts(self):
        ruts = ["12345678-9", "98765432-1", "11111111-1", "22222222-2", "33333333-3"]
        expected_valid = ['11111111-1', '22222222-2', '33333333-3']
        expected_invalid = [('12345678-9', "El dígito verificador '9' no coincide con el dígito verificador calculado '5'."), ('98765432-1', "El dígito verificador '1' no coincide con el dígito verificador calculado '5'.")]

        result = Rut.validar_lista_ruts(ruts)

        assert result['validos'] == expected_valid
        assert result['invalidos'] == expected_invalid

    # create Rut object with invalid RUT string with invalid format
    def test_invalid_rut_string_with_invalid_format(self):
        with pytest.raises(RutInvalidoError):
            Rut("12345.67")

    # create Rut object with invalid RUT string with invalid base
    def test_invalid_rut_string_with_invalid_base(self):
        with pytest.raises(RutInvalidoError):
            Rut("123456789")

    # format RUT with formato='csv'
    def test_format_rut_csv(self):
        ruts = ["12345678-5", "98765432-5", "1-9"]
        expected_output = "RUTs válidos:\nrut\n12345678-5\n98765432-5\n1-9\n\n"

        result = Rut.formatear_lista_ruts(ruts, formato="csv")

        assert result == expected_output

    # format RUT with formato='xml'
    def test_format_rut_xml(self):
        ruts = ["12345678-5", "98765432-5", "1-9"]
        expected_output = "RUTs válidos:\n<root>\n    <rut>12345678-5</rut>\n    <rut>98765432-5</rut>\n    <rut>1-9</rut>\n</root>\n\n"

        result = Rut.formatear_lista_ruts(ruts, formato="xml")

        assert result == expected_output

    # format RUT with formato='json'
    def test_format_rut_with_json_formato(self):
        ruts = ["12345678-5", "98765432-5", "11111111-1"]
        expected_output = 'RUTs válidos:\n[{"rut": "12345678-5"}, {"rut": "98765432-5"}, {"rut": "11111111-1"}]\n\n'

        result = Rut.formatear_lista_ruts(ruts, formato="json")

        assert result == expected_output.replace('"', "'")