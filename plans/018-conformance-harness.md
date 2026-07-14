# Plan 018: Harness de conformidad desde especificación — test vectors publicables y runner standalone

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 6b61e0e..HEAD -- tests/vectors/ tests/test_spec_vectors.py docs/especificacion-reglas-rut.md`
> If the test vectors or spec changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S–M
- **Risk**: LOW
- **Category**: direction
- **Depends on**: none (the vectors already exist)
- **Planned at**: commit `6b61e0e`, 2026-07-14

## Why this matters

La especificación formal (`docs/especificacion-reglas-rut.md`) y los test vectors canónicos (`tests/vectors/`) ya existen como resultado del plan 011. Pero están enterrados dentro del repo Python — un implementador de un port en Rust, TypeScript o Go no puede consumirlos fácilmente. Este plan empaqueta los test vectors como un artifact standalone versionado, crea un harness de conformidad que cualquier implementación puede ejecutar, y lo integra en CI como guardián de regresiones. Es el prerequisito para los ports cross-platform del roadmap (`ROADMAP.md:92-94`).

## Current state

- `tests/vectors/test_vectors_dv.json` — 12 casos de cálculo de DV con base + dv_esperado + configuración de algoritmo
- `tests/vectors/test_vectors_validacion.json` — casos de validación completos con entrada, modo, estado_esperado, normalizado, codigo_error
- `tests/test_spec_vectors.py` — 56 líneas, valida la implementación Python contra los vectores usando `pytest.mark.parametrize`
- `docs/especificacion-reglas-rut.md` — especificación formal de reglas de validación RUT

Los vectores actuales están en un formato ad-hoc (estructura de array JSON plano). Para ser publicables y versionables, necesitan un JSON Schema y una estructura estable.

Convenciones: tests en `tests/` siguen pytest con fixtures y parametrize. La CI ejecuta todos los tests con `pytest`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `.venv/bin/python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` | ≥268 passed |
| Run conformance | `.venv/bin/python scripts/conformance.py` | exit 0 |
| JSON Schema validate | `.venv/bin/python -c "import jsonschema; ..."` | exit 0 (requires `pip install jsonschema`) |
| Export vectors | `.venv/bin/python scripts/export_vectors.py` | exit 0, `dist/vectors/` populated |

## Scope

**In scope** (files to create or modify):
- `tests/vectors/schema.json` — NUEVO: JSON Schema para los test vectors
- `tests/vectors/conformance.json` — NUEVO: archivo unificado de conformidad con schema y metadatos de versión
- `scripts/conformance.py` — NUEVO: runner standalone de conformidad (sin dependencia de pytest)
- `scripts/export_vectors.py` — NUEVO: exporta vectors a formatos alternativos (YAML, JSON plano)
- `.github/workflows/conformance.yml` — NUEVO: workflow que publica los vectors como artifact versionado
- `tests/test_spec_vectors.py` — MODIFICAR: usar el archivo unificado `conformance.json`

**Out of scope** (do NOT touch):
- `docs/especificacion-reglas-rut.md` — la especificación ya está completa
- `rutificador/` — sin cambios en código fuente
- Los valores de los test vectors — solo se re-empaquetan, no se modifican
- Implementaciones en otros lenguajes — este plan solo produce el artifact para que otros lo consuman

## Git workflow

- Branch: `advisor/018-conformance-harness`
- Commit per artifact added; message style: `feat(vectors): <description>`
- Example: `feat(vectors): agregar schema JSON y archivo unificado de conformidad`
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Crear JSON Schema para los test vectors

Crear `tests/vectors/schema.json` que defina la estructura de los vectores:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://tooltician.com/rutificador/vectors/schema.json",
  "title": "RUT Conformance Test Vectors Schema",
  "description": "Schema para vectores de prueba de conformidad del validador de RUT chileno",
  "type": "object",
  "required": ["version", "spec_version", "descripcion", "algoritmo", "configuracion", "casos_dv", "casos_validacion"],
  "properties": {
    "version": {
      "type": "string",
      "description": "Versión semántica de los vectores de prueba"
    },
    "spec_version": {
      "type": "string",
      "description": "Versión de la especificación formal que estos vectores validan"
    },
    "descripcion": { "type": "string" },
    "algoritmo": {
      "type": "object",
      "required": ["nombre", "formula"],
      "properties": {
        "nombre": { "type": "string" },
        "formula": { "type": "string" }
      }
    },
    "configuracion": {
      "type": "object",
      "required": ["factores_verificacion", "modulo", "max_digitos", "min_digitos"],
      "properties": {
        "factores_verificacion": {
          "type": "array",
          "items": { "type": "integer" }
        },
        "modulo": { "type": "integer" },
        "max_digitos": { "type": "integer" },
        "min_digitos": { "type": "integer" }
      }
    },
    "casos_dv": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["base", "dv_esperado"],
        "properties": {
          "base": { "type": "string", "pattern": "^[0-9]+$" },
          "dv_esperado": { "type": "string", "pattern": "^[0-9kK]$" },
          "notas": { "type": "string" }
        }
      }
    },
    "casos_validacion": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["entrada", "modo", "estado_esperado"],
        "properties": {
          "entrada": { "type": "string" },
          "modo": { "type": "string", "enum": ["estricto", "flexible"] },
          "estado_esperado": { "type": "string", "enum": ["valido", "invalido", "posible", "incompleto"] },
          "normalizado": { "type": "string" },
          "codigo_error": { "type": "string" },
          "notas": { "type": "string" }
        }
      }
    }
  }
}
```

