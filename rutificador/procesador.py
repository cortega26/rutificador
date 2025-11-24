import logging
import random
import time
import sys
from functools import partial
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    Union,
)

from .config import ConfiguracionRut, RigorValidacion
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
class RutProcesado:
    """Representa un RUT validado con metadatos adicionales."""

    valor: str
    base: str
    digito: str
    validador_modo: str
    duracion: float = 0.0

    def formatear(
        self,
        separador_miles: bool = False,
        mayusculas: bool = False,
        separador_personalizado: str = ".",
    ) -> str:
        """Formatea el RUT reutilizando la información ya validada."""
        resultado = self.valor
        if separador_miles:
            base_formateada = Rut.agregar_separador_miles(
                self.base, separador_personalizado
            )
            resultado = f"{base_formateada}-{self.digito}"
        if mayusculas:
            resultado = resultado.upper()
        return resultado


@dataclass
class DetalleError:
    """Representa un error asociado a un RUT específico, incluyendo su código."""

    rut: str
    codigo: Optional[str]
    mensaje: str
    duracion: float = 0.0

    def __eq__(self, other: object) -> bool:  # pragma: no cover - comparación simple
        if not isinstance(other, DetalleError):
            return NotImplemented
        # Se ignora la duración porque varía entre ejecuciones y backends
        return (
            self.rut,
            self.codigo,
            self.mensaje,
        ) == (
            other.rut,
            other.codigo,
            other.mensaje,
        )


@dataclass
class ResultadoLote:
    """Contenedor de resultados para operaciones por lotes."""

    detalles_validos: List[RutProcesado] = field(default_factory=list)
    ruts_validos: List[str] = field(default_factory=list)
    ruts_invalidos: List[DetalleError] = field(default_factory=list)
    tiempo_procesamiento: float = 0.0
    total_procesados: int = 0

    @property
    def tasa_exito(self) -> float:
        if self.total_procesados == 0:
            return 0.0
        return (len(self.ruts_validos) / self.total_procesados) * 100


class ResumenValidacion(TypedDict):
    """Resumen tipado del resultado de ``validar_lista_ruts``."""

    validos: List[str]
    invalidos: List[DetalleError]


class ProcesadorLotesRut:
    """Servicio para validar y formatear RUTs en lotes."""

    def __init__(
        self,
        validador: Optional[ValidadorRut] = None,
        max_workers: Optional[int] = None,
        parallel_backend: Literal["thread", "process"] = "process",
    ) -> None:
        self.validador = validador or ValidadorRut()
        self.max_workers: Optional[int] = max_workers
        self.parallel_backend = parallel_backend

    def _executor_class(self):
        if self.parallel_backend == "process" and sys.platform == "win32":
            logger.warning(
                "Procesamiento en paralelo con procesos no está soportado en Windows; "
                "usando ThreadPoolExecutor"
            )
            return ThreadPoolExecutor
        return ProcessPoolExecutor if self.parallel_backend == "process" else ThreadPoolExecutor

    @monitor_de_rendimiento
    def validar_lista_ruts(
        self, ruts: Sequence[str], parallel: bool = False
    ) -> ResultadoLote:
        inicio = time.perf_counter()
        resultado = ResultadoLote()

        if parallel:
            configuracion = self.validador.configuracion
            modo = self.validador.modo
            payloads = ((cadena, configuracion, modo) for cadena in ruts)
            executor_cls = self._executor_class()
            with executor_cls(max_workers=self.max_workers) as executor:
                resultados = executor.map(_validar_rut_en_proceso, payloads)
        else:
            resultados = (
                _validar_rut_local(cadena, self.validador) for cadena in ruts
            )

        for es_valido, valor in resultados:
            if es_valido:
                detalle = valor  # RutProcesado
                resultado.ruts_validos.append(detalle.valor)
                resultado.detalles_validos.append(detalle)
            else:
                resultado.ruts_invalidos.append(valor)

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
        fuentes = resultado_validacion.detalles_validos

        if not fuentes:
            fuentes = [
                RutProcesado(
                    valor=cadena,
                    base=cadena.split("-")[0],
                    digito=cadena.split("-")[-1],
                    validador_modo=self.validador.modo.value,
                )
                for cadena in resultado_validacion.ruts_validos
            ]

        def aplicar_formato(detalle: RutProcesado) -> str:
            return detalle.formatear(
                separador_miles=separador_miles, mayusculas=mayusculas
            )

        formateador_detalle = partial(
            _formatear_detalle,
            separador_miles=separador_miles,
            mayusculas=mayusculas,
        )

        if parallel:
            executor_cls = self._executor_class()
            with executor_cls(max_workers=self.max_workers) as executor:
                ruts_formateados = list(executor.map(formateador_detalle, fuentes))
        else:
            ruts_formateados = [formateador_detalle(item) for item in fuentes]

        if formato:
            formatter = FabricaFormateadorRut.obtener_formateador(
                formato, **formatter_kwargs
            )
            if not formatter:
                disponibles = FabricaFormateadorRut.obtener_formatos_disponibles()
                raise ValueError(
                    f"Formato '{formato}' no soportado. "
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
    parallel_backend: Literal["thread", "process"] = "process",
) -> ResumenValidacion:
    """Valida una secuencia de RUTs utilizando ``ProcesadorLotesRut``."""

    procesador = ProcesadorLotesRut(
        max_workers=max_workers, parallel_backend=parallel_backend
    )
    resultado = procesador.validar_lista_ruts(ruts, parallel=parallel)
    return {"validos": resultado.ruts_validos, "invalidos": resultado.ruts_invalidos}


