import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

from .exceptions import ErrorRut
from .formatter import FabricaFormateadorRut
from .utils import (
    monitor_de_rendimiento,
    asegurar_booleano,
    calcular_digito_verificador,
)
from .validador import ValidadorRut
from .rut import Rut

logger = logging.getLogger(__name__)


@dataclass
class DetalleError:
    """Representa un error asociado a un RUT específico."""

    rut: str
    codigo: Optional[str]
    mensaje: str


@dataclass
class ResultadoLote:
    """Contenedor de resultados para operaciones por lotes."""

    ruts_validos: List[str] = field(default_factory=list)
    ruts_invalidos: List[DetalleError] = field(default_factory=list)
    tiempo_procesamiento: float = 0.0
    total_procesados: int = 0

    @property
    def tasa_exito(self) -> float:
        if self.total_procesados == 0:
            return 0.0
        return (len(self.ruts_validos) / self.total_procesados) * 100


class ProcesadorLotesRut:
    """Servicio para validar y formatear RUTs en lotes."""

    def __init__(
        self,
        validador: Optional[ValidadorRut] = None,
        max_workers: Optional[int] = None,
    ) -> None:
        self.validador = validador or ValidadorRut()
        self.max_workers: Optional[int] = max_workers

    @monitor_de_rendimiento
    def validar_lista_ruts(
        self, ruts: Sequence[str], parallel: bool = False
    ) -> ResultadoLote:
        inicio = time.perf_counter()
        resultado = ResultadoLote()

        def crear_rut(cadena: str) -> Tuple[bool, Union[str, DetalleError]]:
            try:
                rut_obj = Rut(cadena, validador=self.validador)
                return True, str(rut_obj)
            except ErrorRut as exc:
                return False, DetalleError(
                    rut=str(cadena),
                    codigo=exc.error_code,
                    mensaje=str(exc),
                )
            except (ValueError, TypeError) as exc:
                return False, DetalleError(
                    rut=str(cadena),
                    codigo=None,
                    mensaje=str(exc),
                )

        if parallel:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                resultados = list(executor.map(crear_rut, ruts))
            for es_valido, valor in resultados:
                if es_valido:
                    resultado.ruts_validos.append(cast(str, valor))
                else:
                    resultado.ruts_invalidos.append(cast(DetalleError, valor))
        else:
            for cadena in ruts:
                es_valido, valor = crear_rut(cadena)
                if es_valido:
                    resultado.ruts_validos.append(cast(str, valor))
                else:
                    resultado.ruts_invalidos.append(cast(DetalleError, valor))

        resultado.total_procesados = len(ruts)
        resultado.tiempo_procesamiento = time.perf_counter() - inicio
        return resultado

    @monitor_de_rendimiento
    def formatear_lista_ruts(
        self,
        ruts: Sequence[str],
        separador_miles: bool = False,
        mayusculas: bool = False,
        formato: Optional[str] = None,
        parallel: bool = False,
        **formatter_kwargs: Any,
    ) -> str:
        if not isinstance(ruts, (list, tuple)):
            raise ValueError(
                f"ruts debe ser una secuencia, se recibió: {type(ruts).__name__}"
            )
        asegurar_booleano(separador_miles, "separador_miles")
        asegurar_booleano(mayusculas, "mayusculas")

        resultado_validacion = self.validar_lista_ruts(ruts, parallel=parallel)
        partes: List[str] = ["RUTs válidos:"]

        def formatear_cadena(cadena: str) -> str:
            rut_obj = Rut(cadena, validador=self.validador)
            return rut_obj.formatear(
                separador_miles=separador_miles, mayusculas=mayusculas
            )

        if parallel:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                ruts_formateados = list(
                    executor.map(formatear_cadena, resultado_validacion.ruts_validos)
                )
        else:
            ruts_formateados = [
                formatear_cadena(cadena) for cadena in resultado_validacion.ruts_validos
            ]

        if formato:
            formatter = FabricaFormateadorRut.obtener_formateador(
                formato, **formatter_kwargs
            )
            if not formatter:
                disponibles = FabricaFormateadorRut.obtener_formatos_disponibles()
                raise ValueError(
                    "Formato "
                    f"'{formato}' no soportado. "
                    f"Formatos disponibles: {disponibles}"
                )
            partes.append(formatter.formatear(ruts_formateados))
        else:
            partes.append("\n".join(ruts_formateados))

        if resultado_validacion.ruts_invalidos:
            partes.append("")
            partes.append("RUTs inválidos:")
            for detalle in resultado_validacion.ruts_invalidos:
                codigo = detalle.codigo or "SIN_CODIGO"
                partes.append(f"{detalle.rut} [{codigo}] - {detalle.mensaje}")

        tiempo_procesamiento = resultado_validacion.tiempo_procesamiento

        partes.extend(
            [
                "",
                "Estadísticas de procesamiento:",
                f"- Total procesados: {resultado_validacion.total_procesados}",
                f"- RUTs válidos: {len(resultado_validacion.ruts_validos)}",
                f"- RUTs inválidos: {len(resultado_validacion.ruts_invalidos)}",
                f"- Tasa de éxito: {resultado_validacion.tasa_exito:.1f}%",
                f"- Tiempo de procesamiento: {tiempo_procesamiento:.4f}s",
            ]
        )
        return "\n".join(partes)


