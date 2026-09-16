# Plan 007: Evaluar y adoptar la segunda fase de calidad y rendimiento

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso y trata cada
> herramienta como un piloto con criterio de adopción explícito. Ejecuta todas
> las verificaciones antes de avanzar. Si ocurre una condición de parada,
> detente e informa; no sustituyas herramientas ni amplíes el alcance por tu
> cuenta. Al terminar, actualiza el estado de este plan en `plans/README.md`.
>
> **Comprobación de deriva (ejecutar primero)**:
> `git diff --stat e2d9a59..HEAD -- pyproject.toml requirements-dev.txt .github/workflows/ci.yml README.md CONTRIBUTING.md tests rutificador`
> Si cambió algún archivo dentro del alcance, compara el estado actual con los
> extractos de este documento. Una divergencia material es condición de parada.

## Estado

- **Prioridad**: P3
- **Esfuerzo**: L
- **Riesgo**: MED
- **Depende de**: ninguno; los planes 001–005 ya están terminados
- **Categoría**: dx / tests / perf / migration
- **Planificado en**: commit `e2d9a59`, 2026-06-20

## Por qué importa

Rutificador ya dispone de lint, tipos, pruebas, auditoría de dependencias,
benchmark básico y escaneo de seguridad. La segunda fase debe elevar la calidad
sin convertir el mantenimiento de herramientas en un fin en sí mismo. Este
plan evalúa cuatro candidatas: `mutmut` para medir la capacidad de las pruebas
de detectar errores, `import-linter` para fijar límites arquitectónicos,
`pyperf` para mediciones de rendimiento rigurosas y `uv` para instalaciones y
resolución reproducibles. Ninguna debe convertirse en dependencia runtime.

La adopción es incremental: cada piloto debe demostrar valor y estabilidad por
separado. No se deben incorporar las cuatro de forma automática.

## Estado actual

- `pyproject.toml:48-55` contiene las dependencias exclusivas de desarrollo en
  `[tool.poetry.group.dev.dependencies]`.
- `requirements-dev.txt:1-18` es la fuente instalada por GitHub Actions.
- `.github/workflows/ci.yml:57-97` ejecuta Ruff, mypy, deptry y validación de
  pre-commit dentro del job `quality`.
- `tests/test_benchmark.py:8-15` contiene un benchmark funcional con
  `pytest-benchmark` para `Rut.parse()`.
- `rutificador/procesador.py:428-466` contiene `evaluar_rendimiento()`, una
  medición manual basada en `time.perf_counter()` que genera entradas
  aleatorias.
- El núcleo publicado no tiene dependencias obligatorias. En el wheel, FastAPI,
  HTTPX, Pydantic, pandas y polars solo aparecen bajo extras.
- Convención Git observada: ramas `codex/<descripcion>` y commits
  Conventional Commits, por ejemplo
  `chore: strengthen development quality gates`.

Fragmentos de referencia:

```toml
# pyproject.toml:48-55
[tool.poetry.group.dev.dependencies]
pytest = ">=9.0.3,<10.0.0"
pytest-cov = ">=5.0.0,<8.0.0"
pytest-benchmark = "5.2.3"
deptry = "0.25.1"
cyclonedx-bom = "7.3.0"
pre-commit = "4.6.0"
httpx2 = "2.4.0"
```

```python
# tests/test_benchmark.py:8-10
def test_benchmark_parse_rut(benchmark: Any) -> None:
    resultado = benchmark(Rut.parse, "12.345.678-5")
```

## Decisiones de diseño obligatorias

1. `mutmut`, `import-linter` y `pyperf` solo pueden incorporarse como
   dependencias de desarrollo y jobs de CI separados o programados.
2. `uv` es una migración del flujo de dependencias, no una librería del paquete.
   No debe coexistir indefinidamente con dos fuentes de verdad divergentes.
3. `pytest-benchmark` se conserva para feedback rápido. `pyperf`, si se adopta,
   se limita a benchmarks comparativos/nocturnos; no debe duplicar todos los
   benchmarks de pytest.
