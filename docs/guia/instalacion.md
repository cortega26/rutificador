# Instalación

## Requisitos

- Python 3.10 o superior
- Sin dependencias externas (solo biblioteca estándar)

## Instalación base

```sh
pip install rutificador
```

## Extras opcionales

| Extra | Contenido | Instalación |
|---|---|---|
| `pydantic` | Tipo `RutStr` para Pydantic v2 | `pip install rutificador[pydantic]` |
| `fastapi` | Dependencia `parametro_rut` para FastAPI | `pip install rutificador[fastapi]` |
| `pandas` | Accessor `Series.rut` para pandas | `pip install rutificador[pandas]` |
| `polars` | Namespace `Expr.rut` para polars | `pip install rutificador[polars]` |
| `full` | Todos los extras anteriores | `pip install rutificador[full]` |

## Verificar instalación

```python
import rutificador
print(rutificador.__version__)
```
