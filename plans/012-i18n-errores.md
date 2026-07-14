# Plan 012: Infraestructura de i18n para mensajes de error

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving to the next step. If
> anything in the "STOP conditions" section occurs, stop and report — do not
> improvise. When done, update the status row for this plan in
> `plans/README.md`.

> **Drift check (run first)**: `git diff --stat aaca8c4..HEAD -- rutificador/errores.py rutificador/exceptions.py`
> Si la estructura de `CATALOGO_ERRORES` o `crear_detalle_error` cambió,
> comparar los excerpts de "Current state" antes de proceder.

## Status

- **Priority**: P2
- **Effort**: S–M
- **Risk**: LOW — es un refactor interno; la API pública no cambia.
- **Depends on**: none
- **Category**: dx / direction
- **Planned at**: commit `aaca8c4`, 2026-07-14

## Why this matters

El catálogo `CATALOGO_ERRORES` en `errores.py` contiene 16 entradas con
mensajes hardcodeados en español. El roadmap de largo plazo menciona i18n.
Internacionalizar los mensajes de error es un prerequisito para adopción
internacional y para el port TypeScript planeado. Un primer paso de bajo
riesgo: envolver la resolución de mensajes en una función locale-aware sin
romper la API existente, usando un dict por idioma con lazy-load.

## Current state

- `rutificador/errores.py:21-118` — `CATALOGO_ERRORES: Dict[str,
  EntradaCatalogo]` con 16 entradas. Cada entrada tiene `mensaje`, `hint`,
  `severidad`, `recuperable`.
- `rutificador/errores.py:153-184` — `crear_detalle_error(codigo, *, mensaje,
  hint, severidad, recuperable, rut, duracion)` que busca en el catálogo y
  permite overrides.
- El catálogo es un dict de módulo; se accede directamente en
  `crear_detalle_error:165`: `CATALOGO_ERRORES.get(codigo)`.
- `crear_detalle_error` es llamada desde al menos 4 módulos: `rut.py`,
  `validador.py`, `procesador.py`, `sugestor.py`.

Convenciones: código y docstrings en español. Estructura de datos TypedDict
para entradas de catálogo. Sin dependencias externas para el núcleo.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` | 230 passed, 2 skipped |
| Lint | `python -m ruff check rutificador/` | exit 0 |
| Format | `python -m ruff format --check rutificador/` | exit 0 |
| Types | `python -m mypy rutificador/ --ignore-missing-imports` | exit 0 |

## Scope

**In scope** (files to modify):
- `rutificador/errores.py` — refactor del catálogo, función `crear_detalle_error`, agregar `_LOCALE_CATALOGS`
- `tests/test_errores.py` — crear, con tests de i18n
- Opcional: `rutificador/i18n/` — directorio con archivos de locale (solo si se elige lazy-load desde archivos)

**Out of scope** (do NOT touch):
- `rutificador/rut.py`, `rutificador/validador.py`, `rutificador/procesador.py`,
  `rutificador/sugestor.py` — no cambiar las llamadas a `crear_detalle_error`;
  la firma de la función se preserva.
- `rutificador/exceptions.py` — la jerarquía de excepciones no cambia.
- Traducciones completas al inglés — este plan crea la infraestructura, no
  todas las traducciones. Con tener 2-3 entradas en inglés como prueba de
  concepto es suficiente.

## Git workflow

- Branch: `advisor/012-i18n-errores`
- Commits:
  1. `refactor(errores): extraer catálogo a estructura locale-aware`
  2. `test: agregar tests de infraestructura i18n para errores`
- No hacer push ni abrir PR a menos que el operador lo indique.

## Steps

### Step 1: Crear catálogo multi-idioma con dict anidado

En `rutificador/errores.py`, reemplazar `CATALOGO_ERRORES` con:

```python
from typing import Dict, Literal, Optional, TypedDict

Idioma = Literal["es", "en"]

_CATALOGO_ES: Dict[str, EntradaCatalogo] = {
    "ERROR_TIPO": {
        "mensaje": "El RUT debe ser cadena o entero",
        "hint": "Convierta el valor a str o int",
        "severidad": "error",
        "recuperable": False,
    },
    # ... resto de entradas actuales, sin cambios ...
}

