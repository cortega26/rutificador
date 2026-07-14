# Roadmap de Rutificador

Este documento describe la dirección futura del proyecto, los hitos planificados
y la estrategia de versionado. Las fechas son orientativas y pueden ajustarse
según el feedback de la comunidad.

---

## v1.7 (Q3 2026) — Segunda fase de calidad y rendimiento

Objetivo: elevar los gates de calidad sin modificar la API pública ni las
dependencias runtime.

- [x] **Mutation testing con `mutmut`** (REJECTED — incompatible Python 3.12, plan 007)
- [x] **Límites arquitectónicos con `import-linter`** (ADOPTED — 3 contratos en `pyproject.toml`)
- [x] **Benchmarks rigurosos con `pyperf`** (REJECTED — pytest-benchmark superior, plan 007)
- [x] **Spike de migración a `uv`** (REJECTED — Poetry lockfile incompatible, plan 007)

Referencia: `plans/007-segunda-fase-calidad-rendimiento.md`

---

## v1.8 (Q3–Q4 2026) — Expansión del ecosistema

- [x] **Sitio de documentación con MkDocs Material** — desplegado en GitHub Pages vía `.github/workflows/docs.yml`.
- [x] **Gate de regresión de rendimiento en CI** — implementado en `.github/workflows/benchmark-regression.yml` (no bloqueante, umbral 20%).
- [x] **Python 3.14 first-class** — en matriz CI con `continue-on-error`; pendiente remover el flag cuando 3.14 sea estable.
- [x] **Strict mypy progresivo** — habilitado en `errores.py`, `version.py`, `config.py`, `utils.py`, `validador.py`. Ver `plans/009-mypy-strict-core.md`.

---

## v1.9 (Q4 2026) — Pulido de API, CLI e infraestructura

- [x] **mypy --strict progresivo por módulo**: habilitar reglas estrictas incrementalmente empezando por `utils.py`, `errores.py`, `config.py`, `validador.py`. Referencia: `plans/009-mypy-strict-core.md`.
- [x] **Paridad CLI: comando `enmascarar --token`**: exponer tokenización HMAC-SHA256 desde la CLI, con soporte para `--clave` (y variable de entorno `RUTIFICADOR_TOKEN_KEY`). Referencia: `plans/010-cli-tokenize-parity.md`.
- [x] **Spec formal de reglas de validación RUT**: documento de especificación con test vectors canónicos exportables (JSON/YAML), prerrequisito para ports cross-platform. Referencia: `plans/011-spec-formal-reglas-rut.md`.
- [x] **Infraestructura de i18n para mensajes de error**: envolver `CATALOGO_ERRORES` en función locale-aware (`idioma="es"|"en"`), sin romper API. Referencia: `plans/012-i18n-errores.md`.

---

## v2.0 (Q3 2026) — Limpieza mayor y breaking changes

v2.0 es la versión de ruptura de compatibilidad binaria. **Todas las APIs
deprecadas desde v1.4.4 han sido eliminadas.** La guía de migración completa
está en `GUIA_MIGRACION_v2.md` y el script automatizado en `scripts/migrate.py`.

- [x] **Eliminación de 12 símbolos obsoletos** — `RutConfig`, `RutValidator`, `Validador` (Protocol), 7 aliases de excepciones, `ConsultaRut`, `ParametroRut`.
- [x] **Eliminación de `RigorValidacion.LEGADO`** — solo `ESTRICTO` y `FLEXIBLE`.
- [x] **Script de migración automática** — `scripts/migrate.py` con modos `--check` y `--fix`.
- [x] **Guía de migración** — `GUIA_MIGRACION_v2.md`.
- [x] **`mypy --strict` en todo el núcleo** — 10 de 10 módulos.
- [x] **Módulo de calidad de datos** — `rutificador.calidad_datos` (plan 016).

---

## Ideas a largo plazo (exploración)

Estas ideas no tienen fecha comprometida. Se evaluarán según demanda de la
comunidad y disponibilidad de mantenedores.

- **Port cross-platform del validador core** (Rust → WASM, TypeScript):
  permitiría validación client-side en navegadores, un paquete npm
  `@tooltician/rutificador`, y uso en Deno/Cloudflare Workers.
- **Integración con SRI** (Servicio de Impuestos Internos): lookup opcional
  contra registros oficiales como extra `[sri]`.
- **CLI interactiva**: modo `--watch` para procesamiento continuo de archivos,
  integración con `jq` para pipelines JSON.
- **Internacionalización (i18n)**: mensajes de error en inglés para adopción
  internacional manteniendo español como default.

---

## Política de versionado

Rutificador sigue [SemVer](https://semver.org/lang/es/):

- **PATCH** (1.6.x): correcciones de bugs, sin cambios de API.
- **MINOR** (1.x.0): nuevas funcionalidades retrocompatibles, nuevas
  deprecaciones (con `DeprecationWarning`).
- **MAJOR** (x.0.0): breaking changes planificados y anunciados con
  anticipación.

---

*Última actualización: 2026-07-14 · v2.0.0*
