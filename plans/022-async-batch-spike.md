# Plan 022: Spike — API async de procesamiento por lotes

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat d6c28d8..HEAD -- rutificador/procesador.py rutificador/contrib/fastapi.py tests/test_procesador_flujo.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: S–M (spike, time-boxed)
- **Risk**: LOW (prototipo en /tmp + notas; cero cambios de API)
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `d6c28d8`, 2026-09-15

## Why this matters

Todo `rutificador/procesador.py` es síncrono (generadores + hilos/procesos)
mientras el único consumidor web, `contrib/fastapi.py:28`
(`obtener_param_rut`), es async: validar un lote mediano dentro de un
handler async hoy bloquea el event loop y degrada la concurrencia del
servicio. Antes de agregar superficie API (decisión difícil de revertir),
este spike mide con un prototipo desechable si un puente async aporta algo
real frente al modo `motor_paralelo="thread"` existente. Si no hay
ganancia, se rechaza con evidencia como el spike 017.

## Current state

- `rutificador/procesador.py:326-367` — `validar_flujo_ruts(ruts,
  paralelo=False, max_trabajadores=None, motor_paralelo="process",
  chunksize=CHUNKSIZE_FLUJO_POR_DEFECTO)`; generador síncrono; en modo
  paralelo usa `ejecutor.map(...)` por chunks sin materializar el lote
  (`procesador.py:359-363`); en serial itera `_validar_rut_local`
  (`procesador.py:364-367`). No hay `async` en todo el archivo.
- `rutificador/procesador.py:417-420` — `flujo(ruts)` delega en
  `ProcesadorLotesRut().flujo(ruts)`; también síncrono.
- `rutificador/procesador.py:286-298` — `validar_lista_ruts(...)` retorna
  `ResumenValidacion` (`{"validos", "invalidos"}`).
- `rutificador/contrib/fastapi.py:28-51` — dependencia async que valida UN
  RUT por request (`Rut(rut)` + `HTTPException` 422). No existe variante
  por lotes.
- Patrón de tests de flujo: `tests/test_procesador_flujo.py:18-47` —
  generador puro `_muestra(n)` de RUTs válidos consecutivos (base +
  `calcular_digito_verificador`), comparación serial-vs-paralelo.
  Reutiliza `_muestra` en tu benchmark.
- Patrón de benchmark: `tests/test_benchmark.py:8-15` (fixture
  `benchmark` de pytest-benchmark) y `tests/benchmarks/` (léelo antes del
  paso 2; si su conftest es incompatible con tu entorno, usa
  `time.perf_counter` + `asyncio` puro y anótalo).
- Criterio de veredicto (fijado por adelantado, no negociable en el
  spike): **go** solo si el prototipo async, dentro de un event loop con
  otra tarea concurrente viva, completa el lote sin bloquearla Y (a) es
  ≥15 % más rápido que `motor_paralelo="thread"` en el mismo lote, O (b)
  demuestra concurrencia real (la tarea testigo avanza durante la
  validación) donde el modo serial/hilos la bloquea. En cualquier otro
  caso: **no-go**.

## Commands you will need

| Purpose | Command | Provenance | Expected on success |
|---------|---------|------------|---------------------|
| Baseline tests | `.venv/bin/python -m pytest tests/test_procesador_flujo.py tests/contrib/test_fastapi.py -q` | declared | all pass |
| Lint (notas n/a) | `.venv/bin/ruff check plans/022-SPIKE-NOTES.md` | declared | n/a (markdown; ruff no lo chequea — el paso real es el siguiente) |
| Python | `.venv/bin/python /tmp/async-spike/bench.py` | declared | imprime tabla + veredicto numérico |
| Drift check | `git diff --stat d6c28d8..HEAD -- <paths>` | declared | vacío |

## Scope

**In scope**:

- `plans/022-SPIKE-NOTES.md` (crear — el producto del spike)
- `plans/README.md` (solo tu fila de estado)
- Prototipo desechable en `/tmp/async-spike/` (nunca en el repo)

**Out of scope** (NO tocar):

- `rutificador/` completo — ninguna API nueva en un spike.
- `tests/` — ningún test nuevo en el repo (el benchmark vive en `/tmp`).
- Dependencias nuevas (`anyio`, `aiofiles`, etc.) — el prototipo usa
  solo stdlib (`asyncio`) + el paquete instalado.
- Decisiones de denominación final (`validar_flujo_ruts_async` u otras):
  propón como máximo 2 opciones en las notas, no implementes ninguna.

## Git workflow

