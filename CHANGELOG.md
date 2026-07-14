# Historial de Cambios (Changelog)

Todas las modificaciones notables de este proyecto se documentarán en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y este proyecto adhiere a la [Semántica de Versiones](https://semver.org/lang/es/).

## [1.9.0] - 2026-07-14

### Añadido

- [FEAT] CLI: subcomando `enmascarar` ahora soporta tokenización HMAC-SHA256 con los flags `--token` y `--clave` (y variable de entorno `RUTIFICADOR_TOKEN_KEY`).
- [DOC] Especificación formal de reglas de validación RUT con test vectors canónicos en JSON (`docs/especificacion-reglas-rut.md`, `tests/vectors/`).
- [I18N] Infraestructura de internacionalización en `crear_detalle_error(idioma="es"|"en")`. Catálogo en español e inglés con fallback automático.

### Calidad

- [TYPES] `mypy --strict` habilitado en 5 módulos del núcleo: `errores.py`, `version.py`, `config.py`, `utils.py`, `validador.py`. CI verifica estricto en esos módulos.

### Documentación

- [DOC] MkDocs desplegado en GitHub Pages: `tooltician.com/rutificador/`.
- [DOC] `workflow_dispatch` agregado al workflow de documentación para despliegues manuales.

## [1.8.0] - 2026-06-20

### Añadido

- [DEVOPS] Workflow de regresión de rendimiento en CI: benchmarks comparados contra rama base con umbral de 20% (no bloqueante).
- [DEVOPS] Workflow de despliegue de documentación MkDocs a GitHub Pages.

### Calidad

- [DEVOPS] Python 3.14 en matriz CI con `continue-on-error`.

### Documentación

- [DOC] Sitio de documentación con MkDocs Material: API reference desde docstrings, buscador, ejemplos interactivos.

## [1.7.0] - 2026-06-20

### Calidad

- [DEVOPS] `import-linter` adoptado: 3 contratos de arquitectura (`nucleo-no-depende-de-contrib`, `nucleo-no-depende-de-cli`, `contrib-no-depende-entre-si`) en `pyproject.toml`.
- [DEVOPS] `mutmut` (mutation testing) evaluado y rechazado: incompatible con Python 3.12.
- [DEVOPS] `pyperf` evaluado y rechazado: `pytest-benchmark` ofrece mejor integración.
- [DEVOPS] `uv` evaluado y rechazado: incompatible con Poetry lockfile.

## [1.6.1] - 2026-06-20

### Mantenimiento

- [DEVOPS] Añadidos `deptry`, `pytest-benchmark`, `cyclonedx-bom`, `pre-commit` y `httpx2` como dependencias exclusivas de desarrollo, sin modificar las dependencias de instalación del núcleo; `httpx2` elimina la advertencia obsoleta de `TestClient` en Starlette reciente.
- [DEVOPS] CI valida la coherencia de dependencias y la configuración de pre-commit; el flujo de seguridad genera y conserva un SBOM CycloneDX reproducible.
- [DEVOPS] Migrada la configuración obsoleta `poetry.dev-dependencies` a `poetry.group.dev.dependencies` y eliminado `tomli`, que no era utilizado, para conservar un núcleo sin dependencias también en Python 3.10.

### Tests

- [TEST] Benchmark funcional de `Rut.parse()` para verificar la integración de `pytest-benchmark` y habilitar futuras líneas base de rendimiento.

## [1.6.0] - 2026-06-12

### Rendimiento

- [PERF] `validar_flujo_ruts` y `formatear_flujo_ruts` en modo `paralelo=True` ahora usan `chunksize=256` por defecto en `Executor.map`, eliminando un overhead de ~10× respecto al modo serial que se producía con el valor por defecto `chunksize=1`. El parámetro `chunksize` queda expuesto como kwarg opcional en ambas funciones para ajuste manual.
- [PERF] Constante pública `CHUNKSIZE_FLUJO_POR_DEFECTO = 256` añadida a `procesador.py`.

### Deprecaciones

- [DEPRECATED] `RigorValidacion.LEGADO` ahora emite `DeprecationWarning` al usarse en `ValidadorRut`, `Rut.parse` y `Rut.normalizar`. El valor se eliminará en v2.0; usar `RigorValidacion.FLEXIBLE` en su lugar.

### Calidad

- [REFACTOR] Rama muerta eliminada de `formatear_lista_ruts`: el bloque `if not fuentes` reconstruía `RutProcesado` desde `ruts_validos`, pero ambas listas siempre se llenan en paralelo por `validar_lista_ruts`, por lo que el bloque era inalcanzable.

### Documentación

- [DOC] Contrato builder/classifier documentado en `Rut`, `Rut.__init__` y `Rut.parse`: el constructor normaliza la entrada y lanza excepciones tipadas; `parse()` clasifica bajo el `modo` indicado y devuelve un `ValidacionResultado`. Actualizado también en `CLAUDE.md`.
- [DOC] `RigorValidacion` con docstring de clase que define la semántica de cada modo (`ESTRICTO`, `FLEXIBLE`, `LEGADO` obsoleto).

### Tests

- [TEST] `tests/test_procesador_flujo.py`: tests de regresión para la corrección de `chunksize`; incluye un caso con generador puro (sin `__len__`) que garantiza que no se llame `len()` sobre el iterable de flujo.
- [TEST] `tests/test_consistencia_parse.py`: tests de caracterización que fijan el contrato constructor↔`parse()`; incluye tests de deprecación de `LEGADO` y el test de contrato builder/classifier.
- [TEST] `tests/test_procesador_paralelo.py`: cobertura de las ramas paralelas de `ProcesadorLotesRut.validar_lista_ruts`.

## [1.5.8] - 2026-05-14

### Mantenimiento

- [DEVOPS] Workflows CI consolidados: `quality.yml` fusionado dentro de `ci.yml` como job independiente; ejecución de tests reducida a 1 pasada (antes eran 2: cobertura + deprecaciones); `security.yml` simplificado de 3 auditorías pip-audit a 1; `pylint.yml` y `repo-hygiene-gate.yml` eliminados.
- [DEVOPS] Dependencias muertas eliminadas de `requirements-dev.txt`: `black` (reemplazado por `ruff format`), `requests` y `zipp` (pins transitivos de Snyk).
- [DEVOPS] `dependency-review-action` actualizado a v5; Python de quality/security estandarizado a 3.13.
- [CLEANUP] Código muerto eliminado de `config.py`: alias `RutConfig` y `__getattr__` deprecado que era inalcanzable (la deprecación ya se maneja en `__init__.py`).
- [CLEANUP] `pylintrc` eliminado (pylint reemplazado por `ruff check`).
- [CLEANUP] `coverage.lcov` añadido a `.gitignore`.

### Documentación

- [DOC] README reestructurado: mejor jerarquía visual con separadores, secciones reorganizadas en orden progresivo, tabla de errores dividida en errores/advertencias, tabla de formatos CLI corregida (bug `|0|`).

## [1.5.7] - 2026-05-13

### Añadido

- [DOC] Google-style docstrings en español en métodos públicos clave (`Rut.__init__`, `Rut.formatear`, `ValidadorRut`, `ProcesadorLotesRut`, `FormateadorJSON`, `aplicar_formato`).
- [DOC] Docstrings de módulo en 9 archivos: `version.py`, `rut.py`, `validador.py`, `procesador.py`, `cli.py`, `sugestor.py`, `contrib/fastapi.py`, `contrib/pandas.py`, `contrib/polars.py`.
- [DOC] Texto `help=` para los subcomandos `formatear` (`--separador-miles`, `--mayusculas`) y `enmascarar` (descripción del comando, `archivo`, `--mantener`, `--caracter`, `--separador-miles`, `--mayusculas`).
- [DOC] `CONTRIBUTING.md` — guía de contribución completa en español con setup, quality gates, estilo Google-style, Conventional Commits, estructura del proyecto y PR process.

### Mantenimiento

- [DEVOPS] `filterwarnings` eliminado de `pyproject.toml` — las causas raíz ya están corregidas vía `spawn` en `conftest.py`.

## [1.5.6] - 2026-05-13

### Corregido

- [FIX] `conftest.py` global con `multiprocessing.set_start_method("spawn")` para eliminar los 48 DeprecationWarnings de `fork()` con hilos en Python 3.13+.

### Mantenimiento

- [DEVOPS] mypy ahora bloquea el CI (`continue-on-error` eliminado en `quality.yml`).

## [1.5.5] - 2026-05-13

### Añadido

- [QUALITY] Marcador `py.typed` para señalizar PEP 561 (tipado estático para consumidores).
- [QUALITY] Paso `-W error::DeprecationWarning` en CI para detectar deprecaciones de librerías temprano.
- [QUALITY] `conftest.py` global con `multiprocessing.set_start_method("spawn")` para evitar race conditions de `fork()` con hilos en Python 3.13+.
- [DEV] `__init__.py` añadidos en `tests/contrib/` y `tests/contrib/pydantic/`.
- [DOC] Anotaciones `# nosec` en los 2 hallazgos aceptables de bandit (XML generado internamente, random para benchmarks).

### Corregido

- [FIX] Deprecación `starlette.status.HTTP_422_UNPROCESSABLE_ENTITY` reemplazada por `HTTP_422_UNPROCESSABLE_CONTENT` en `contrib/fastapi.py`.
- [FIX] `assert` reemplazados por guardas explícitas en `rut.py` (B101, se pierden con `python -O`).
- [FIX] `except Exception: pass` reemplazados por `logger.warning` en `sugestor.py` (B110).
- [FIX] 14 errores de mypy corregidos (tipos de retorno en `procesador.py`, `cli.py`, `test_rutstr.py`; narrowing en `rut.py`).
- [FIX] Import no usado `importlib` eliminado de `test_rutstr.py`.
- [FIX] Pre-commit migrado de black+flake8 a ruff (elimina redundancia, black 23→26).

### Seguridad

- [SECURITY] Workflow `publish-package.yml`: `workflow_dispatch` restringido a la rama `master`.
- [SECURITY] `quality.yml`: mypy ahora bloquea el CI si hay errores de tipos (`continue-on-error` eliminado).

### Mantenimiento

- [DEVOPS] `ruff` actualizado a 0.15.12 y `mypy` a 2.1.0 en `requirements-dev.txt`.
- [DEVOPS] `pytest-cov` ampliado a `<8.0.0` en `pyproject.toml`.
- [DEVOPS] Filtro `filterwarnings` para suprimir DeprecationWarning de `multiprocessing.fork` en Python 3.13+.

## [1.5.4] - 2026-05-09

### Corregido

- [FIX] Todos los `import warnings` movidos a toplevel para cumplir con pylint `C0415`.
- [FIX] Aliases deprecados removidos de `__all__` en `__init__.py` (pylint `E0603`).
- [FIX] Tests actualizados: `RutInvalidoError` → `ErrorValidacionRut` (pylint `E0611`); imports locales duplicados consolidados (pylint `W0404`/`W0621`).

## [1.5.3] - 2026-05-09

### Corregido

- [FIX] Tests de versión ahora usan `__version__` dinámico en vez de strings hardcodeadas para evitar regresiones en futuros bumps.
- [FIX] Tests de pandas/polars: `Rut.parse()` siempre retorna `ValidacionResultado` (nunca `None`), corregida aserción que esperaba `None` para RUTs inválidos.

## [1.5.2] - 2026-05-09

### Corregido

- [SECURITY] pytest actualizado de `^7.2.1` a `>=9.0.3` para corregir vulnerabilidad de tmpdir (CVE en `/tmp/pytest-of-{user}`).
- [FIX] Tests de `test_audit_v2.py` usaban versión hardcodeada `1.4.5` en vez de `__version__`.
- [FIX] Tests de pandas/polars `test_validar_series` corregidos: validación inválida retorna `ValidacionResultado`, no `None`.

## [1.5.1] - 2026-05-09

### Corregido

- [DEVOPS] Workflow `security.yml`: reemplazada la lectura de `poetry.lock` (no versionado) por `pip freeze` para la exportación de dependencias runtime.

## [1.5.0] - 2026-05-09

### Añadido

- [SECURITY] Sanitización de PII (RUT) en los logs de `ErrorRut.__init__`: el mensaje que recibe `logger.exception()` ya no contiene RUTs en texto plano.
- [SECURITY] Mitigación de inyección de fórmulas CSV en la salida de la CLI (`_emitir_resultados`), alineada con el `FormateadorCSV` del módulo `formatter`.
- [TEST] Suite de tests para CLI (`test_cli.py`), incluyendo `_comando_enmascarar`, `_comando_info` y tests de memoria con pipeline real.
- [TEST] Tests de cobertura para 9 códigos de error faltantes (`FORMATO_GUION`, `DV_INVALIDO`, `LONGITUD_MAXIMA`, `NORMALIZACION_DV`, `CEROS_IZQUIERDA`, `NORMALIZACION_PUNTOS`, `ESTADO_ENMASCARADO`, `CLAVE_TOKEN_REQUERIDA`, `LONGITUD_MAXIMA`).
- [TEST] Tests basados en propiedades con Hypothesis: roundtrip de `Rut.parse`, idempotencia de `normalizar`, enmascarado preserva DV, seguridad CSV.
- [TEST] Tests de integración para contrib/pandas y contrib/polars (`s.rut.es_valido`, `formatear`, `validar`, `normalizar`).
- [TEST] Tests para `Rut.__init__` con argumento `int`, `Rut.enmascarar` con paths extremos (`mantener=0`, `separador_miles`, `mayusculas`, token con `clave=bytes`).
- [TEST] Test end-to-end con backend `ProcessPoolExecutor`.

### Cambiado

- [REFACTOR] Descomposición de `Rut.normalizar()` (87→9 métodos helper estáticos) para reducir complejidad ciclomática.
- [REFACTOR] Estrategias de emisión en CLI: `_emitir_resultados` extraído en 5 clases Strategy (`_EmisionTexto`, `_EmisionJSON`, `_EmisionJSONL`, `_EmisionCSV`, `_EmisionXML`).
- [REFACTOR] Lógica de transposición duplicada en `sugestor.py` consolidada en helper `_generar_transposiciones`.
- [REFACTOR] Regex `RE_BASE_CON_PUNTOS`/`RE_BASE_DIGITOS` deduplicados: movidos a `utils.py`, reimportados en `rut.py` / `validador.py`.
- [REFACTOR] Lógica de formato de Pandas/Polars deduplicada en helper compartido `contrib/_formato_comun.py`.
- [REFACTOR] `_normalizar_entrada` eliminado de `ValidadorRut` (inline directo de `_limpiar_entrada`).
- [REFACTOR] `monitor_de_rendimiento` actualizado con `ParamSpec` para tipos precisos (Python 3.10+).
- [REFACTOR] `ConfiguracionRut.__post_init__` levanta `ErrorValidacionRut` en vez de `ValueError` para consistencia.
- [DEVOPS] Cobertura de tests unificada en `ci.yml`; eliminado `coveralls.yml`.
- [DEVOPS] Workflow `security.yml` corregido: triggers apuntan a `master` en vez de `main`.
- [DEVOPS] `publish-package.yml` ya no se dispara en cada push.
- [DEVOPS] `quality.yml`: mypy con `continue-on-error: true` (no bloqueante); tests removidos (se ejecutan en `ci.yml`).
- [DEVOPS] Clasificador Python 3.9 eliminado de `pyproject.toml` (requerido 3.10+).
- [DEVOPS] Pines de FastAPI/httpx flexibilizados (`^0.110.0` → `>=0.110.0,<2.0.0`, `^0.27.0` → `>=0.27.0,<1.0.0`).

### Corregido

- [FIX] Versión hardcodeada `"1.4.0"` en metadatos de auditoría CLI: ahora usa `obtener_informacion_version()["version"]`.
- [FIX] `__init__.py` (`_registrar_contribs`): cambio de `except (ImportError, AttributeError)` a solo `except ImportError`.
- [FIX] `_leer_ruts`: captura de `FileNotFoundError` y `UnicodeDecodeError` con mensajes legibles y `sys.exit(1)`.
- [FIX] Tests de memoria: reemplazados monkeypatches no-op por pipeline real con 1000 RUTs.
- [FIX] Parámetro muerto en test (`_ = esperado`) corregido a aserción real.

### Deprecado

- [DEPR] Aliases de compatibilidad (`RutInvalidoError`, `RutError`, `RutValidationError`, `RutFormatError`, `RutDigitError`, `RutLengthError`, `RutProcessingError`, `RutValidator`, `RutConfig`) emiten `DeprecationWarning` al ser accedidos. Se eliminarán en v2.0.

## [1.4.5] - 2026-03-29

### Cambiado

- [MAINTENANCE] Refactorización de la clase `RutStr` para reducir la complejidad ciclomática de sus validadores internos de 11 a menos de 8.

### Corregido

- [FIX] Endurecimiento del manejo de excepciones en la detección dinámica de la versión del paquete en `version.py`, reemplazando capturas genéricas por excepciones específicas (`OSError`, `re.error`, `UnicodeDecodeError`).

## [1.4.4] - 2026-03-29

### Cambiado

- [STYLE] Renombrado de funciones públicas a `snake_case` en `contrib/fastapi` (`consulta_rut`, `parametro_rut`) y `contrib/pydantic` (`rut_str_annotated`) para cumplir con PEP 8. Se mantienen alias para asegurar compatibilidad retroactiva.
- [MAINTENANCE] Centralización de la versión en `pyproject.toml` como única fuente de verdad, utilizando recuperación dinámica vía `importlib.metadata` con fallback para desarrollo local.
- [MAINTENANCE] Refactorización integral del codebase para alcanzar una puntuación de 10/10 en Pylint.
- [MAINTENANCE] Mejora de la estructura de imports en `rutificador/rut.py` eliminando imports locales innecesarios y comentarios de desactivación de Pylint.
- [MAINTENANCE] Implementación de `lazy % formatting` en logs y mejora de la trazabilidad de excepciones con `from exc`.

### Corregido

- [FIX] Error de miembro inexistente `RigorValidacion.HOLGADO` en las integraciones de Pandas y Polars (corregido a `FLEXIBLE`).
- [FIX] Eliminación de importaciones no utilizadas y limpieza de espacios en blanco en todo el proyecto y suite de pruebas.

## [1.4.3] - 2026-03-29

### Corregido

- [DEVOPS] Actualización de GitHub Actions (`checkout`, `setup-python`, `upload-artifact`, `cache`) para soportar Node.js 24 y resolver advertencias de deprecación.

## [1.4.2] - 2026-03-28

### Añadido

- [PERF] Integración nativa (accessors) para **Pandas** y **Polars**.
- [PERF] Soporte para `chunksize` en `ProcesadorLotesRut` para optimizar el procesamiento paralelo masivo.
- [PERF] Cálculo automático de `chunksize` basado en la carga y el número de núcleos.
- Extras `[pandas]`, `[polars]` y `[full]` en dependencias.

### Corregido

- Optimización del overhead de comunicación IPC en procesamiento multiproceso.

## [1.4.1] - 2026-03-28

### Añadido

- **CLI Info**: Nuevo comando `rutificador info` para diagnósticos del sistema.
- **Pydantic Dinámico**: Soporte para múltiples formatos en `RutStr` mediante la función factory `RutStrAnnotated(formato=...)`.
- **Integración Unix**: Flags `--quiet` y `--sugerir` en la CLI para control granular de la salida.

### Cambiado

- **Salida de CLI**: Las estadísticas de auditoría ahora se envían a `stderr` por defecto para mantener `stdout` limpio.
- **Sugerencias**: Ahora son desactivadas por defecto (opt-in) vía `--sugerir`.

### Corregido

- **Privacidad**: Sanitización de valores PII (RUT) en los logs de excepciones de `ErrorRut`.
- **Limpieza de Código**: Eliminación de redundancias en rtas de retorno de la CLI y definiciones de excepciones.

## [1.4.0] - 2026-03-28

## [1.3.0] - 2026-03-??

### Añadido

- Soporte para procesamiento en paralelo mediante `parallel_backend`.
- Nuevas excepciones estructuradas en `rutificador.exceptions`.
- Validación de longitud mínima y máxima configurable.

### Cambiado

- Mejora en el rendimiento de normalización de cadenas.

## [1.2.1] - 2025-10-15

### Corregido

- Error en el cálculo del dígito verificador para RUTs de 9 dígitos.
- Soporte para Python 3.12.

## [1.2.0] - 2025-09-01

### Añadido

- Soporte inicial para Pydantic v1.
- Comandos CLI básicos.

---

[1.5.8]: https://github.com/cortega26/rutificador/compare/v1.5.7...v1.5.8
[1.5.7]: https://github.com/cortega26/rutificador/compare/v1.5.6...v1.5.7
[1.5.6]: https://github.com/cortega26/rutificador/compare/v1.5.5...v1.5.6
[1.5.5]: https://github.com/cortega26/rutificador/compare/v1.5.4...v1.5.5
[1.5.4]: https://github.com/cortega26/rutificador/compare/v1.5.3...v1.5.4
[1.5.3]: https://github.com/cortega26/rutificador/compare/v1.5.2...v1.5.3
[1.5.2]: https://github.com/cortega26/rutificador/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/cortega26/rutificador/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/cortega26/rutificador/compare/v1.4.5...v1.5.0
[1.4.5]: https://github.com/cortega26/rutificador/compare/v1.4.4...v1.4.5
[1.4.4]: https://github.com/cortega26/rutificador/compare/v1.4.3...v1.4.4
[1.4.3]: https://github.com/cortega26/rutificador/compare/v1.4.2...v1.4.3
[1.4.2]: https://github.com/cortega26/rutificador/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/cortega26/rutificador/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/cortega26/rutificador/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/cortega26/rutificador/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/cortega26/rutificador/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/cortega26/rutificador/releases/tag/v1.2.0