**Verify**: validar el schema contra sí mismo y contra los datos existentes:
```bash
python -c "
import json
from jsonschema import validate

with open('tests/vectors/schema.json') as f:
    schema = json.load(f)

# El schema debe ser válido contra el meta-schema
# (jsonschema lo valida implícitamente)
print('Schema válido')

# Cargar datos existentes y mapearlos al nuevo formato
with open('tests/vectors/test_vectors_dv.json') as f:
    dv_data = json.load(f)
with open('tests/vectors/test_vectors_validacion.json') as f:
    val_data = json.load(f)

print(f'{len(dv_data[\"casos\"])} casos DV, {len(val_data[\"casos\"])} casos validación')
print('Datos existentes OK')
"
```

### Step 2: Crear archivo unificado `conformance.json`

Crear `tests/vectors/conformance.json` unificando los dos archivos existentes con el schema definido:

```json
{
  "version": "1.0.0",
  "spec_version": "1.0",
  "descripcion": "Test vectors canónicos para conformidad de implementaciones de RUT chileno",
  "algoritmo": {
    "nombre": "módulo 11 con factores cíclicos",
    "formula": "dv = 11 - (suma % 11); si dv == 11 → 0; si dv == 10 → K"
  },
  "configuracion": {
    "factores_verificacion": [2, 3, 4, 5, 6, 7],
    "modulo": 11,
    "max_digitos": 9,
    "min_digitos": 1
  },
  "casos_dv": [
    ... (copiar de test_vectors_dv.json["casos"])
  ],
  "casos_validacion": [
    ... (copiar de test_vectors_validacion.json["casos"])
  ]
}
```

**Verify**: validar contra el schema:
```bash
python -c "
import json
from jsonschema import validate, ValidationError

with open('tests/vectors/schema.json') as f:
    schema = json.load(f)
with open('tests/vectors/conformance.json') as f:
    data = json.load(f)

try:
    validate(instance=data, schema=schema)
    print('conformance.json válido contra schema.json')
except ValidationError as e:
    print(f'Error de validación: {e}')
    exit(1)
"
```

### Step 3: Crear runner de conformidad standalone

Crear `scripts/conformance.py` — un script que no depende de pytest y puede ejecutarse contra cualquier implementación que exponga una API compatible:

