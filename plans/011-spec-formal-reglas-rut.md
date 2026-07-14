# Plan 011: Spec formal de reglas de validación RUT con test vectors

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving to the next step. If
> anything in the "STOP conditions" section occurs, stop and report — do not
> improvise. When done, update the status row for this plan in
> `plans/README.md`.

> **Drift check (run first)**: `git diff --stat aaca8c4..HEAD -- rutificador/utils.py rutificador/validador.py rutificador/rut.py rutificador/config.py`
> Si la lógica de DV, validación de formato o configuración cambió, proceder
> con precaución y verificar que los excerpts de "Current state" sigan siendo
> correctos.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW — es un artefacto de documentación, no modifica código.
- **Depends on**: none
- **Category**: docs / direction
- **Planned at**: commit `aaca8c4`, 2026-07-14

## Why this matters

La lógica de validación RUT está dispersa en 4 archivos (`utils.py`,
`validador.py`, `config.py`, `rut.py:nolexer()`), lo que hace que entender
"qué es exactamente un RUT válido" requiera leer ~200 líneas de código Python.
El roadmap de largo plazo planea ports a Rust→WASM y TypeScript; sin una
especificación formal con test vectors canónicos, esos ports duplicarán la
lógica bug-por-bug del intérprete Python en lugar de implementar contra una
especificación. Este plan produce esa especificación y los test vectors
asociados.

## Current state

**Cálculo de DV** (`rutificador/utils.py:123-164`):
```python
@lru_cache(maxsize=1024)
def calcular_digito_verificador(base_numerica, configuracion=CONFIGURACION_POR_DEFECTO):
    factores = cycle(configuracion.factores_verificacion)  # (2,3,4,5,6,7)
    suma_parcial = sum(int(d) * f for d, f in zip(reversed(base_numerica), factores))
    digito_verificador = (configuracion.modulo - suma_parcial % configuracion.modulo) % configuracion.modulo
    return str(digito_verificador) if digito_verificador < 10 else "k"
```

**Configuración** (`rutificador/config.py:10-17`):
```python
@dataclass(frozen=True)
class ConfiguracionRut:
    factores_verificacion: Tuple[int, ...] = (2, 3, 4, 5, 6, 7)
    modulo: int = 11
    max_digitos: int = 9
    min_digitos: int = 1
```

**Validación de formato** (`rutificador/validador.py:154`):
```python
RUT_REGEX = re.compile(r"^((?:\d{1,3}(?:\.\d{3})*)|\d+)(-([0-9kK]))?$")
```

**Normalización** (`rutificador/rut.py:232-288`): `Rut.normalizar()` aplica 9
pasos de limpieza (tipo, espacios, guiones alternativos, caracteres base,
separación base/DV, puntos, ceros, DV, reconstrucción).

