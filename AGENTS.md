# AGENTS.md · rutificador

Librería Python para validar/formatear RUT chileno. Core con **cero dependencias** (solo stdlib); integraciones opcionales en `rutificador/contrib/` (pydantic, fastapi, pandas, polars). Python `>=3.10` (CI: 3.10–3.14, dev: 3.13); mantener compatibilidad con 3.10. Rama principal: `master`. Detalle de arquitectura: `CLAUDE.md`.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

## Comandos (orden CI: formato → lint → tipos → tests)

```bash
pytest -q                                   # suite completa
pytest tests/test_rutificador.py -v --tb=short        # un archivo
pytest tests/test_rutificador.py::test_nombre -v      # un test
ruff format . --check                       # formato (CI falla con `git diff --exit-code`)
ruff check .                                # lint
mypy rutificador/ --ignore-missing-imports  # tipos; estricto en CI para los 10 módulos core
bandit -r rutificador/                      # seguridad
deptry rutificador                          # coherencia dependencias
lint-imports                                # límites arquitectónicos (import-linter)
mkdocs build --strict                       # solo si tocas docs/
pytest tests/benchmarks/ tests/test_benchmark.py --benchmark-only  # caro; solo cambios de perf
```

## Límites arquitectónicos (verifica `lint-imports`, contratos en `pyproject.toml`)

- Núcleo (`config`, `validador`, `rut`, `procesador`, `formatter`, `sugestor`, `utils`, `errores`, `exceptions`, `version`, `calidad_datos`) **no** puede importar `rutificador.contrib.*` ni `rutificador.cli`.
- Módulos `contrib` independientes entre sí (excepción: `pandas`/`polars` → `_formato_comun`).
- Nuevas dependencias third-party van solo a `contrib/` + extra en `pyproject.toml` (+ `requirements-dev.txt` para tests).

## Gotchas que rompen CI o el playground

- **Import liviano**: `from rutificador import Rut` debe funcionar sin `multiprocessing` (playground Pyodide, `tests/test_import_liviano.py`). No importes `multiprocessing`/`concurrent.futures.process` a nivel de módulo en el núcleo; hazlo lazy dentro de funciones.
- **API dual de `Rut`**: `Rut(s)` lanza excepción si inválido; `Rut.parse(s, modo=)` nunca lanza, retorna `ValidacionResultado(estado, errores)`. `ESTRICTO` rechaza espacios/guiones internos; `FLEXIBLE` los acepta con advertencia `NORMALIZACION_*`.
- **Warnings en tests**: `conftest.py` ignora `DeprecationWarning` globalmente (ruido anyio/starlette) y fuerza `spawn` en multiprocessing. No "arregles" esos filtros ni asumas semántica `fork`.
- **Seguridad**: no loguear RUTs crudos (excepciones sanitizan PII); CSV escapa inyección de fórmulas (`=+-@` con prefijo `'`); DV se calcula con `itertools.cycle`, no lo cambies a aritmética con `%` en el loop.
- **CLI**: `validar --max-tasa-error` retorna `2` (no `1`) si se supera el umbral; es el gate de calidad en CI ajenos.
- **Versionado bloqueante**: `version-bump-gate.yml` exige diff en `rutificador/version.py` para todo PR que toque `rutificador/`; `publish-package.yml` publica según `version` en `pyproject.toml` (fuente real, `version.py` la lee dinámicamente). Para cambios de código: bump en `pyproject.toml` + entrada en `CHANGELOG.md` + un toque a `rutificador/version.py` (aunque sea docstring) para pasar el gate.

## Convenciones

- Español: código, docstrings (estilo Google), commits y docs.
- Commits Convencionales (`feat:`, `fix:`, `docs:`, `chore:`, `release:`); SemVer; release vía tag `v*`.
- Type hints obligatorios en código nuevo (mypy estricto en core). `ruff` para formato/lint (pre-commit solo tiene ruff; ignora la mención a black/flake8 en `CLAUDE.md`, está desactualizada).