def validar_lista_ruts(
    ruts: Sequence[str],
    parallel: bool = False,
    max_workers: Optional[int] = None,
) -> Dict[str, List[Union[str, DetalleError]]]:
    """Valida una secuencia de RUTs utilizando ``ProcesadorLotesRut``.

    Args:
        ruts: Colección de cadenas con RUTs a validar.
        parallel: Indica si la validación debe ejecutarse en paralelo.
        max_workers: Cantidad máxima de hilos para el procesamiento
            paralelo. Se delega a
            :class:`concurrent.futures.ThreadPoolExecutor`. Usa el valor por
            defecto del intérprete cuando es ``None``.

    Returns:
        Diccionario con las listas de RUTs válidos e inválidos. Los elementos
        inválidos se representan mediante instancias de :class:`DetalleError`.
    """

    procesador = ProcesadorLotesRut(max_workers=max_workers)
    resultado = procesador.validar_lista_ruts(ruts, parallel=parallel)
    return {"validos": resultado.ruts_validos, "invalidos": resultado.ruts_invalidos}


def formatear_lista_ruts(
    ruts: Sequence[str],
    separador_miles: bool = False,
    mayusculas: bool = False,
    formato: Optional[str] = None,
    parallel: bool = False,
    max_workers: Optional[int] = None,
    **formatter_kwargs: Any,
) -> str:
    """Valida y formatea una secuencia de RUTs.

    Args:
        ruts: Colección de cadenas a procesar.
        separador_miles: Si ``True``, agrega separador de miles al formatear.
        mayusculas: Si ``True``, devuelve el resultado en mayúsculas.
        formato: Identificador de formateador registrado en
            :class:`FabricaFormateadorRut`.
        parallel: Indica si el procesamiento debe ejecutarse en paralelo.
        max_workers: Cantidad máxima de hilos para el procesamiento
            paralelo. Se delega a
            :class:`concurrent.futures.ThreadPoolExecutor`. Usa el valor por
            defecto del intérprete cuando es ``None``.
        **formatter_kwargs: Parámetros adicionales para el formateador
            seleccionado.

    Returns:
        Cadena con el resultado del formateo.
    """

    procesador = ProcesadorLotesRut(max_workers=max_workers)
    return procesador.formatear_lista_ruts(
        ruts,
        separador_miles=separador_miles,
        mayusculas=mayusculas,
        formato=formato,
        parallel=parallel,
        **formatter_kwargs,
    )


def validar_stream_ruts(
    ruts: Iterable[str],
) -> Iterator[Tuple[bool, Union[str, DetalleError]]]:
    """Valida RUTs desde cualquier iterable y produce resultados uno a uno.

    Yields:
        Tuplas ``(es_valido, resultado)`` donde ``resultado`` será la cadena del
        RUT normalizado si la validación es exitosa o una instancia de
        :class:`DetalleError` cuando existe un problema.
    """

    procesador = ProcesadorLotesRut()
    for rut in ruts:
        resultado = procesador.validar_lista_ruts([rut], parallel=False)
        if resultado.ruts_validos:
            yield True, resultado.ruts_validos[0]
        else:
            yield False, resultado.ruts_invalidos[0]


def formatear_stream_ruts(
    ruts: Iterable[str],
    separador_miles: bool = False,
    mayusculas: bool = False,
) -> Iterator[Tuple[bool, Union[str, DetalleError]]]:
    """Valida y formatea RUTs provenientes de cualquier iterable.

    Yields:
        Tuplas ``(es_valido, resultado)`` donde ``resultado`` es la cadena
        formateada o una instancia de :class:`DetalleError` con información del
        fallo.
    """

    asegurar_booleano(separador_miles, "separador_miles")
    asegurar_booleano(mayusculas, "mayusculas")
    procesador = ProcesadorLotesRut()
    for rut in ruts:
        resultado = procesador.validar_lista_ruts([rut], parallel=False)
        if resultado.ruts_validos:
            rut_obj = Rut(resultado.ruts_validos[0], validador=procesador.validador)
            yield True, rut_obj.formatear(
                separador_miles=separador_miles, mayusculas=mayusculas
            )
        else:
            yield False, resultado.ruts_invalidos[0]


def evaluar_rendimiento(num_ruts: int = 10000, parallel: bool = True) -> Dict[str, Any]:
    pruebas = []
    for _ in range(num_ruts):
        base = str(random.randint(1_000_000, 99_999_999))
        dv = calcular_digito_verificador(base)
        pruebas.append(f"{base}-{dv}")

    procesador = ProcesadorLotesRut()
    inicio = time.perf_counter()
    resultado = procesador.validar_lista_ruts(pruebas, parallel=parallel)
    tiempo_validacion = time.perf_counter() - inicio

    inicio = time.perf_counter()
    procesador.formatear_lista_ruts(pruebas[:1000], parallel=parallel)
    tiempo_formato = time.perf_counter() - inicio

    return {
        "test_ruts_count": num_ruts,
        "parallel_processing": parallel,
        "validation_time": tiempo_validacion,
        "validation_rate": num_ruts / tiempo_validacion if tiempo_validacion else 0,
        "formatting_time": tiempo_formato,
        "formatting_rate": 1000 / tiempo_formato if tiempo_formato else 0,
        "tasa_exito": resultado.tasa_exito,
        "estadisticas_cache": Rut.estadisticas_cache(),
    }


__all__ = [
    "DetalleError",
    "ResultadoLote",
    "ProcesadorLotesRut",
    "validar_lista_ruts",
    "formatear_lista_ruts",
    "validar_stream_ruts",
    "formatear_stream_ruts",
    "evaluar_rendimiento",
]
