# Roadmap de Rutificador

Este documento describe la dirección futura del proyecto. Las fechas son
orientativas y pueden ajustarse según el feedback de la comunidad.

El historial de hitos ya completados (v1.7 → v2.2) vive en `CHANGELOG.md`.

---

## Ideas a largo plazo (exploración)

Estas ideas no tienen fecha comprometida. Se evaluarán según demanda de la
comunidad y disponibilidad de mantenedores.

- **Port cross-platform del validador core** (Rust → WASM, TypeScript):
  permitiría validación client-side en navegadores, un paquete npm
  `@tooltician/rutificador`, y uso en Deno/Cloudflare Workers.
  Contrato de conformidad obligatorio: `docs/conformidad.md` y
  `tests/vectors/conformance.json` (harness versionado, plan 018).
- **Integración con SRI** (Servicio de Impuestos Internos): lookup opcional
  contra registros oficiales como extra `[sri]`.
- **CLI interactiva**: modo `--watch` para procesamiento continuo de archivos,
  integración con `jq` para pipelines JSON.

---

## Política de versionado

Rutificador sigue [SemVer](https://semver.org/lang/es/):

- **PATCH** (1.6.x): correcciones de bugs, sin cambios de API.
- **MINOR** (1.x.0): nuevas funcionalidades retrocompatibles, nuevas
  deprecaciones (con `DeprecationWarning`).
- **MAJOR** (x.0.0): breaking changes planificados y anunciados con
  anticipación.

---

Última actualización: 2026-09-16 · v2.2.1