```python
#!/usr/bin/env python3
"""Harness de conformidad para implementaciones de validador de RUT chileno.

Uso:
    python scripts/conformance.py              # valida la implementación Python
    python scripts/conformance.py --vectors path/to/conformance.json  # vectors personalizados

El script carga los test vectors canónicos y verifica que la implementación
local produce los resultados esperados para cada caso.

Exit code 0 = todos los casos pasan. Exit code 1 = hay fallos.
"""

import json
import sys
from pathlib import Path
from typing import Any

# --- Sección de adaptación para implementaciones externas ---
# Para usar con otra implementación, reemplaza estas funciones.

def dv_implementation(base: str, config: dict) -> str:
    """Calcula el dígito verificador para una base numérica."""
    from rutificador.utils import calcular_digito_verificador
    return calcular_digito_verificador(base)

def validation_implementation(entrada: str, modo: str, config: dict) -> dict:
    """Valida una entrada y retorna {estado, normalizado, codigos_error}."""
    from rutificador import Rut, RigorValidacion
    from rutificador.config import ConfiguracionRut

    modo_enum = RigorValidacion.ESTRICTO if modo == "estricto" else RigorValidacion.FLEXIBLE
    resultado = Rut.parse(entrada, modo=modo_enum)
    return {
        "estado": resultado.estado,
        "normalizado": resultado.normalizado,
        "codigos_error": [e.codigo for e in resultado.errores],
    }

# --- Fin de sección de adaptación ---


def run_conformance(vectors_path: Path) -> int:
    with open(vectors_path, encoding="utf-8") as f:
        vectors = json.load(f)

    config = vectors["configuracion"]
    failures = 0
    total = 0

    print(f"Vectors v{vectors['version']} (spec v{vectors['spec_version']})")
    print(f"Algoritmo: {vectors['algoritmo']['nombre']}")
    print()

    # Casos de DV
    print("--- Cálculo de Dígito Verificador ---")
    for caso in vectors["casos_dv"]:
        total += 1
        result = dv_implementation(caso["base"], config)
        expected = caso["dv_esperado"].lower()
        status = "PASS" if result.lower() == expected else "FAIL"
        if status == "FAIL":
            failures += 1
        print(f"  [{status}] base={caso['base']:>10}  esperado={expected}  obtenido={result}")

    # Casos de validación
    print("\n--- Validación de RUT ---")
    for caso in vectors["casos_validacion"]:
        total += 1
        result = validation_implementation(caso["entrada"], caso["modo"], config)
        estado_ok = result["estado"] == caso["estado_esperado"]
        codigo_ok = True
        if "codigo_error" in caso:
            codigo_ok = caso["codigo_error"] in result.get("codigos_error", [])

        status = "PASS" if (estado_ok and codigo_ok) else "FAIL"
        if status == "FAIL":
            failures += 1
        print(f"  [{status}] entrada='{caso['entrada']}'  modo={caso['modo']}  "
              f"estado={result['estado']} (esperado={caso['estado_esperado']})")

    print(f"\n{'='*50}")
    print(f"Resultado: {total - failures}/{total} pasaron")
    if failures:
        print(f"  {failures} FALLOS")
    return 0 if failures == 0 else 1


def main():
    default = Path(__file__).parent.parent / "tests" / "vectors" / "conformance.json"
    vectors_path = default
    if len(sys.argv) > 2 and sys.argv[1] == "--vectors":
        vectors_path = Path(sys.argv[2])
    elif len(sys.argv) > 1:
        vectors_path = Path(sys.argv[1])

    if not vectors_path.exists():
        print(f"Error: archivo de vectores no encontrado: {vectors_path}")
        return 1

    return run_conformance(vectors_path)


if __name__ == "__main__":
    sys.exit(main())
```

**Verify**: `python scripts/conformance.py` → exit 0, todos los casos PASS.

### Step 4: Crear script de exportación de vectores

Crear `scripts/export_vectors.py` para generar formatos alternativos:

```python
#!/usr/bin/env python3
"""Exporta los test vectors canónicos a formatos alternativos.

Uso:
    python scripts/export_vectors.py --format yaml  # YAML
    python scripts/export_vectors.py --format json  # JSON plano (sin schema)
    python scripts/export_vectors.py --all          # todos los formatos
"""

import json
import sys
from pathlib import Path


def export_json(vectors, output_dir):
    path = output_dir / "conformance.json"
    path.write_text(json.dumps(vectors, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  JSON → {path}")

def export_yaml(vectors, output_dir):
    try:
        import yaml
    except ImportError:
        print("  YAML: PyYAML no instalado. Saltando.")
        return
    path = output_dir / "conformance.yaml"
    path.write_text(yaml.dump(vectors, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"  YAML → {path}")


def main():
    vectors_dir = Path(__file__).parent.parent / "tests" / "vectors"
    with open(vectors_dir / "conformance.json", encoding="utf-8") as f:
        vectors = json.load(f)

    output_dir = Path("dist/vectors")
    output_dir.mkdir(parents=True, exist_ok=True)

    export_json(vectors, output_dir)
    export_yaml(vectors, output_dir)

    print(f"\nVectors exportados a {output_dir}/")

if __name__ == "__main__":
    main()
```

**Verify**: `python scripts/export_vectors.py --all` → crea `dist/vectors/conformance.json` y opcionalmente `.yaml`.

### Step 5: Actualizar `test_spec_vectors.py` para usar `conformance.json`

