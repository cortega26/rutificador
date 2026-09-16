# Spike 022: Notas — API async de procesamiento por lotes

**Fecha**: 2026-09-15 | **Commit base**: `0e49f21` (plan redactado en `d6c28d8`; drift vacío) | **Decisión**: **No-concluyente**

> Segundo intento del spike. El intento 1 (ver "Antecedente" en §5) reportó paridad OK
> pero paró su benchmark por varianza sin controles (>30 %). Este intento aplicó los
> controles de entorno refinados y la calibración no pasó ni con lote de 50 000,
> por lo que —según la regla del plan— el veredicto es **no-concluyente** (es la
> máquina, no el prototipo). No se corrió el benchmark completo.

---

## 1. Setup

| Componente | Valor |
|-----------|-------|
| Python (venv del worktree) | 3.13.12 (verificado: `.venv/bin/python --version`) |
| Plataforma | Linux x86_64, 16 CPUs |
| Carga de la máquina | `loadavg ≈ 21.6` con **0–2 % idle en las 16 CPUs** (medido vía `/proc/stat`, Δ 2 s): máquina compartida saturada, sin CPUs libres |
| Afinidad (plan: `taskset` a 2 CPUs libres) | `taskset -c 2,3` aplicado a **todas** las corridas; anotación: no existían CPUs libres, se fijó afinidad para reducir migración entre núcleos, no como aislamiento |
| Drift check | `git diff --stat d6c28d8..HEAD -- rutificador/procesador.py rutificador/contrib/fastapi.py tests/test_procesador_flujo.py` → **vacío** |
| Baseline tests | `.venv/bin/python -m pytest tests/test_procesador_flujo.py tests/contrib/test_fastapi.py -q` → **9 passed** |
| Firma verificada | `validar_flujo_ruts(ruts, paralelo=False, max_trabajadores=None, motor_paralelo="process", chunksize=...)` en `rutificador/procesador.py:326-332` — coincide con el plan, sin drift |

## 2. Implementación

Prototipo **reutilizado sin cambios** desde `/tmp/async-spike/` (no reescrito, según el plan):

- `aprot.py:18-55` — `async def avaliar_flujo_ruts(ruts, *, max_trabajadores=None, limite=100)`: trocea el iterable en chunks de 500 (`TAMANO_CHUNK`), ejecuta cada chunk en modo **serial** dentro de `asyncio.to_thread` con un `asyncio.Semaphore` como cota de concurrencia, y re-emite los `(es_valido, detalle)` **en orden** vía `asyncio.gather`.
- Por qué este puente: es el cambio mínimo que evita bloquear el event loop sin tocar `rutificador/` (el trabajo CPU-bound se deriva a hilos y el loop queda libre entre `await`s); solo stdlib `asyncio` + paquete instalado, sin dependencias nuevas.
- `bench.py` **no** se extendió: la calibración detuvo el trabajo antes del benchmark completo (regla del plan).

## 3. Validación

### 3.1 Paridad (Step 1) — OK con una salvedad documentada

Corrida de paridad sobre 200 RUTs (`muestra` base + `calcular_digito_verificador`, como `tests/test_procesador_flujo.py:18-47`):

- Comparación ingenua por igualdad total: **difiere** — únicamente en el campo `duracion` de `RutProcesado` (artefacto de medición por ítem, p. ej. `8.26e-05` vs `3.68e-05` en el mismo RUT `1000000-9`).
- Comparación semántica (tupla `(es_valido, detalle)` excluyendo `duracion`): **`PARIDAD: OK`** en los 200 RUTs y en el mismo orden.
- Control: `serial-vs-thread` exhibe exactamente la misma propiedad (difiere solo en `duracion`), por lo que el criterio de paridad del prototipo es equivalente al que ya aceptan los tests del repo entre motores.

### 3.2 Calibración con controles (Step 2) — NO PASA → STOP

