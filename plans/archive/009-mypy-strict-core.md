# Plan 009: Rollout progresivo de `mypy --strict` en módulos del núcleo

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving to the next step. If
> anything in the "STOP conditions" section occurs, stop and report — do not
> improvise. When done, update the status row for this plan in
> `plans/README.md`.

> **Drift check (run first)**: `git diff --stat aaca8c4..HEAD -- rutificador/ .github/workflows/ci.yml`
> If the mypy invocation in CI or any core module changed since this plan was
> written, compare the "Current state" excerpts against the live code before
> proceeding; on a mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED — `--strict` puede exponer code smells estructurales que
  requieran refactors más grandes de lo esperado.
- **Depends on**: none
- **Category**: dx / tech-debt
- **Planned at**: commit `aaca8c4`, 2026-07-14

## Why this matters

El proyecto tiene marcador `py.typed` (PEP 561), tipado exhaustivo con
anotaciones en todas las funciones públicas, y CI que ejecuta `mypy
rutificador/ --ignore-missing-imports` sin errores. Pero `--strict` está
deshabilitado, lo que deja pasar: `Optional` no declarados donde se asigna
`None`, `Any` implícitos que eluden verificación, y `@overload` faltantes en
funciones polimórficas. Habilitar `--strict` incrementalmente —un módulo a la
vez, cada uno en su propio PR— fortalece la seguridad de tipos sin arriesgar
una refactorización masiva.

## Current state

- `.github/workflows/ci.yml:89` — mypy corre con `--ignore-missing-imports`,
  sin flag `--strict`:
  ```yaml
  - name: Tipos (mypy)
    run: |
      python -m mypy rutificador/ --ignore-missing-imports
  ```
- `rutificador/py.typed` — marcador PEP 561 presente. Los consumidores que
  importan `rutificador` reciben verificación de tipos.
- Módulos del núcleo (candidatos al rollout, ordenados por tamaño/riesgo):
  - `rutificador/errores.py` (192 líneas) — catálogo de errores, dataclass,
    TypedDict. Sin IO, sin imports circulares.
  - `rutificador/version.py` (77 líneas) — obtención dinámica de versión.
  - `rutificador/config.py` (61 líneas) — dataclass y enum.
  - `rutificador/utils.py` (213 líneas) — funciones utilitarias, ParamSpec,
    TypeVar.
  - `rutificador/validador.py` (171 líneas) — clase validador, Protocol.
  - `rutificador/formatter.py` — estrategias de formateo.
  - `rutificador/exceptions.py` — jerarquía de excepciones.
  - `rutificador/rut.py` (659 líneas) — clase principal. Dejar para el final
    por ser el módulo más grande y complejo.
  - `rutificador/cli.py` (403 líneas) — CLI con argparse.
  - `rutificador/procesador.py` (525 líneas) — procesamiento paralelo.
  - `rutificador/sugestor.py` (217 líneas) — sugerencias fuzzy.
  - `rutificador/contrib/*` — integraciones opcionales (último, dependen de
    librerías externas).

Convenciones: tests en `tests/`, imports absolutos desde `rutificador`,
Google-style docstrings en español, ruff para lint/formato. CI se ejecuta en
push/PR a master.

Ejemplo de commit: `abbe027 chore: update version to 1.6.0 in pyproject.toml`

## Commands you will need

| Purpose    | Command                                    | Expected on success           |
|------------|--------------------------------------------|-------------------------------|
| Tests      | `python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` | 230 passed, 2 skipped |
| Lint       | `python -m ruff check rutificador/`        | exit 0, no output             |
| Format     | `python -m ruff format --check rutificador/` | exit 0, no output           |
| Types (current) | `python -m mypy rutificador/ --ignore-missing-imports` | exit 0                |
| Types (strict on file) | `python -m mypy --strict <file>`    | verify per step               |
| Types (strict on all)  | `python -m mypy --strict rutificador/` | verify at end              |

