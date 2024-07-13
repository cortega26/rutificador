"""
Rutificador: Una biblioteca Python para validar y formatear RUTs chilenos.

Este módulo proporciona herramientas para trabajar con RUTs chilenos (Rol Único Tributario),
incluyendo validación, formateo y verificación de dígitos.

Clases:
    Rut: Representa un RUT chileno, con métodos para validación y formateo.
    RutDigitoVerificador: Calcula y representa el dígito verificador de un RUT chileno.
    RutInvalidoError: Excepción personalizada para errores de RUT inválido.

Versión: 0.2.19
Autor: Carlos Ortega González
Licencia: MIT
"""

__version__ = "0.2.19"
__author__ = "Carlos Ortega González"
__license__ = "MIT"

from .main import Rut, RutDigitoVerificador, RutInvalidoError

__all__ = ["Rut", "RutDigitoVerificador", "RutInvalidoError"]