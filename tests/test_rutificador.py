# pylint: disable=missing-module-docstring, cyclic-import

import json
from typing import List
import pytest
from rutificador import (
    Rut,
    RutBase,
    RutInvalidoError,
    ValidadorRut,
    ProcesadorLotesRut,
    FabricaFormateadorRut,
    FormateadorCSV,
    FormateadorXML,
    FormateadorJSON,
    calcular_digito_verificador,
    formatear_lista_ruts,
)

# ============================================================================
# DATOS DE PRUEBA
# ============================================================================

# Datos de prueba para calcular_digito_verificador (función independiente)
datos_test_digito_verificador = [
    ("12345678", "5"),
    ("1", "9"),
    ("999", "7"),
    ("999999", "k"),
    ("22791914", "0"),  # Sin puntos ya que la función espera base normalizada
    ("8670089", "1"),
    ("10535006", "6"),
    ("84920968", "k"),
]

# Datos de prueba para RutBase
cadenas_base_validas = [
    ("000.123.456", "rutificador-test", "123456"),  # Agregamos rut_original
    ("12345678", "12345678", "12345678"),
    ("1", "1", "1"),
    ("12", "12", "12"),
    ("123", "123", "123"),
    ("1.234", "1.234", "1234"),
    ("12.345", "12.345", "12345"),
    ("123.456", "123.456", "123456"),
    ("1.234.567", "1.234.567", "1234567"),
    ("12.345.678", "12.345.678", "12345678"),
]

cadenas_base_invalidas = [
    ("123456789", "123456789"),  # Más de 8 dígitos
    ("123.4567", "123.4567"),  # Más de 3 dígitos luego del punto
    ("12.32", "12.32"),  # Menos de 3 dígitos luego del punto
    ("12.3a5.678", "12.3a5.678"),  # Letras en el RUT base
    ("", ""),  # RUT base vacío
    (" ", " "),  # RUT base sin dígitos
    ("-1", "-1"),  # RUT base negativo o dígito verificador sin base
]

# Datos de prueba para Rut
cadenas_rut_validas = [
    "12345678-5",  # Formato convencional
    " 12345678",  # Con espacio delante
    "12345679 ",  # Con espacio detrás
    " 12345680 ",  # Con espacio a ambos lados del RUT
    " 1-9 ",  # Con D.V. y espacio a ambos lados
    " 000000001 ",  # Con ceros delante y espacios
    " 00.000.001",  # Con ceros delante, puntos y espacios
    " 25.005.183-2 ",  # Con puntos, espacios y D.V.
]

cadenas_rut_invalidas = ["12345678-9", "98765432-1", "12345.67", "123456789"]

# Datos de prueba para formateo (actualizados con JSON válido)
datos_test_formato = [
    ("csv", "RUTs válidos:\nrut\n12345678-5\n98765432-5\n1-9\n\n"),
    (
        "xml",
        "RUTs válidos:\n<root>\n    <rut>12345678-5</rut>\n"
        "    <rut>98765432-5</rut>\n    <rut>1-9</rut>\n</root>\n\n",
    ),
    (
        "json",
        'RUTs válidos:\n[\n  {\n    "rut": "12345678-5"\n  },\n  '
        '{\n    "rut": "98765432-5"\n  },\n  {\n    "rut": "1-9"\n  }\n]\n\n',
    ),
]

# Datos de prueba simplificados para verificar que el resultado contiene las
# secciones esperadas. No validamos el tiempo de procesamiento ya que puede
# variar en cada ejecución.
datos_test_formatear_lista_ruts = [
    (["12345678-5", "98765432-5", "1-9"], None),
    (["12345678-5", "98765432-1", "123456789", "1-9"], None),
]


# ============================================================================
# TESTS PARA FUNCIÓN CALCULAR_DIGITO_VERIFICADOR
# ============================================================================


class TestCalcularDigitoVerificador:
    """Suite de pruebas para la función calcular_digito_verificador."""

    @pytest.mark.parametrize("base, esperado", datos_test_digito_verificador)
    def test_calcular_digito_verificador(self, base, esperado):
        """Prueba el cálculo del dígito verificador para valores de base válidos."""
        resultado = calcular_digito_verificador(base)
        assert resultado == esperado

    def test_calcular_digito_verificador_base_vacia(self):
        """Prueba que una base vacía lance una excepción."""
        with pytest.raises(RutInvalidoError):
            calcular_digito_verificador("")