Procedimiento del plan: solo serial, 3 corridas, varianza = (max−min)/mediana; umbral 10 %.

Lote 10 000 RUTs (`taskset -c 2,3`):

| Corrida | Segundos (n=10000) |
|---------|--------------------|
| 1 | 0.183 |
| 2 | 0.173 |
| 3 | 0.209 |
| **mediana** | **0.183** |
| **varianza** | **19.6 % (> 10 % → agrandar lote)** |

Lote 50 000 RUTs (`taskset -c 2,3`):

| Corrida | Segundos (n=50000) |
|---------|--------------------|
| 1 | 0.765 |
| 2 | 0.872 |
| 3 | 0.798 |
| **mediana** | **0.798** |
| **varianza** | **13.4 % (> 10 % → STOP no-concluyente)** |

Tabla de 4 variantes × 5 corridas: **no generada** — el plan ordena parar aquí ("si sigue >10 %, STOP como no-concluyente"). No hay veredicto numérico go/no-go que reportar porque nunca se midió el prototipo contra `motor_paralelo="thread"`.

## 4. Decisión: **no-concluyente**

**Decisión: no-concluyente** — la calibración serial supera el umbral del 10 % en lote 10 000 (19.6 %) y en lote 50 000 (13.4 %) bajo `taskset -c 2,3` en una máquina compartida saturada (load ≈ 21.6, 0–2 % idle en 16 CPUs); según la regla de varianza del plan, sin calibración estable no hay evidencia válida para aplicar el criterio go/no-go (≥15 % más rápido que hilos, o testigo que avanza), por lo que no se afirma nada sobre el prototipo.

## 5. Factores de la decisión y antecedente

- **Antecedente (intento 1)**: paridad OK en 200 RUTs; benchmark parado por varianza sin controles (thread 38.8 %/31.9 %); señal débil no-citable (serial más rápido, thread 3–4× más lento, async intermedio, testigo casi quieto) apuntando a no-go **sin** evidencia suficiente.
- **Este intento** confirma la causa raíz de la varianza del intento 1: la máquina compartida está saturada de forma sostenida (no un pico transitorio), de modo que ni el control de afinidad ni el lote 5× mayor estabilizan la medición.
- **Qué haría falta para un tercer intento**: máquina dedicada o ventana de carga baja verificada (p. ej. load < nº CPUs e idle sostenido >50 % en los núcleos fijados) antes de repetir calibración → benchmark completo de 4 variantes × 5 corridas.
- **Sin boceto de API**: al no haber veredicto go, el plan no requiere proponer firmas; no se agrega superficie API.
- **Repo intacto**: ningún archivo de `rutificador/` ni `tests/` fue tocado; sin código async nuevo ni dependencias nuevas (el prototipo vive solo en `/tmp/async-spike/`, fuera del repo).

---

# Intento 3 (2026-09-15) — veredicto: **no-go**

