# Contratos machine-readable

Las salidas `--format json|jsonl` de la CLI y el detalle de error 422 del
contrib FastAPI tienen JSON Schemas versionados en `schemas/`, verificados
por `tests/test_contracts.py`. Permiten a bancos, ETLs y frontends validar
las respuestas sin re-derivar las formas a mano.

## Qué cubre cada schema

- `schemas/cli-salida.json` (v1.0.0): `$defs/item` (un resultado por RUT;
  `required: [valido, original]`, resto strings), `$defs/salida_json`
  (`items` + `metadata.audit` con `version`, `total`, `validos`,
  `invalidos`, `tiempo_segundos`, `tasa_exito`, `tasa_error`) y
  `$defs/salida_jsonl` (un ítem por línea). Disposición real: con
  `--format json` stdout lleva el array de ítems y stderr el objeto
  metadata; con `--format jsonl` stdout lleva un ítem por línea.
- `schemas/fastapi-error-422.json` (v1.0.0): objeto con `detail` como array
  no vacío de `{loc, msg, type}` al estilo FastAPI
  (`loc` típicamente `["query", "rut"]`). El 422 viaja en el status HTTP,
  no en el cuerpo.

## Qué queda fuera

- Formatos `text`/`csv`/`xml`: no son machine-readable estables (texto
  libre para humanos, CSV con mitigación de inyección por prefijo `'`,
  XML de depuración). Si los consumes, no hay contrato que los ampare.
- Exit codes (0/1/2): viajan en el proceso, no en el cuerpo; ver la guía
  de CLI.

## Versionado independiente

Cada schema lleva su propio `version` semántico (empiezan en `1.0.0`,
como los vectores de conformidad), desacoplado de la versión del paquete:

- MINOR: campos nuevos opcionales.
- MAJOR: campos nuevos requeridos o cambios de tipo.
- Cada cambio a ítems, metadata o el 422 obliga bump de `version` del
  schema correspondiente + test en verde.

## Ejemplo

```python
import json, jsonschema

item_schema = json.load(open("schemas/cli-salida.json"))["$defs"]["item"]
jsonschema.validate({"valido": True, "original": "12345678-5"}, item_schema)
```

Verificación completa: `pytest tests/test_contracts.py`.
