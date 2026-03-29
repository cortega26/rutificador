# Historial de Cambios (Changelog)

Todas las modificaciones notables de este proyecto se documentarán en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y este proyecto adhiere a la [Semántica de Versiones](https://semver.org/lang/es/).

## [1.4.3] - 2026-03-29

### Corregido

- [DEVOPS] Actualización de GitHub Actions (`checkout`, `setup-python`, `upload-artifact`, `cache`) para soportar Node.js 24 y resolver advertencias de deprecación.

## [1.4.2] - 2026-03-28

### Added

- [PERF] Integración nativa (accessors) para **Pandas** y **Polars**.
- [PERF] Soporte para `chunksize` en `ProcesadorLotesRut` para optimizar el procesamiento paralelo masivo.
- [PERF] Cálculo automático de `chunksize` basado en la carga y el número de núcleos.
- Extras `[pandas]`, `[polars]` y `[full]` en dependencias.

### Fixed

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

[1.4.1]: https://github.com/cortega26/rutificador/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/cortega26/rutificador/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/cortega26/rutificador/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/cortega26/rutificador/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/cortega26/rutificador/releases/tag/v1.2.0
