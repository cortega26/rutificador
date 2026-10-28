"""End-to-end real: Chromium + Pyodide + wheel PyPI, sin mocks.

Se ejecuta exclusivamente con datos sintéticos y comprueba los archivos
descargados en el propio navegador. No requiere datos de usuarios.
"""

import csv
import io
import os
from pathlib import Path

from playwright.sync_api import Error, TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright


URL = os.environ.get("PLAYGROUND_URL", "http://127.0.0.1:8765/guia/playground/")
ARTEFACTOS = Path(os.environ.get("PLAYGROUND_E2E_ARTIFACTS", "artifacts/playground-e2e"))
ARTEFACTOS.mkdir(parents=True, exist_ok=True)

RUT_VALIDO = "12.345.678-5"
RUT_NORMALIZADO = "12345678-5"
RUT_INVALIDO = "12345678-9"
DATOS = (
    "\ufeffRUT,Nombre,Nota\r\n"
    f"{RUT_VALIDO},Persona A,Valor normal\r\n"
    f"{RUT_NORMALIZADO},Persona B,=2+2\r\n"
    f"{RUT_INVALIDO},Persona C,DV incorrecto\r\n"
)


def verificar_csv(ruta: Path) -> None:
    with ruta.open(encoding="utf-8-sig", newline="") as entrada:
        filas = list(csv.reader(entrada))
    assert len(filas) == 4, f"Se esperaban 3 registros, recibidos {len(filas) - 1}"
    assert filas[0] == [
        "RUT", "Nombre", "Nota",
        "rutificador_fila", "rutificador_estado",
        "rutificador_normalizado", "rutificador_errores", "rutificador_duplicado",
    ], filas[0]
    assert filas[1][0:3] == [RUT_VALIDO, "Persona A", "Valor normal"]
    assert filas[2][0:3] == [RUT_NORMALIZADO, "Persona B", "'=2+2"]
    assert filas[3][0:3] == [RUT_INVALIDO, "Persona C", "DV incorrecto"]
    assert filas[1][4:6] == ["valido", RUT_NORMALIZADO]
    assert filas[2][7] == "si" and filas[1][7] == "si"
    assert filas[3][4] == "invalido"
    assert "DV_DISCORDANTE" in filas[3][6]


def verificar_pantalla(page, ancho: int) -> None:
    page.set_viewport_size({"width": ancho, "height": 844})
    page.screenshot(path=str(ARTEFACTOS / f"playground-{ancho}.png"), full_page=True)
    resultado = page.evaluate("""() => ({
        total: document.documentElement.scrollWidth,
        ventana: window.innerWidth,
        archivo: document.querySelector('#rut-csv-archivo').getBoundingClientRect().toJSON(),
        auditar: document.querySelector('#rut-csv-auditar').getBoundingClientRect().toJSON(),
        descarga: document.querySelector('#rut-csv-descargar').getBoundingClientRect().toJSON()
    })""")
    assert resultado["total"] <= resultado["ventana"] + 2, (
        f"Desbordamiento horizontal en {ancho}px: {resultado}"
    )
    for control in ("archivo", "auditar", "descarga"):
        caja = resultado[control]
        assert caja["width"] > 0, (control, caja)
        assert caja["left"] >= -2 and caja["right"] <= ancho + 2, (
            f"{control} sale del viewport {ancho}px: {caja}"
        )


def ejecutar():
    errores_js = []
    solicitudes = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 844})
        page = context.new_page()
        page.on("pageerror", lambda error: errores_js.append(str(error)))

        def registrar(request):
            datos = request.post_data or ""
            solicitudes.append((request.url, datos))
        page.on("request", registrar)

        print(f"Abriendo {URL}")
        page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        expect(page.locator("#rut-validar")).to_be_visible()
        expect(page.locator("#rut-csv-archivo")).to_be_visible()

        # El primer clic descarga Pyodide y rutificador desde la red REAL.
        page.locator("#rut-validar").click()
        expect(page.locator("#rut-salida")).to_contain_text("valido", timeout=150000)
        expect(page.locator("#rut-salida")).to_contain_text(RUT_NORMALIZADO)

        page.locator("#rut-csv-archivo").set_input_files(
            files={"name": "clientes-sinteticos.csv", "mimeType": "text/csv", "buffer": DATOS.encode("utf-8")}
        )
        expect(page.locator("#rut-csv-columna")).to_be_enabled(timeout=10000)
        expect(page.locator("#rut-csv-columna")).to_have_value("RUT")
        page.locator("#rut-csv-auditar").click()
        expect(page.locator("#rut-csv-descargar")).to_be_enabled(timeout=120000)
        expect(page.locator("#rut-csv-resumen")).to_contain_text("Total: 3")
        expect(page.locator("#rut-csv-resumen")).to_contain_text("Válidos: 2")
        expect(page.locator("#rut-csv-resumen")).to_contain_text("Duplicados adicionales: 1")
        with page.expect_download(timeout=20000) as descarga:
            page.locator("#rut-csv-descargar").click()
        ruta = ARTEFACTOS / "rutificador-auditoria-sintetica.csv"
        descarga.value.save_as(ruta)
        verificar_csv(ruta)
        verificar_pantalla(page, 1280)
        verificar_pantalla(page, 390)
        # La aplicación puede descargar bibliotecas, nunca enviar las muestras.
        for url, cuerpo in solicitudes:
            for valor in (RUT_VALIDO, RUT_NORMALIZADO, RUT_INVALIDO,
                          "Persona A", "Persona B", "Persona C"):
                assert valor not in url and valor not in cuerpo, (
                    "Posible exfiltración de datos sintéticos a red", url, valor
                )
        assert not errores_js, f"Excepciones JavaScript: {errores_js}"
        print("PASS: Chromium real, Pyodide, wheel PyPI, auditoría CSV, exportación, privacidad, 390/1280px")
        print(f"Solicitudes de descarga/control (sin datos): {len(solicitudes)}")
        context.close()
        browser.close()


if __name__ == "__main__":
    try:
        ejecutar()
    except (PlaywrightTimeoutError, Error, AssertionError) as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        raise
