import argparse
import csv
import json
import sys
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, Iterator, List, Optional, Union

from .procesador import (
    DetalleError,
    RutProcesado,
    formatear_flujo_ruts,
    validar_flujo_ruts,
)
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


def _emitir_resultados(
    resultados: Iterator[tuple[bool, Union[str, DetalleError]]],
    formato: str,
    usar_sugerencias: bool = True,
) -> int:
    codigo_salida = 0
    total = 0
    validos = 0
    inicio_audit = time.perf_counter()

    # Pre-emisión según formato
    if formato == "json":
        print("[", end="", flush=True)
    elif formato == "xml":
        print("<rutificador>", flush=True)
    elif formato == "csv":
        # La cabecera se escribe en el primer elemento o antes
        pass

    escritor_csv = None
    primer_elemento = True

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
                if usar_sugerencias:
                    sugerencias = Rut.sugerir(resultado.rut)
                    if sugerencias:
                        item["sugerencia"] = sugerencias[0]
            else:
                item["original"] = str(resultado)
                item["mensaje_error"] = str(resultado)
                item["codigo_error"] = "ERROR"

        # Emisión incremental
        if formato == "text":
            if es_valido:
                print(item["resultado"])
            else:
                msg = f"{item['original']} [{item['codigo_error']}] - {item['mensaje_error']}"
                if item["sugerencia"]:
                    msg += f" (¿Quisiste decir {item['sugerencia']}?)"
                print(msg, file=sys.stderr)

        elif formato == "json":
            if not primer_elemento:
                print(",", end="")
            print(json.dumps(item, ensure_ascii=False), end="")

        elif formato == "jsonl":
            print(json.dumps(item, ensure_ascii=False))

        elif formato == "csv":
            if escritor_csv is None:
                escritor_csv = csv.DictWriter(sys.stdout, fieldnames=item.keys())
                escritor_csv.writeheader()
            escritor_csv.writerow(item)

        elif formato == "xml":
            reg = ET.Element("registro")
            for k, v in item.items():
                elem = ET.SubElement(reg, k)
                elem.text = str(v)
            print(ET.tostring(reg, encoding="unicode"), end="")

        primer_elemento = False

    # Post-emisión y Metadatos de Auditoría
    final_audit = time.perf_counter()
    metadata = {
        "audit": {
            "version": "1.4.0",
            "total": total,
            "validos": validos,
            "invalidos": total - validos,
            "tiempo_segundos": round(final_audit - inicio_audit, 4),
            "tasa_exito": f"{(validos / total * 100):.1f}%" if total > 0 else "0%",
        }
    }

    if formato == "json":
        print("]")
        print(json.dumps(metadata, indent=2, ensure_ascii=False), file=sys.stderr)
    elif formato == "jsonl":
        print(json.dumps(metadata, ensure_ascii=False))
    elif formato == "xml":
        print("</rutificador>")
        print(f"<!-- Audit: {metadata['audit']} -->", file=sys.stderr)
    elif formato == "text":
        print("\n--- RESUMEN DE AUDITORÍA ---")
        for k, v in metadata["audit"].items():
            print(f"{k.capitalize()}: {v}")

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
    return _emitir_resultados(resultados, args.format)


def _comando_formatear(args: argparse.Namespace) -> int:
    ruts = _leer_ruts(args.archivo)
    ruts_procesados = _procesar_con_mejorar(ruts, args.mejorar)

    resultados = formatear_flujo_ruts(
        ruts_procesados,
        separador_miles=args.separador_miles,
        mayusculas=args.mayusculas,
        paralelo=args.paralelo,
    )
    return _emitir_resultados(resultados, args.format)


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

    return parser

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _crear_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
