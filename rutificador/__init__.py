"""
Rutificador: Una biblioteca Python para validar y formatear RUTs chilenos.

Este módulo proporciona herramientas para trabajar con RUTs chilenos (Rol Único Tributario),
incluyendo validación, formateo y verificación de dígitos.

Clases:
    Rut: Representa un RUT chileno, con métodos para validación y formateo.
    RutDigitoVerificador: Calcula y representa el dígito verificador de un RUT chileno.
    RutInvalidoError: Excepción personalizada para errores de RUT inválido.
    RutValidador: Valida un RUT chileno.

Versión: 0.2.22
Autor: Carlos Ortega González
Licencia: MIT
"""

from typing import List

__version__ = "0.2.22"
__author__ = "Carlos Ortega González"
__license__ = "MIT"

from .main import Rut, RutDigitoVerificador, RutInvalidoError, RutValidador

__all__: List[str] = ["Rut", "RutDigitoVerificador", "RutInvalidoError", "RutValidador"]