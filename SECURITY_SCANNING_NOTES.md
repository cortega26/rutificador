# Notas sobre el flujo de "Security Scanning"

## Alcance del escaneo
- `pip-audit` se ejecuta tres veces: contra el entorno instalado completo, contra un snapshot derivado de `poetry.lock` (solo dependencias de ejecución) y contra `requirements-dev.txt`.
- Con este enfoque se cubren tanto las dependencias de ejecución declaradas en `pyproject.toml` —incluso aquellas condicionadas por versión de Python— como las herramientas de desarrollo.
- Los reportes JSON (`audit-report-env.json`, `audit-report-runtime.json` y `audit-report-dev.json`) se publican como artefactos para facilitar la revisión.

## Gestión del CVE GHSA-4xh5-x5gv-qwph
- Los runners vienen con `pip` vulnerable (25.1.1). La solución es actualizar explícitamente a `pip>=25.2`, versión que corrige la alerta.
- `requirements-dev.txt` deja de forzar un downgrade; ahora solo exige la versión corregida o superior.
- Mientras `pip` no esté incluido explícitamente como dependencia de aplicación, queda fuera del alcance auditado.

## Próximos pasos
- Revisar periódicamente las notas de lanzamiento de `pip` y quitar esta sección cuando la versión corregida sea estándar en los runners.
- Si se migra a otro gestor de dependencias, actualizar `.pip-audit.toml` para mantener la configuración por defecto y revisar los comandos del flujo de trabajo.