Modificar `tests/test_spec_vectors.py` para cargar desde el archivo unificado:

Cambiar la línea 19:
```python
    with open(VECTORS_DIR / nombre, encoding="utf-8") as f:
```
A usar `conformance.json` como fuente única. Los casos DV se toman de `data["casos_dv"]` y los de validación de `data["casos_validacion"]`.

**Verify**: `python -m pytest tests/test_spec_vectors.py -q` → todos los tests pasan usando el nuevo archivo unificado.

### Step 6: Agregar workflow de CI para publicar vectores

Crear `.github/workflows/conformance.yml`:

```yaml
name: Publicar vectores de conformidad

on:
  push:
    branches: [ master ]
    paths:
      - 'tests/vectors/**'
      - 'docs/especificacion-reglas-rut.md'
  workflow_dispatch:

jobs:
  publish-vectors:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - name: Validar vectores contra schema
        run: |
          pip install jsonschema
          python -c "
          import json
          from jsonschema import validate
          with open('tests/vectors/schema.json') as f:
              schema = json.load(f)
          with open('tests/vectors/conformance.json') as f:
              data = json.load(f)
          validate(instance=data, schema=schema)
          print('Vectores válidos contra schema')
          "

      - name: Verificar conformidad de implementación Python
        run: |
          pip install -e .
          python scripts/conformance.py

      - name: Exportar vectores
        run: |
          python scripts/export_vectors.py --all

      - name: Subir vectores como artifact
        uses: actions/upload-artifact@v7
        with:
          name: rutificador-conformance-vectors
          path: dist/vectors/
```

**Verify**: el workflow debe ser sintácticamente válido (revisión manual del YAML).

### Step 7: Verificación final

```bash
# Runner de conformidad
python scripts/conformance.py

# Tests actualizados
python -m pytest tests/test_spec_vectors.py -q

# Suite completa
python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q

# Exportación
python scripts/export_vectors.py --all
ls dist/vectors/
```

## Test plan

- `tests/test_spec_vectors.py` actualizado para usar `conformance.json` como fuente única
- Los 12 casos DV + N casos de validación deben pasar
- `scripts/conformance.py` debe retornar exit 0 cuando todos los casos pasan
- `scripts/conformance.py` debe retornar exit 1 si algún caso falla (probar temporalmente modificando un vector)

## Done criteria

- [ ] `tests/vectors/schema.json` define el JSON Schema de los vectores
- [ ] `tests/vectors/conformance.json` unifica los dos archivos existentes en uno solo con metadatos de versión
- [ ] `scripts/conformance.py` existe y pasa todos los casos (exit 0)
- [ ] `scripts/export_vectors.py` existe y genera `dist/vectors/conformance.json`
- [ ] `tests/test_spec_vectors.py` usa `conformance.json` como fuente
- [ ] `.github/workflows/conformance.yml` valida, verifica y publica vectores
- [ ] Todos los tests existentes siguen pasando
- [ ] `plans/README.md` status row updated

## STOP conditions

- Si `jsonschema` no está disponible en el entorno, instalar con `pip install jsonschema` (es solo para validación en CI, no es dependencia runtime)
- Si los archivos `test_vectors_dv.json` y `test_vectors_validacion.json` tienen más campos de los documentados aquí, incluirlos en el schema y en `conformance.json`
- Si modificar `test_spec_vectors.py` rompe otros tests que dependen de la estructura antigua, verificar con `grep -rn "test_vectors_dv\|test_vectors_validacion" tests/` y actualizar todas las referencias
- Si `scripts/conformance.py` falla en algún caso, el vector o la implementación están mal — corregir antes de continuar

## Maintenance notes

- Los test vectors son versionados independientemente de la librería. `conformance.json` tiene su propio campo `version`. Cuando se agreguen nuevos casos, incrementar la versión de vectors.
- Cualquier cambio en el algoritmo de DV o reglas de validación DEBE reflejarse tanto en `docs/especificacion-reglas-rut.md` como en `tests/vectors/conformance.json` y en el schema.
- El harness `scripts/conformance.py` está diseñado para que implementadores externos copien solo la "sección de adaptación" y reemplacen las funciones `dv_implementation` y `validation_implementation` por las de su propio lenguaje.
- El workflow `conformance.yml` publica los vectores como artifact de CI. Si se quiere publicar como release de GitHub o como paquete npm/PyPI, eso requeriría un plan separado.
