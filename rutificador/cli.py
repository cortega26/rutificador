import argparse
import csv
import json
import sys
import time
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Union

from .procesador import (
    DetalleError,
    RutProcesado,
    formatear_flujo_ruts,
    validar_flujo_ruts,
)
from .rut import Rut
from .version import obtener_informacion_version


def _leer_ruts(ruta_archivo: Optional[str]) -> Iterator[str]:
    """Lee RUTs desde un archivo o desde la entrada estándar."""
    if ruta_archivo:
        try:

            def _desde_archivo() -> Iterator[str]:
                with open(ruta_archivo, encoding="utf-8") as archivo:
                    for linea in archivo:
                        linea = linea.strip()
                        if linea:
                            yield linea

            return _desde_archivo()
        except FileNotFoundError:
            print(f"Error: archivo no encontrado — '{ruta_archivo}'", file=sys.stderr)
            sys.exit(1)
        except UnicodeDecodeError:
            print(
                f"Error: el archivo '{ruta_archivo}' no es un texto UTF-8 válido",
                file=sys.stderr,
            )
            sys.exit(1)
    return (linea.strip() for linea in sys.stdin if linea.strip())


def _formatear_error(detalle: DetalleError) -> str:
    codigo = detalle.codigo or "SIN_CODIGO"
    return f"{detalle.rut} [{codigo}] - {detalle.mensaje}"


class _EstrategiaEmision(ABC):
    """Estrategia base para emitir resultados en diferentes formatos."""

    def __init__(self) -> None:
        self.primer_elemento = True

    @abstractmethod
    def iniciar(self) -> None:
        """Pre-emisión antes del bucle."""

    @abstractmethod
    def emitir(self, item: Dict[str, Any]) -> None:
        """Emite un elemento individual."""

    @abstractmethod
    def finalizar(self, metadata: Dict[str, Any]) -> None:
        """Post-emisión y metadatos."""


class _EmisionTexto(_EstrategiaEmision):
    def iniciar(self) -> None:
        pass

    def emitir(self, item: Dict[str, Any]) -> None:
        if item["valido"]:
            print(item["resultado"])
        else:
            msg = (
                f"{item['original']} [{item['codigo_error']}] - {item['mensaje_error']}"
            )
            if item["sugerencia"]:
                msg += f" (¿Quisiste decir {item['sugerencia']}?)"
            print(msg, file=sys.stderr)

    def finalizar(self, metadata: Dict[str, Any]) -> None:
        print("\n--- RESUMEN DE AUDITORÍA ---", file=sys.stderr)
        for k, v in metadata["audit"].items():
            print(f"{k.capitalize()}: {v}", file=sys.stderr)


class _EmisionJSON(_EstrategiaEmision):
    def iniciar(self) -> None:
        print("[", end="", flush=True)

    def emitir(self, item: Dict[str, Any]) -> None:
        if not self.primer_elemento:
            print(",", end="")
        print(json.dumps(item, ensure_ascii=False), end="")
        self.primer_elemento = False

    def finalizar(self, metadata: Dict[str, Any]) -> None:
        print("]")
        print(json.dumps(metadata, indent=2, ensure_ascii=False), file=sys.stderr)


class _EmisionJSONL(_EstrategiaEmision):
    def iniciar(self) -> None:
        pass

    def emitir(self, item: Dict[str, Any]) -> None:
        print(json.dumps(item, ensure_ascii=False))

    def finalizar(self, metadata: Dict[str, Any]) -> None:
        print(json.dumps(metadata, ensure_ascii=False), file=sys.stderr)


class _EmisionCSV(_EstrategiaEmision):
    def __init__(self) -> None:
        super().__init__()
        self._escritor: Optional[csv.DictWriter] = None

    def iniciar(self) -> None:
        pass

    def emitir(self, item: Dict[str, Any]) -> None:
        # Mitigación de inyección de fórmulas (CSV injection)
        item_csv = {
            k: f"'{v}"
            if isinstance(v, str) and v and v[0] in {"=", "+", "-", "@"}
            else v
            for k, v in item.items()
        }
        if self._escritor is None:
            self._escritor = csv.DictWriter(sys.stdout, fieldnames=item_csv.keys())
            self._escritor.writeheader()
        self._escritor.writerow(item_csv)

    def finalizar(self, metadata: Dict[str, Any]) -> None:
        pass


class _EmisionXML(_EstrategiaEmision):
    def iniciar(self) -> None:
        print("<rutificador>", flush=True)

    def emitir(self, item: Dict[str, Any]) -> None:
        reg = ET.Element("registro")
        for k, v in item.items():
            elem = ET.SubElement(reg, k)
            elem.text = str(v)
        print(ET.tostring(reg, encoding="unicode"), end="")

    def finalizar(self, metadata: Dict[str, Any]) -> None:
        print("</rutificador>")
        print(f"<!-- Audit: {metadata['audit']} -->", file=sys.stderr)


_ESTRATEGIAS_FORMATO: Dict[str, type] = {
    "text": _EmisionTexto,
    "json": _EmisionJSON,
    "jsonl": _EmisionJSONL,
    "csv": _EmisionCSV,
    "xml": _EmisionXML,
}


