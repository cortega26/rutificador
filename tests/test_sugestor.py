from rutificador.sugestor import (
    sugerir_ruts,
    distancia_levenshtein,
    mejorar_con_confianza,
)
import rutificador.sugestor


def test_distancia_levenshtein():
    # Identidad
    assert distancia_levenshtein("123", "123") == 0
    # Transposición (Damerau)
    assert distancia_levenshtein("123", "132") == 1
    # Inserción
    assert distancia_levenshtein("123", "1234") == 1
    # Eliminación
    assert distancia_levenshtein("123", "12") == 1
    # Sustitución
    assert distancia_levenshtein("123", "124") == 1


def test_sugerir_ruts_transposicion():
    # 12.345.678-5 -> transponer 5 y 4
    mal = "12.354.678-5"
    sugerencias = sugerir_ruts(mal)
    assert "12345678-5" in sugerencias


def test_sugerir_ruts_ocr():
    # Reemplazar 0 por O e I por 1
    mal = "I2.345.678-O"
    sugerencias = sugerir_ruts(mal)
    # Debería corregir OCR y luego calcular el DV correcto (5)
    assert "12345678-5" in sugerencias


def test_sugerir_ruts_dv_erroneo():
    # RUT válido con DV mal puesto
    mal = "12.345.678-k"  # El real es 5
    sugerencias = sugerir_ruts(mal)
    assert "12345678-5" in sugerencias


def test_sugerir_ruts_sin_guion():
    # RUT de 8 dígitos sin guion, asumiendo que el último es el DV
    mal = "12345678"  # base 1234567, dv 8? NO, base 1234567 es dv 2.
    # Si probamos base 12345678, el dv es 5.
    sugerencias = sugerir_ruts(mal)
    assert "12345678-5" in sugerencias


def test_sugerir_ruts_vacio():
    assert sugerir_ruts("") == []
    assert sugerir_ruts("   ") == []


def test_sugerir_ruts_muy_lejano():
    # Distancia > 2 no debería sugerir nada útil bajo el umbral actual
    mal = "abcdefgh-i"
    assert sugerir_ruts(mal) == []


def test_mejorar_con_confianza_seguro():

    # Caso NO ambiguo: Solo el DV está mal
    # 12.345.678-1 (El real es 5)
    # Sugerencia dist 1 -> 12345678-5
    # Otros cambios (como transposición) requerirían cambiar el DV a K (dist 2)
    mal = "12.345.678-1"
    assert mejorar_con_confianza(mal) == "12345678-5"


def test_mejorar_con_confianza_inseguro_por_distancia():

    # Caso ambiguo real: 12.354.678-5
    # Solución A (dist 1): 12354678-4 (Cambiar 5 por 4)
    # Solución B (dist 1): 12345678-5 (Transponer 54 a 45)
    # El motor SEGURO debe retornar None al detectar el empate
    mal = "12.354.678-5"
    assert mejorar_con_confianza(mal) is None
    # Caso distancia > 1
    # '123456pp' requiere cambiar dos caracteres para ser un RUT válido
    mal_lejos = "123456pp"
    assert mejorar_con_confianza(mal_lejos) is None


def test_mejorar_con_confianza_ambiguedad(monkeypatch):

    # Simulamos un caso de ambigüedad (dos sugerencias a la misma distancia)
    def mock_sugerir_dist(valor, limite):
        _ = (valor, limite)
        return [("12345678-5", 1), ("87654321-k", 1)]

    monkeypatch.setattr(
        rutificador.sugestor, "_sugerir_ruts_con_distancia", mock_sugerir_dist
    )

    # Debería retornar None al detectar el empate en distancia
    assert mejorar_con_confianza("cualquier-cosa") is None
