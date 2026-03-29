import pytest
from pydantic import BaseModel, ValidationError
from rutificador.contrib.pydantic.rutstr import RutStr


class MiModelo(BaseModel):
    """Modelo de prueba para RutStr."""

    rut: RutStr


def test_pydantic_rutstr_valido():
    m = MiModelo(rut="12.345.678-5")
    assert m.rut == "12345678-5"
    assert isinstance(m.rut, str)


def test_pydantic_rutstr_sin_puntos():
    m = MiModelo(rut="12345678-5")
    assert m.rut == "12345678-5"


def test_pydantic_rutstr_invalido():
    with pytest.raises(ValidationError) as excinfo:
        MiModelo(rut="12345678-k")
    errors = excinfo.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "DV_DISCORDANTE"
    # Verificar que el hint incluye la sugerencia
    assert "¿Quisiste decir 12345678-5?" in errors[0]["ctx"]["hint"]


def test_pydantic_rutstr_normalizacion_parcial():
    # 12345678 sin guión. Si es posible calcular DV, se autocompleta.
    m = MiModelo(rut="12345678")
    assert m.rut == "12345678-5"


def test_pydantic_rutstr_tipo_erroneo():
    with pytest.raises(ValidationError) as excinfo:
        MiModelo(rut=123)  # Debe ser str conforme al contrato
    errors = excinfo.value.errors()
    assert errors[0]["type"] == "ERROR_TIPO"


def test_pydantic_json_schema():
    schema = MiModelo.model_json_schema()
    prop = schema["properties"]["rut"]
    assert prop["title"] == "Identificador de RUT Chileno"
    assert "description" in prop
    assert "pattern" in prop
    assert "examples" in prop