def _emitir_resultados(
    resultados: Iterator[tuple[bool, Union[str, RutProcesado, DetalleError]]],
    formato: str,
    usar_sugerencias: bool = False,
    quiet: bool = False,
) -> int:
    codigo_salida = 0
    total = 0
    validos = 0
    inicio_audit = time.perf_counter()

    estrategia_cls = _ESTRATEGIAS_FORMATO.get(formato)
    if not estrategia_cls:
        raise ValueError(f"Formato no soportado: {formato}")
    estrategia = estrategia_cls()
    estrategia.iniciar()

    for es_valido, resultado in resultados:
        total += 1
        item: Dict[str, Any] = {
            "valido": es_valido,
            "original": "",
            "resultado": "",
            "mensaje_error": "",
            "codigo_error": "",
            "sugerencia": "",
        }
        if es_valido:
            validos += 1
            if isinstance(resultado, RutProcesado):
                item["resultado"] = resultado.valor
                item["original"] = resultado.valor
            else:
                item["resultado"] = str(resultado)
                item["original"] = str(resultado)
        else:
            codigo_salida = 1
            if isinstance(resultado, DetalleError):
                item["original"] = resultado.rut
                item["mensaje_error"] = resultado.mensaje
                item["codigo_error"] = resultado.codigo
                if usar_sugerencias and resultado.rut is not None:
                    sugerencias = Rut.sugerir(resultado.rut)
                    if sugerencias:
                        item["sugerencia"] = sugerencias[0]
            else:
                item["original"] = str(resultado)
                item["mensaje_error"] = str(resultado)
                item["codigo_error"] = "ERROR"

        estrategia.emitir(item)

    final_audit = time.perf_counter()
    metadata = {
        "audit": {
            "version": obtener_informacion_version()["version"],
            "total": total,
            "validos": validos,
            "invalidos": total - validos,
            "tiempo_segundos": round(final_audit - inicio_audit, 4),
            "tasa_exito": f"{(validos / total * 100):.1f}%" if total > 0 else "0%",
        }
    }

    if not quiet:
        estrategia.finalizar(metadata)

    return codigo_salida


def _procesar_con_mejorar(ruts: Iterator[str], mejorar: bool = False) -> Iterator[str]:
    """Intercala la mejora automática en el flujo de entrada si está activa."""
    for rut in ruts:
        if mejorar:
            mejorado = Rut.mejorar(rut)
            yield mejorado if mejorado else rut
        else:
            yield rut


def _comando_validar(args: argparse.Namespace) -> int:
    ruts = _leer_ruts(args.archivo)
    ruts_procesados = _procesar_con_mejorar(ruts, args.mejorar)

    resultados = validar_flujo_ruts(
        ruts_procesados,
        paralelo=args.paralelo,
    )
    return _emitir_resultados(
        resultados, args.format, usar_sugerencias=args.sugerir, quiet=args.quiet
    )


def _comando_formatear(args: argparse.Namespace) -> int:
    ruts = _leer_ruts(args.archivo)
    ruts_procesados = _procesar_con_mejorar(ruts, args.mejorar)

    resultados = formatear_flujo_ruts(
        ruts_procesados,
        separador_miles=args.separador_miles,
        mayusculas=args.mayusculas,
        paralelo=args.paralelo,
    )
    return _emitir_resultados(
        resultados, args.format, usar_sugerencias=args.sugerir, quiet=args.quiet
    )


def _comando_enmascarar(args: argparse.Namespace) -> int:
    codigo_salida = 0
    ruts = _leer_ruts(args.archivo)
    for rut_str in ruts:
        try:
            resultado = Rut.enmascarar(
                rut_str,
                mantener=args.mantener,
                caracter=args.caracter,
                separador_miles=args.separador_miles,
                mayusculas=args.mayusculas,
            )
            print(resultado)
        except Exception as exc:
            codigo_salida = 1
            print(f"{rut_str} [ERROR] - {str(exc)}", file=sys.stderr)
    return codigo_salida


def _comando_info(args: argparse.Namespace) -> int:
    info = obtener_informacion_version()
    if args.format == "json":
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print(f"--- RUTIFICADOR v{info['version']} ---")
        print(f"Descripción: {info['descripcion']}")
        print(f"Autor: {info['autor']}")
        print(f"Licencia: {info['licencia']}")
        print("\nFuncionalidades principales:")
        for func in info["funcionalidades"]:
            print(f"  - {func}")
        print(f"\nEntorno: Python {sys.version.split()[0]}")
    return 0


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rutificador")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    # Comunes
    for sub in ["validar", "formatear"]:
        p = subparsers.add_parser(sub)
        p.add_argument("archivo", nargs="?", help="Ruta de archivo con RUTs")
        p.add_argument(
            "--format",
            choices=["text", "json", "jsonl", "csv", "xml"],
            default="text",
            help="Formato de salida",
        )
        p.add_argument("--paralelo", action="store_true", help="Procesamiento paralelo")
        p.add_argument(
            "--mejorar", action="store_true", help="Auto-corrección inteligente"
        )
        p.add_argument(
            "--sugerir", action="store_true", help="Incluir sugerencias en la salida"
        )
        p.add_argument(
            "--quiet", "-q", action="store_true", help="Suprime el resumen de auditoría"
        )
        if sub == "validar":
            p.set_defaults(func=_comando_validar)
        else:
            p.add_argument("--separador-miles", action="store_true")
            p.add_argument("--mayusculas", action="store_true")
            p.set_defaults(func=_comando_formatear)

    parser_enmascarar = subparsers.add_parser("enmascarar")
    parser_enmascarar.add_argument("archivo", nargs="?")
    parser_enmascarar.add_argument("--mantener", type=int, default=4)
    parser_enmascarar.add_argument("--caracter", default="*")
    parser_enmascarar.add_argument("--separador-miles", action="store_true")
    parser_enmascarar.add_argument("--mayusculas", action="store_true")
    parser_enmascarar.set_defaults(func=_comando_enmascarar)

    parser_info = subparsers.add_parser("info")
    parser_info.add_argument(
        "--format", choices=["text", "json"], default="text", help="Formato de salida"
    )
    parser_info.set_defaults(func=_comando_info)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _crear_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
