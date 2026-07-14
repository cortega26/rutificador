# Plan 017: Spike — extensión nativa PyO3 para el camino caliente de validación

> **Executor instructions**: This is a **spike**, not a full implementation.
> The goal is to answer: *"Is a PyO3/Rust native extension worth the
> maintenance cost for rutificador?"* You will build a minimal proof-of-concept
> that accelerates the DV calculation hot path, benchmark it against the pure
> Python baseline, and produce a go/no-go recommendation with evidence.
>
> Run every verification command and confirm the expected result before moving
> to the next step. If anything in the "STOP conditions" section occurs, stop
> and report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 6b61e0e..HEAD -- rutificador/utils.py rutificador/config.py tests/benchmarks/`
> If the hot path code changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, update the benchmarks to match.

## Status

- **Priority**: P3
- **Effort**: L (but this spike is S–M — only the PoC)
- **Risk**: HIGH (new toolchain, maintenance burden)
- **Depends on**: 018 (conformance test harness) — recommended so the native implementation can be validated against canonical test vectors
- **Category**: direction (spike)
- **Planned at**: commit `6b61e0e`, 2026-07-14

## Why this matters

El cálculo de dígito verificador y la validación de formato son las operaciones más frecuentes en rutificador — cada `Rut.parse()`, cada `validar_flujo_ruts()`, y cada `ProcesadorLotesRut.validar_lista_ruts()` pasan por estas funciones. La implementación actual es Python puro (`utils.py:159-164` para DV, `validador.py` para formato). Un port a Rust vía PyO3 podría ofrecer 10–100× speedup en el camino caliente, eliminando también el overhead de serialización inter-proceso del modo paralelo. Además, una extensión Rust sería la base para los ports WASM y TypeScript listados en el roadmap de largo plazo (`ROADMAP.md:92-94`).

Este spike NO implementa el port completo. Implementa SOLO el cálculo de DV en Rust/PyO3, lo compara con el baseline Python, y produce una recomendación fundamentada.

## Current state

El hot path actual está en dos funciones:

**Cálculo de DV** (`rutificador/utils.py`, función `calcular_digito_verificador`):
```python
def calcular_digito_verificador(
    base: str, configuracion: ConfiguracionRut = CONFIGURACION_POR_DEFECTO
) -> str:
    base_str = str(base)
    suma = 0
    factores = configuracion.factores_verificacion
    idx_factor = 0
    for i in range(len(base_str) - 1, -1, -1):
        digito = int(base_str[i])
        suma += digito * factores[idx_factor % len(factores)]
        idx_factor += 1
    resto = suma % configuracion.modulo
    digito_verificador = configuracion.modulo - resto
    if digito_verificador == 11:
        return "0"
    elif digito_verificador == 10:
        return "K"
    else:
        return str(digito_verificador)
```

El benchmark existente: `tests/benchmarks/` y `tests/test_benchmark.py` usan `pytest-benchmark`.

Configuración por defecto (`config.py:14-16`):
```python
factores_verificacion: Tuple[int, ...] = (2, 3, 4, 5, 6, 7)
modulo: int = 11
```

La especificación formal del algoritmo está en `docs/especificacion-reglas-rut.md` §2, con test vectors en `tests/vectors/test_vectors_dv.json`.

**Convenciones relevantes**:
- El proyecto usa Poetry para gestión de dependencias (`pyproject.toml`)
- Python ≥3.10. Una extensión nativa debe compilar wheels para cp310–cp314, manylinux + musllinux + macOS + Windows
- El núcleo tiene cero dependencias runtime. Agregar una extensión nativa rompe esto técnicamente, aunque PyO3 wheels son autocontenidos
- Los tests siguen `tests/test_rutificador.py` como patrón

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Rust toolchain | `rustc --version` | ≥1.75 |
| Create PyO3 project | `maturin new rutificador-core` | project created |
| Build wheel | `cd rutificador-core && maturin develop --release` | exit 0 |
| Python import | `python -c "import rutificador_core"` | exit 0 |
| Benchmark | `.venv/bin/python -m pytest tests/benchmarks/ --benchmark-only -q` | exits 0 |

## Scope

**In scope** (create):
- `rutificador-core/` — directorio separado con proyecto PyO3 (Rust)
  - `Cargo.toml`, `src/lib.rs` con función `calcular_dv_rust(base: &str) -> String`
- `scripts/bench_dv_comparison.py` — script de benchmark comparativo
- `plans/017-SPIKE-NOTES.md` — informe de resultados y recomendación

**Out of scope** (do NOT modify):
- `rutificador/` — ningún cambio en el paquete Python existente
- No integrar la extensión en el paquete principal — eso se decide después del spike
- No implementar validación de formato en Rust — solo DV
- No configurar CI/CD para compilar wheels multiplataforma — eso es parte de un plan de implementación futuro

## Git workflow

- Branch: `advisor/017-pyO3-spike`
- Commit message style: `spike(pyo3): <description>`
- Example: `spike(pyo3): implementar cálculo de DV en Rust con benchmark comparativo`
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Verificar que Rust está instalado

```bash
rustc --version
cargo --version
```

Si no está instalado: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`