- Branch: `advisor/022-async-batch-spike`
- 1–2 commits; estilo conventional commits (ej.:
  `docs(planes): agregar notas del spike async 022`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 0: Baseline y lectura

1. Drift check → vacío.
2. Lee `rutificador/procesador.py:97-140` (clase `ProcesadorLotesRut`,
   constructor y defaults) y `tests/benchmarks/test_benchmarks_core.py`
   (patrón de medición del repo).
3. Corre los tests de flujo + fastapi del cuadro.

**Verify**: drift vacío; tests verdes; anotas defaults del procesador.

### Step 1: Prototipo async en /tmp

En `/tmp/async-spike/`, escribe `aprot.py` con:

```python
async def avaliar_flujo_ruts(ruts, *, max_trabajadores=None, limite=100):
    """Prototipo: consume validar_flujo_ruts en thread + semáforo acotado."""
```

Implementación sugerida (adáptala si el repo driftó): itera el generador
síncrono por chunks en `asyncio.to_thread` con `asyncio.Semaphore(limite)`
acotando el trabajo en vuelo; produce `(es_valido, detalle)` en orden.
Solo stdlib + `from rutificador.procesador import validar_flujo_ruts`.

**Verify**: script que valida 200 RUTs del generador `_muestra`
(copiado en `/tmp`, no importado de tests) retorna los mismos
`(bool, valor)` que `validar_flujo_ruts` serial. Paridad exacta o STOP.

### Step 2: Benchmark con tarea testigo

> **Lección del intento 2026-09-15 (ver historial al pie)**: en entorno
> compartido/ruidoso la varianza supera el 30 % y el plan obliga a parar
> como no-concluyente. Antes de medir, aplica los controles de abajo; son
> parte del paso, no opcionales.

Controles de entorno (en orden, parar en el primero que falle):

1. Máquina quieta: cierra cargas pesadas vecinas; si existe `taskset`,
   fija afinidad a 2 CPUs libres (`taskset -c 2,3 ...`) para todas las
   corridas y anótalo.
2. Calibración: corre SOLO el serial 3 veces sobre 10 000 RUTs. Si la
   varianza (max-min)/mediana supera el 10 %, el entorno no sirve:
   agranda el lote a 50 000 y repite; si sigue >10 %, STOP como
   no-concluyente (no es tu prototipo, es la máquina).
3. Recién entonces corre el benchmark completo: lote 10 000 (o 50 000 si
   calibraste con ese), 4 variantes, **5 corridas**, mediana. Reporta
   varianza por variante.
mide con `time.perf_counter`:

1. serial (`paralelo=False`),
2. `motor_paralelo="thread"`,
3. prototipo async del paso 1,
4. cada variante corriendo junto a una tarea testigo
   (`await asyncio.sleep(0)` en loop contando iteraciones) para medir
   bloqueo del loop.

Imprime tabla `variante | segundos | iteraciones_testigo` y el veredicto
numérico según el criterio de "Current state". Si tras los controles la
varianza de alguna variante sigue >30 %, el veredicto es **no-go** (una
API nueva necesita evidencia positiva; ganancia persistentemente
inmedible = no agregar superficie). Solo si ni siquiera la calibración
pasa se reporta no-concluyente.

**Verify**: tabla impresa con 4 filas × 3 corridas + veredicto que cita
los números. Guarda la salida: va pegada en las notas.

### Step 3: Escribir `plans/022-SPIKE-NOTES.md`

Secciones (sigue `plans/017-SPIKE-NOTES.md`): Setup (Python, CPU,
commit, defaults del procesador); Implementación (el puente usado, por
qué ese y no `run_in_executor` directo / `anyio` / cola con
`async for`); Validación (paridad + tabla pegada); Decisión
**go / no-go** en una línea aplicando el criterio prefijado; si go,
boceto de API (≤2 opciones de firma + dónde viviría + qué tests exigiría
el plan de construcción).

**Verify**: archivo con las 5 secciones y decisión en una línea citable.

## Test plan

Spike: sin tests en el repo. Evidencia = paridad exacta serial-vs-async
(200 RUTs) + tabla de benchmark (10 000 RUTs × 3 corridas) pegada en las
notas. Si la paridad falla, el prototipo está mal: corrígelo en `/tmp`;
si falla dos veces, STOP.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `git diff --name-only d6c28d8...HEAD` lista solo
  `plans/022-SPIKE-NOTES.md` (+ fila en `plans/README.md`)
- [ ] Las notas contienen tabla de benchmark con 4 variantes × 3 corridas
- [ ] Las notas contienen `Decisión: go|no-go` trazable a los números y
  al criterio prefijado
- [ ] `plans/README.md` fila 022 actualizada
- [ ] El repo no contiene código async nuevo ni dependencias nuevas

## STOP conditions

Stop and report back (do not improvise) if:

- `validar_flujo_ruts` ya no existe o su firma/retorno cambió (drift).
- La paridad serial-vs-async falla dos veces (prototipo o semántica
  cambió bajo tus pies).
- El benchmark no discrimina: si la calibración (Step 2, control 2) no
  pasa ni con lote 50 000, repórtalo como no-concluyente (es la máquina).
  Si la calibración pasa pero una variante sigue con varianza >30 % tras
  los controles, el veredicto es **no-go** (ver Step 2), no inconcluyente.
- El puente requeriría dependencias nuevas para funcionar: STOP, eso
  invalida la premisa "stdlib + instalado".
- Cualquier verificación falla dos veces tras intento razonable.

## Maintenance notes

- Historial 2026-09-15 (intento 2, worktree `/tmp/rutificador-exec-022`,
  commit `ad52a53`, notas con 5 secciones y `Decisión: no-concluyente`):
  con controles (taskset, calibración serial), la calibración no pasó
  ni en lote 50 000 (19.6 % en 10k, 13.4 % en 50k; load ≈21.6
  sostenido). Se confirmó que la varianza del intento 1 era la
  máquina, no el prototipo. Tercer intento solo con hardware quieto
  (load < nº CPUs, idle >50 % sostenido).

- Si go: el plan de construcción debe incluir test de no-bloqueo del
  loop (tarea testigo como assert, no solo benchmark manual) o la
  propiedad que justifica la API se pierde en la primera refactorización.
- Revisores del futuro: `motor_paralelo="process"` queda fuera del
  benchmark a propósito (procesos + event loop = pickling y señales;
  el async apunta al caso I/O-bound/web, no CPU-bound).
- **Deferred:** variante por lotes del contrib FastAPI (endpoint que
  acepta lista) — lo desbloquea el go de este spike, pertenece al plan
  de construcción. **Deferred:** `async for` nativo sobre archivos
  (`aiofiles`) — dependencia nueva, fuera de cuestión hasta tener caso
  de uso.
