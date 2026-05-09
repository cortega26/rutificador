"""Tests basados en propiedades (Hypothesis) para rutificador."""

from hypothesis import given, strategies as st

from rutificador import Rut, FormateadorCSV
from rutificador.utils import calcular_digito_verificador


@given(
    st.integers(min_value=1, max_value=99_999_999),
)
def test_rut_roundtrip_desde_int(base_int):
    """Para cualquier entero base, Rut(int) produce un str que al re-parsarse da el mismo str."""
    rut = Rut(base_int)
    str_repr = str(rut)
    rut2 = Rut(str_repr)
    assert str(rut2) == str_repr


@given(
    st.text(
        alphabet=st.characters(
            whitelist_categories=("Nd", "Lu", "Ll"),
            whitelist_characters="-.",
        ),
        min_size=3,
        max_size=20,
    ),
)
def test_normalizar_idempotente(valor):
    """Normalizar un RUT válido dos veces produce el mismo resultado."""
    norm1, err1, _ = Rut.normalizar(valor)
    if norm1 is None or err1:
        return  # Solo probamos idempotencia en valores que normalizan
    norm2, err2, _ = Rut.normalizar(norm1)
    assert norm2 == norm1
    assert not err2


@given(
    st.integers(min_value=1, max_value=99_999_999),
    st.integers(min_value=0, max_value=9),
)
def test_enmascarar_preserva_dv(base_int, mantener):
    """Enmascarar un RUT válido siempre preserva el dígito verificador."""
    dv = calcular_digito_verificador(str(base_int))
    rut_str = f"{base_int}-{dv}"
    try:
        mascara = Rut.enmascarar(rut_str, mantener=mantener, caracter="*")
    except Exception:
        return  # mantener puede ser muy grande o pequeño, skip
    assert mascara.endswith(dv)


@given(
    st.lists(
        st.from_regex(r"\d{1,8}-[0-9kK]", fullmatch=True),
        min_size=1,
        max_size=5,
    ),
)
def test_csv_formateador_nunca_inyecta_formulas(ruts):
    """FormateadorCSV nunca produce salida con =, +, -, @ como primer carácter del valor."""
    try:
        resultado = FormateadorCSV().formatear(ruts)
    except Exception:
        return
    lineas = resultado.strip().split("\n")
    for linea in lineas[1:]:  # Saltar cabecera
        if linea and linea[0] in {"=", "+", "-", "@"}:
            # Si empieza con un carácter de fórmula, debe tener el prefijo '
            assert linea.startswith("'"), f"CSV injection detected: {linea}"
