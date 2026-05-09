# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands

```bash
# Install dev dependencies (use venv)
pip install -r requirements-dev.txt
pip install -e .

# Run all tests
pytest -q

# Run a single test file
pytest tests/test_rutificador.py -v --tb=short

# Run a single test
pytest tests/test_rutificador.py::test_nombre -v

# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy rutificador/ --ignore-missing-imports

# Security scan
bandit -r rutificador/

# Pre-commit (black + flake8)
pre-commit run --all-files
```

## Architecture

`rutificador` is a Python library for validating, calculating, and formatting Chilean RUTs (Rol Único Tributario). Package name on PyPI: `rutificador`.

### Core Module Layer (`rutificador/`)

- **`config.py`** — Configuration dataclasses: `ConfiguracionRut` (factores_verificacion, modulo, min/max_digitos), `RigorValidacion` enum (ESTRICTO/FLEXIBLE/LEGADO).
- **`validador.py`** — `ValidadorRut`: regex-based format validation, base normalization, DV validation. Supports configurable rigor modes.
- **`rut.py`** — Core `Rut` class: constructor validates RUT, stores `base` (RutBase) + computed `digito_verificador`. Static methods: `parse()` (incremental, no exceptions), `normalizar()`, `enmascarar()`, `sugerir()`, `mejorar()`. LRU-cached factory `obtener_rut()`.
- **`procesador.py`** — `ProcesadorLotesRut`: batch validation/formatting with optional parallel execution (ProcessPoolExecutor or ThreadPoolExecutor). Streaming via `flujo()` / `validar_flujo_ruts()`. Returns `ResultadoLote` with `RutProcesado` metadata.
- **`formatter.py`** — Strategy pattern: `FormateadorRut` ABC with `FormateadorCSV`, `FormateadorXML`, `FormateadorJSON`. `FabricaFormateadorRut` registry.
- **`cli.py`** — Argparse CLI: `rutificador validar`, `rutificador formatear`, `rutificador enmascarar`, `rutificador info`. Streams large files, supports --paralelo, --format (text/json/jsonl/csv/xml), --mejorar, --sugerir.
- **`utils.py`** — `calcular_digito_verificador()` (lru_cached), `normalizar_base_rut()`, `_limpiar_entrada()` (Unicode NFKC normalization), `configurar_registro()`, `monitor_de_rendimiento` decorator.
- **`errores.py`** — Error code definitions with stable codigos (DV_DISCORDANTE, CARACTERES_INVALIDOS, etc.) and severity levels.
- **`exceptions.py`** — Exception hierarchy: `ErrorRut` → `ErrorValidacionRut` → `ErrorFormatoRut` / `ErrorDigitoRut` / `ErrorLongitudRut`. All PII-sanitized before logging.
- **`sugestor.py`** — Fuzzy matching engine for typo correction (transpositions, character swaps).
- **`version.py`** — Single source of version.

### Contrib Module (`rutificador/contrib/`)

Optional integrations (installed via extras):
- **`pydantic/rutstr.py`** — `RutStr` type for Pydantic v2 with configurable output formats (base-dv, canonico, miles, miles-con-guion). Uses `Rut.parse()` under the hood.
- **`fastapi.py`** — FastAPI dependency `parametro_rut` for automatic RUT validation in path/query params.
- **`pandas.py`** / **`polars.py`** — Extension accessors.

### Data Flow

1. **Validation**: input str → `_limpiar_entrada()` (NFKC, spaces, hyphens) → `ValidadorRut.validar_formato()` (regex match) → `ValidadorRut.validar_base()` (digit count) → `calcular_digito_verificador()` → `ValidadorRut.validar_digito_verificador()` → `Rut` instance.
2. **Batch**: `ProcesadorLotesRut` uses `_validar_rut_local()` (sync) or `_validar_rut_en_proceso()` (pickle-safe for multiprocessing).
3. **Pydantic**: `RutStr.__get_pydantic_core_schema__` → `RutStr._validar_y_normalizar` → `Rut.parse()` → `_manejar_resultado_exitoso/error`.
4. **CLI**: `_leer_ruts()` (file or stdin) → `_procesar_con_mejorar()` (optional auto-correct) → `validar_flujo_ruts()` or `formatear_flujo_ruts()` → `_emitir_resultados()` (incremental format emission).

### Key Design Decisions

- **No external dependencies** for core functionality (only stdlib). Optional extras for Pydantic, FastAPI, pandas, polars.
- **Immutable Rut/RutBase** dataclass pattern. `Rut` validates on construction; `Rut.parse()` is the exception-safe alternative.
- **Parallelism**: ProcessPoolExecutor default for CPU-bound DV calculation, ThreadPoolExecutor fallback on Windows.
- **Security**: DV calculation via `itertools.cycle` (no modulo in loop). CSV output formula injection protection (`'` prefix for `=`, `+`, `-`, `@`). PII sanitization in exception logging.
- **Compatibility aliases**: English-named exceptions (`RutInvalidoError`, `RutValidator`) kept for backward compat.