_CATALOGO_EN: Dict[str, EntradaCatalogo] = {
    # Inicialmente vacío o con 2-3 entradas de prueba.
    # Las entradas faltantes caen en fallback a español.
    "ERROR_TIPO": {
        "mensaje": "RUT must be a string or integer",
        "hint": "Convert the value to str or int",
        "severidad": "error",
        "recuperable": False,
    },
    "RUT_VACIO": {
        "mensaje": "RUT cannot be empty",
        "hint": "Enter at least one digit",
        "severidad": "error",
        "recuperable": True,
    },
    "DV_DISCORDANTE": {
        "mensaje": "Check digit does not match",
        "hint": "Correct the check digit",
        "severidad": "error",
        "recuperable": False,
    },
}

_LOCALE_CATALOGS: Dict[Idioma, Dict[str, EntradaCatalogo]] = {
    "es": _CATALOGO_ES,
    "en": _CATALOGO_EN,
}

# Mantener el nombre CATALOGO_ERRORES como alias para retrocompatibilidad
CATALOGO_ERRORES = _CATALOGO_ES
```

Esto preserva la retrocompatibilidad: cualquier código que acceda a
`CATALOGO_ERRORES` directamente sigue funcionando (obtiene el catálogo en
español).

### Step 2: Modificar `crear_detalle_error` para aceptar `idioma`

Agregar el parámetro `idioma` a `crear_detalle_error`:

```python
def crear_detalle_error(
    codigo: str,
    *,
    mensaje: Optional[str] = None,
    hint: Optional[str] = None,
    severidad: Optional[Severidad] = None,
    recuperable: Optional[bool] = None,
    rut: Optional[str] = None,
    duracion: float = 0.0,
    idioma: Idioma = "es",
) -> DetalleError:
    """Crea un DetalleError a partir del catálogo o con overrides.

    Args:
        codigo: Código de error del catálogo.
        mensaje: Override del mensaje.
        hint: Override del hint.
        severidad: Override de la severidad.
        recuperable: Override de recuperabilidad.
        rut: RUT asociado al error.
        duracion: Tiempo de procesamiento.
        idioma: Idioma para los mensajes (``"es"`` o ``"en"``).
            Si la entrada no existe en el idioma solicitado, se usa
            el catálogo en español como fallback.
    """
    catalogo = _LOCALE_CATALOGS.get(idioma, _CATALOGO_ES)
    entrada = catalogo.get(codigo)
    if entrada is None and idioma != "es":
        # Fallback a español si la entrada no está en el idioma solicitado
        entrada = _CATALOGO_ES.get(codigo)

    mensaje_final = mensaje or (entrada["mensaje"] if entrada else "Error desconocido")
    hint_final = hint or (
        entrada["hint"] if entrada else "Consulte el catálogo de errores"
    )
    severidad_final = severidad or (entrada["severidad"] if entrada else "error")
    recuperable_final = (
        recuperable
        if recuperable is not None
        else (entrada["recuperable"] if entrada else False)
    )
    return DetalleError(
        codigo=codigo,
        mensaje=mensaje_final,
        hint=hint_final,
        severidad=severidad_final,
        recuperable=recuperable_final,
        rut=rut,
        duracion=duracion,
    )
```

El parámetro `idioma` tiene default `"es"`, por lo que todas las llamadas
existentes siguen funcionando sin cambios.

**Verify**: `python -m mypy rutificador/errores.py --ignore-missing-imports` → exit 0.

### Step 3: Ejecutar tests existentes para verificar retrocompatibilidad

```bash
python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q
```

**Verify**: 230 tests pasan. Ningún test existente debe romperse porque la API
no cambió (el nuevo parámetro tiene default).

### Step 4: Crear tests para i18n

Crear `tests/test_errores.py`:

```python
"""Tests para la infraestructura de i18n de errores."""

from rutificador.errores import crear_detalle_error, CATALOGO_ERRORES