## Scope

**In scope** (files to modify in order):
- `rutificador/errores.py` — paso 1
- `rutificador/version.py` — paso 2
- `rutificador/config.py` — paso 3
- `rutificador/utils.py` — paso 4
- `rutificador/validador.py` — paso 5
- `.github/workflows/ci.yml` — paso 6 (cambiar mypy invocation para usar
  `--strict` en los módulos ya migrados)

**Out of scope** (do NOT touch in this plan):
- `rutificador/rut.py`, `rutificador/cli.py`, `rutificador/procesador.py`,
  `rutificador/sugestor.py`, `rutificador/formatter.py`,
  `rutificador/exceptions.py` — se abordarán en planes futuros (o en una
  extensión de este plan si se decide continuar).
- `rutificador/contrib/*` — integraciones opcionales con dependencias externas;
  el `--ignore-missing-imports` las maneja.
- `tests/` — no modificar tests existentes a menos que `--strict` revele que un
  test llama una API con tipos incorrectos.

## Git workflow

- Branch: `advisor/009-mypy-strict-core`
- Un commit por módulo migrado, mensaje estilo Conventional Commits en español:
  `refactor(errores): habilitar mypy --strict en errores.py`
- No hacer push ni abrir PR a menos que el operador lo indique.

## Steps

### Step 1: Habilitar `--strict` en `errores.py`

Agregar al tope del archivo (después del docstring del módulo):

```python
# mypy: strict
```

Ejecutar `python -m mypy --strict rutificador/errores.py` y corregir los
errores que aparezcan. Los errores típicos incluyen:

- `None` no declarado en Optional: agregar `Optional[X]` o `X | None`.
- `Any` implícito en dict/set vacío: tipar explícitamente (el catálogo ya usa
  `Dict[str, EntradaCatalogo]`, probablemente ya esté limpio).
- Funciones sin anotación de retorno: agregar `-> None` o el tipo correcto.

Si un error requiere un cambio que afecta la API pública (cambio de firma de
`crear_detalle_error`), detenerse y reportar.

**Verify**: `python -m mypy --strict rutificador/errores.py` → exit 0, sin errores.

### Step 2: Habilitar `--strict` en `version.py`

Agregar `# mypy: strict` al tope y corregir errores. Posibles issues:

- `import importlib_metadata` con `# type: ignore` ya existe (línea 16).
- `re.search` puede retornar `Optional[Match]`.
- `Path` operations tipificados.

**Verify**: `python -m mypy --strict rutificador/version.py` → exit 0, sin errores.

### Step 3: Habilitar `--strict` en `config.py`

Agregar `# mypy: strict` al tope y corregir errores. El módulo es pequeño
(dataclass + enum). Posibles issues: `Tuple[int, ...]` vs `tuple[int, ...]` en
Python 3.10+.

**Verify**: `python -m mypy --strict rutificador/config.py` → exit 0, sin errores.

### Step 4: Habilitar `--strict` en `utils.py`

Agregar `# mypy: strict` al tope y corregir errores. Este módulo es más
complejo (ParamSpec, TypeVar, decoradores). Posibles issues:

- `ParamSpec` y `TypeVar` binding con `--strict`.
- `Any` en `asegurar_cadena_no_vacia` y `asegurar_booleano` (parámetro `Any`).
  Si `--strict` rechaza `Any`, cambiar a `object` con cast interno o usar
  `# type: ignore[explicit-any]` con justificación.
- `setattr` y `getattr` dinámicos en `configurar_registro`.

**Verify**: `python -m mypy --strict rutificador/utils.py` → exit 0, sin errores.

### Step 5: Habilitar `--strict` en `validador.py`

Agregar `# mypy: strict` al tope y corregir errores. Posibles issues:

- `Optional` en parámetros de `__init__`.
- `Protocol` con `@runtime_checkable`.
- `re.Match` tipado.

