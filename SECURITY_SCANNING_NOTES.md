# Notas sobre el flujo de "Security Scanning"

## Alcance del escaneo
- `pip-audit` se ejecuta una sola vez y toma como entrada `requirements-dev.txt` mediante la configuración declarada en `.pip-audit.toml`.
- Con esta configuración, solo se auditan las dependencias del proyecto y no las herramientas globales del runner.
- El reporte JSON (`audit-report.json`) se publica como artefacto para facilitar la revisión.

## Gestión del CVE GHSA-4xh5-x5gv-qwph
- Los runners vienen con `pip` vulnerable (25.1.1). La solución es actualizar explícitamente a `pip>=25.2`, versión que corrige la alerta.
- `requirements-dev.txt` deja de forzar un downgrade; ahora solo exige la versión corregida o superior.
- Mientras `pip` no esté incluido explícitamente como dependencia de aplicación, queda fuera del alcance auditado.

## Próximos pasos
- Revisar periódicamente las notas de lanzamiento de `pip` y quitar esta sección cuando la versión corregida sea estándar en los runners.
- Si se migra a otro gestor de dependencias, actualizar `.pip-audit.toml` para que el escaneo siga acotado al árbol del proyecto.
