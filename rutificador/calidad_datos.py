"""Herramientas de calidad de datos para columnas de RUTs.

Ofrece deteccion de duplicados, auditoria de consistencia de formatos,
perfilamiento estadistico y reportes de calidad. Todas las operaciones
aceptan secuencias de cadenas (RUTs en cualquier formato) y usan
internamente ``Rut.parse`` para normalizar antes de comparar.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from .rut import Rut


@dataclass
class InformeDuplicados:
    """Resultado de una operacion de deteccion de duplicados."""

    total_procesados: int
    total_unicos: int
    total_duplicados: int
    duplicados: list[tuple[str, int]]  # (base_normalizada, conteo)


def detectar_duplicados(
    ruts: Sequence[str],
    *,
    sensible_a_formato: bool = False,
) -> InformeDuplicados:
    """Detecta RUTs duplicados en una secuencia.

    Por defecto (``sensible_a_formato=False``), compara usando la base
    y DV normalizados — ``12.345.678-5`` y ``12345678-5`` se consideran
    el mismo RUT.

    Con ``sensible_a_formato=True``, compara usando la representacion
    exacta de la entrada — util para detectar variaciones de formato en
    un dataset (ej: mezcla de con/sin puntos).

    Los resultados usan enmascaramiento PII-safe: solo se muestran los
    ultimos 4 digitos de la base + DV.

    Args:
        ruts: Secuencia de cadenas con RUTs.
        sensible_a_formato: Si ``True``, compara texto exacto de entrada.

    Returns:
        ``InformeDuplicados`` con conteos y valores repetidos.
    """
    contador: Counter[str] = Counter()
    procesados = 0

    for valor in ruts:
        procesados += 1
        resultado = Rut.parse(valor)
        if resultado.estado not in ("valido", "posible"):
            continue

        if sensible_a_formato:
            clave = resultado.original
        elif resultado.normalizado is not None:
            clave = resultado.normalizado
        else:
            continue

        contador[clave] += 1

    # Solo incluir los que aparecen mas de una vez, enmascarados
    duplicados: list[tuple[str, int]] = []
    for clave, conteo in contador.most_common():
        if conteo > 1:
            try:
                enmascarado = Rut.enmascarar(clave, mantener=4)
            except Exception:
                enmascarado = clave[-4:] if len(clave) >= 4 else clave
            duplicados.append((enmascarado, conteo))

    unicos = sum(1 for c in contador.values())
    total_dup = sum(c for c in contador.values() if c > 1)

    return InformeDuplicados(
        total_procesados=procesados,
        total_unicos=unicos,
        total_duplicados=total_dup,
        duplicados=duplicados,
    )


@dataclass
class AuditoriaFormato:
    """Resultado de una auditoria de consistencia de formatos."""

    total: int
    con_puntos: int
    sin_puntos: int
    con_guion: int
    sin_guion: int
    con_espacios: int
    dv_mayuscula: int
    dv_minuscula: int
    formatos_distintos: list[tuple[str, int]]  # (formato, conteo)


def _clasificar_formato(original: str) -> str:
    """Clasifica el formato de una entrada de RUT."""
    partes = []
    if "." in original:
        partes.append("con_puntos")
    else:
        partes.append("sin_puntos")

    if "-" in original:
        partes.append("con_guion")
    else:
        partes.append("sin_guion")

    if " " in original:
        partes.append("con_espacios")

    if original and original[-1].isupper():
        partes.append("dv_mayuscula")
    elif original and original[-1].islower():
        partes.append("dv_minuscula")

    return "+".join(partes)


def auditar_consistencia_formato(
    ruts: Sequence[str],
) -> AuditoriaFormato:
    """Analiza la consistencia de formatos en una secuencia de RUTs.

    Clasifica cada entrada segun presencia de puntos, guiones, espacios
    y capitalizacion del DV. Util para limpieza de datos: si una columna
    tiene 80% con puntos y 20% sin puntos, sabes que necesitas normalizar.

    Args:
        ruts: Secuencia de cadenas con RUTs.

    Returns:
        ``AuditoriaFormato`` con desglose por categoria de formato.
    """
    total = 0
    con_puntos = 0
    sin_puntos = 0
    con_guion = 0
    sin_guion = 0
    con_espacios = 0
    dv_mayuscula = 0
    dv_minuscula = 0
    formatos: Counter[str] = Counter()

    for valor in ruts:
        if not isinstance(valor, str) or not valor.strip():
            continue
        total += 1
        original = valor.strip()

        if "." in original:
            con_puntos += 1
        else:
            sin_puntos += 1

        if "-" in original:
            con_guion += 1
        else:
            sin_guion += 1

        if " " in original:
            con_espacios += 1

        ultimo = original[-1] if original else ""
        if ultimo == "K":
            dv_mayuscula += 1
        elif ultimo == "k":
            dv_minuscula += 1

        formato = _clasificar_formato(original)
        formatos[formato] += 1

    return AuditoriaFormato(
        total=total,
        con_puntos=con_puntos,
        sin_puntos=sin_puntos,
        con_guion=con_guion,
        sin_guion=sin_guion,
        con_espacios=con_espacios,
        dv_mayuscula=dv_mayuscula,
        dv_minuscula=dv_minuscula,
        formatos_distintos=formatos.most_common(),
    )


@dataclass
class PerfilRut:
    """Perfil estadistico de una columna de RUTs."""

    total: int
    validos: int
    invalidos: int
    incompletos: int
    tasa_validez: float
    distribucion_longitud: dict[int, int]  # longitud base -> conteo
    distribucion_dv: dict[str, int]  # digito verificador -> conteo


def perfilar_ruts(
    ruts: Sequence[str],
) -> PerfilRut:
    """Genera un perfil estadistico de una secuencia de RUTs.

    Calcula tasas de validez, distribucion de longitudes de base,
    y distribucion de digitos verificadores. Los RUTs invalidos se
    excluyen de las distribuciones de longitud y DV.

    Args:
        ruts: Secuencia de cadenas con RUTs.

    Returns:
        ``PerfilRut`` con estadisticas agregadas.
    """
    total = 0
    validos = 0
    invalidos = 0
    incompletos = 0
    longitudes: Counter[int] = Counter()
    dvs: Counter[str] = Counter()

    for valor in ruts:
        if not isinstance(valor, str):
            continue
        total += 1
        resultado = Rut.parse(valor)

        if resultado.estado == "valido":
            validos += 1
            if resultado.base is not None:
                longitudes[len(resultado.base)] += 1
            if resultado.dv is not None:
                dvs[resultado.dv.lower()] += 1
        elif resultado.estado == "posible":
            validos += 1
            if resultado.base is not None:
                longitudes[len(resultado.base)] += 1
        elif resultado.estado == "invalido":
            invalidos += 1
        elif resultado.estado == "incompleto":
            incompletos += 1

    tasa = validos / total if total > 0 else 0.0

    return PerfilRut(
        total=total,
        validos=validos,
        invalidos=invalidos,
        incompletos=incompletos,
        tasa_validez=tasa,
        distribucion_longitud=dict(longitudes.most_common()),
        distribucion_dv=dict(dvs.most_common()),
    )


__all__ = [
    "InformeDuplicados",
    "AuditoriaFormato",
    "PerfilRut",
    "detectar_duplicados",
    "auditar_consistencia_formato",
    "perfilar_ruts",
]