**Verify**: `python -m mypy --strict rutificador/validador.py` → exit 0, sin errores.

### Step 6: Actualizar CI para usar `--strict` en los módulos migrados

En `.github/workflows/ci.yml`, modificar el paso "Tipos (mypy)" para que use
`--strict`:

```yaml
- name: Tipos (mypy)
  run: |
    python -m mypy --strict rutificador/errores.py rutificador/version.py rutificador/config.py rutificador/utils.py rutificador/validador.py
    python -m mypy rutificador/ --ignore-missing-imports
```

La primera línea verifica los módulos ya migrados con `--strict`. La segunda
línea mantiene la verificación actual para el resto como red de seguridad. A
medida que más módulos se migren en el futuro, se agregan a la primera línea.

**Verify**: ejecutar ambas líneas localmente → ambas exit 0.

### Step 7: Verificación final completa

Ejecutar la suite completa:

```bash
python -m ruff check rutificador/ && \
python -m ruff format --check rutificador/ && \
python -m mypy --strict rutificador/errores.py rutificador/version.py rutificador/config.py rutificador/utils.py rutificador/validador.py && \
python -m mypy rutificador/ --ignore-missing-imports && \
python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q
```

**Verify**: todos los comandos exit 0. 230 tests pass.

## Test plan

No se requieren nuevos tests. El plan no modifica comportamiento, solo agrega
anotaciones de tipos. La suite de tests existente (`230 passed`) verifica que
los cambios de tipo no rompen nada.

Si una corrección de `--strict` requiere cambiar lógica (no solo anotaciones),
agregar un test mínimo en `tests/test_quick_wins.py` siguiendo el patrón de ese
archivo:

```python
def test_<descripcion>():
    """<docstring en español>."""
    # setup, act, assert
```

## Done criteria

- [ ] `rutificador/errores.py` tiene `# mypy: strict` y pasa `--strict` sin errores
- [ ] `rutificador/version.py` tiene `# mypy: strict` y pasa `--strict` sin errores
- [ ] `rutificador/config.py` tiene `# mypy: strict` y pasa `--strict` sin errores
- [ ] `rutificador/utils.py` tiene `# mypy: strict` y pasa `--strict` sin errores
- [ ] `rutificador/validador.py` tiene `# mypy: strict` y pasa `--strict` sin errores
- [ ] `.github/workflows/ci.yml` actualizado con las dos líneas de mypy
- [ ] `ruff check` y `ruff format --check` pasan
- [ ] 230 tests pasan
- [ ] Ningún archivo fuera de `in scope` fue modificado
- [ ] `plans/README.md` status row actualizada

## STOP conditions

- Si un módulo genera más de 20 errores de `--strict`: reportar el conteo y el
  tipo de errores; no intentar resolverlos todos sin revisión humana.
- Si una corrección de tipo requiere cambiar una firma pública exportada en
  `__all__` o `__init__.py`: detenerse y reportar cuál.
- Si `--strict` rechaza un patrón que está documentado como válido en Python
  3.10+ (ej. `X | None` vs `Optional[X]`): usar la sintaxis moderna y
  continuar; el proyecto ya requiere ≥3.10.
- Si los tests fallan después de un cambio de tipo: revertir ese paso y
  reportar.
- Si `ruff` rechaza el `# mypy: strict` como comentario sin usar: agregar
  `# noqa` si es necesario, pero reportarlo.

## Maintenance notes

- Cada vez que un nuevo módulo del núcleo se migre a `--strict`, agregarlo a
  la primera línea de mypy en `ci.yml`.
- Cuando todos los módulos del núcleo estén migrados, la segunda línea
  (`--ignore-missing-imports`) se puede eliminar y reemplazar por `--strict`
  global con `--ignore-missing-imports` solo para `contrib/*`.
- Los módulos `rut.py` y `procesador.py` son los más difíciles por su tamaño y
  uso de `Any`/`Optional`/`Union`. Reservarlos para un plan futuro específico.
