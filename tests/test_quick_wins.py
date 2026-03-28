from rutificador import Rut, ValidadorRut, RigorValidacion


def test_full_width_digits_normalization():
    """Verifica que los dígitos de ancho completo (Unicode) sean aceptados y normalizados."""
    # '１２３４５６７８-５' en caracteres de ancho completo
    rut_unicode = "１２３４５６７８-５"
    rut = Rut(rut_unicode)
    assert str(rut) == "12345678-5"
    assert rut.base.base == "12345678"
    assert rut.digito_verificador == "5"


def test_max_digitos_extension_default():
    """Verifica que el nuevo límite por defecto sea 9 dígitos."""
    # 123.456.789-2 (9 dígitos en la base)
    base_9 = "123456789"
    # El DV para 123456789 es '2'
    rut_str = f"{base_9}-2"
    rut = Rut(rut_str)
    assert str(rut) == rut_str


def test_repr_is_masked():
    """Verifica que repr() no exponga el RUT completo por seguridad."""
    rut = Rut("12345678-5")
    representacion = repr(rut)
    assert "12345678" not in representacion
    assert "Rut(base='********', dv='*')" in representacion


def test_unified_cleaning_excessive_dashes():
    """Verifica que diversos tipos de guiones sean normalizados."""
    # Guion largo (em-dash), guion medio (en-dash), guion bajo
    casos = [
        "12345678_5",
        "12345678–5",
        "12345678—5",
        "12345678−5",
    ]
    for caso in casos:
        rut = Rut(caso)
        assert str(rut) == "12345678-5"


def test_flexible_mode_with_unicode_spaces():
    """Verifica que espacios unicode sean eliminados en modo flexible."""
    # Espacio de no ruptura (u00A0)
    rut_con_espacio = "12\u00a0345\u00a0678-5"
    # Rut() usa ValidadorRut() por defecto el cual usa modo estricto.
    # Vamos a forzar un validador flexible.
    validador = ValidadorRut(modo=RigorValidacion.FLEXIBLE)
    rut = Rut(rut_con_espacio, validador=validador)
    assert str(rut) == "12345678-5"
