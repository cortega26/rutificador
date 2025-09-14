import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union

from .exceptions import ErrorRut
from .formatter import FabricaFormateadorRut
from .utils import monitor_de_rendimiento, asegurar_booleano, calcular_digito_verificador
from .validador import ValidadorRut
from .rut import Rut

logger = logging.getLogger(__name__)


@dataclass
class ResultadoLote:
    """Contenedor de resultados para operaciones por lotes."""

    ruts_validos: List[str] = field(default_factory=list)
    ruts_invalidos: List[Tuple[str, str]] = field(default_factory=list)
    tiempo_procesamiento: float = 0.0
    total_procesados: int = 0

    @property
    def tasa_exito(self) -> float:
        if self.total_procesados == 0:
            return 0.0
        return (len(self.ruts_validos) / self.total_procesados) * 100


class ProcesadorLotesRut:
    """Servicio para validar y formatear RUTs en lotes."""

    def __init__(self, validador: Optional[ValidadorRut] = None) -> None:
        self.validador = validador or ValidadorRut()

    @monitor_de_rendimiento
    def validar_lista_ruts(
        self, ruts: Sequence[str], parallel: bool = False
    ) -> ResultadoLote:
        inicio = time.perf_counter()
        resultado = ResultadoLote()

        def crear_rut(cadena: str) -> Tuple[bool, Union[str, Tuple[str, str]]]:
            try:
                rut_obj = Rut(cadena, validador=self.validador)
                return True, str(rut_obj)
            except (ErrorRut, ValueError, TypeError) as exc:
                return False, (str(cadena), str(exc))

        if parallel:
            with ThreadPoolExecutor() as executor:
                resultados = list(executor.map(crear_rut, ruts))
            for es_valido, valor in resultados:
                if es_valido:
                    resultado.ruts_validos.append(valor)  # type: ignore[arg-type]
                else:
                    resultado.ruts_invalidos.append(valor)  # type: ignore[arg-type]
        else:
            for cadena in ruts:
                es_valido, valor = crear_rut(cadena)
                if es_valido:
                    resultado.ruts_validos.append(valor)  # type: ignore[arg-type]
                else:
                    resultado.ruts_invalidos.append(valor)  # type: ignore[arg-type]

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
            with ThreadPoolExecutor() as executor:
                ruts_formateados = list(
                    executor.map(formatear_cadena, resultado_validacion.ruts_validos)
                )
        else:
            ruts_formateados = [
                formatear_cadena(cadena)
                for cadena in resultado_validacion.ruts_validos
            ]

        if formato:
            formatter = FabricaFormateadorRut.obtener_formateador(
                formato, **formatter_kwargs
            )
            if not formatter:
                disponibles = FabricaFormateadorRut.obtener_formatos_disponibles()
                raise ValueError(
                    f"Formato '{formato}' no soportado. Formatos disponibles: {disponibles}"
                )
            partes.append(formatter.formatear(ruts_formateados))
        else:
            partes.append("\n".join(ruts_formateados))

        if resultado_validacion.ruts_invalidos:
            partes.append("")
            partes.append("RUTs inválidos:")
            for rut, error in resultado_validacion.ruts_invalidos:
                partes.append(f"{rut} - {error}")

        partes.extend(
            [
                "",
                "Estadísticas de procesamiento:",
                f"- Total procesados: {resultado_validacion.total_procesados}",
                f"- RUTs válidos: {len(resultado_validacion.ruts_validos)}",
                f"- RUTs inválidos: {len(resultado_validacion.ruts_invalidos)}",
                f"- Tasa de éxito: {resultado_validacion.tasa_exito:.1f}%",
                f"- Tiempo de procesamiento: {resultado_validacion.tiempo_procesamiento:.4f}s",
            ]
        )
        return "\n".join(partes)


def validar_lista_ruts(
    ruts: Sequence[str],
) -> Dict[str, List[Union[str, Tuple[str, str]]]]:
    procesador = ProcesadorLotesRut()
    resultado = procesador.validar_lista_ruts(ruts, parallel=False)
    return {"validos": resultado.ruts_validos, "invalidos": resultado.ruts_invalidos}


def formatear_lista_ruts(
    ruts: Sequence[str],
    separador_miles: bool = False,
    mayusculas: bool = False,
    formato: Optional[str] = None,
    parallel: bool = False,
    **formatter_kwargs: Any,
) -> str:
    procesador = ProcesadorLotesRut()
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
) -> Iterator[Tuple[bool, Union[str, Tuple[str, str]]]]:
    """Valida RUTs desde cualquier iterable y produce resultados uno a uno."""

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
) -> Iterator[Tuple[bool, Union[str, Tuple[str, str]]]]:
    """Valida y formatea RUTs provenientes de cualquier iterable."""

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
    "ResultadoLote",
    "ProcesadorLotesRut",
    "validar_lista_ruts",
    "formatear_lista_ruts",
    "validar_stream_ruts",
    "formatear_stream_ruts",
    "evaluar_rendimiento",
]
