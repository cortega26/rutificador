# Plan 016: Toolkit de calidad de datos y deduplicación para RUTs

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 6b61e0e..HEAD -- rutificador/rut.py rutificador/procesador.py rutificador/__init__.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MEDIUM
- **Depends on**: 014 (mypy strict) — recommended so the new module starts strict from day one
- **Category**: direction
- **Planned at**: commit `6b61e0e`, 2026-07-14

## Why this matters

rutificador valida RUTs individuales con excelencia, pero los pipelines de datos reales necesitan más que validación sintáctica: identificar duplicados (exactos y con variaciones de formato), auditar la consistencia de formatos en una columna, detectar valores atípicos, y generar reportes de perfilamiento. Un módulo `rutificador.calidad_datos` (o `rutificador.data_quality`) expande la audiencia de desarrolladores a analistas e ingenieros de datos, usando la infraestructura de validación existente sin duplicar lógica.

## Current state

El código existente ya provee las primitivas necesarias:

- `Rut.parse(valor)` → `ValidacionResultado` con `estado`, `base`, `dv`, `normalizado`, `errores`, `advertencias` — clasifica cualquier entrada sin lanzar excepción (`rut.py:291-387`)
- `Rut.enmascarar(valor)` → `str` — ofusca RUTs para reportes PII-safe (`rut.py:389-463`)
- `ProcesadorLotesRut.validar_lista_ruts()` → `ResultadoLote` — procesa lotes con paralelismo opcional (`procesador.py:148-194`)
- `validar_flujo_ruts()` → `Iterator[Tuple[bool, ...]]` — streaming para archivos grandes (`procesador.py:331-372`)

Lo que falta: operaciones de más alto nivel que consuman estas primitivas y produzcan análisis agregados.

Convenciones del proyecto:
- Módulos nuevos en `rutificador/` con `__all__` explícito
- Exports públicos en `rutificador/__init__.py`
- Docstrings Google-style en español
- Tests en `tests/` siguiendo `tests/test_rutificador.py` como patrón (pytest fixtures, parametrize)
- `import-linter` prohíbe que el núcleo dependa de `contrib` — el nuevo módulo es parte del núcleo y tampoco puede depender de `contrib`

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `.venv/bin/python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` | ≥268 passed |
| Lint | `.venv/bin/python -m ruff check rutificador/` | exit 0 |
| Types | `.venv/bin/python -m mypy --strict rutificador/calidad_datos.py` | exit 0 |
| Architecture | `lint-imports` | exit 0 (3 contracts) |

## Scope

**In scope** (files to create or modify):
- `rutificador/calidad_datos.py` — NUEVO: módulo de calidad de datos
- `tests/test_calidad_datos.py` — NUEVO: tests del módulo
- `rutificador/__init__.py` — agregar exports del nuevo módulo

**Out of scope** (do NOT touch):
- `rutificador/rut.py` — sin cambios
- `rutificador/procesador.py` — sin cambios (usar su API pública)
- `rutificador/cli.py` — sin cambios (una futura integración CLI puede exponer estos comandos)
- `rutificador/contrib/` — sin cambios
- `rutificador/validador.py`, `rutificador/config.py`, `rutificador/utils.py` — sin cambios

## Git workflow

- Branch: `advisor/016-data-quality-toolkit`
- Commit per function/feature added; message style: `feat(calidad): agregar <funcionalidad>`
- Example: `feat(calidad): agregar detección de duplicados exactos y normalizados`
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Crear el módulo `rutificador/calidad_datos.py`

Crear el archivo con la siguiente estructura. El diseño se basa en funciones stateless que reciben secuencias de strings y retornan resultados estructurados con dataclasses.