Convenciones: el proyecto usa español para documentación, Google-style
docstrings, y pytest para tests.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` | 230 passed, 2 skipped |

## Scope

**In scope** (files to create/modify):
- `docs/especificacion-reglas-rut.md` — spec formal (crear)
- `tests/vectors/` — directorio de test vectors (crear)
- `tests/vectors/test_vectors_dv.json` — test vectors para DV (crear)
- `tests/vectors/test_vectors_validacion.json` — test vectors para validación (crear)
- `tests/test_spec_vectors.py` — test que verifica los vectors contra la
  implementación actual (crear)

**Out of scope** (do NOT touch):
- Código fuente en `rutificador/` — este plan es solo documentación y tests de
  caracterización.
- `ROADMAP.md` — ya se actualiza en el plan 008.
- Otros documentos en `docs/`.

## Git workflow

- Branch: `advisor/011-spec-formal-reglas-rut`
- Commits:
  1. `docs: agregar especificación formal de reglas de validación RUT`
  2. `test: agregar test vectors canónicos para DV y validación`
- No hacer push ni abrir PR a menos que el operador lo indique.

## Steps

### Step 1: Crear el documento de especificación formal

Crear `docs/especificacion-reglas-rut.md` con el siguiente contenido mínimo:

1. **Definición de RUT**: base numérica (1-9 dígitos) + guion + DV (0-9, K).
2. **Algoritmo de dígito verificador**: módulo 11 con factores (2,3,4,5,6,7)
   cíclicos, aplicados de derecha a izquierda. Fórmula: `11 - (suma % 11)`,
   con 11→0 y 10→K.
3. **Reglas de formato**:
   - Caracteres permitidos: dígitos, puntos (separador de miles en grupos de
     3), un guion antes del DV.
   - Dígito verificador: exactamente 1 carácter [0-9kK] después del guion.
   - Ceros a la izquierda: ignorados en la base.
4. **Reglas de normalización** (enumerar los 9 pasos de `Rut.normalizar()`).
5. **Modos de rigor**: ESTRICTO (rechaza espacios, guiones alternativos) vs
   FLEXIBLE (acepta y normaliza).
6. **Casos límite documentados**: RUT con base "0", RUT con solo base sin DV,
   RUT de 1 dígito, RUT de 9 dígitos, DV='K'.

El documento debe estar en español, usar Markdown con sintaxis matemática donde
aplique, y referenciar los archivos fuente (`file:line`) para trazabilidad.

**Verify**: `ls docs/especificacion-reglas-rut.md` existe.

### Step 2: Crear test vectors para cálculo de DV

Crear `tests/vectors/` y `tests/vectors/test_vectors_dv.json`:

```json
{
  "descripcion": "Test vectors canónicos para cálculo de dígito verificador RUT chileno",
  "algoritmo": "módulo 11, factores (2,3,4,5,6,7) cíclicos de derecha a izquierda",
  "formula": "dv = 11 - (suma % 11); si dv == 11 → 0; si dv == 10 → K",
  "casos": [
    {"base": "12345678", "dv_esperado": "5"},
    {"base": "98765432", "dv_esperado": "1"},
    {"base": "1", "dv_esperado": "9"},
    {"base": "0", "dv_esperado": "0"},
    {"base": "12345670", "dv_esperado": "k"},
    {"base": "99999999", "dv_esperado": "6"},
    {"base": "11111111", "dv_esperado": "2"},
    {"base": "100000000", "dv_esperado": "9"},
    {"base": "123456789", "dv_esperado": "2"},
    {"base": "50000000", "dv_esperado": "4"}
  ],
  "notas": [
    "El caso '12345670' produce DV='k' (10 → K).",
    "La base '0' es válida (representa RUT 0-0).",
    "Los factores se aplican de derecha a izquierda: el dígito más a la derecha se multiplica por 2, el siguiente por 3, etc."
  ]
}
```

Los casos deben incluir: RUTs conocidos, casos límite (1 dígito, 9 dígitos),
DV=K, y al menos un caso de cada longitud representativa.

**Verify**: `python -c "import json; json.load(open('tests/vectors/test_vectors_dv.json'))"` → sin errores.

### Step 3: Crear test vectors para validación completa

Crear `tests/vectors/test_vectors_validacion.json`:

```json
{
  "descripcion": "Test vectors canónicos para validación completa de RUT",
  "casos": [
    {"entrada": "12.345.678-5", "modo": "estricto", "estado_esperado": "valido", "normalizado": "12345678-5"},
    {"entrada": "12345678-5", "modo": "estricto", "estado_esperado": "valido", "normalizado": "12345678-5"},
    {"entrada": "12.345.678-9", "modo": "estricto", "estado_esperado": "invalido", "codigo_error": "DV_DISCORDANTE"},
    {"entrada": "12 345 678-5", "modo": "estricto", "estado_esperado": "invalido", "codigo_error": "CARACTERES_INVALIDOS"},
    {"entrada": "12 345 678-5", "modo": "flexible", "estado_esperado": "valido", "normalizado": "12345678-5"},
    {"entrada": "1-9", "modo": "flexible", "estado_esperado": "valido", "normalizado": "1-9"},
    {"entrada": "12345678", "modo": "estricto", "estado_esperado": "posible"},
    {"entrada": "12345670-k", "modo": "estricto", "estado_esperado": "valido", "normalizado": "12345670-k"},
    {"entrada": "12345670-K", "modo": "estricto", "estado_esperado": "valido", "normalizado": "12345670-k"},
    {"entrada": "", "modo": "estricto", "estado_esperado": "incompleto", "codigo_error": "RUT_VACIO"},
    {"entrada": "abc", "modo": "estricto", "estado_esperado": "invalido", "codigo_error": "CARACTERES_INVALIDOS"},
    {"entrada": "12.34.567-8", "modo": "estricto", "estado_esperado": "invalido", "codigo_error": "FORMATO_PUNTOS"},
    {"entrada": "000012345678-5", "modo": "flexible", "estado_esperado": "valido", "normalizado": "12345678-5"},
    {"entrada": "12345678-k", "modo": "estricto", "estado_esperado": "valido", "normalizado": "12345678-k"}
  ],
  "notas": [
    "En modo ESTRICTO, los espacios internos producen CARACTERES_INVALIDOS.",
    "En modo FLEXIBLE, los espacios se normalizan con advertencia NORMALIZACION_ESPACIOS.",
    "Una base sin DV (ej. '12345678') tiene estado 'posible', no 'valido'.",
    "Los puntos deben estar en grupos de 3 dígitos exactos; '12.34.567-8' es inválido."
  ]
}
```

**Verify**: `python -c "import json; json.load(open('tests/vectors/test_vectors_validacion.json'))"` → sin errores.

### Step 4: Crear test de caracterización que verifica los vectors

Crear `tests/test_spec_vectors.py`:

```python
"""Verifica que la implementación actual cumple la especificación formal.

Los test vectors en tests/vectors/ son la fuente canónica de verdad.
Este módulo los valida contra la implementación de rutificador.
"""

