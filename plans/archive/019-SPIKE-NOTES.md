# Spike 019: Notas — port TypeScript del validador core con gate de conformidad

**Fecha**: 2026-09-15 | **Commit base**: `d6c28d8` (drift check vacío; trabajo sobre `0e49f21`) | **Rama**: `advisor/019-typescript-port-spike` | **Decisión**: **Go-condicional**

---

## 1. Setup

| Componente | Versión |
|-----------|---------|
| Node | v24.19.0 (≥20 requerido — OK) |
| npm | 11.17.0 |
| TypeScript (vía `npx -p typescript@5`) | 5.9.3 |
| Vectores `tests/vectors/conformance.json` | `1.0.0` / spec `1.0` — 12 casos DV + 15 validación |
| Plataforma | Linux x64 |

Documentos leídos completos antes de escribir código: `docs/especificacion-reglas-rut.md` (§2–§6),
`docs/conformidad.md`, `tests/vectors/schema.json`, `tests/vectors/conformance.json`,
`scripts/conformance.py` (interfaz y regla de comparación `:79-87`), `rutificador/rut.py:107-230`
(normalización en 9 pasos) y `rutificador/utils.py:124-204` (`calcular_digito_verificador`, `_limpiar_entrada`).

Desviaciones menores respecto al plan (sin impacto en la evidencia):
- El comando declarado `npx -y typescript@5 tsc` no es sintaxis válida de npx (no resuelve el
  binario); el equivalente usado fue `npx --yes -p typescript@5 tsc` (mismo paquete y major).
- El `tsc` sin `tsconfig` usa lib ES5 por defecto, donde `String.prototype.includes` y
  `String.prototype.normalize` no existen como tipos. Se escribió `rut.ts` compatible con lib ES5
  (`indexOf`, helper `nfkc()` con fallback a identidad); en Node ≥20 `normalize("NFKC")` existe y
  se usa, por lo que la fidelidad con `_limpiar_entrada` se mantiene.
- `plans/README.md` no se tocó (override del revisor).

Prototipo desechable (NO está en el repo, solo en `/tmp/ts-port-spike/`):
`rut.ts` (191 líneas) + `run.mjs` (82 líneas), cero dependencias.

## 2. Implementación

`rut.ts` expone dos funciones puras que replican la especificación y el código Python de referencia:

- `calcularDV(base, factores = [2..7], modulo = 11): string` — §2 de la especificación;
  `dv = 11 - (suma % 11)`; `11 → "0"`, `10 → "k"` (minúscula, igual que
  `rutificador/utils.py:162-165`). Factores y módulo parametrizables desde `configuracion` de los vectores.
- `validar(entrada, modo: "estricto" | "flexible", maxDigitos = 9, minDigitos = 1)` →
  `{ estado, normalizado, codigos_error }` — réplica fiel de `Rut.normalizar` (9 pasos) +
  classifier `Rut.parse:284-380`, incluyendo los detalles no obvios:
  - espacios → `CARACTERES_INVALIDOS` en estricto, advertencia+tolerancia en flexible;
  - `""` → `RUT_VACIO` + `incompleto`; cadena sin dígitos pero sin error añadido → `incompleto`
    (rama `!/\d/` de `_validar_caracteres_base`, sin código de error);
  - `>1` guion → `FORMATO_GUION`; puntos con grupos no exactos de 3 → `FORMATO_PUNTOS`;
  - ceros a la izquierda con `lstrip("0")` (`""` → `"0"`); DV lowercased (`"K"` → `"k"`);
  - sin DV → `posible`; DV discordante → `DV_DISCORDANTE` + `invalido`; longitudes contra
    `min/max_digitos` de la config.

Los 4 estados (`valido | invalido | posible | incompleto`) y ambos modos son alcanzables y quedan
cubiertos por los 15 casos. Ninguna laguna de vectores/especificación bloqueó el trabajo; una
observación menor (no bloqueante): el docstring de `Rut.parse` dice que en ESTRICTO los guiones
alternativos se rechazan, pero el código (`_verificar_guiones_alternativos`) solo añade advertencia
`NORMALIZACION_GUION` en ambos modos — el prototipo replica el código, no el docstring. Ningún
vector cubre ese caso.