4. Los umbrales iniciales deben registrar una línea base antes de bloquear CI.
5. Cada piloto se entrega en un PR independiente y en el orden indicado abajo.

## Comandos necesarios

| Propósito | Comando | Resultado esperado |
|---|---|---|
| Instalar desarrollo | `python -m pip install -r requirements-dev.txt && python -m pip install -e .` | exit 0 |
| Formato | `ruff format --check rutificador tests` | exit 0, sin cambios |
| Lint | `ruff check rutificador tests` | exit 0 |
| Tipos | `mypy rutificador/ --ignore-missing-imports` | sin errores |
| Dependencias | `deptry rutificador` | `Success! No dependency issues found.` |
| Pruebas | `pytest -W error -q tests/` | todas pasan, sin warnings |
| Seguridad | `bandit -q -r rutificador/ --severity-level medium --confidence-level medium` | exit 0 |
| Auditoría | `pip-audit --progress-spinner off --skip-editable` | 0 vulnerabilidades |
| Build | `python -m build` | wheel y sdist construidos |

## Alcance

**Dentro del alcance**:

- `pyproject.toml`
- `requirements-dev.txt`
- `.github/workflows/ci.yml` y, solo si se justifica, un workflow nuevo y
  específico bajo `.github/workflows/`
- `tests/test_benchmark.py` y nuevos archivos bajo `tests/benchmarks/`
- configuración nueva de `import-linter`, `mutmut`, `pyperf` o `uv`
- `README.md`, `CONTRIBUTING.md` y `CHANGELOG.md`
- `rutificador/version.py` únicamente si el workflow de publicación exige
  sincronizar una nueva versión; la fuente de versión actual es
  `pyproject.toml`

**Fuera del alcance**:

- Añadir cualquiera de las cuatro herramientas a `[tool.poetry.dependencies]`
  o a extras de usuario.
- Cambiar la API pública o los resultados de validación del RUT.
- Reescribir algoritmos para mejorar un benchmark antes de obtener una línea
  base estable.
- Sustituir Ruff, mypy, pytest, deptry, Bandit, pip-audit o CycloneDX.
- Modificar integraciones opcionales de FastAPI, Pydantic, pandas o polars.
- Publicar a PyPI automáticamente como parte de estos pilotos.

## Flujo Git

- Crear un PR por piloto con ramas:
  - `codex/007-mutmut-pilot`
  - `codex/007-import-boundaries`
  - `codex/007-pyperf-baseline`
  - `codex/007-uv-spike`
- Usar commits Conventional Commits: `test: add mutation testing pilot`,
  `chore: enforce import boundaries`, `perf: establish pyperf baseline` y
  `build: evaluate uv workflow`.
- No hacer push, abrir PR ni fusionar salvo instrucción del operador.
- No comenzar el siguiente piloto hasta que el anterior esté fusionado y verde.

## Pasos

### Paso 1: Pilotar `mutmut` sobre el núcleo matemático

1. Consultar PyPI/documentación oficial y fijar una versión compatible con
   Python 3.10–3.14.
2. Añadir `mutmut` a ambos manifiestos de desarrollo.
3. Configurar el alcance exclusivamente sobre `rutificador/utils.py`,
   `rutificador/validador.py` y las funciones críticas de `rutificador/rut.py`.
4. Ejecutar primero una corrida informativa. Clasificar mutantes en:
   eliminados, sobrevivientes equivalentes y sobrevivientes accionables.
5. Añadir pruebas solo para sobrevivientes que representen una regresión real;
   no escribir tests que congelen detalles internos sin valor contractual.
6. Crear un job manual o programado. No incluir mutation testing en cada celda
   de la matriz Python.
7. Documentar duración, mutation score inicial y decisión de adopción.

**Verificar**:

- `mutmut run` termina sin errores de infraestructura.
- `mutmut results` no contiene mutantes no clasificados.
- `pytest -W error -q tests/` permanece verde.
- La instalación del wheel base sigue sin `mutmut` en `Requires-Dist`.

