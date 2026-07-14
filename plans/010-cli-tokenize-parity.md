# Plan 010: Paridad CLI — exponer tokenización en `rutificador enmascarar`

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving to the next step. If
> anything in the "STOP conditions" section occurs, stop and report — do not
> improvise. When done, update the status row for this plan in
> `plans/README.md`.

> **Drift check (run first)**: `git diff --stat aaca8c4..HEAD -- rutificador/cli.py rutificador/rut.py tests/test_cli.py`
> If any of these files changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx / direction
- **Planned at**: commit `aaca8c4`, 2026-07-14

## Why this matters

La API Python de `Rut.enmascarar()` soporta dos modos: `"mascarada"` (default,
ofusca dígitos) y `"token"` (HMAC-SHA256 determinista). El subcomando CLI
`rutificador enmascarar` solo expone el modo mascarada. Un usuario de shell que
necesite tokenizar RUTs —por ejemplo, para anonimizar datos antes de subirlos a
un pipeline— está forzado a escribir Python. Agregar los flags `--token` y
`--clave` (con soporte para variable de entorno `RUTIFICADOR_TOKEN_KEY`) cierra
esta brecha API↔CLI con ~30 líneas de código.

## Current state

- `rutificador/rut.py:390-466` — `Rut.enmascarar()` acepta `modo="token"` y
  `clave: Optional[Union[str, bytes]]`. La lógica de tokenización (líneas
  425-442) usa HMAC-SHA256 + base32.
- `rutificador/rut.py:466` — alias `Rut.mask = enmascarar`.
- `rutificador/cli.py:281-297` — `_comando_enmascarar()` solo llama
  `Rut.enmascarar()` sin pasar `modo` ni `clave`. Siempre opera en modo
  mascarada.
- `rutificador/cli.py:355-385` — el parser `enmascarar` define flags:
  `--mantener`, `--caracter`, `--separador-miles`, `--mayusculas`. No tiene
  `--token` ni `--clave`.
- `tests/test_cli.py` — existe suite de tests CLI. Patrón a seguir:
  ```python
  def test_comando_enmascarar_basico(self):
      args = self.parser.parse_args(["enmascarar", ...])
      ...
  ```

Convenciones: argparse con argumentos posicionales `nargs="?"`, flags
`--kebab-case` con `action="store_true"` o `type=int`. El código está en
español. Los tests usan `unittest` o pytest estándar.

Ejemplo de commit: `c36e74d docs: add future tooling adoption plan (#71)`

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q` | 230 passed, 2 skipped |
| Lint | `python -m ruff check rutificador/` | exit 0 |
| Format | `python -m ruff format --check rutificador/` | exit 0 |
| Types | `python -m mypy rutificador/ --ignore-missing-imports` | exit 0 |
| CLI smoke test | `python -m rutificador.cli enmascarar --help` | muestra ayuda con nuevos flags |

## Scope

**In scope** (files to modify):
- `rutificador/cli.py` — parser y `_comando_enmascarar`
- `tests/test_cli.py` — nuevos tests de tokenización CLI

**Out of scope** (do NOT touch):
- `rutificador/rut.py` — la lógica de tokenización ya existe, no modificarla.
- `rutificador/errores.py` — no agregar nuevos códigos de error.
- Otros comandos CLI (`validar`, `formatear`, `info`).

## Git workflow

- Branch: `advisor/010-cli-tokenize`
- Un commit con mensaje: `feat(cli): exponer tokenización en comando enmascarar`
- No hacer push ni abrir PR a menos que el operador lo indique.

## Steps

### Step 1: Agregar flags `--token` y `--clave` al parser

En `rutificador/cli.py`, dentro del bloque de `parser_enmascarar` (línea 355),
agregar después del flag `--mayusculas`:

```python
parser_enmascarar.add_argument(
    "--token",
    action="store_true",
    help="Tokeniza los RUTs con HMAC-SHA256 en vez de enmascarar",
)
parser_enmascarar.add_argument(
    "--clave",
    default=None,
    help=(
        "Clave para tokenización. Si no se proporciona, se usa la variable "
        "de entorno RUTIFICADOR_TOKEN_KEY"
    ),
)
```

**Verify**: `python -m rutificador.cli enmascarar --help` muestra los nuevos flags en la salida.

### Step 2: Actualizar `_comando_enmascarar` para usar tokenización

Modificar `_comando_enmascarar` (`cli.py:281-297`) para:

1. Leer `args.token` y `args.clave`.
2. Si `--token` está activo, resolver la clave: usar `args.clave` si se
   proporcionó, sino leer `os.environ.get("RUTIFICADOR_TOKEN_KEY")`.
3. Si la clave es `None` o vacía en modo token, imprimir error en stderr y
   retornar 1.
4. Pasar `modo="token"` y `clave=clave` a `Rut.enmascarar()` cuando corresponda.

El código resultante (reemplazar el bloque `_comando_enmascarar` completo):

```python
def _comando_enmascarar(args: argparse.Namespace) -> int:
    import os

    codigo_salida = 0
    modo: Literal["mascarada", "token"] = "token" if args.token else "mascarada"
    clave: Optional[str] = None

    if modo == "token":
        clave = args.clave or os.environ.get("RUTIFICADOR_TOKEN_KEY")
        if not clave:
            print(
                "Error: --token requiere --clave o la variable de entorno "
                "RUTIFICADOR_TOKEN_KEY",
                file=sys.stderr,
            )
            return 1

    ruts = _leer_ruts(args.archivo)
    for rut_str in ruts:
        try:
            resultado = Rut.enmascarar(
                rut_str,
                mantener=args.mantener,
                caracter=args.caracter,
                modo=modo,
                clave=clave,
                separador_miles=args.separador_miles,
                mayusculas=args.mayusculas,
            )
            print(resultado)
        except Exception as exc:
            codigo_salida = 1
            print(f"{rut_str} [ERROR] - {str(exc)}", file=sys.stderr)
    return codigo_salida