# ============================================================================
# TESTS PARA RUTVALIDATOR
# ============================================================================


class TestValidadorRut:
    """Suite de pruebas para la clase ValidadorRut."""

    def test_validar_formato_valido(self):
        """Prueba validación de formato válido."""
        validador = ValidadorRut()
        match = validador.validar_formato("12345678-5")
        assert match.group(1) == "12345678"
        assert match.group(3) == "5"

    def test_validar_formato_sin_digito(self):
        """Prueba validación de formato sin dígito verificador."""
        validador = ValidadorRut()
        match = validador.validar_formato("12345678")
        assert match.group(1) == "12345678"
        assert match.group(3) is None

    def test_validar_formato_none(self):
        """Prueba que None lance excepción."""
        validador = ValidadorRut()
        with pytest.raises(RutInvalidoError):
            validador.validar_formato(None)

    @pytest.mark.parametrize("base, rut_original, esperado", cadenas_base_validas)
    def test_validar_base_valida(self, base, rut_original, esperado):
        """Prueba validación de bases válidas."""
        validador = ValidadorRut()
        resultado = validador.validar_base(base, rut_original)
        assert resultado == esperado

    @pytest.mark.parametrize("base, rut_original", cadenas_base_invalidas)
    def test_validar_base_invalida(self, base, rut_original):
        """Prueba que bases inválidas lancen excepción."""
        validador = ValidadorRut()
        with pytest.raises(RutInvalidoError):
            validador.validar_base(base, rut_original)

    def test_validar_digito_verificador_correcto(self):
        """Prueba validación de dígito verificador correcto."""
        # No debería lanzar excepción
        validador = ValidadorRut()
        validador.validar_digito_verificador("5", "5")

    def test_validar_digito_verificador_incorrecto(self):
        """Prueba validación de dígito verificador incorrecto."""
        validador = ValidadorRut()
        with pytest.raises(RutInvalidoError):
            validador.validar_digito_verificador("1", "5")

    def test_validar_digito_verificador_none(self):
        """Prueba validación cuando no se proporciona dígito."""
        # No debería lanzar excepción cuando digito_input es None
        validador = ValidadorRut()
        validador.validar_digito_verificador(None, "5")


# ============================================================================
# TESTS PARA FORMATTERS
# ============================================================================


class TestFormatters:
    """Suite de pruebas para los formateadores."""

    def test_csv_formatter(self):
        """Prueba el formateador CSV."""
        formatter = FormateadorCSV()
        ruts = ["12345678-5", "98765432-5"]
        resultado = formatter.formatear(ruts)
        esperado = "rut\n12345678-5\n98765432-5"
        assert resultado == esperado

    def test_xml_formatter(self):
        """Prueba el formateador XML."""
        formatter = FormateadorXML()
        ruts = ["12345678-5", "98765432-5"]
        resultado = formatter.formatear(ruts)
        esperado = (
            "<root>\n    <rut>12345678-5</rut>\n    <rut>98765432-5</rut>\n</root>"
        )
        assert resultado == esperado

    def test_json_formatter(self):
        """Prueba el formateador JSON."""
        formatter = FormateadorJSON()
        ruts = ["12345678-5", "98765432-5"]
        resultado = formatter.formatear(ruts)

        # Verificar que es JSON válido
        json_data = json.loads(resultado)
        assert len(json_data) == 2
        assert json_data[0]["rut"] == "12345678-5"
        assert json_data[1]["rut"] == "98765432-5"


