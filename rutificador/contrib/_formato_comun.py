"""Helpers compartidos para los accesors de pandas y polars."""

from ..rut import Rut


def aplicar_formato(res, formato: str):
    """Aplica un formato de salida a un ``ValidacionResultado``.

    Args:
        res: Resultado de validación (``ValidacionResultado``).
        formato: Tipo de formato (``"miles"``, ``"canonico"``,
            ``"miles-con-guion"`` o ``None`` para el normalizado).

    Returns:
        RUT formateado como cadena, o ``None`` si la validación
        no fue exitosa.
    """
    if res.estado != "valido":
        return None
    if formato == "miles":
        base = Rut.agregar_separador_miles(res.base)
        return f"{base}-{res.dv}"
    if formato == "canonico":
        return res.normalizado.upper() if res.normalizado else None
    if formato == "miles-con-guion":
        base = Rut.agregar_separador_miles(res.base)
        return f"{base}-{res.dv}".upper()
    return res.normalizado
