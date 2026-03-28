# SECURITY-CRITICAL
import logging
from typing import Dict, List, Optional, Set, Tuple

from .utils import calcular_digito_verificador, _limpiar_entrada

logger = logging.getLogger(__name__)

# Mapa de sustituciones comunes por errores de digitación o lectura OCR
_SUSTITUCIONES_OCR: Dict[str, str] = {
    "o": "0",
    "O": "0",
    "i": "1",
    "I": "1",
    "l": "1",
    "L": "1",
    "z": "2",
    "Z": "2",
    "s": "5",
    "S": "5",
    "b": "8",
    "B": "8",
}


def distancia_levenshtein(s1: str, s2: str) -> int:
    """Calcula la distancia de Damerau-Levenshtein entre dos cadenas.

    Detecta inserción, eliminación, sustitución y transposición de dos caracteres
    adyacentes (error común de digitación).
    """
    d: Dict[Tuple[int, int], int] = {}
    long1 = len(s1)
    long2 = len(s2)
    for i in range(-1, long1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, long2 + 1):
        d[(-1, j)] = j + 1

    for i in range(long1):
        for j in range(long2):
            costo = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,  # Eliminación
                d[(i, j - 1)] + 1,  # Inserción
                d[(i - 1, j - 1)] + costo,  # Sustitución
            )
            # Transposición (Damerau)
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[(i - 2, j - 2)] + costo)

    return d[(long1 - 1, long2 - 1)]


def sugerir_ruts(valor: str, limite: int = 5) -> List[str]:
    """Genera sugerencias de RUTs válidos basados en una entrada posiblemente errónea.

    Utiliza heurísticas de OCR y distancia de edición para encontrar el RUT
    más probable.

    Args:
        valor: Cadena de entrada (ej: '12.345.678-k', '12435678-5', 'I2.345.678-5').
        limite: Número máximo de sugerencias a devolver.

    Returns:
        Lista de RUTs sugeridos en formato 'base-dv'.
    """
    candidatos_con_dist = _sugerir_ruts_con_distancia(valor, limite)
    return [rut for rut, dist in candidatos_con_dist]


def mejorar_con_confianza(valor: str, distancia_max: int = 1) -> Optional[str]:
    """Toma una decisión de corrección automática solo si es inequívoca.

    Para ser 'segura', una sugerencia debe:
    1. Ser la única con la distancia mínima encontrada.
    2. Tener una distancia <= distancia_max (por defecto 1).

    Returns:
        El RUT sugerido si es seguro, None en caso de ambigüedad o baja confianza.
    """
    # Obtenemos las 2 mejores para detectar empates
    candidatos = _sugerir_ruts_con_distancia(valor, limite=2)

    if not candidatos:
        return None

    mejor_rut, mejor_dist = candidatos[0]

    # 1. Verificar umbral de confianza (distancia de edición razonable)
    if mejor_dist > distancia_max:
        return None

    # 2. Verificar ambigüedad (si hay un segundo candidato con la misma distancia mínima)
    if len(candidatos) > 1:
        segundo_rut, segunda_dist = candidatos[1]
        if mejor_dist == segunda_dist:
            logger.warning(
                f"Ambigüedad detectada para '{valor}': varios candidatos a distancia {mejor_dist}. "
                f"Opciones: {mejor_rut}, {segundo_rut}"
            )
            return None

    return mejor_rut


