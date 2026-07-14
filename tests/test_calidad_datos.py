"""Tests para el modulo de calidad de datos."""

from rutificador.calidad_datos import (
    detectar_duplicados,
    auditar_consistencia_formato,
    perfilar_ruts,
)


class TestDetectarDuplicados:
    def test_sin_duplicados(self):
        r = detectar_duplicados(["12.345.678-5", "12345670-k", "1-9"])
        assert r.total_procesados == 3
        assert r.total_unicos == 3
        assert r.total_duplicados == 0
        assert r.duplicados == []

    def test_duplicado_exacto(self):
        r = detectar_duplicados(
            ["12.345.678-5", "12.345.678-5", "12345670-k"]
        )
        assert r.total_unicos == 2
        assert r.total_duplicados == 2

    def test_duplicado_normalizado(self):
        r = detectar_duplicados(
            ["12.345.678-5", "12345678-5", "12345670-k"]
        )
        assert r.total_unicos == 2

    def test_sensible_a_formato_no_detecta_dup_normalizado(self):
        r = detectar_duplicados(
            ["12.345.678-5", "12345678-5"], sensible_a_formato=True
        )
        assert r.total_unicos == 2

    def test_lista_vacia(self):
        r = detectar_duplicados([])
        assert r.total_procesados == 0
        assert r.total_unicos == 0
        assert r.duplicados == []

    def test_entradas_invalidas_ignoradas(self):
        r = detectar_duplicados(["abc", "12.345.678-5", "12.345.678-5"])
        assert r.total_procesados == 3
        assert r.total_unicos == 1

    def test_resultado_pii_safe(self):
        r = detectar_duplicados(["12.345.678-5", "12.345.678-5"])
        assert len(r.duplicados) == 1
        enmascarado, conteo = r.duplicados[0]
        assert "12345678" not in enmascarado
        assert conteo == 2


class TestAuditarConsistenciaFormato:
    def test_todos_con_puntos(self):
        a = auditar_consistencia_formato(["12.345.678-5", "12345670-k"])
        assert a.total == 2
        assert a.con_puntos == 1
        assert a.sin_puntos == 1

    def test_mezcla_formatos(self):
        a = auditar_consistencia_formato(["12.345.678-5", "12345678-5"])
        assert a.con_puntos == 1
        assert a.sin_puntos == 1

    def test_dv_mayuscula_vs_minuscula(self):
        a = auditar_consistencia_formato(["12345670-K", "12345670-k"])
        assert a.dv_mayuscula == 1
        assert a.dv_minuscula == 1

    def test_con_espacios(self):
        a = auditar_consistencia_formato(["12 345 678-5"])
        assert a.con_espacios == 1

    def test_formatos_distintos_tracking(self):
        a = auditar_consistencia_formato(
            ["12.345.678-5", "12345678-k", "12345670-K"]
        )
        assert len(a.formatos_distintos) >= 2


class TestPerfilarRuts:
    def test_todos_validos(self):
        p = perfilar_ruts(["12.345.678-5", "12345670-k", "1-9"])
        assert p.total == 3
        assert p.validos == 3
        assert p.invalidos == 0
        assert p.tasa_validez == 1.0

    def test_mezcla_validos_invalidos(self):
        p = perfilar_ruts(["12.345.678-5", "abc", "1-9", ""])
        assert p.validos == 2
        assert p.invalidos == 1
        assert p.incompletos == 1
        assert p.tasa_validez == 0.5

    def test_distribucion_longitud(self):
        p = perfilar_ruts(["1-9", "12.345.678-5"])
        assert p.distribucion_longitud == {1: 1, 8: 1}

    def test_distribucion_dv(self):
        p = perfilar_ruts(["12.345.678-5", "12345670-k", "1-9"])
        assert "5" in p.distribucion_dv
        assert "k" in p.distribucion_dv
        assert "9" in p.distribucion_dv

    def test_lista_vacia(self):
        p = perfilar_ruts([])
        assert p.total == 0
        assert p.tasa_validez == 0.0
