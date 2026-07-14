# Roadmap de Rutificador

Este documento describe la dirección futura del proyecto, los hitos planificados
y la estrategia de versionado. Las fechas son orientativas y pueden ajustarse
según el feedback de la comunidad.

---

## v1.7 (Q3 2026) — Segunda fase de calidad y rendimiento

Objetivo: elevar los gates de calidad sin modificar la API pública ni las
dependencias runtime.

- [ ] **Mutation testing con `mutmut`** sobre el núcleo matemático (`utils.py`,
  `validador.py`, funciones críticas de `rut.py`). Criterio: adoptar solo si
  descubre huecos de prueba reales en <20 min de CI.
- [ ] **Límites arquitectónicos con `import-linter`**: contratos formales para
  `rutificador` → `tests`, `core` → `contrib`, `core` → `cli`.
- [ ] **Benchmarks rigurosos con `pyperf`**: scripts deterministas en
  `tests/benchmarks/` para `calcular_digito_verificador`, `Rut.parse()`,
  lotes seriales y streaming. Criterio: adoptar si la variabilidad permite
  detectar regresiones ≥10%.
- [ ] **Spike de migración a `uv`**: evaluar si reduce tiempos de CI o mejora
  reproducibilidad sin duplicar fuentes de dependencias.

Referencia: `plans/007-segunda-fase-calidad-rendimiento.md`

---

## v1.8 (Q3–Q4 2026) — Expansión del ecosistema

- [ ] **Sitio de documentación con MkDocs Material**: API reference generada
  desde docstrings Google-style, buscador, ejemplos interactivos, changelog
  integrado. Publicado en GitHub Pages.
- [ ] **Gate de regresión de rendimiento en CI**: comparación automática de
  benchmarks contra la rama base antes del merge. Inicia como job no
  bloqueante.
- [ ] **Python 3.14 first-class**: eliminar `continue-on-error` en la matriz
  de CI cuando 3.14 alcance estabilidad suficiente.
- [ ] **Strict mypy progresivo**: habilitar reglas estrictas incrementalmente
  en módulos del núcleo.

---

## v2.0 (2027) — Limpieza mayor y breaking changes

v2.0 es la versión de ruptura de compatibilidad binaria planificada. **Todas
las APIs deprecadas desde v1.5.0 se eliminarán.** Se publicará una guía de
migración completa y un script automatizado de actualización.

### Lo que se elimina

| Símbolo obsoleto | Reemplazo | Introducido | Archivo |
|---|---|---|---|
| `RigorValidacion.LEGADO` | `RigorValidacion.FLEXIBLE` | v1.6.0 | `config.py:54` |
| `RutInvalidoError` | `ErrorValidacionRut` | v1.5.0 | `exceptions.py:109` |
| `RutError` | `ErrorRut` | v1.5.0 | `exceptions.py:110` |
| `RutValidationError` | `ErrorValidacionRut` | v1.5.0 | `exceptions.py:111` |
| `RutFormatError` | `ErrorFormatoRut` | v1.5.0 | `exceptions.py:112` |
| `RutDigitError` | `ErrorDigitoRut` | v1.5.0 | `exceptions.py:113` |
| `RutLengthError` | `ErrorLongitudRut` | v1.5.0 | `exceptions.py:114` |
| `RutProcessingError` | `ErrorProcesamientoRut` | v1.5.0 | `exceptions.py:115` |
| `RutConfig` | `ConfiguracionRut` | v1.5.0 | `__init__.py:65` |
| `RutValidator` | `ValidadorRut` | v1.5.0 | `__init__.py:66`, `validador.py:152` |
| `Validador` (Protocol) | `ValidadorRut` | v1.5.0 | `validador.py:35-50` |
| `ConsultaRut` | `consulta_rut` | v1.4.4 | `fastapi.py:71` |
| `ParametroRut` | `parametro_rut` | v1.4.4 | `fastapi.py:76` |

### Lo que cambia

- **`RigorValidacion`**: solo dos modos — `ESTRICTO` y `FLEXIBLE`.
- **`__init__.py`**: sin `__getattr__` ni `_DEPRECATED_EXPORTS`. API pública
  explícita y plana.
- **`exceptions.py`**: sin aliases a nivel de módulo ni `__getattr__`.
- **`validador.py`**: sin protocolo `Validador` ni `__getattr__`.
- **Mínimo Python**: se evaluará subir a 3.11 según la adopción en el
  ecosistema Chileno al momento del release.

### Estrategia de migración

1. **Detección temprana**: desde v1.5.0, todos los símbolos obsoletos emiten
   `DeprecationWarning`. Los usuarios pueden activar
   `python -W error::DeprecationWarning` para detectar usos en sus tests.
2. **Script de migración**: se publicará `rutificador-migrate` como herramienta
   CLI que parcha imports automáticamente.
3. **Ventana de transición**: 6 meses entre la publicación de la guía de
   migración y el release de v2.0.

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

*Última actualización: 2026-07-14 · v1.6.1*
