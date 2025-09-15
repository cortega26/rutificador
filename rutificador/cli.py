import argparse
import sys
from typing import List, Optional

from .procesador import validar_stream_ruts, formatear_stream_ruts


def _leer_ruts(ruta_archivo: Optional[str]) -> List[str]:
    """Lee RUTs desde un archivo o desde la entrada estándar."""
    if ruta_archivo:
        with open(ruta_archivo, encoding="utf-8") as archivo:
            return [linea.strip() for linea in archivo if linea.strip()]
    return [linea.strip() for linea in sys.stdin if linea.strip()]


def _comando_validar(args: argparse.Namespace) -> int:
    ruts = _leer_ruts(args.archivo)
    codigo_salida = 0
    for es_valido, resultado in validar_stream_ruts(ruts):
        if es_valido:
            print(resultado)
        else:
            codigo_salida = 1
            rut, error = resultado
            print(f"{rut} - {error}", file=sys.stderr)
    return codigo_salida


def _comando_formatear(args: argparse.Namespace) -> int:
    ruts = _leer_ruts(args.archivo)
    codigo_salida = 0
    for es_valido, resultado in formatear_stream_ruts(
        ruts,
        separador_miles=args.separador_miles,
        mayusculas=args.mayusculas,
    ):
        if es_valido:
            print(resultado)
        else:
            codigo_salida = 1
            rut, error = resultado
            print(f"{rut} - {error}", file=sys.stderr)
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
    parser_formatear.set_defaults(func=_comando_formatear)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _crear_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
