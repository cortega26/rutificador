# CHANGELOG

## 1.1.2 - 2026-02-01
- [FIX] Se rechazan dígitos Unicode fullwidth incluso si hay guiones Unicode normalizados.

## 1.1.1 - 2026-02-01
- [FIX] Ajustes de formato para cumplir con ruff format en CI.

## 1.1.0 - 2026-02-01
- [FEATURE] Se incorporan `Rut.parse`, `Rut.normalizar`, `Rut.mask` y el modelo `ValidacionResultado`.
- [FEATURE] Nuevo streaming estructurado con `ProcesadorLotesRut.stream`.
- [SECURITY] Se marcan módulos con `# SECURITY-CRITICAL` y se evita loggear RUT completo por defecto.
- [DX] Se documenta el alcance y la política de errores en README.