class TestCrearDetalleErrorI18n:
    def test_idioma_es_por_defecto(self):
        detalle = crear_detalle_error("ERROR_TIPO")
        assert detalle.mensaje == "El RUT debe ser cadena o entero"
        assert detalle.hint == "Convierta el valor a str o int"

    def test_idioma_en_explicito(self):
        detalle = crear_detalle_error("ERROR_TIPO", idioma="en")
        assert detalle.mensaje == "RUT must be a string or integer"
        assert detalle.hint == "Convert the value to str or int"

    def test_fallback_a_es_cuando_en_no_tiene_entrada(self):
        # 'FORMATO_PUNTOS' no está en el catálogo en inglés
        detalle = crear_detalle_error("FORMATO_PUNTOS", idioma="en")
        # Debe caer en el mensaje en español
        assert "Separadores" in detalle.mensaje or "separadores" in detalle.mensaje.lower()

    def test_override_mensaje_ignora_catalogo(self):
        detalle = crear_detalle_error(
            "ERROR_TIPO", mensaje="Mensaje personalizado", idioma="en"
        )
        assert detalle.mensaje == "Mensaje personalizado"

    def test_catalogo_es_accesible_retrocompatibilidad(self):
        assert CATALOGO_ERRORES["ERROR_TIPO"]["mensaje"] == "El RUT debe ser cadena o entero"
```

**Verify**: `python -m pytest tests/test_errores.py -v` → todos los tests pasan.

### Step 5: Verificación final completa

```bash
python -m ruff check rutificador/ tests/ && \
python -m ruff format --check rutificador/ tests/ && \
python -m mypy rutificador/ --ignore-missing-imports && \
python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q
```

**Verify**: todos los comandos exit 0. Tests pasan (230+ existentes + 5 nuevos).

## Test plan

Nuevos tests en `tests/test_errores.py`:

1. **Default español**: `crear_detalle_error("ERROR_TIPO")` → mensaje en español.
2. **Inglés explícito**: `crear_detalle_error("ERROR_TIPO", idioma="en")` → mensaje en inglés.
3. **Fallback a español**: código no traducido en `"en"` → mensaje en español.
4. **Override de mensaje**: `mensaje=` ignora el catálogo en cualquier idioma.
5. **Retrocompatibilidad**: `CATALOGO_ERRORES` sigue siendo accesible como dict.

Los tests siguen el patrón de `tests/test_quick_wins.py`: imports planos,
funciones sin clase (o clase si se prefiere agrupar), docstrings en español.

## Done criteria

- [ ] `CATALOGO_ERRORES` sigue accesible como alias (retrocompatibilidad)
- [ ] `crear_detalle_error` acepta `idioma="es"|"en"` con default `"es"`
- [ ] 2-3 entradas en inglés existen en `_CATALOGO_EN`
- [ ] Fallback a español cuando una entrada no está en el idioma solicitado
- [ ] 5 tests nuevos en `tests/test_errores.py` pasan
- [ ] 230 tests existentes pasan sin modificaciones
- [ ] `ruff check`, `ruff format --check`, `mypy` pasan
- [ ] Ningún archivo fuera de `in scope` fue modificado
- [ ] `plans/README.md` status row actualizada

## STOP conditions

- Si algún test existente falla después del refactor: revertir y reportar cuál
  test, con su mensaje de error.
- Si `mypy` rechaza el tipo `Idioma = Literal["es", "en"]` en la firma de
  `crear_detalle_error`: verificar que `Literal` esté importado de `typing` (ya
  lo está).
- Si se descubre que `CATALOGO_ERRORES` se usa fuera de `errores.py` de forma
  que rompería con el cambio (ej. mutación del dict): reportar el uso exacto.
  La inspección inicial no encontró usos externos más allá de lectura.
- Si el equipo decide que no se quiere i18n en absoluto: marcar REJECTED con
  rationale.

## Maintenance notes

- Para agregar un nuevo idioma (ej. `"pt"`): crear `_CATALOGO_PT` y agregarlo
  a `_LOCALE_CATALOGS`. Ningún otro archivo necesita cambios.
- Para traducciones completas al inglés: extender `_CATALOGO_EN` con las 13
  entradas restantes. Este plan solo incluye 3 como proof-of-concept.
- Si en el futuro se quiere lazy-load desde archivos JSON (ej.
  `rutificador/i18n/en.json`), se puede hacer sin romper la API: modificar
  `_LOCALE_CATALOGS` para que sea una función con caché que lea el archivo la
  primera vez.
- Considerar exponer `crear_detalle_error` con `idioma` en la CLI (plan
  separado). La CLI actualmente no internacionaliza salida.
