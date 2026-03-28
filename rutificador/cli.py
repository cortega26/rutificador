import argparse
import csv
import json
import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, Iterator, List, Optional, Union
from io import StringIO

from .procesador import DetalleError, formatear_stream_ruts, validar_stream_ruts
from .rut import Rut


def _leer_ruts(ruta_archivo: Optional[str]) -> Iterator[str]:
    """Lee RUTs desde un archivo o desde la entrada estándar."""
    if ruta_archivo:

        def _desde_archivo() -> Iterator[str]:
            with open(ruta_archivo, encoding="utf-8") as archivo:
                for linea in archivo:
                    linea = linea.strip()
                    if linea:
                        yield linea

        return _desde_archivo()
    return (linea.strip() for linea in sys.stdin if linea.strip())


def _formatear_error(detalle: DetalleError) -> str:
    codigo = detalle.codigo or "SIN_CODIGO"
    return f"{detalle.rut} [{codigo}] - {detalle.mensaje}"


def _emitir_resultados(resultados: Iterator[tuple[bool, Union[str, DetalleError]]], formato: str) -> int:
    codigo_salida = 0
    datos = []

    for es_valido, resultado in resultados:
        item: Dict[str, Any] = {
            "valido": es_valido,
            "original": "",
            "resultado": "",
            "error_mensaje": "",
            "error_codigo": "",
        }
        if es_valido:
            item["resultado"] = str(resultado)
            item["original"] = str(resultado)
            item["valido"] = True
        else:
            codigo_salida = 1
            item["valido"] = False
            if isinstance(resultado, DetalleError):
                item["original"] = resultado.rut
                item["error_mensaje"] = resultado.mensaje
                item["error_codigo"] = resultado.codigo
            else:
                item["original"] = str(resultado)
                item["error_mensaje"] = str(resultado)
                item["error_codigo"] = "ERROR"
        
        if formato == "text":
            if es_valido:
                print(item["resultado"])
            else:
                print(f"{item['original']} [{item['error_codigo']}] - {item['error_mensaje']}", file=sys.stderr)
        else:
            datos.append(item)

    if formato == "json":
        print(json.dumps(datos, indent=2, ensure_ascii=False))
    elif formato == "csv":
        if datos:
            escritor = csv.DictWriter(sys.stdout, fieldnames=datos[0].keys())
            escritor.writeheader()
            escritor.writerows(datos)
    elif formato == "xml":
        raiz = ET.Element("rutificador")
        for d in datos:
            reg = ET.SubElement(raiz, "registro")
            for k, v in d.items():
                elem = ET.SubElement(reg, k)
                elem.text = str(v)
        print(ET.tostring(raiz, encoding="unicode"))

    return codigo_salida


def _comando_validar(args: argparse.Namespace) -> int:
    return _emitir_resultados(validar_stream_ruts(_leer_ruts(args.archivo)), args.format)


def _comando_formatear(args: argparse.Namespace) -> int:
    resultados = formatear_stream_ruts(
        _leer_ruts(args.archivo),
        separador_miles=args.separador_miles,
        mayusculas=args.mayusculas,
    )
    return _emitir_resultados(resultados, args.format)


def _comando_mask(args: argparse.Namespace) -> int:
    codigo_salida = 0
    for rut_str in _leer_ruts(args.archivo):
        try:
            resultado = Rut.mask(
                rut_str,
                keep=args.keep,
                char=args.char,
                separador_miles=args.separador_miles,
                mayusculas=args.mayusculas,
            )
            print(resultado)
        except Exception as exc:
            codigo_salida = 1
            print(f"{rut_str} [ERROR] - {str(exc)}", file=sys.stderr)
    return codigo_salida


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rutificador")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    parser_validar = subparsers.add_parser(
        "validar", help="Valida RUTs desde archivo o stdin"
    )
    parser_validar.add_argument(
        "archivo", nargs="?", help="Ruta de archivo con RUTs (uno por línea)"
    )
    parser_validar.add_argument(
        "--format",
        choices=["text", "json", "csv", "xml"],
        default="text",
        help="Formato de salida (default: text)",
    )
    parser_validar.set_defaults(func=_comando_validar)

    parser_formatear = subparsers.add_parser(
        "formatear",
        help="Valida y formatea RUTs",
    )
    parser_formatear.add_argument(
        "archivo", nargs="?", help="Ruta de archivo con RUTs (uno por línea)"
    )
    parser_formatear.add_argument(
        "--separador-miles",
        action="store_true",
        help="Agrega separador de miles",
    )
    parser_formatear.add_argument(
        "--mayusculas",
        action="store_true",
        help="Convierte el resultado a mayúsculas",
    )
    parser_formatear.add_argument(
        "--format",
        choices=["text", "json", "csv", "xml"],
        default="text",
        help="Formato de salida (default: text)",
    )
    parser_formatear.set_defaults(func=_comando_formatear)

    parser_mask = subparsers.add_parser(
        "mask", help="Enmascara RUTs válidos"
    )
    parser_mask.add_argument(
        "archivo", nargs="?", help="Ruta de archivo con RUTs (uno por línea)"
    )
    parser_mask.add_argument(
        "--keep",
        type=int,
        default=4,
        help="Número de dígitos a mantener al final (default: 4)",
    )
    parser_mask.add_argument(
        "--char", default="*", help="Carácter de enmascarado (default: *)"
    )
    parser_mask.add_argument(
        "--separador-miles",
        action="store_true",
        help="Agrega separador de miles al resultado",
    )
    parser_mask.add_argument(
        "--mayusculas",
        action="store_true",
        help="Convierte el resultado a mayúsculas",
    )
    parser_mask.set_defaults(func=_comando_mask)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _crear_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