> Tercer intento. La calibración PASÓ (lote 50 000, varianza 4.2 % ≤ 10 %),
> por lo que se corrió el benchmark completo 4 variantes × 5 corridas.
> Todas las variantes superaron el 30 % de varianza (coincidiendo con un pico
> de carga transitorio: loadavg 1 min subió de ~4 a ~14.8 durante la corrida),
> de modo que —según la regla prefijada del plan ("si una variante >30 % →
> **no-go**, no inconcluyente")— el veredicto es **no-go**. Esta decisión
> sustituye a la del intento 2; lo anterior queda como historia.

## Setup (intento 3)

| Componente | Valor |
|-----------|-------|
| Python (venv del worktree) | 3.13.12 (verificado) |
| Plataforma | Linux x86_64, 16 CPUs |
| Carga medida | inicio: `loadavg 3.99 5.30 7.67`, idle global ≈54 %; afinidad: CPUs 3 (77 % idle) y 5 (81 % idle) elegidas por mayor idle; `taskset -c 3,5` aplicado a calibración y benchmark |
| Pico durante el benchmark | `loadavg 14.82 8.51 8.61` (1 min; <16 CPUs pero pico transitorio frente al inicio) |
| Drift check | `git diff --stat d6c28d8..HEAD -- rutificador/procesador.py rutificador/contrib/fastapi.py tests/test_procesador_flujo.py` → **vacío** |
| Baseline tests | `.venv/bin/python -m pytest tests/test_procesador_flujo.py tests/contrib/test_fastapi.py -q` → **9 passed** |
| Prototipo | reutilizado sin cambios (`aprot.py`); `bench.py` extendido de forma aditiva (env `SPIKE_N`/`SPIKE_CORRIDAS`, sin reescribir lógica) — ambos en `/tmp/async-spike/`, fuera del repo |

## Paridad (Step 1) — OK

200 RUTs, comparación semántica `(es_valido, detalle)` excluyendo `duracion`
(mismo criterio del intento 2): **`PARIDAD: OK`** (200/200 en orden).

## Calibración (Step 2) — PASA en 50 000

Solo serial, 3 corridas, varianza = (max−min)/mediana, umbral 10 %,
bajo `taskset -c 3,5`:

| Lote | Corridas (s) | Mediana | Varianza |
|------|--------------|---------|----------|
| 10 000 | 0.079, 0.065, 0.066 | 0.066 | **21.9 % (>10 % → agrandar)** |
| 50 000 | 0.361, 0.354, 0.369 | 0.361 | **4.2 % (≤10 % → PASA)** |

## Benchmark completo (Step 2) — lote 50 000, 5 corridas, `taskset -c 3,5`

| Corrida | serial+testigo (s / it) | thread+testigo (s / it) | async+testigo (s / it) | testigo-sola iters |
|---------|------------------------|------------------------|------------------------|--------------------|
| 1 | 0.398 / 0 | 2.375 / 0 | 0.773 / 9187 | 134618 |
| 2 | 0.729 / 0 | 1.149 / 0 | 0.484 / 426 | 296128 |
| 3 | 0.367 / 0 | 1.261 / 0 | 0.503 / 5242 | 346871 |
| 4 | 0.339 / 0 | 0.868 / 0 | 0.416 / 7 | 350099 |
| 5 | 0.352 / 0 | 1.039 / 0 | 0.427 / 271 | 352169 |
| **mediana** | **0.367 / 0** | **1.149 / 0** | **0.484 / 426** | — / 346871 |
| **varianza** | **106.1 %** | **131.1 %** | **73.7 %** | — |

- Speedup async vs thread (medianas): +57.9 % — numérico, **no citable** (varianza >30 %).
- Condición-a (≥15 % más rápido): SÍ numérico / no citable. Condición-b (testigo avanza solo en async): SÍ numérico (426 vs 0/0) / no citable (rango async 7–9187).
- Señal sustantiva (coherente con intentos 1–2): el serial es el más rápido en mediana; `thread` es ~3× más lento que serial; el prototipo async queda intermedio. Nada evidencia una ganancia fiable del puente async.

Desviación procedimental: la primera invocación corrió con los valores por
defecto de `bench.py` (10 000 × 3; thread 34.1 % → también habría dado no-go
por la misma regla); se descartó y se repitió correctamente a 50 000 × 5
(tabla de arriba, la única citable).

## Decisión: **no-go**

**Decisión: no-go** — la calibración pasó (4.2 % en 50 000) pero las tres
variantes del benchmark superan el 30 % de varianza (106.1 % / 131.1 % /
73.7 %); la regla prefijada del plan ordena veredicto **no-go** en este caso,
y además el serial sigue siendo lo más rápido en mediana sin evidencia fiable
de ganancia del puente async. Sin boceto de API (solo requerido si go).
Repo intacto: ningún archivo de `rutificador/` ni `tests/` tocado; sin
dependencias nuevas.