def formatear_lista_ruts(
    ruts: Sequence[str],
    separador_miles: bool = False,
    mayusculas: bool = False,
    formato: Optional[str] = None,
    parallel: bool = False,
    max_workers: Optional[int] = None,
    parallel_backend: Literal["thread", "process"] = "process",
    **formatter_kwargs: Any,
) -> str:
    """Valida y formatea una secuencia de RUTs."""

    procesador = ProcesadorLotesRut(
        max_workers=max_workers, parallel_backend=parallel_backend
    )
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
    """Valida RUTs desde cualquier iterable y produce resultados uno a uno."""

    procesador = ProcesadorLotesRut()
    for rut in ruts:
        resultado = procesador.validar_lista_ruts([rut], parallel=False)
        if resultado.detalles_validos:
            yield True, resultado.detalles_validos[0].valor
        else:
            yield False, resultado.ruts_invalidos[0]


def formatear_stream_ruts(
    ruts: Iterable[str],
    separador_miles: bool = False,
    mayusculas: bool = False,
) -> Iterator[Tuple[bool, Union[str, DetalleError]]]:
    """Valida y formatea RUTs provenientes de cualquier iterable."""

    asegurar_booleano(separador_miles, "separador_miles")
    asegurar_booleano(mayusculas, "mayusculas")
    procesador = ProcesadorLotesRut()
    for rut in ruts:
        resultado = procesador.validar_lista_ruts([rut], parallel=False)
        if resultado.detalles_validos:
            yield True, resultado.detalles_validos[0].formatear(
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


def _validar_rut_local(
    cadena: str, validador: ValidadorRut
) -> Tuple[bool, Union[RutProcesado, DetalleError]]:
    inicio = time.perf_counter()
    try:
        rut_obj = Rut(cadena, validador=validador)
        detalle = RutProcesado(
            valor=str(rut_obj),
            base=str(rut_obj.base),
            digito=rut_obj.digito_verificador,
            validador_modo=validador.modo.value,
            duracion=time.perf_counter() - inicio,
        )
        return True, detalle
    except ErrorRut as exc:
        return False, DetalleError(
            rut=str(cadena),
            codigo=exc.error_code,
            mensaje=str(exc),
            duracion=time.perf_counter() - inicio,
        )
    except Exception:
        # Re-lanzamos para evitar silenciar fallos de programación o configuraciones corruptas
        raise


def _validar_rut_en_proceso(
    payload: Tuple[str, ConfiguracionRut, RigorValidacion]
) -> Tuple[bool, Union[RutProcesado, DetalleError]]:
    cadena, configuracion, modo = payload
    validador = ValidadorRut(configuracion=configuracion, modo=modo)
    return _validar_rut_local(cadena, validador)

def _formatear_detalle(
    detalle: RutProcesado, separador_miles: bool, mayusculas: bool
) -> str:
    """Función separada para permitir pickling en ejecución con procesos."""
    return detalle.formatear(
        separador_miles=separador_miles,
        mayusculas=mayusculas,
    )


__all__ = [
    "DetalleError",
    "RutProcesado",
    "ResultadoLote",
    "ProcesadorLotesRut",
    "validar_lista_ruts",
    "formatear_lista_ruts",
    "validar_stream_ruts",
    "formatear_stream_ruts",
    "evaluar_rendimiento",
]