**Criterio de adopción**: adoptar si la corrida completa del alcance termina en
menos de 20 minutos en CI y descubre al menos un hueco de prueba real o produce
un score reproducible útil. En caso contrario, documentar el rechazo y retirar
la dependencia/configuración antes de cerrar el piloto.

### Paso 2: Formalizar límites con `import-linter`

1. Añadir `import-linter` solo a desarrollo.
2. Declarar contratos mínimos:
   - `rutificador` no puede importar desde `tests`;
   - módulos del núcleo (`config`, `errores`, `exceptions`, `utils`,
     `validador`, `rut`) no pueden importar desde `rutificador.contrib`;
   - `rutificador.contrib` puede depender del núcleo, pero el núcleo no puede
     depender de integraciones;
   - `rutificador.cli` puede depender del núcleo, pero el núcleo no puede
     depender de `cli`.
3. Ejecutar los contratos contra el estado actual. Si revelan una violación,
   no relajar el contrato automáticamente: confirmar primero si la dirección
   de dependencia es intencional.
4. Añadir `lint-imports` al job `quality` después de deptry.
5. Documentar los contratos y cómo actualizarlos al añadir módulos.

**Verificar**: `lint-imports` termina con todos los contratos `KEPT`; los gates
generales permanecen verdes.

**Criterio de adopción**: adoptar si los contratos expresan límites reales y
estables. Rechazar si solo reproducen reglas que Ruff ya garantiza o requieren
excepciones amplias.

### Paso 3: Crear una línea base rigurosa con `pyperf`

1. Añadir `pyperf` solo a desarrollo.
2. Crear scripts bajo `tests/benchmarks/` para:
   - `calcular_digito_verificador`;
   - `Rut.parse()` con entrada válida e inválida;
   - lote serial de 1.000 y 10.000 entradas;
   - streaming serial;
   - comparación serial/procesos únicamente para tamaños donde el overhead de
     procesos sea representativo.
3. Usar datos deterministas. No reutilizar la aleatoriedad de
   `evaluar_rendimiento()` sin fijar semilla y separar generación de medición.
4. Guardar resultados como artefactos JSON; no versionar resultados propios de
   una máquina.
5. Ejecutar inicialmente en workflow manual/nocturno sobre runner fijo. No
   introducir un umbral bloqueante hasta reunir al menos cinco ejecuciones.
6. Mantener `tests/test_benchmark.py` como smoke benchmark rápido.

**Verificar**: cada script `pyperf` produce JSON válido y una segunda ejecución
puede compararse con `python -m pyperf compare_to`; pytest sigue verde.

**Criterio de adopción**: adoptar si la variabilidad de las métricas críticas
es suficientemente baja para distinguir regresiones de al menos 10 %. Si no,
conservar únicamente `pytest-benchmark` y documentar el rechazo.

### Paso 4: Ejecutar un spike de migración a `uv`

1. No modificar manifiestos al comenzar. Medir en checkout limpio:
   instalación actual, resolución y duración del job CI.
2. Probar `uv` con el `pyproject.toml` existente y producir un lockfile para
   desarrollo compatible con Python 3.10–3.14 y extras opcionales.
3. Verificar que `uv` instala el editable, todos los extras de pruebas y las
   cuatro plataformas Python de CI sin cambiar metadata del wheel.
4. Comparar tres opciones y registrar la decisión:
   - mantener Poetry + pip actuales;
   - usar `uv` solo como instalador de CI;
   - migrar resolución/lock completamente a `uv`.
5. Si se adopta `uv`, definir una única fuente de verdad, actualizar
   Dependabot, caché de Actions, README y CONTRIBUTING, y retirar los archivos
   que queden reemplazados. No conservar un lock de uv y requirements manuales
   divergentes.

**Verificar**:

- Una instalación desde cero con la opción elegida termina exit 0.
- Toda la matriz Python 3.10–3.14 pasa.
- `python -m build` mantiene el wheel base sin dependencias obligatorias.
- El tiempo de instalación queda registrado antes/después.

