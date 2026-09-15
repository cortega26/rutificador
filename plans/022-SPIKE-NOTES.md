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
