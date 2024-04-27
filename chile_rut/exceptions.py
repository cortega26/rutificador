"""
Módulo exceptions.py

Este módulo contiene las excepciones personalizadas utilizadas por la librería
para el cálculo y validación de RUT chilenos.

Excepciones:
   RutError: Excepción base para errores relacionados con el RUT.
   RutInvalidoError: Lanzada cuando el formato del RUT ingresado es inválido.
   RutDigitoVerificadorInvalidoError: Lanzada cuando el formato del número base
                                      es inválido para el cálculo del dígito
                                      verificador.
"""


class RutError(Exception):
   """Excepción base para errores relacionados con el RUT."""


class RutInvalidoError(RutError):
   """Lanzada cuando el formato del RUT ingresado es inválido."""


class RutDigitoVerificadorInvalidoError(RutError):
   """Lanzada cuando el formato del número base es inválido para el cálculo
   del dígito verificador."""