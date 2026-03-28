# CHANGELOG

## 1.3.0 - 2026-03-28

- [FEATURE] Motor de sugerencias inteligente (Fuzzy Matching) con `Rut.suggest()` y `Rut.mejorar()`.
- [FEATURE] Soporte para salida estructurada en CLI mediante `--format [json|csv|xml]`.
- [FEATURE] Integración nativa con FastAPI mediante la dependencia `RutParam`.
- [ENHANCEMENT] Esquemas JSON enriquecidos para `RutStr` (Pydantic v2) para mejor documentación OpenAPI/Swagger.
- [DX] Actualización de `pyproject.toml` con extras opcionales: `[pydantic]` y `[fastapi]`.

## 1.2.2 - 2026-02-06

- [FIX] Ajustes de CI: se elimina Python 3.9 (EOL) y se agrega Python 3.14 como prerelease no bloqueante.

## 1.2.1 - 2026-02-06
- [FIX] Endurecimiento y correcciones de empaquetado/tests/documentación posteriores a `v1.2.0`.

## 1.2.0 - 2026-02-06
- [FEATURE] Se incorpora `rutificador.contrib.pydantic.RutStr` (Pydantic v2, extra opcional; se instala explícitamente con `rutificador[pydantic]`).

## 1.1.2 - 2026-02-01
- [FIX] Se rechazan dígitos Unicode fullwidth incluso si hay guiones Unicode normalizados.

## 1.1.1 - 2026-02-01
- [FIX] Ajustes de formato para cumplir con ruff format en CI.

## 1.1.0 - 2026-02-01
- [FEATURE] Se incorporan `Rut.parse`, `Rut.normalizar`, `Rut.mask` y el modelo `ValidacionResultado`.
- [FEATURE] Nuevo streaming estructurado con `ProcesadorLotesRut.stream`.
- [SECURITY] Se marcan módulos con `# SECURITY-CRITICAL` y se evita loggear RUT completo por defecto.
- [DX] Se documenta el alcance y la política de errores en README.
