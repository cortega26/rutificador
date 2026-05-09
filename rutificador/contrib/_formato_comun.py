"""Helpers compartidos para los accesors de pandas y polars."""

from ..rut import Rut


def aplicar_formato(res, formato: str):
    """Aplica un formato de salida a un resultado de validación."""
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