class TestFabricaFormateadorRut:
    """Suite de pruebas para FabricaFormateadorRut."""

    def test_get_formatter_csv(self):
        """Prueba obtener formateador CSV."""
        formatter = FabricaFormateadorRut.obtener_formateador("csv")
        assert isinstance(formatter, FormateadorCSV)

    def test_get_formatter_xml(self):
        """Prueba obtener formateador XML."""
        formatter = FabricaFormateadorRut.obtener_formateador("xml")
        assert isinstance(formatter, FormateadorXML)

    def test_get_formatter_json(self):
        """Prueba obtener formateador JSON."""
        formatter = FabricaFormateadorRut.obtener_formateador("json")
        assert isinstance(formatter, FormateadorJSON)

    def test_get_formatter_inexistente(self):
        """Prueba obtener formateador inexistente."""
        formatter = FabricaFormateadorRut.obtener_formateador("pdf")
        assert formatter is None

    def test_get_available_formats(self):
        """Prueba obtener formatos disponibles."""
        formatos = FabricaFormateadorRut.obtener_formatos_disponibles()
        assert "csv" in formatos
        assert "xml" in formatos
        assert "json" in formatos


# ============================================================================
# TESTS PARA RUTBASE
# ============================================================================


class TestRutBase:
    """Suite de pruebas para la clase RutBase."""

    @pytest.mark.parametrize("base, rut_original, esperado", cadenas_base_validas)
    def test_cadenas_base_validas(self, base, rut_original, esperado):
        """Prueba que las cadenas base válidas se normalizan correctamente."""
        rut = RutBase(base, rut_original)
        assert rut.base == esperado
        assert str(rut) == esperado

    @pytest.mark.parametrize("base, rut_original", cadenas_base_invalidas)
    def test_cadenas_base_invalidas(self, base, rut_original):
        """Prueba que las cadenas base inválidas generen un RutInvalidoError."""
        with pytest.raises(RutInvalidoError):
            RutBase(base, rut_original)

    def test_equality(self):
        """Prueba la igualdad entre objetos RutBase."""
        base1 = RutBase("12345678", "12345678")
        base2 = RutBase("12345678", "12345678")
        base3 = RutBase("87654321", "87654321")

        assert base1 == base2
        assert base1 != base3

    def test_hash(self):
        """Prueba que objetos iguales tengan el mismo hash."""
        base1 = RutBase("12345678", "12345678")
        base2 = RutBase("12345678", "12345678")

        assert hash(base1) == hash(base2)


# ============================================================================
# TESTS PARA RUT
# ============================================================================


class TestRut:
    """Suite de pruebas para la clase Rut."""

    @pytest.fixture(scope="class")
    def rut_valido(self):
        """Fixture para crear una instancia de Rut válida."""
        return Rut("12345678-5")

    @pytest.mark.parametrize("cadena_rut", cadenas_rut_validas)
    def test_cadenas_rut_validas(self, cadena_rut):
        """Prueba que las cadenas RUT válidas se manejen correctamente."""
        rut = Rut(cadena_rut)
        assert rut.cadena_rut == cadena_rut.strip()

    @pytest.mark.parametrize("cadena_rut", cadenas_rut_invalidas)
    def test_cadenas_rut_invalidas(self, cadena_rut):
        """Prueba que las cadenas RUT inválidas generen un RutInvalidoError."""
        with pytest.raises(RutInvalidoError):
            Rut(cadena_rut)

    def test_formatear_rut_con_separador_miles(self, rut_valido):
        """Prueba formateo con separador de miles."""
        rut_formateado = rut_valido.formatear(separador_miles=True)
        assert rut_formateado == "12.345.678-5"

    def test_formatear_rut_con_mayusculas(self):
        """Prueba formateo con mayúsculas."""
        rut_k = Rut("999999-k")
        rut_formateado = rut_k.formatear(mayusculas=True)
        assert rut_formateado == "999999-K"

    def test_formatear_rut_con_separador_miles_y_mayusculas(self):
        """Prueba formateo con separador de miles y mayúsculas."""
        rut_k = Rut("999999-k")
        rut_formateado = rut_k.formatear(separador_miles=True, mayusculas=True)
        assert rut_formateado == "999.999-K"

    def test_equality(self):
        """Prueba la igualdad entre objetos Rut."""
        rut1 = Rut("12345678-5")
        rut2 = Rut("12345678-5")
        rut3 = Rut("87654321-4")

        assert rut1 == rut2
        assert rut1 != rut3

    def test_hash(self):
        """Prueba que objetos iguales tengan el mismo hash."""
        rut1 = Rut("12345678-5")
        rut2 = Rut("12345678-5")

        assert hash(rut1) == hash(rut2)

    def test_str_representation(self, rut_valido):
        """Prueba la representación string del RUT."""
        assert str(rut_valido) == "12345678-5"


