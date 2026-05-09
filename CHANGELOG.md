# Historial de Cambios (Changelog)

Todas las modificaciones notables de este proyecto se documentarán en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y este proyecto adhiere a la [Semántica de Versiones](https://semver.org/lang/es/).

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