import json
from pathlib import Path

import pytest

from rutificador import Rut, RigorValidacion
from rutificador.utils import calcular_digito_verificador

VECTORS_DIR = Path(__file__).parent / "vectors"


def _cargar_vectors(nombre: str):
    with open(VECTORS_DIR / nombre, encoding="utf-8") as f:
        return json.load(f)


class TestVectoresDigitoVerificador:
    @pytest.mark.parametrize(
        "caso",
        _cargar_vectors("test_vectors_dv.json")["casos"],
        ids=lambda c: f"base={c['base']}",
    )
    def test_dv(self, caso):
        assert calcular_digito_verificador(caso["base"]) == caso["dv_esperado"]


class TestVectoresValidacion:
    @pytest.mark.parametrize(
        "caso",
        _cargar_vectors("test_vectors_validacion.json")["casos"],
        ids=lambda c: f"{c['entrada'][:20]} [{c['modo']}]",
    )
    def test_validacion(self, caso):
        modo = (
            RigorValidacion.ESTRICTO
            if caso["modo"] == "estricto"
            else RigorValidacion.FLEXIBLE
        )
        resultado = Rut.parse(caso["entrada"], modo=modo)

        assert resultado.estado == caso["estado_esperado"]

        if "normalizado" in caso:
            assert resultado.normalizado == caso["normalizado"]

        if "codigo_error" in caso:
            codigos = [e.codigo for e in resultado.errores]
            assert caso["codigo_error"] in codigos, (
                f"Esperado {caso['codigo_error']} en {codigos}"
            )
```

**Verify**: `python -m pytest tests/test_spec_vectors.py -v` → todos los tests
pasan.

### Step 5: Verificación final

```bash
python -m ruff check tests/test_spec_vectors.py && \
python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q
```

**Verify**: ruff clean, 230+ tests pasan (incluidos los nuevos de vectors).

## Test plan

El plan en sí crea tests de caracterización (`tests/test_spec_vectors.py`) que
validan los test vectors contra la implementación actual. Si la implementación
cambia en el futuro, estos tests deben actualizarse para reflejar la nueva
especificación (o fallar si el cambio es una regresión).

Los test vectors están en JSON para que sean legibles por cualquier lenguaje
(Rust, TypeScript, etc.) y sirvan como fixtures cross-platform para los ports
futuros.

## Done criteria

- [ ] `docs/especificacion-reglas-rut.md` existe y cubre: definición,
  algoritmo DV, reglas de formato, normalización, modos de rigor, casos límite
- [ ] `tests/vectors/test_vectors_dv.json` existe con ≥10 casos
- [ ] `tests/vectors/test_vectors_validacion.json` existe con ≥12 casos
  cubriendo estados válido, inválido, posible, incompleto
- [ ] `tests/test_spec_vectors.py` existe y todos los tests parametrizados pasan
- [ ] `ruff check` pasa en el nuevo archivo de test
- [ ] Ningún archivo en `rutificador/` fue modificado
- [ ] `plans/README.md` status row actualizada

## STOP conditions

- Si alguno de los test vectors no coincide con la implementación actual:
  **NO modificar la implementación**. En su lugar, corregir el vector para que
  refleje el comportamiento real (este plan es de caracterización, no de
  cambio de comportamiento).
- Si el directorio `tests/vectors/` ya existe con contenido incompatible:
  reportar y preguntar si se debe hacer merge o reemplazar.
- Si `rutificador.utils.calcular_digito_verificador` cambió de firma o
  algoritmo: reportar el drift y detenerse.

## Maintenance notes

- Cuando el algoritmo de DV cambie (ej. si se adopta un nuevo módulo o
  factores), actualizar los test vectors PRIMERO y luego la implementación.
  Los tests de vectors deben fallar antes del cambio y pasar después.
- Los archivos JSON en `tests/vectors/` deben mantenerse sincronizados con
  `docs/especificacion-reglas-rut.md`.
- Para el port a Rust/WASM/TypeScript, estos JSON son la fuente canónica de
  verdad. El port debe pasar los mismos vectors.
- Si se agregan nuevos modos de rigor o códigos de error, extender
  `test_vectors_validacion.json` con los nuevos casos.