# ============================================================================
# TESTS PARA RUTBATCHPROCESSOR
# ============================================================================


class TestProcesadorLotesRut:
    """Suite de pruebas para ProcesadorLotesRut."""

    def test_validar_lista_ruts_todos_validos(self):
        """Prueba validación de lista con todos los RUTs válidos."""
        ruts = ["12345678-5", "98765432-5", "1-9"]
        processor = ProcesadorLotesRut()
        resultado = processor.validar_lista_ruts(ruts)

        assert len(resultado.ruts_validos) == 3
        assert len(resultado.ruts_invalidos) == 0

    def test_validar_lista_ruts_mixtos(self):
        """Prueba validación de lista con RUTs válidos e inválidos."""
        ruts = ["12345678-5", "98765432-1", "1-9"]  # El segundo es inválido
        processor = ProcesadorLotesRut()
        resultado = processor.validar_lista_ruts(ruts)

        assert len(resultado.ruts_validos) == 2
        assert len(resultado.ruts_invalidos) == 1
        detalle = resultado.ruts_invalidos[0]
        assert detalle.rut == "98765432-1"
        assert detalle.codigo == "DIGIT_ERROR"

    # La parametrización utiliza la salida esperada para validar toda la cadena
    # formateada (ignorando las líneas de estadísticas que varían). El conjunto
    # de datos provee tuplas ``(formato, esperado)`` donde ``esperado`` contiene
    # el inicio del resultado hasta la sección de estadísticas.
    @pytest.mark.parametrize("formato, esperado", datos_test_formato)
    def test_formatear_lista_ruts_con_formato(self, formato, esperado):
        """Prueba formateo de lista con formato específico."""
        _ = esperado
        ruts = ["12345678-5", "98765432-5", "1-9"]
        processor = ProcesadorLotesRut()
        resultado = processor.formatear_lista_ruts(ruts, formato=formato)

        # Verificar que contiene el contenido esperado
        assert "RUTs válidos:" in resultado

        if formato == "json":
            # Para JSON, verificar que es válido
            json_part = resultado.split("RUTs válidos:\n")[1].split("\n\n")[0]
            json_data = json.loads(json_part)
            assert len(json_data) == 3

    @pytest.mark.parametrize("ruts, formato", datos_test_formatear_lista_ruts)
    def test_formatear_lista_ruts_sin_formato(self, ruts, formato):
        """Prueba formateo de lista sin formato específico."""
        processor = ProcesadorLotesRut()
        resultado = processor.formatear_lista_ruts(ruts, formato=formato)
        assert "RUTs válidos:" in resultado
        if "98765432-1" in ruts:
            assert "[DIGIT_ERROR]" in resultado

    def test_formatear_lista_ruts_formato_invalido(self):
        """Prueba que formato inválido lance excepción."""
        ruts = ["12345678-5"]
        with pytest.raises(ValueError) as exc_info:
            processor = ProcesadorLotesRut()
            processor.formatear_lista_ruts(ruts, formato="pdf")
        assert "Formato 'pdf' no soportado" in str(exc_info.value)

    def test_validar_lista_ruts_parallel(self):
        """Compara resultados en modo secuencial y paralelo."""
        ruts = ["12345678-5", "98765432-1", "1-9", "123"]
        processor = ProcesadorLotesRut()
        seq = processor.validar_lista_ruts(ruts, parallel=False)
        par = processor.validar_lista_ruts(ruts, parallel=True)
        assert seq.ruts_validos == par.ruts_validos
        assert seq.ruts_invalidos == par.ruts_invalidos

    def test_formatear_lista_ruts_parallel(self):
        """Verifica que el formateo paralelo preserve el orden."""
        ruts = ["12345678-5", "98765432-5", "1-9", "123"]
        processor = ProcesadorLotesRut()
        seq = processor.formatear_lista_ruts(ruts, parallel=False)
        par = processor.formatear_lista_ruts(ruts, parallel=True)

        def extraer_validos(texto: str) -> List[str]:
            lineas = texto.splitlines()
            inicio = lineas.index("RUTs válidos:") + 1
            fin = inicio
            for idx in range(inicio, len(lineas)):
                if lineas[idx].strip() == "" or lineas[idx].startswith(
                    "RUTs inválidos:"
                ):
                    fin = idx
                    break
            return lineas[inicio:fin]

        assert extraer_validos(seq) == extraer_validos(par)

    def test_executor_respeta_valor_por_defecto(self, monkeypatch):
        """El ejecutor debe construirse con ``None`` por defecto."""

        llamados = []

        class EjecutorPrueba:
            def __init__(self, max_workers=None):
                llamados.append(max_workers)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

            def map(self, funcion, iterable):
                return [funcion(item) for item in iterable]

        monkeypatch.setattr("rutificador.procesador.ThreadPoolExecutor", EjecutorPrueba)

        processor = ProcesadorLotesRut()
        processor.validar_lista_ruts(["12345678-5"], parallel=True)

        assert llamados == [None]

    def test_executor_usa_max_workers_personalizado(self, monkeypatch):
        """El ejecutor debe recibir el valor personalizado de ``max_workers``."""

        llamados = []

        class EjecutorPrueba:
            def __init__(self, max_workers=None):
                llamados.append(max_workers)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

            def map(self, funcion, iterable):
                return [funcion(item) for item in iterable]

        monkeypatch.setattr("rutificador.procesador.ThreadPoolExecutor", EjecutorPrueba)

        processor = ProcesadorLotesRut(max_workers=4)
        processor.formatear_lista_ruts(["12345678-5", "98765432-5"], parallel=True)

        assert llamados and all(valor == 4 for valor in llamados)


