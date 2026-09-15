# Harness de conformidad RUT

> **Contrato para ports**: cualquier port del validador (Rust → WASM,
> TypeScript, Go u otro) debe pasar este harness antes de considerarse
> conforme. Los vectores son la fuente canónica de verdad; el código
> Python es solo una implementación de referencia.

## Artefactos

| Artefacto | Propósito |
|-----------|-----------|
| `tests/vectors/conformance.json` | Vectores unificados y versionados (`version`, `spec_version`) |
| `tests/vectors/schema.json` | JSON Schema (draft 2020-12) que fija el formato estable |
| `tests/vectors/test_vectors_dv.json` | Legado: casos de cálculo de DV (referencia histórica) |
| `tests/vectors/test_vectors_validacion.json` | Legado: casos de validación (referencia histórica) |
| `scripts/conformance.py` | Runner standalone, sin dependencia de pytest |
| `scripts/export_vectors.py` | Exporta los vectores a `dist/vectors/` (JSON, YAML) |
| `.github/workflows/conformance.yml` | CI: valida contra el schema, verifica la implementación Python, publica los vectores como artifact |

`conformance.json` unifica los dos archivos legado sin alterar ningún valor.
Si alguna verificación detecta inconsistencia entre vectores e
implementación, los vectores mandan: no se modifican sin aprobación del
mantenedor (ver plan 018).

## Versionado

Los vectores se versionan de forma independiente de la librería mediante el
campo `version` de `conformance.json` (hoy `1.0.0`, spec `1.0`). Al agregar
casos, incrementar esa versión. La especificación formal vive en
`docs/especificacion-reglas-rut.md` y cualquier cambio de algoritmo o regla
debe reflejarse en ambos documentos a la vez.

## Interfaz del runner

`scripts/conformance.py` ejecuta cualquier implementación detrás de dos
funciones (sección de adaptación, al inicio del archivo):

```python
def dv_implementation(base: str, config: dict) -> str: ...
def validation_implementation(entrada: str, modo: str, config: dict) -> dict: ...
```

`validation_implementation` retorna
`{estado, normalizado, codigos_error}` donde `estado` es uno de
`valido | invalido | posible | incompleto` y `modo` es
`estricto | flexible`. Exit code `0` = todos los casos pasan,
`1` = hay fallos. Para portar, copiar el script y reemplazar esas dos
funciones por las del lenguaje destino:

```bash
python scripts/conformance.py --vectors tests/vectors/conformance.json
```

## Consumo desde un port

1. Descargar el artifact `rutificador-conformance-vectors` del workflow
   `conformance.yml` (o copiar `tests/vectors/conformance.json`).
2. Validar el archivo contra `tests/vectors/schema.json`.
3. Adaptar `scripts/conformance.py` (o reimplementar el runner) y exigir
   exit code `0` en CI del port.
4. El port recomendado como base nativa es Rust (ver `plans/017-pyO3-native-spike.md`;
   depende de este harness para validar la implementación nativa).

## Alcance y guardas

- Este harness no cambia el comportamiento del validador ni la API pública.
- Ítems REJECTED del roadmap (`mutmut`, `pyperf`, migración a `uv`,
  `ROADMAP.md:14-17`) siguen fuera de alcance y no se tocan en este trabajo.
- Referencias: `plans/011-spec-formal-reglas-rut.md` (especificación y
  vectores), `plans/018-conformance-harness.md` (diseño del harness),
  `plans/017-pyO3-native-spike.md` (consumidor nativo).