**Verify**: `rustc --version` → versión ≥1.75

### Step 2: Crear proyecto PyO3 con maturin

```bash
pip install maturin
maturin new rutificador-core --bindings pyo3
cd rutificador-core
```

Esto crea:
```
rutificador-core/
├── Cargo.toml
├── pyproject.toml
└── src/
    └── lib.rs
```

### Step 3: Implementar el cálculo de DV en Rust

Reemplazar el contenido de `src/lib.rs` con:

```rust
use pyo3::prelude::*;

const FACTORS: [u32; 6] = [2, 3, 4, 5, 6, 7];
const MODULUS: u32 = 11;

#[pyfunction]
fn calcular_dv_rust(base: &str) -> PyResult<String> {
    let mut sum: u32 = 0;
    let mut factor_idx = 0usize;

    for ch in base.chars().rev() {
        let digit = ch.to_digit(10).ok_or_else(|| {
            pyo3::exceptions::PyValueError::new_err(format!(
                "Base contiene carácter no numérico: '{}'",
                ch
            ))
        })?;
        sum += digit * FACTORS[factor_idx % FACTORS.len()];
        factor_idx += 1;
    }

    let remainder = sum % MODULUS;
    let dv = MODULUS - remainder;

    let result = match dv {
        11 => "0".to_string(),
        10 => "K".to_string(),
        _ => dv.to_string(),
    };

    Ok(result)
}

#[pymodule]
fn rutificador_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calcular_dv_rust, m)?)?;
    Ok(())
}
```

**Verify**: 
```bash
cd rutificador-core
maturin develop --release
cd ..
python -c "from rutificador_core import calcular_dv_rust; print(calcular_dv_rust('12345678'))"
# Esperado: 5
```

### Step 4: Validar el DV de Rust contra los test vectors canónicos

Ejecutar una validación rápida contra los vectores:

```bash
python -c "
import json
from rutificador_core import calcular_dv_rust

with open('tests/vectors/test_vectors_dv.json') as f:
    vectors = json.load(f)

for entry in vectors:
    base = entry['base']
    expected = str(entry['dv'])
    result = calcular_dv_rust(base)
    assert result == expected, f'Base {base}: esperado {expected}, obtenido {result}'
print(f'{len(vectors)} vectores verificados OK')
"
```

**Verify**: todos los vectores pasan sin errores.

### Step 5: Escribir benchmark comparativo

Crear `scripts/bench_dv_comparison.py`:

```python
"""Benchmark comparativo: cálculo DV Python vs Rust."""

import time
import sys
sys.path.insert(0, '.')

from rutificador.utils import calcular_digito_verificador
from rutificador_core import calcular_dv_rust

BASES = [
    "1", "12", "123", "1234", "12345", "123456", "1234567", "12345678",
    "99999999", "1000000", "50000000", "76000000", "12345678",
]

def bench_python(iterations: int = 100_000):
    start = time.perf_counter()
    for _ in range(iterations):
        for base in BASES:
            calcular_digito_verificador(base)
    elapsed = time.perf_counter() - start
    return elapsed

def bench_rust(iterations: int = 100_000):
    start = time.perf_counter()
    for _ in range(iterations):
        for base in BASES:
            calcular_dv_rust(base)
    elapsed = time.perf_counter() - start
    return elapsed

if __name__ == "__main__":
    ITER = 100_000
    print(f"Benchmark: {len(BASES)} bases × {ITER} iteraciones")
    print(f"{'='*50}")

    # Warmup
    bench_python(1000)
    bench_rust(1000)

    t_py = bench_python(ITER)
    t_rs = bench_rust(ITER)

    print(f"Python: {t_py:.4f}s")
    print(f"Rust:   {t_rs:.4f}s")
    print(f"Speedup: {t_py / t_rs:.1f}×")
```

