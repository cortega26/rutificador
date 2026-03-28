# Historial de Cambios (Changelog)

Todas las modificaciones notables de este proyecto se documentarán en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y este proyecto adhiere a la [Semántica de Versiones](https://semver.org/lang/es/).

## [1.4.0] - 2026-03-28

### Añadido

- **Castellanización Total**: Refactorización completa de la API y metadatos al español.
- **Motor de Sugerencias Inteligente**: Nuevos métodos `Rut.sugerir` y `Rut.mejorar` con soporte para Damerau-Levenshtein y heurísticas OCR.
- **Auditoría Masiva y Streaming CLI**:
  - Salida incremental (OOM-Safe) para JSON, CSV y XML, permitiendo procesar archivos de escala ilimitada.
  - Nuevos formatos soportados: `jsonl` (JSON Lines).
  - Flags avanzados: `--paralelo` para ejecución multi-núcleo y `--mejorar` para auto-corrección **segura** (rechaza sugerencias ambiguas o de baja confianza).
  - Generación de bloques de metadatos de auditoría comparables para trazabilidad y cumplimiento.
- Integración nativa con FastAPI mediante la dependencia `ParametroRut` (v1.4.0+).
- Soporte mejorado para Pydantic v2 con el tipo `RutStr`.
- **Toolchain**: Actualización de la versión de desarrollo y entorno base a Python 3.13.12.

### Cambiado

- **API Pública (Breaking Changes)**:
  - `Rut.mask` -> `Rut.enmascarar`.
  - `ProcesadorLotesRut.stream` -> `ProcesadorLotesRut.flujo`.
  - Argumentos de enmascarado: `keep` -> `mantener`, `char` -> `caracter`.
  - Argumentos de procesamiento: `parallel_backend` -> `motor_paralelo`.
  - Códigos de error: ahora usan nomenclatura en español (ej. `DV_MISMATCH` -> `DV_DISCORDANTE`).
  - Claves de salida JSON/CSV castellanizadas (ej. `error_message` -> `mensaje_error`).
- Registro de auditoría (logging) actualizado a términos en español.

### Corregido

- Manejo de dependencias opcionales para `fastapi` y `pydantic`.
- Normalización de guiones Unicode y espacios de ancho completo.
- Validación de tipos en parámetros de entrada de la CLI.

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

[1.4.0]: https://github.com/cortega26/rutificador/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/cortega26/rutificador/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/cortega26/rutificador/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/cortega26/rutificador/releases/tag/v1.2.0