## 3. Validación

`run.mjs` carga `tests/vectors/conformance.json`, ejecuta los 27 casos con la regla exacta de
`scripts/conformance.py:79-87` e imprime PASS/FAIL por caso + resumen. Salida íntegra:

```
Vectors v1.0.0 (spec v1.0)
Algoritmo: modulo 11 con factores ciclicos

--- Calculo de Digito Verificador ---
  [PASS] base=  12345678  esperado=5  obtenido=5
  [PASS] base=  98765432  esperado=5  obtenido=5
  [PASS] base=         1  esperado=9  obtenido=9
  [PASS] base=         0  esperado=0  obtenido=0
  [PASS] base=  12345670  esperado=k  obtenido=k
  [PASS] base=  99999999  esperado=9  obtenido=9
  [PASS] base=  11111111  esperado=1  obtenido=1
  [PASS] base= 100000000  esperado=7  obtenido=7
  [PASS] base= 123456789  esperado=2  obtenido=2
  [PASS] base=  50000000  esperado=7  obtenido=7
  [PASS] base=  76543210  esperado=3  obtenido=3
  [PASS] base=  22222222  esperado=2  obtenido=2

--- Validacion de RUT ---
  [PASS] entrada='12.345.678-5'  modo=estricto  estado=valido
  [PASS] entrada='12345678-5'  modo=estricto  estado=valido
  [PASS] entrada='12.345.678-9'  modo=estricto  estado=invalido
  [PASS] entrada='12 345 678-5'  modo=estricto  estado=invalido
  [PASS] entrada='12 345 678-5'  modo=flexible  estado=valido
  [PASS] entrada='1-9'  modo=flexible  estado=valido
  [PASS] entrada='12345678'  modo=estricto  estado=posible
  [PASS] entrada='12345670-k'  modo=estricto  estado=valido
  [PASS] entrada='12345670-K'  modo=estricto  estado=valido
  [PASS] entrada=''  modo=estricto  estado=incompleto
  [PASS] entrada='abc'  modo=estricto  estado=invalido
  [PASS] entrada='12.34.567-8'  modo=estricto  estado=invalido
  [PASS] entrada='000012345678-5'  modo=flexible  estado=valido
  [PASS] entrada='0-0'  modo=estricto  estado=valido
  [PASS] entrada='12-3-4'  modo=estricto  estado=invalido

==================================================
Resultado: 27/27 pasaron
```

`tsc --noEmit` exit `0`; `node run.mjs` → **27/27, exit `0`**. Conformidad conseguida al primer
intento del runner (sin iterar sobre el prototipo): la especificación + vectores bastaron, sin
necesidad de leer el Python más allá de confirmar detalles.

## 4. Empaquetado y CI

1. **Nombre npm**: `npm view @tooltician/rutificador version` → `E404 Not Found` — **nombre libre**.
   Nota: el scope `@tooltician` tampoco existe aún; hay que crear la organización en npm antes de
   publicar (requiere cuenta con 2FA + token de provenance).
2. **Opción A (repo separado, recomendado) vs. B (monorepo `packages/ts`)**:
   - A: versionado npm independiente — coherente con plan 018 (los vectores ya versionan aparte de
     la librería); CI propia (setup-node, tsc, vitest, gate); cero riesgo para `publish-package.yml`,
     que detecta releases por `pyproject.toml` y tags `v*` (colisionarían con releases npm) y para la
     regla de AGENTS.md que exige bump de `rutificador/version.py` por release. Coste: segundo repo;
     los vectores se consumen vía artifact `rutificador-conformance-vectors` o pin por tag.
   - B: vectores sincronizados por construcción y gate en el mismo workflow; pero obliga a reescribir
     triggers de `publish-package.yml` (tags `ts-v*`, `paths:`), añadir toolchain Node al CI Python y
     acoplar releases PyPI↔npm. Para un solo mantenedor, el acoplamiento cuesta más que el segundo repo.
