# SECURITY-CRITICAL
import logging
import os
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
from .errores import DetalleError, crear_detalle_error
from .exceptions import ErrorRut
from .formatter import FabricaFormateadorRut
from .utils import (
    monitor_de_rendimiento,
    asegurar_booleano,
    calcular_digito_verificador,
)
from .validador import ValidadorRut
from .rut import Rut, ValidacionResultado

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
        max_trabajadores: Optional[int] = None,
        motor_paralelo: Literal["thread", "process"] = "process",
    ) -> None:
        self.validador = validador or ValidadorRut()
        self.max_trabajadores: Optional[int] = max_trabajadores
        self.motor_paralelo = motor_paralelo

    def _clase_ejecutor(self):
        if self.motor_paralelo == "process" and sys.platform == "win32":
            logger.warning(
                "Procesamiento en paralelo con procesos no está soportado en Windows; "
                "usando ThreadPoolExecutor"
            )
            return ThreadPoolExecutor
        return (
            ProcessPoolExecutor
            if self.motor_paralelo == "process"
            else ThreadPoolExecutor
        )

    def _calcular_chunksize(self, n_items: int, max_workers: int) -> int:
        """Calcula un chunksize óptimo para el procesamiento paralelo."""
        if n_items <= 0:
            return 1
        return max(1, min(1000, n_items // (max_workers * 4)))

    @monitor_de_rendimiento
    def validar_lista_ruts(
        self,
        ruts: Sequence[str],
        paralelo: bool = False,
        chunksize: Optional[int] = None,
    ) -> ResultadoLote:
        inicio = time.perf_counter()
        resultado = ResultadoLote()

        if paralelo:
            configuracion = self.validador.configuracion
            modo = self.validador.modo
            cargas = ((cadena, configuracion, modo) for cadena in ruts)
            cls_ejecutor = self._clase_ejecutor()
            n_workers = self.max_trabajadores or (os.cpu_count() or 1)
            c_size = chunksize or self._calcular_chunksize(len(ruts), n_workers)
            
            with cls_ejecutor(max_workers=self.max_trabajadores) as ejecutor:
                resultados = ejecutor.map(_validar_rut_en_proceso, cargas, chunksize=c_size)
        else:
            resultados = (_validar_rut_local(cadena, self.validador) for cadena in ruts)

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

    def flujo(self, ruts: Iterable[Union[str, int]]) -> Iterator[ValidacionResultado]:
        """Procesa RUTs en flujo continuo (streaming) sin materializar el lote completo."""
        for rut in ruts:
            yield Rut.parse(
                rut,
                modo=self.validador.modo,
                configuracion=self.validador.configuracion,
            )

    @monitor_de_rendimiento
    def formatear_lista_ruts(
        self,
        ruts: Sequence[str],
        separador_miles: bool = False,
        mayusculas: bool = False,
        formato: Optional[str] = None,
        paralelo: bool = False,
        **kwargs_formateador: Any,
    ) -> str:
        if not isinstance(ruts, (list, tuple)):
            raise ValueError(
                f"ruts debe ser una secuencia, se recibió: {type(ruts).__name__}"
            )
        asegurar_booleano(separador_miles, "separador_miles")
        asegurar_booleano(mayusculas, "mayusculas")

        resultado_validacion = self.validar_lista_ruts(ruts, paralelo=paralelo)
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

        formateador_detalle = partial(
            _formatear_detalle,
            separador_miles=separador_miles,
            mayusculas=mayusculas,
        )

        if paralelo:
            cls_ejecutor = self._clase_ejecutor()
            with cls_ejecutor(max_workers=self.max_trabajadores) as ejecutor:
                ruts_formateados = list(ejecutor.map(formateador_detalle, fuentes))
        else:
            ruts_formateados = [formateador_detalle(item) for item in fuentes]

        if formato:
            formatter = FabricaFormateadorRut.obtener_formateador(
                formato, **kwargs_formateador
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
    paralelo: bool = False,
    max_trabajadores: Optional[int] = None,
    motor_paralelo: Literal["thread", "process"] = "process",
) -> ResumenValidacion:
    """Valida una secuencia de RUTs utilizando ``ProcesadorLotesRut``."""

    procesador = ProcesadorLotesRut(
        max_trabajadores=max_trabajadores, motor_paralelo=motor_paralelo
    )
    resultado = procesador.validar_lista_ruts(ruts, paralelo=paralelo)
    return {"validos": resultado.ruts_validos, "invalidos": resultado.ruts_invalidos}


def formatear_lista_ruts(
    ruts: Sequence[str],
    separador_miles: bool = False,
    mayusculas: bool = False,
    formato: Optional[str] = None,
    paralelo: bool = False,
    max_trabajadores: Optional[int] = None,
    motor_paralelo: Literal["thread", "process"] = "process",
    **kwargs_formateador: Any,
) -> str:
    """Valida y formatea una secuencia de RUTs."""

    procesador = ProcesadorLotesRut(
        max_trabajadores=max_trabajadores, motor_paralelo=motor_paralelo
    )
    return procesador.formatear_lista_ruts(
        ruts,
        separador_miles=separador_miles,
        mayusculas=mayusculas,
        formato=formato,
        paralelo=paralelo,
        **kwargs_formateador,
    )


def validar_flujo_ruts(
    ruts: Iterable[Union[str, int]],
    paralelo: bool = False,
    max_trabajadores: Optional[int] = None,
    motor_paralelo: Literal["thread", "process"] = "process",
) -> Iterator[Tuple[bool, Union[str, DetalleError]]]:
    """Valida RUTs desde cualquier iterable y produce resultados uno a uno.

    Si paralelo es True, distribuye la carga entre múltiples trabajadores
    manteniendo la naturaleza de generador (no materializa el lote).
    """
    procesador = ProcesadorLotesRut(
        max_trabajadores=max_trabajadores, motor_paralelo=motor_paralelo
    )

    if paralelo:
        configuracion = procesador.validador.configuracion
        modo = procesador.validador.modo
        cargas = ((str(rut), configuracion, modo) for rut in ruts)
        cls_ejecutor = procesador._clase_ejecutor()

        with cls_ejecutor(max_workers=procesador.max_trabajadores) as ejecutor:
            # yield de los resultados conforme los entrega el ejecutor.map (que ya es perezoso)
            for es_valido, detalle in ejecutor.map(_validar_rut_en_proceso, cargas):
                yield es_valido, detalle
    else:
        for rut in ruts:
            es_valido, detalle = _validar_rut_local(str(rut), procesador.validador)
            yield es_valido, detalle


def formatear_flujo_ruts(
    ruts: Iterable[Union[str, int]],
    separador_miles: bool = False,
    mayusculas: bool = False,
    paralelo: bool = False,
    max_trabajadores: Optional[int] = None,
    motor_paralelo: Literal["thread", "process"] = "process",
) -> Iterator[Tuple[bool, Union[str, DetalleError]]]:
    """Valida y formatea RUTs provenientes de cualquier iterable.

    Soporta opcionalmente procesamiento paralelo manteniendo el flujo iterativo.
    """
    asegurar_booleano(separador_miles, "separador_miles")
    asegurar_booleano(mayusculas, "mayusculas")

    # Reutilizamos la lógica de validación de flujo y simplemente mapeamos el formateo
    for es_valido, detalle in validar_flujo_ruts(
        ruts,
        paralelo=paralelo,
        max_trabajadores=max_trabajadores,
        motor_paralelo=motor_paralelo,
    ):
        if es_valido:
            # Si el detalle es de una validación exitosa, es un RutProcesado
            # que ya tiene el método .formatear()
            yield (
                True,
                detalle.formatear(  # type: ignore[union-attr]
                    separador_miles=separador_miles, mayusculas=mayusculas
                ),
            )
        else:
            yield False, detalle


def flujo(ruts: Iterable[Union[str, int]]) -> Iterator[ValidacionResultado]:
    """Procesa RUTs en flujo continuo sin materializar el lote completo."""
    procesador = ProcesadorLotesRut()
    yield from procesador.flujo(ruts)


def evaluar_rendimiento(num_ruts: int = 10000, paralelo: bool = True) -> Dict[str, Any]:
    pruebas = []
    for _ in range(num_ruts):
        base = str(random.randint(1_000_000, 99_999_999))
        dv = calcular_digito_verificador(base)
        pruebas.append(f"{base}-{dv}")

    procesador = ProcesadorLotesRut()
    inicio = time.perf_counter()
    resultado = procesador.validar_lista_ruts(pruebas, paralelo=paralelo)
    tiempo_validacion = time.perf_counter() - inicio

    inicio = time.perf_counter()
    procesador.formatear_lista_ruts(pruebas[:1000], paralelo=paralelo)
    tiempo_formato = time.perf_counter() - inicio

    return {
        "conteo_ruts_prueba": num_ruts,
        "procesamiento_paralelo": paralelo,
        "tiempo_validacion": tiempo_validacion,
        "tasa_validacion": num_ruts / tiempo_validacion if tiempo_validacion else 0,
        "tiempo_formateo": tiempo_formato,
        "tasa_formateo": 1000 / tiempo_formato if tiempo_formato else 0,
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
        codigo = exc.codigo_error or "SIN_CODIGO"
        detalle_error = crear_detalle_error(
            codigo,
            mensaje=str(exc),
            severidad="error",
            recuperable=False,
            rut=str(cadena),
            duracion=time.perf_counter() - inicio,
        )
        return False, detalle_error


def _validar_rut_en_proceso(
    payload: Tuple[str, ConfiguracionRut, RigorValidacion],
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
    "validar_flujo_ruts",
    "formatear_flujo_ruts",
    "evaluar_rendimiento",
    "flujo",
]