**Verify**: 
```bash
python scripts/bench_dv_comparison.py
```
El speedup debe ser ≥5×. Si es menor, documentarlo — sigue siendo útil, pero el caso de negocio es más débil.

### Step 6: Documentar el spike en SPIKE NOTES

Crear `plans/017-SPIKE-NOTES.md` con el formato de `plans/006-SPIKE-NOTES.md`:

1. **Setup**: Rust/PyO3 versión, maturin versión, plataforma
2. **Resultados del benchmark**: tabla con los números exactos
3. **Validación**: todos los test vectors pasan (Sí/No)
4. **Factores de decisión**:
   - **A favor**: speedup medido, habilitante para WASM/TypeScript, elimina overhead de proceso en paralelo
   - **En contra**: nueva toolchain (Rust + maturin), compilación de wheels multiplataforma es compleja (CI matrix), dependencia runtime de facto (aunque el wheel sea autocontenido), mantenimiento a largo plazo para un solo maintainer
5. **Recomendación**: Go / No-go con justificación

### Step 7: Si es GO — esbozar el plan de implementación completo

Si la recomendación es GO, agregar a `plans/017-SPIKE-NOTES.md` un esbozo de lo que implicaría el plan completo:

1. Mover `rutificador-core` dentro del repo como un subpaquete
2. Integrar con Poetry (usando `maturin` como build backend o manteniéndolo como paquete separado)
3. Compilar wheels multiplataforma en CI (manylinux, musllinux, macOS, Windows) para cp310–cp314
4. Crear un fallback Python puro si la extensión nativa no está disponible
5. Reemplazar `calcular_digito_verificador` en `utils.py` con una llamada a la extensión nativa (con fallback)
6. Extender a validación de formato en Rust (segunda fase)

## Test plan

- Validación contra `tests/vectors/test_vectors_dv.json` — todos los vectores deben coincidir (Step 4)
- Benchmark comparativo con ≥10× speedup esperado (Step 5)
- El benchmark no debe regresionar: ejecutar `python -m pytest tests/test_benchmark.py --benchmark-only -q` antes y después para asegurar que no hay impacto en el código Python existente

## Done criteria

- [ ] `rutificador-core/` existe con `Cargo.toml` y `src/lib.rs`
- [ ] `calcular_dv_rust` pasa todos los test vectors canónicos
- [ ] `scripts/bench_dv_comparison.py` existe y corre exitosamente
- [ ] `plans/017-SPIKE-NOTES.md` con resultados, análisis y recomendación Go/No-go
- [ ] Si Go: esbozo de plan de implementación completo incluido en SPIKE NOTES
- [ ] `plans/README.md` status row updated

## STOP conditions

- Si Rust no está instalado y no se puede instalar (entorno restringido), documentar en SPIKE NOTES y marcarlo como bloqueado
- Si `maturin develop --release` falla por incompatibilidad de versiones (Python, Rust, PyO3), documentar las versiones exactas y marcar como bloqueado
- Si el speedup es <2×, el caso de negocio es débil — documentar como No-go con justificación
- Si los test vectors no pasan (el cálculo de Rust produce resultados diferentes), hay un bug en la implementación — revisar y corregir antes de continuar

## Maintenance notes

- `rutificador-core/` es un proyecto separado. No se integra en el paquete Python principal como parte de este spike.
- Si el spike resulta en GO, el plan de implementación completo debe abordar: CI/CD de compilación de wheels, estrategia de fallback, y documentación para contribuidores sobre el toolchain Rust.
- La especificación formal (`docs/especificacion-reglas-rut.md`) y los test vectors son la fuente de verdad para validar la implementación nativa. Cualquier cambio en el algoritmo debe reflejarse en ambos.
- PyO3 tiene buen soporte para WASM (vía `wasm-pack`), lo que hace viable el port a navegador/TypeScript si la extensión Rust existe.