```

Asegurarse de que `Literal` y `Optional` estén importados (ya lo están en
`cli.py:15`).

**Verify**: `python -m ruff check rutificador/cli.py` → exit 0.

### Step 3: Agregar tests de CLI para tokenización

En `tests/test_cli.py`, agregar tests siguiendo el patrón existente:

```python
def test_comando_enmascarar_token_basico():
    """Tokenización produce prefijo tok_ con salida determinista."""
    ...

def test_comando_enmascarar_token_sin_clave():
    """Token sin --clave ni variable de entorno debe fallar con código 1."""
    ...

def test_comando_enmascarar_token_con_variable_entorno():
    """Token lee RUTIFICADOR_TOKEN_KEY del entorno correctamente."""
    ...
```

El patrón de tests CLI (extraído de `tests/test_cli.py`):
- Parsear args con el parser de `_crear_parser()`.
- Llamar `args.func(args)` o la función del comando directamente.
- Capturar stdout/stderr con `capsys`.
- Verificar `codigo_salida` y contenido de salida.

**Verify**: `python -m pytest tests/test_cli.py -q` → todos los tests pasan,
incluidos los nuevos.

### Step 4: Verificación final completa

```bash
python -m ruff check rutificador/ && \
python -m ruff format --check rutificador/ && \
python -m mypy rutificador/ --ignore-missing-imports && \
python -m pytest tests/ --ignore=tests/benchmarks --ignore=tests/test_benchmark.py -q
```

**Verify**: todos los comandos exit 0. 230+ tests pass.

### Step 5: Smoke test manual

```bash
echo "12.345.678-5" | python -m rutificador.cli enmascarar --token --clave "test-key"
```

Debe producir una salida como `tok_<hash>` (prefijo `tok_` seguido de caracteres
alfanuméricos en minúscula). La misma entrada con la misma clave debe producir
la misma salida (determinismo).

**Verify**: ejecutar dos veces, comparar salidas → idénticas.

## Test plan

Tests nuevos en `tests/test_cli.py`, modelados según los tests existentes en
ese archivo:

1. **Token básico**: `RUT válido + --token --clave "k"` → stdout contiene
   `tok_`, exit 0.
2. **Token sin clave**: `RUT válido + --token` sin `--clave` ni env var →
   stderr contiene mensaje de error, exit 1.
3. **Token con variable de entorno**: `os.environ["RUTIFICADOR_TOKEN_KEY"] =
   "k"`, `--token` sin `--clave` → funciona, exit 0.
4. **Token con RUT inválido**: `RUT inválido + --token --clave "k"` → stderr
   contiene error, exit 1.
5. **Modo mascarada intacto**: `RUT válido` sin `--token` → sigue funcionando
   igual (regresión).

## Done criteria

- [ ] `rutificador enmascarar --help` muestra `--token` y `--clave`
- [ ] `--token --clave "k"` produce tokens con prefijo `tok_`
- [ ] `--token` sin clave ni env var produce error en stderr y exit 1
- [ ] `--token` con `RUTIFICADOR_TOKEN_KEY` en entorno funciona
- [ ] Modo mascarada sin `--token` no se rompió (regresión)
- [ ] `ruff check`, `ruff format --check`, `mypy` pasan
- [ ] 5+ tests nuevos en `tests/test_cli.py` pasan
- [ ] Ningún archivo fuera de `in scope` fue modificado
- [ ] `plans/README.md` status row actualizada

## STOP conditions

- Si `Rut.enmascarar()` cambió su firma desde que este plan se escribió:
  verificar que los parámetros `modo` y `clave` sigan siendo keyword-only y
  compatibles.
- Si el parser `enmascarar` de argparse fue refactorizado significativamente
  (ej. extraído a otra función): adaptar los cambios, pero reportar el drift.
- Si los tests CLI existentes fallan después de los cambios: revertir y
  reportar el test específico que falla.
- Si `mypy` rechaza el uso de `os.environ.get()`: agregar `# type:
  ignore[assignment]` con comentario justificando que `os.environ` es `Mapping`
  pero en runtime es `dict`.

## Maintenance notes

- Si en el futuro se agrega un flag `--algoritmo` para elegir SHA256 vs otro
  hash, modificar este bloque. Por ahora HMAC-SHA256 con base32 es suficiente
  para anonimización no criptográfica.
- La clave `RUTIFICADOR_TOKEN_KEY` es un secreto: documentar en el `--help` y
  en el README que no debe hardcodearse en scripts compartidos.
- Considerar en v2.0: migrar de `argparse` a `typer` para mejor DX de CLI; en
  ese caso, este código se reescribe pero la semántica de los flags se
  preserva.
