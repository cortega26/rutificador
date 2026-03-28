import pytest
from rutificador.sugestor import sugerir_ruts, distancia_levenshtein
from rutificador.rut import Rut

def test_distancia_levenshtein():
    # Misma cadena
    assert distancia_levenshtein("123", "123") == 0
    # Una sustitución
    assert distancia_levenshtein("123", "124") == 1
    # Una inserción
    assert distancia_levenshtein("123", "1234") == 1
    # Una eliminación
    assert distancia_levenshtein("1234", "123") == 1
    # Una transposición (Damerau)
    assert distancia_levenshtein("123", "132") == 1

def test_sugestor_dv_mismatch():
    # RUT con DV incorrecto: 12.345.678-k (debería ser -5)
    sugerencias = sugerir_ruts("12345678-k")
    assert "12345678-5" in sugerencias

def test_sugestor_transposicion():
    # Transposición en la base: 12.345.687-5 (debería ser 12.345.678-5)
    sugerencias = sugerir_ruts("12345687-5")
    assert "12345678-5" in sugerencias

def test_sugestor_falta_digito():
    # Falta el último dígito verificador: 12.345.678
    sugerencias = sugerir_ruts("12345678")
    assert "12345678-5" in sugerencias

def test_rut_suggest_api():
    # Probar la API de alto nivel
    sugerencias = Rut.suggest("12345678-0")
    assert len(sugerencias) > 0
    assert "12345678-5" in sugerencias

def test_rut_mejorar_api():
    # Probar la corrección automática
    mejor_opcion = Rut.mejorar("12a345678-k") # Con basura
    assert mejor_opcion == "12345678-5"

def test_sugestor_sin_entrada():
    assert sugerir_ruts("") == []
    assert sugerir_ruts("   ") == []