```python
"""Herramientas de calidad de datos para columnas de RUTs.

Ofrece detección de duplicados, auditoría de consistencia de formatos,
perfilamiento estadístico y reportes de calidad. Todas las operaciones
aceptan secuencias de cadenas (RUTs en cualquier formato) y usan
internamente ``Rut.parse`` para normalizar antes de comparar.
"""

from dataclasses import dataclass, field
from typing import Iterator, Optional, Sequence

from .rut import Rut


@dataclass
class InformeDuplicados:
    """Resultado de una operación de detección de duplicados."""

    total_procesados: int
    total_unicos: int
    total_duplicados: int
    duplicados: list[tuple[str, int]]  # (base_normalizada, conteo)
    # PII-safe: solo muestra la base sin DV


def detectar_duplicados(
    ruts: Sequence[str],
    *,
    sensible_a_formato: bool = False,
) -> InformeDuplicados:
    """Detecta RUTs duplicados en una secuencia.

    Por defecto (``sensible_a_formato=False``), compara usando la base
    y DV normalizados — ``12.345.678-5`` y ``12345678-5`` se consideran
    el mismo RUT.

    Con ``sensible_a_formato=True``, compara usando la representación
    exacta de la entrada — útil para detectar variaciones de formato en
    un dataset (ej: mezcla de con/sin puntos).

    Args:
        ruts: Secuencia de cadenas con RUTs.
        sensible_a_formato: Si ``True``, compara texto exacto de entrada.

    Returns:
        ``InformeDuplicados`` con conteos y valores repetidos.
    """
    ...


@dataclass
class AuditoriaFormato:
    """Resultado de una auditoría de consistencia de formatos."""

    total: int
    con_puntos: int
    sin_puntos: int
    con_guion: int
    sin_guion: int
    con_espacios: int
    dv_mayuscula: int
    dv_minuscula: int
    formatos_distintos: list[tuple[str, int]]  # (formato, conteo)


def auditar_consistencia_formato(
    ruts: Sequence[str],
) -> AuditoriaFormato:
    """Analiza la consistencia de formatos en una secuencia de RUTs.

    Clasifica cada entrada según presencia de puntos, guiones, espacios
    y capitalización del DV. Útil para limpieza de datos: si una columna
    tiene 80% con puntos y 20% sin puntos, sabes que necesitas normalizar.

    Args:
        ruts: Secuencia de cadenas con RUTs.

    Returns:
        ``AuditoriaFormato`` con desglose por categoría de formato.
    """
    ...


@dataclass
class PerfilRut:
    """Perfil estadístico de una columna de RUTs."""

    total: int
    validos: int
    invalidos: int
    incompletos: int
    tasa_validez: float
    distribucion_longitud: dict[int, int]  # longitud base → conteo
    distribucion_dv: dict[str, int]  # dígito verificador → conteo


def perfilar_ruts(
    ruts: Sequence[str],
) -> PerfilRut:
    """Genera un perfil estadístico de una secuencia de RUTs.

    Calcula tasas de validez, distribución de longitudes de base,
    y distribución de dígitos verificadores. Los RUTs inválidos se
    excluyen de las distribuciones de longitud y DV.

    Args:
        ruts: Secuencia de cadenas con RUTs.

    Returns:
        ``PerfilRut`` con estadísticas agregadas.
    """
    ...


__all__ = [
    "InformeDuplicados",
    "AuditoriaFormato",
    "PerfilRut",
    "detectar_duplicados",
    "auditar_consistencia_formato",
    "perfilar_ruts",
]
```

**Verify**: `python -c "from rutificador.calidad_datos import detectar_duplicados, auditar_consistencia_formato, perfilar_ruts"` ejecuta sin error (aunque las funciones aún no están implementadas, los stubs deben ser importables).

### Step 2: Implementar `detectar_duplicados`

Implementar la función. Lógica:

1. Para cada entrada, ejecutar `Rut.parse(valor)`
2. Si `sensible_a_formato=False` y `resultado.estado == "valido"`, usar `resultado.normalizado` como clave de agrupación
3. Si `sensible_a_formato=True`, usar `resultado.original` como clave
4. Contar ocurrencias con `collections.Counter`
5. Retornar `InformeDuplicados` con: totales, y la lista de duplicados (solo los que aparecen >1 vez) ordenada por conteo descendente

IMPORTANTE: para la salida PII-safe, los valores en `duplicados` deben usar `Rut.enmascarar()` con `mantener=4` o bien mostrar solo la base normalizada (sin el DV), no el RUT completo.

**Verify**: 
```bash
.venv/bin/python -c "
from rutificador.calidad_datos import detectar_duplicados
r = detectar_duplicados(['12.345.678-5', '12345678-5', '98.765.432-1'])
print(r.total_unicos, r.total_duplicados)
"
# Esperado: 2 2 (o similar, 12.345.678-5 y 12345678-5 son el mismo)
```

### Step 3: Implementar `auditar_consistencia_formato`

Implementar la función. Lógica:

1. Para cada entrada, clasificar según características de formato:
   - `con_puntos`: si contiene `.` en la entrada original
   - `con_guion`: si contiene `-` en la entrada original
   - `con_espacios`: si contiene espacios
   - `dv_mayuscula`: si el DV es 'K' (mayúscula) vs 'k' (minúscula)
2. Agrupar los formatos distintos (ej: `"con_puntos+con_guion"`, `"sin_puntos+sin_guion"`, etc.)
3. Retornar el desglose

**Verify**: 
```bash
.venv/bin/python -c "
from rutificador.calidad_datos import auditar_consistencia_formato
a = auditar_consistencia_formato(['12.345.678-5', '12345678-k', '98765432-K'])
print(a.con_puntos, a.sin_puntos, a.dv_mayuscula, a.dv_minuscula)
"
```

### Step 4: Implementar `perfilar_ruts`

Implementar la función. Lógica:

1. Para cada entrada, `Rut.parse(valor)`
2. Clasificar por estado (valido, invalido, incompleto)
3. Para RUTs válidos: extraer longitud de `base` y `dv`, acumular distribuciones
4. Calcular `tasa_validez = validos / total`
5. Retornar `PerfilRut`

**Verify**: 
```bash
.venv/bin/python -c "
from rutificador.calidad_datos import perfilar_ruts
p = perfilar_ruts(['12.345.678-5', '98.765.432-1', '1-9', 'invalid'])
print(p.validos, p.invalidos, p.tasa_validez)
"
# Esperado: 3 1 (1-9 es válido: base=1 dv=9; 'invalid' es inválido)
```

