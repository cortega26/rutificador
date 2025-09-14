"""Utilidades para formatear listas de números RUT chilenos."""

import csv
import html
import json
import logging
from abc import ABC, abstractmethod
from io import StringIO
from typing import Any, ClassVar, Dict, List, Optional, Sequence, Type

logger = logging.getLogger(__name__)


class FormateadorRut(ABC):
    """Clase base abstracta para formateadores de RUT con validación."""

    @abstractmethod
    def formatear(self, ruts: Sequence[str]) -> str:
        """Formatea una secuencia de RUTs."""
        raise NotImplementedError

    def validar_entrada(self, ruts: Sequence[str]) -> None:
        """Valida la entrada antes de formatear."""
        if not isinstance(ruts, (list, tuple)):
            raise TypeError(
                f"Se esperaba una secuencia, se recibió {type(ruts).__name__}"
            )

        if not ruts:
            logger.warning("Se proporcionó una secuencia vacía de RUTs para formateo")


class FormateadorCSV(FormateadorRut):
    """Formateador CSV con opciones configurables."""

    def __init__(self, encabezado: str = "rut", delimitador: str = "\n") -> None:
        self.encabezado = encabezado
        self.delimitador = delimitador

    def formatear(self, ruts: Sequence[str]) -> str:
        """Genera una representación CSV segura de la lista de RUTs.

        Se utiliza :mod:`csv` para garantizar el escapado correcto y se
        mitiga la inyección de fórmulas en herramientas de hoja de cálculo
        prefixando con una comilla simple (``'``) los valores que inician con
        ``=``, ``+``, ``-`` o ``@``.
        """

        self.validar_entrada(ruts)

        buffer = StringIO()
        writer = csv.writer(buffer, lineterminator=self.delimitador)
        writer.writerow([self.encabezado])

        for rut in ruts:
            valor = str(rut)
            if valor and valor[0] in {"=", "+", "-", "@"}:
                valor = f"'{valor}"
            writer.writerow([valor])

        contenido = buffer.getvalue().rstrip(self.delimitador)
        buffer.close()
        return contenido


class FormateadorXML(FormateadorRut):
    """Formateador XML con escape y validación apropiados."""

    def __init__(self, elemento_raiz: str = "root", elemento_item: str = "rut") -> None:
        self.elemento_raiz = elemento_raiz
        self.elemento_item = elemento_item

    def formatear(self, ruts: Sequence[str]) -> str:
        """Genera una representación XML escapando caracteres especiales."""
        self.validar_entrada(ruts)

        lineas_xml = [f"<{self.elemento_raiz}>"]

        for rut in ruts:
            rut_escapado = html.escape(str(rut), quote=True).replace("'", "&#x27;")
            lineas_xml.append(
                f"    <{self.elemento_item}>{rut_escapado}</{self.elemento_item}>"
            )

        lineas_xml.append(f"</{self.elemento_raiz}>")
        return "\n".join(lineas_xml)


class FormateadorJSON(FormateadorRut):
    """Formateador JSON con estructura configurable."""

    def __init__(self, nombre_clave: str = "rut", imprimir_bonito: bool = True) -> None:
        self.nombre_clave = nombre_clave
        self.imprimir_bonito = imprimir_bonito

    def formatear(self, ruts: Sequence[str]) -> str:
        self.validar_entrada(ruts)

        ruts_json = [{self.nombre_clave: str(rut)} for rut in ruts]

        return json.dumps(
            ruts_json,
            indent=2 if self.imprimir_bonito else None,
            ensure_ascii=False,
            separators=(",", ": ") if self.imprimir_bonito else (",", ":"),
        )


class FabricaFormateadorRut:
    """Fábrica para crear formateadores de RUT con soporte de configuración."""

    _formatters: ClassVar[Dict[str, Type[FormateadorRut]]] = {
        "csv": FormateadorCSV,
        "xml": FormateadorXML,
        "json": FormateadorJSON,
    }

    @classmethod
    def registrar_formateador(
        cls, nombre: str, clase_formateador: Type[FormateadorRut]
    ) -> None:
        """Registra una clase formateadora personalizada."""
        if not issubclass(clase_formateador, FormateadorRut):
            raise TypeError("El formateador debe heredar de FormateadorRut")
        cls._formatters[nombre.lower()] = clase_formateador
        logger.info("Formateador personalizado registrado: %s", nombre)

    @classmethod
    def obtener_formateador(
        cls, formato: str, **kwargs: Any
    ) -> Optional[FormateadorRut]:
        """Obtiene una instancia de formateador por nombre."""
        if not isinstance(formato, str):
            return None

        clase_formateador = cls._formatters.get(formato.lower())
        if clase_formateador:
            return clase_formateador(**kwargs)
        return None

    @classmethod
    def obtener_formatos_disponibles(cls) -> List[str]:
        """Devuelve la lista de nombres de formateadores soportados."""
        return list(cls._formatters.keys())