def _sugerir_ruts_con_distancia(valor: str, limite: int = 5) -> List[Tuple[str, int]]:
    """Lógica interna que devuelve tuplas (rut, distancia) ordenadas."""
    sugerencias: Set[str] = set()

    # 1. Limpieza básica y aplicación de heurísticas OCR
    def aplicar_ocr(s: str) -> str:
        for original, reemplazo in _SUSTITUCIONES_OCR.items():
            s = s.replace(original, reemplazo)
        return s

    entrada_ocr = aplicar_ocr(valor)
    cadena, _ = _limpiar_entrada(entrada_ocr)

    if not cadena:
        return []

    # 2. Estrategia: Manejo de RUTs con guion (asumimos separación tentativa)
    if "-" in cadena:
        partes = cadena.split("-")
        base_orig = "".join(c for c in partes[0] if c.isdigit())

        # Probar la base tal cual con su DV correcto calculado
        if base_orig:
            try:
                dv_calc = calcular_digito_verificador(base_orig).lower()
                sugerencias.add(f"{base_orig}-{dv_calc}")
            except Exception:
                pass

            # Probar transposiciones simples en la base (error 1243 -> 1234)
            digitos_base = list(base_orig)
            for i in range(len(digitos_base) - 1):
                copia = digitos_base[:]
                copia[i], copia[i + 1] = copia[i + 1], copia[i]
                base_cand = "".join(copia)
                try:
                    dv_cand = calcular_digito_verificador(base_cand).lower()
                    sugerencias.add(f"{base_cand}-{dv_cand}")
                except Exception:
                    pass

    # 3. Estrategia: Cadena continua (probar cortes razonables)
    solo_digitos = "".join(c for c in cadena if c.isdigit() or c.lower() == "k")
    if len(solo_digitos) >= 7:
        # 3.1 Asumir que el último es DV (si es dígito o K)
        base_1 = solo_digitos[:-1]
        try:
            dv_c = calcular_digito_verificador(base_1).lower()
            sugerencias.add(f"{base_1}-{dv_c}")
            
            # Probar transposiciones en esta base tentativa
            digitos_base = list(base_1)
            for i in range(len(digitos_base) - 1):
                copia = digitos_base[:]
                copia[i], copia[i + 1] = copia[i + 1], copia[i]
                base_cand = "".join(copia)
                try:
                    dv_cand = calcular_digito_verificador(base_cand).lower()
                    sugerencias.add(f"{base_cand}-{dv_cand}")
                except Exception:
                    pass
        except Exception:
            pass

        # 3.2 Asumir que todos son parte de la base y falta el DV
        # Solo probar esto si la longitud sugiere que solo tenemos la base (7-8 caracteres)
        if 7 <= len(solo_digitos) <= 8:
            try:
                dv_f = calcular_digito_verificador(solo_digitos).lower()
                sugerencias.add(f"{solo_digitos}-{dv_f}")
            except Exception:
                pass

    # 4. Filtrado y ordenamiento por distancia de edición (Damerau-Levenshtein)
    def normalizar_para_dist(s: str) -> str:
        return s.replace(".", "").replace("-", "").lower()

    entrada_normalizada = normalizar_para_dist(valor)

    def calcular_puntaje(s: str) -> int:
        return distancia_levenshtein(entrada_normalizada, normalizar_para_dist(s))

    # Solo sugerir si son mejores que un umbral razonable (Distancia <= 2)
    candidatos_raw = [(s, calcular_puntaje(s)) for s in sugerencias]
    candidatos_filtrados = [c for c in candidatos_raw if c[1] <= 2]

    # Ordenar por:
    # 1. Menor distancia de edición (más parecido)
    # 2. Diferencia de longitud mínima (preferir misma cantidad de dígitos)
    # 3. Prioridad a bases originales (si el RUT sugerido tiene la misma base que la entrada)
    # 4. Mayor longitud absoluta (preferir RUTs más completos)
    base_entrada, _ = _limpiar_entrada(valor)

    def tiene_misma_base(s: str) -> int:
        base_s = s.split("-")[0]
        return 0 if base_s in base_entrada else 1

    candidatos_filtrados.sort(
        key=lambda x: (
            x[1],  # distancia (Score)
            abs(len(normalizar_para_dist(x[0])) - len(entrada_normalizada)),
            tiene_misma_base(x[0]),
            -len(x[0]),
        )
    )

    return candidatos_filtrados[:limite]
