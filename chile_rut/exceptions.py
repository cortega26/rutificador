class RutError(Exception):
    """Excepción base para errores relacionados con el RUT."""


class RutInvalidoError(RutError):
    """Lanzada cuando el formato del RUT ingresado es inválido."""


class RutDigitoVerificadorInvalidoError(RutError):
    """Lanzada cuando el formato del número base es inválido para el cálculo del dígito verificador."""