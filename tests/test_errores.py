"""Tests para la infraestructura de i18n de errores."""

from rutificador.errores import crear_detalle_error, CATALOGO_ERRORES


class TestCrearDetalleErrorI18n:
    def test_idioma_es_por_defecto(self):
        detalle = crear_detalle_error("ERROR_TIPO")
        assert detalle.mensaje == "El RUT debe ser cadena o entero"
        assert detalle.hint == "Convierta el valor a str o int"

    def test_idioma_en_explicito(self):
        detalle = crear_detalle_error("ERROR_TIPO", idioma="en")
        assert detalle.mensaje == "RUT must be a string or integer"
        assert detalle.hint == "Convert the value to str or int"

    def test_fallback_a_es_cuando_en_no_tiene_entrada(self):
        detalle = crear_detalle_error("FORMATO_PUNTOS", idioma="en")
        assert "separadores" in detalle.mensaje.lower()

    def test_override_mensaje_ignora_catalogo(self):
        detalle = crear_detalle_error(
            "ERROR_TIPO", mensaje="Mensaje personalizado", idioma="en"
        )
        assert detalle.mensaje == "Mensaje personalizado"

    def test_catalogo_es_accesible_retrocompatibilidad(self):
        assert (
            CATALOGO_ERRORES["ERROR_TIPO"]["mensaje"]
            == "El RUT debe ser cadena o entero"
        )
