# Rutificador

Biblioteca Python para validar, calcular y formatear el Rol Único Tributario
(RUT) chileno. **Sin dependencias externas**, tipado estático completo, y
soporte para procesamiento por lotes, streaming, CLI, e integraciones opcionales
con Pydantic v2, FastAPI, pandas y polars.

```python
from rutificador import Rut

rut = Rut("12.345.678-5")
print(rut.formatear(separador_miles=True))  # 12.345.678-5

resultado = Rut.parse("12.345.678-9")
print(resultado.estado, resultado.codigo_error)  # invalido DV_DISCORDANTE
```

## Características

- **Cero dependencias base** — solo estándar de Python
- **Validación completa** — formato, dígito verificador, longitud configurable, modos de rigor
- **Formateo flexible** — separador de miles, mayúsculas en DV, separador personalizado
- **Streaming y lotes** — archivos de millones de líneas sin cargar todo en memoria
- **Procesamiento en paralelo** — motor por procesos (CPU-bound) o hilos (I/O-bound)
- **Parseo seguro** — `Rut.parse()` nunca lanza excepción
- **Enmascaramiento y tokenización** — protege datos sensibles
- **Motor de sugerencias** — corrección fuzzy de errores tipográficos
- **Integraciones opcionales** — Pydantic v2, FastAPI, pandas, polars
- **Tipado estático** — `py.typed` (PEP 561)
- **CLI profesional** — salida en text, JSON, JSONL, CSV y XML

## Instalación rápida

```sh
pip install rutificador
```

Con extras:

```sh
pip install rutificador[pydantic]   # Pydantic v2
pip install rutificador[fastapi]    # FastAPI + Pydantic
pip install rutificador[pandas]     # pandas accessor
pip install rutificador[polars]     # polars namespace
pip install rutificador[full]       # todo lo anterior
```

## Licencia

MIT &copy; Carlos Ortega González — [tooltician.com](https://tooltician.com)

Parte del [ecosistema Tooltician](https://tooltician.com).