**Criterio de adopción**: adoptar solo si reduce de forma medible el tiempo de
CI o mejora reproducibilidad sin duplicar fuentes de dependencias. Si no,
eliminar los artefactos del spike y registrar `REJECTED` con cifras.

### Paso 5: Cerrar la fase y documentar decisiones

1. Actualizar `README.md`, `CONTRIBUTING.md` y `CHANGELOG.md` solo con las
   herramientas efectivamente adoptadas.
2. Actualizar versión siguiendo el gate `version-bump-gate.yml` antes del PR
   que libere cambios versionables.
3. Registrar para cada candidata: versión, duración CI, beneficio observado,
   coste de mantenimiento y veredicto `ADOPTED`/`REJECTED`.
4. Ejecutar todos los gates locales y remotos; no fusionar con checks pendientes
   o amarillos.

**Verificar**: no quedan comandos documentados que no existan en los
manifiestos o workflows; `git diff --check` y todos los comandos de la tabla
terminan exit 0.

## Plan de pruebas

- `mutmut`: usar `tests/test_property.py`, `tests/test_consistencia_parse.py` y
  `tests/test_rutificador.py` como patrones para invariantes y regresiones.
- `import-linter`: probar un contrato válido en el repositorio real y añadir un
  fixture/proyecto mínimo solo si la herramienta permite verificar que una
  violación intencional falla.
- `pyperf`: separar preparación de datos de la región medida; cubrir entradas
  válidas, inválidas, lotes y streaming.
- `uv`: probar instalación desde un entorno vacío, paquete editable, build de
  wheel y todos los extras empleados por tests.
- Gate final: `pytest -W error -q tests/` debe mantener al menos las 247 pruebas
  existentes y todas las nuevas.

## Criterios de finalización

- [ ] Cada herramienta tiene un veredicto explícito `ADOPTED` o `REJECTED` con
      evidencia cuantitativa.
- [ ] Ninguna candidata aparece en las dependencias runtime o extras de usuario.
- [ ] `ruff format --check rutificador tests` termina exit 0.
- [ ] `ruff check rutificador tests` termina exit 0.
- [ ] `mypy rutificador/ --ignore-missing-imports` termina sin errores.
- [ ] `deptry rutificador` informa cero problemas.
- [ ] `pytest -W error -q tests/` pasa sin warnings.
- [ ] Bandit y pip-audit terminan sin hallazgos bloqueantes.
- [ ] `python -m build` produce wheel y sdist.
- [ ] El wheel no contiene dependencias obligatorias nuevas.
- [ ] CI completo, CodeQL, Codacy y Snyk quedan verdes antes de cada merge.
- [ ] `plans/README.md` refleja el estado final de este plan.

## Condiciones de parada

Detenerse e informar si:

- Los extractos o comandos base ya no coinciden con el repositorio.
- Una herramienta no soporta alguna versión de Python 3.10–3.14.
- La adopción exige añadir una dependencia runtime.
- `uv` obliga a mantener dos fuentes de verdad que no pueden generarse una
  desde otra de forma determinista.
- Un benchmark no es estable tras tres intentos razonables de aislamiento.
- Mutation testing supera 20 minutos en CI o genera sobrevivientes imposibles
  de clasificar sin cambiar comportamiento público.
- Un contrato de imports requiere refactorizar la API pública.
- Un gate falla dos veces después de una corrección razonable.
- Se requiere modificar un archivo fuera del alcance.

## Notas de mantenimiento

- Revisar versiones fijadas trimestralmente junto con Dependabot.
- Los benchmarks deben ejecutarse en runners comparables; resultados entre
  hardware distinto no son una regresión válida.
- Los contratos de imports deben actualizarse cuando aparezca una nueva capa,
  no desactivarse para resolver rápidamente una violación.
- Mutation score es una señal sobre las pruebas, no un KPI que justifique tests
  artificiales.
- La decisión sobre `uv` debe revisarse si Poetry o GitHub Actions cambian
  sustancialmente sus tiempos o soporte de lockfiles.