3. **Bosquejo del workflow CI del port** (solo bosquejo, sin código):
   `setup-node` (Node 20 LTS+) → `npm ci` → `tsc --noEmit` → build (tsup/tsc, ESM+CJS+`.d.ts`) →
   descargar artifact `rutificador-conformance-vectors` del workflow `conformance.yml` (o pin por tag)
   → validar vectores contra `schema.json` (ajv) → `node ./conformance/run.mjs` con **exit 0 bloqueante**
   en push y PR. Publicación npm con provenance (`id-token: write`, como ya hace `publish-package.yml`
   para PyPI) solo desde tags.
4. **Estimación gruesa: S/M** — S el núcleo conforme (evidencia: 273 líneas totales, una sesión, 27/27
   al primer intento); M el paquete v0.1 publicable (1–2 semanas): `package.json` con exports
   ESM+CJS+types, suite vitest espejo de los vectores + property-based (factores/DV), README/CHANGELOG/
   LICENSE, CI con gate bloqueante, `publint` + provenance npm. Alcance v0.1 = núcleo validado por el
   harness (`calcularDV` + `validar`); builder `Rut`, formateo, enmascarado/token, sugestor y CLI quedan
   fuera (paridad total = trabajo posterior, solo si hay adopción).

## 5. Decisión: go-condicional

**Decisión: go-condicional** — portar el núcleo validador a `@tooltician/rutificador` en repo separado,
con gate de conformidad bloqueante desde el día uno; paridad total de la librería, diferida.

Factores:
1. **A favor — coste probado bajo**: 27/27 al primer intento con ~190 líneas TS sin dependencias; la
   especificación + vectores son suficientes como contrato (no hizo falta adivinar semántica).
2. **A favor — motivo distinto al rechazo 017**: aquel no-go fue por rendimiento FFI; aquí el motivo es
   distribución client-side (navegador, Deno, Cloudflare Workers), que Python no cubre.
3. **A favor — nombre libre y contrato consumible**: E404 en npm; artifact + schema + runner ya existen.
4. **Condición — alcance acotado**: el spike solo cubre DV + classifier; v0.1 = núcleo del harness, nada más.
5. **Condición — anti-divergencia**: sin gate bloqueante en CI del port desde el día uno, dos
   implementaciones divergen; con él, los vectores mandan (principio ya establecido en plan 018).

## 6. Plan de construcción (si go) — fases y done criteria

- **Fase 1 — Repo y gate (done: repo `rutificador-ts` con CI en verde corriendo tsc + gate 27/27 exit 0
  bloqueante en push/PR; vectores consumidos por pin versionado, no por copia manual)**:
  scaffolding (`package.json` con exports ESM+CJS+types, `tsconfig` estricto, vitest), port endurecido de
  `rut.ts` (incluido caso guion-alternativo-en-estricto según lo que decida el mantenedor Python),
  `conformance/run.mjs` + validación ajv contra `schema.json`.
- **Fase 2 — Suite propia (done: `vitest --run` ≥85% cobertura en líneas del núcleo; property-based sobre
  DV — p. ej. `calcularDV` coincide con implementación ingenua independiente; negativos: entradas
  maliciosas/sobretamaño)**.
- **Fase 3 — Publicación v0.1 (done: `npm publish --provenance` de `@tooltician/rutificador@0.1.0` con
  `publint` limpio, README con ejemplo client-side, CHANGELOG, LICENSE; tag y GitHub Release)**.
- **Fase 4 — Mantenimiento (done: documento de sincronización de vectores — renovar pin + CHANGELOG
  `[CONFORMANCE]` ante cada bump de `conformance.json`; ADR con la decisión de este spike)**.
- **Explícitamente fuera de v0.1 (deferred, pertenecen a planes posteriores)**: release cadence
  automatizada, docs del port más allá del README, paridad con builder/formateo/enmascarado/sugestor/CLI.