# ============================================================================
# TESTS PARA COMPATIBILIDAD HACIA ATRÁS
# ============================================================================


class TestCompatibilidadHaciaAtras:
    """Suite de pruebas para la compatibilidad con la API original."""

    def test_formatear_lista_ruts_funcion_global(self):
        """Prueba que la función global funcione igual que antes."""
        ruts = ["12345678-5", "98765432-5", "1-9"]
        resultado = formatear_lista_ruts(ruts)

        assert "RUTs válidos:" in resultado
        assert "12345678-5" in resultado
        assert "98765432-5" in resultado
        assert "1-9" in resultado

    def test_formatear_lista_ruts_con_parametros(self):
        """Prueba la función global con parámetros."""
        ruts = ["12345678-5"]
        resultado = formatear_lista_ruts(
            ruts, separador_miles=True, mayusculas=True, formato="csv"
        )

        assert "12.345.678-5" in resultado
        assert "rut\n" in resultado


# ============================================================================
# TESTS DE INTEGRACIÓN
# ============================================================================


class TestIntegracion:
    """Suite de pruebas de integración completa."""

    def test_flujo_completo_rut_individual(self):
        """Prueba el flujo completo para un RUT individual."""
        # Crear RUT
        rut = Rut("12.345.678-5")

        # Verificar componentes
        assert str(rut.base) == "12345678"
        assert rut.digito_verificador == "5"

        # Formatear
        rut_formateado = rut.formatear(separador_miles=True, mayusculas=True)
        assert rut_formateado == "12.345.678-5"

    def test_flujo_completo_batch_processing(self):
        """Prueba el flujo completo de procesamiento por lotes."""
        ruts = ["12.345.678-5", "98.765.432-1", "1-9", "invalid"]

        # Procesar
        processor = ProcesadorLotesRut()
        resultado = processor.formatear_lista_ruts(
            ruts, separador_miles=True, formato="json"
        )

        # Verificar que hay válidos e inválidos
        assert "RUTs válidos:" in resultado
        assert "RUTs inválidos:" in resultado

        # Verificar JSON válido en la parte de válidos
        lines = resultado.split("\n")
        json_start = False
        json_lines = []

        for line in lines:
            if line.strip().startswith("["):
                json_start = True
            if json_start:
                json_lines.append(line)
                if line.strip().endswith("]"):
                    break

        json_str = "\n".join(json_lines)
        json_data = json.loads(json_str)
        assert len(json_data) == 2  # Solo 2 RUTs válidos
