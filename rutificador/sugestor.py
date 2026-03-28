# SECURITY-CRITICAL
import logging
from typing import List, Optional, Set

from .utils import calcular_digito_verificador, _limpiar_entrada

logger = logging.getLogger(__name__)

def distancia_levenshtein(s1: str, s2: str) -> int:
    """Calcula la distancia de Damerau-Levenshtein entre dos cadenas."""
    d = {}
    len1 = len(s1)
    len2 = len(s2)
    for i in range(-1, len1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, len2 + 1):
        d[(-1, j)] = j + 1

    for i in range(len1):
        for j in range(len2):
            cost = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,      # Deletion
                d[(i, j - 1)] + 1,      # Insertion
                d[(i - 1, j - 1)] + cost # Substitution
            )
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[(i - 2, j - 2)] + cost) # Transposition

    return d[(len1 - 1, len2 - 1)]

def sugerir_ruts(valor: str, limite: int = 5) -> List[str]:
    """Genera sugerencias de RUTs válidos basados en una entrada posiblemente errónea."""
    sugerencias: Set[str] = set()
    
    cadena, _ = _limpiar_entrada(valor)
    if not cadena:
        return []

    # 1. Caso: El usuario puso un guion (asumimos separación clara)
    if "-" in cadena:
        partes = cadena.split("-")
        base_orig = "".join(c for c in partes[0] if c.isdigit())
        dv_orig = partes[1].strip().lower() if len(partes) > 1 else ""
        
        # Probar la base tal cual con nuevo DV
        if base_orig:
            try:
                sugerencias.add(f"{base_orig}-{calcular_digito_verificador(base_orig)}")
            except: pass
            
            # Probar transposiciones en la base manteniendo el DV original si parece válido
            digitos_base = list(base_orig)
            for i in range(len(digitos_base) - 1):
                copia = digitos_base[:]
                copia[i], copia[i+1] = copia[i+1], copia[i]
                base_cand = "".join(copia)
                try:
                    # Sugerir la base con su DV real
                    sugerencias.add(f"{base_cand}-{calcular_digito_verificador(base_cand)}")
                except: pass

    # 2. Caso: Sin guion o entrada ambigua (probar todas las posibilidades razonables)
    solo_digitos = "".join(c for c in cadena if c.isdigit())
    if len(solo_digitos) >= 7:
        # Asumir que el último es DV
        base_1 = solo_digitos[:-1]
        try: sugerencias.add(f"{base_1}-{calcular_digito_verificador(base_1)}")
        except: pass
        
        # Asumir que todos son parte de la base y falta el DV
        try: sugerencias.add(f"{solo_digitos}-{calcular_digito_verificador(solo_digitos)}")
        except: pass

    # 3. Filtrado y ordenamiento por distancia de edición (Damerau-Levenshtein)
    # Normalizamos para comparar peras con peras
    def normalizar_para_dist(s: str) -> str:
        return s.replace(".", "").replace("-", "").lower()

    eval_orig = normalizar_para_dist(valor)
    
    def score(s: str) -> int:
        return distancia_levenshtein(eval_orig, normalizar_para_dist(s))

    # Solo sugerir si son mejores que un umbral (Distancia <= 2)
    resultados = [s for s in sugerencias if score(s) <= 2]
    # Ordenar por score y luego por longitud (más probable a menos probable)
    resultados.sort(key=lambda x: (score(x), -len(x)))
    
    return resultados[:limite]