### Step 5: Exportar desde `rutificador/__init__.py`

Agregar al `__init__.py`:

```python
from .calidad_datos import (
    InformeDuplicados,
    AuditoriaFormato,
    PerfilRut,
    detectar_duplicados,
    auditar_consistencia_formato,
    perfilar_ruts,
)
```

Agregar a `__all__` los 6 nombres.

**Verify**: 
```bash
.venv/bin/python -c "from rutificador import detectar_duplicados, auditar_consistencia_formato, perfilar_ruts"
```

### Step 6: Agregar el nuevo módulo a los contratos de `import-linter`

En `pyproject.toml`, el contrato `nucleo-no-depende-de-contrib` lista los módulos del núcleo (líneas 93-103). Agregar `rutificador.calidad_datos` a `source_modules`:

```toml
source_modules = [
    "rutificador.calidad_datos",
    "rutificador.config",
    ...
]
```

**Verify**: `lint-imports` → exit 0

### Step 7: Escribir tests

Crear `tests/test_calidad_datos.py` con el siguiente plan de casos. Seguir el patrón de `tests/test_rutificador.py` (pytest fixtures, `parametrize`, `caplog`).

Casos para `detectar_duplicados`:
1. Lista sin duplicados → `total_unicos == total_procesados`
2. Duplicado exacto (misma cadena) → detectado
3. Duplicado normalizado (`12.345.678-5` vs `12345678-5`) → detectado como duplicado
4. `sensible_a_formato=True` → no detecta el duplicado del caso 3
5. Lista vacía → manejo correcto
6. Entradas inválidas mezcladas con válidas → las inválidas se ignoran o reportan aparte
7. Verificar PII-safe: los valores retornados no contienen RUTs completos desenmascarados

Casos para `auditar_consistencia_formato`:
1. Todos con puntos → `con_puntos == total`
2. Mezcla con/sin puntos → ambos conteos > 0
3. DV mayúscula vs minúscula → correcto
4. Entradas con espacios → contabilizadas

Casos para `perfilar_ruts`:
1. Todos válidos → `tasa_validez == 1.0`
2. Mezcla válidos/inválidos → tasa correcta
3. Distribución de DV → verificar conteo correcto
4. Distribución de longitud de base → verificar

**Verify**: `python -m pytest tests/test_calidad_datos.py -q` → todos pasan

## Test plan

- Nuevo archivo: `tests/test_calidad_datos.py`
- ~15 casos de prueba entre las 3 funciones
- Patrón: `tests/test_rutificador.py` como referencia estructural
- Usar `@pytest.mark.parametrize` donde sea natural
- Incluir pruebas con `caplog` para verificar que las entradas inválidas se manejan sin excepciones
- Verificación: `python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` → ≥283 passed

## Done criteria

- [ ] `rutificador/calidad_datos.py` existe con 3 funciones + 3 dataclasses
- [ ] Las 3 funciones están implementadas y documentadas con docstrings Google-style en español
- [ ] `rutificador/__init__.py` exporta los 6 nuevos símbolos
- [ ] `import-linter` incluye `rutificador.calidad_datos` en el contrato de núcleo
- [ ] `tests/test_calidad_datos.py` con ≥15 tests que pasan
- [ ] `mypy --strict` pasa en el nuevo módulo
- [ ] Todos los gates CI pasan (ruff, mypy, deptry, lint-imports, pytest)
- [ ] Los resultados de los duplicados son PII-safe (usan `Rut.enmascarar()` con `mantener=4`)
- [ ] `plans/README.md` status row updated

## STOP conditions

- Si `import-linter` rechaza el nuevo módulo porque `source_modules` ya estaba fijo con una lista explícita (ver `pyproject.toml:93-103`), agregar `rutificador.calidad_datos` a esa lista y re-verificar
- Si alguna función tiene problemas de rendimiento con >100k entradas (timeout en tests), agregar un parámetro `limite` y documentar la complejidad O(n)
- Si `Rut.parse()` lanza excepción en vez de retornar `ValidacionResultado` con `estado="invalido"`, el código está usando la API incorrecta — verificar que se usa `Rut.parse()`, no el constructor `Rut()`
- Si los resultados de `detectar_duplicados` exponen RUTs completos en texto claro, revisar que se está usando `Rut.enmascarar()` con `mantener=4`

## Maintenance notes

- `calidad_datos` es parte del núcleo y no debe importar de `rutificador.contrib` ni de `rutificador.cli`.
- Las funciones aceptan `Sequence[str]`, no DataFrames. Si en el futuro se quiere integración directa con pandas/polars, los accessors en `contrib/` pueden delegar a estas funciones.
- Los valores en `InformeDuplicados.duplicados` solo muestran los últimos 4 dígitos de la base + DV para cumplir con PII. Si un usuario necesita el RUT completo (ej: para depuración interna), podría agregarse un parámetro `enmascarar=False` en una iteración futura.
- La detección de duplicados "fuzzy" (con distancia de edición) está fuera de este plan. El módulo `sugestor.py` ya tiene `distancia_levenshtein` que podría reutilizarse en una futura expansión.
