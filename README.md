<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/rutificador.svg)](https://pypi.org/project/rutificador/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![Downloads](https://img.shields.io/pypi/dm/rutificador)](https://pypi.org/project/rutificador/)
[![Licencia](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Estilo de código](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)
[![Integración continua](https://github.com/cortega26/rutificador/actions/workflows/ci.yml/badge.svg)](https://github.com/cortega26/rutificador/actions/workflows/ci.yml)

</div>

# Rutificador

Biblioteca en Python para validar, calcular y formatear RUTs (Rol Único Tributario) chilenos. **Sin dependencias externas**, con tipado estático completo y soporte para procesamiento por lotes, streaming, CLI y extras opcionales para Pydantic v2, FastAPI, pandas y polars.

```python
from rutificador import Rut

# Validar y formatear en una línea
rut = Rut("12.345.678-5")
print(rut.formatear(separador_miles=True))  # 12.345.678-5

# Parseo seguro sin excepciones
resultado = Rut.parse("12.345.678-9")
print(resultado.estado, resultado.codigo_error)  # invalido DV_DISCORDANTE
```

## Tabla de Contenidos

- [Características](#caracteristicas)
- [Instalación](#instalacion)
- [Uso básico](#uso-basico)
  - [Validar un RUT](#validar-un-rut)
  - [Formatear](#formatear)
  - [Parseo seguro](#parseo-seguro-sin-excepciones)
  - [Calcular dígito verificador](#calcular-digito-verificador)
  - [Enmascarar datos sensibles](#enmascarar-datos-sensibles)
  - [Sugerencias y autocorrección](#sugerencias-y-autocorreccion)
- [Línea de comandos](#linea-de-comandos)
- [Procesamiento por lotes](#procesamiento-por-lotes)
- [Integraciones](#integraciones)
  - [Pydantic v2](#pydantic-v2-extra-opcional)
  - [FastAPI](#fastapi-extra-opcional)
  - [pandas](#pandas-extra-opcional)
  - [polars](#polars-extra-opcional)
- [Personalizar validación](#personalizar-la-validacion)
- [Política de errores](#politica-de-errores)
- [Registro y depuración](#registro-y-depuracion)
- [API de referencia](#api-de-referencia)
  - [Metadatos de validación](#acceder-a-metadatos-de-validacion)
  - [Evaluar rendimiento](#evaluar-rendimiento)
  - [Formateador personalizado](#registrar-un-formateador-personalizado)
- [Desarrollo](#desarrollo)
- [Licencia](#licencia)

## Características

- **0 dependencias base** — solo estándar de Python. Instalación liviana y segura.
- **Validación completa** — formato, dígito verificador, longitud configurable y modos de rigor (`ESTRICTO`, `FLEXIBLE`, `LEGADO`).
- **Formateo configurable** — separador de miles, mayúsculas en DV, separador personalizado.
- **Streaming y lotes** — procesa archivos de millones de líneas sin cargar todo en memoria.
- **Paralelismo adaptable** — motor por procesos (CPU-bound) o hilos (I/O-bound).
- **Parseo seguro** — `Rut.parse()` retorna siempre un resultado estructurado, nunca lanza excepción.
- **Enmascarado y tokenización** — protege datos sensibles en logs, exports o pantallas.
- **Motor de sugerencias** — corrección fuzzy de errores tipográficos comunes (transposiciones, DV erróneo).
- **Extraíbles opcionales** — integraciones nativas con Pydantic v2, FastAPI, pandas y polars.
- **Tipado estático** — `py.typed` (PEP 561), cobertura mypy completa.
- **CLI profesional** — salida en text, JSON, JSONL, CSV y XML; auto-corrección, sugerencias y auditoría.

## Instalación

```sh
pip install rutificador
```

Con extras opcionales:

```sh
pip install rutificador[pydantic]   # Pydantic v2
pip install rutificador[fastapi]    # FastAPI + Pydantic
pip install rutificador[pandas]     # pandas accessor
pip install rutificador[polars]     # polars namespace
pip install rutificador[full]       # todo lo anterior
```

## Uso básico

### Validar un RUT

```python
from rutificador import Rut

# Creación directa — valida en el constructor
rut = Rut("12345678-5")

# Desde entradas con formato libre
rut = Rut("12.345.678-5")
rut = Rut("12345678-5")
```

Si el RUT es inválido, se lanza `ErrorValidacionRut`:

```python
from rutificador import Rut
from rutificador.exceptions import ErrorValidacionRut

try:
    Rut("12.345.678-9")
except ErrorValidacionRut as e:
    print(e.codigo_error)  # DV_DISCORDANTE
```

### Formatear

```python
rut = Rut("12345678-5")

print(rut.formatear())                             # 12345678-5
print(rut.formatear(separador_miles=True))         # 12.345.678-5
print(rut.formatear(mayusculas=True))              # 12345678-5
print(rut.formatear(separador_miles=True, mayusculas=True))  # 12.345.678-5

# RUT con DV 'k'
rut_k = Rut("12345670-k")
print(rut_k.formatear(separador_miles=True, mayusculas=True))  # 12.345.670-K
```

### Parseo seguro (sin excepciones)

```python
from rutificador import Rut

resultado = Rut.parse("12.345.678-5")
print(resultado.estado)       # valido
print(resultado.normalizado)  # 12345678-5

resultado = Rut.parse("12.345.678-9")
print(resultado.estado)        # invalido
print(resultado.codigo_error)  # DV_DISCORDANTE

# Normalización con rigor flexible
from rutificador.config import RigorValidacion

normalizado, errores, advertencias = Rut.normalizar(
    "12 345 678-5", modo=RigorValidacion.FLEXIBLE
)
print(normalizado)  # 12345678-5
```

### Calcular dígito verificador

```python
from rutificador import calcular_digito_verificador

dv = calcular_digito_verificador("12345678")
print(dv)  # 5
```

### Enmascarar datos sensibles

```python
from rutificador import Rut

# Ofuscar parcialmente
print(Rut.enmascarar("12.345.678-5", mantener=3, caracter="X"))  # XXXXX678-5
print(Rut.enmascarar("12.345.678-5", mantener=4))                 # ****5678-5

# Tokenización
print(Rut.enmascarar("12.345.678-5", modo="token", clave="mi-clave"))  # tok_abc123...
```

### Sugerencias y autocorrección

```python
from rutificador import Rut

# Sugerir correcciones para un RUT con error tipográfico
sugerencias = Rut.sugerir("12.345.687-5")
print(sugerencias)  # ['12345678-5', ...]

# Autocorrección inteligente
mejor_opcion = Rut.mejorar("12a345678-k")
print(mejor_opcion)  # 12345678-5
```

## Línea de comandos

```bash
# Validar desde un archivo
rutificador validar ruts.txt

# Validar desde stdin
cat ruts.txt | rutificador validar

# Formatear con separador de miles
rutificador formatear ruts.txt --separador-miles --mayusculas

# Enmascarar datos sensibles
rutificador enmascarar ruts.txt --mantener 3

# Salida estructurada
rutificador validar ruts.txt --format jsonl > resultados.jsonl

# Procesamiento paralelo
rutificador validar ruts_pesados.txt --paralelo --format csv

# Autocorrección + sugerencias
rutificador validar sucia_db.txt --mejorar --sugerir

# Información del sistema
rutificador info
```

### Formatos de salida

| Formato | Descripción |
|---------|-------------|
| `text` | Legible por humanos con resumen de auditoría en stderr |
| `json` | Array JSON estándar (OOM-Safe via streaming) |
| `jsonl` | Una línea por registro — ideal para Big Data |
| `csv` | Hoja de cálculo con cabecera |0|
| `xml` | Estructura incremental para integraciones legacy |

### Comandos disponibles

| Comando | Descripción |
|---------|-------------|
| `validar` | Valida RUTs desde archivo o stdin |
| `formatear` | Valida y formatea RUTs con opciones de salida |
| `enmascarar` | Ofusca/tokeniza RUTs para proteger datos sensibles |
| `info` | Muestra versión, entorno y funcionalidades |

## Procesamiento por lotes

```python
from rutificador import ProcesadorLotesRut

ruts = ['12.345.678-5', '98.765.432-1', '1-9']
procesador = ProcesadorLotesRut()

# Validar lote
resultado = procesador.validar_lista_ruts(ruts)
print(len(resultado.detalles_validos))    # 2
print(len(resultado.detalles_invalidos))  # 1

# Formatear a JSON, CSV o XML
csv = procesador.formatear_lista_ruts(ruts, formato="csv")
print(csv)
# rut
# 12345678-5
# ...

# Paralelismo explícito
procesador = ProcesadorLotesRut(motor_paralelo="process")
resultado = procesador.validar_lista_ruts(ruts, paralelo=True)
```

### Streaming (archivos grandes)

```python
from rutificador import (
    validar_flujo_ruts,
    formatear_flujo_ruts,
)

# Validar millones de RUTs sin cargar todo en memoria
ruts = (linea.strip() for linea in open("muy_grande.txt"))
for es_valido, resultado in validar_flujo_ruts(ruts):
    if es_valido:
        print(resultado.valor)
```

## Integraciones

### Pydantic v2 (extra opcional)

```sh
pip install rutificador[pydantic]
```

```python
from pydantic import BaseModel
from rutificador.contrib.pydantic import RutStr, rut_str_annotated

class Usuario(BaseModel):
    rut: RutStr

u = Usuario(rut="12.345.678-5")
print(u.rut)  # 12345678-5

# Formato específico
RutConPuntos = rut_str_annotated(formato="miles-con-guion")

class UsuarioV2(BaseModel):
    rut: RutConPuntos

u2 = UsuarioV2(rut="12.345.678-5")
print(u2.rut)  # 12.345.678-5
```

### FastAPI (extra opcional)

```sh
pip install rutificador[fastapi]
```

```python
from fastapi import FastAPI, Depends
from rutificador import Rut
from rutificador.contrib.fastapi import parametro_rut

app = FastAPI()

@app.get("/usuario/{rut}")
def obtener_usuario(rut: Rut = Depends(parametro_rut)):
    return {"rut_normalizado": str(rut), "dv": rut.digito_verificador}
```

Errores de validación retornan **422 Unprocessable Entity** con código estructurado (`DV_DISCORDANTE`, `CARACTERES_INVALIDOS`, etc.).

### pandas (extra opcional)

```sh
pip install rutificador[pandas]
```

```python
import pandas as pd
import rutificador.pandas  # activa el accessor .rut

s = pd.Series(["12.345.678-5", "12.345.678-9", "invalid"])
print(s.rut.es_valido())
# 0     True
# 1    False
# 2    False

print(s.rut.formatear(formato="miles"))
# 0    12.345.678-5
# 1          None
# 2          None
```

### polars (extra opcional)

```sh
pip install rutificador[polars]
```

```python
import polars as pl
import rutificador.polars  # activa el namespace .rut

df = pl.DataFrame({"rut": ["12.345.678-5", "12.345.678-9", "invalid"]})
print(df.with_columns(pl.col("rut").rut.es_valido()))
```

## Personalizar la validación

```python
from rutificador import Rut, ValidadorRut
from rutificador.config import RigorValidacion, ConfiguracionRut

# Modo flexible: tolera espacios, guiones extra, etc.
validador = ValidadorRut(modo=RigorValidacion.FLEXIBLE)
rut = Rut('12 345 678-5', validador=validador)

# Configuración avanzada
config = ConfiguracionRut(max_digitos=10)
validador = ValidadorRut(configuracion=config)
```

## Política de errores

Todos los errores tienen códigos estables y severidad explícita:

```python
from rutificador import Rut

res = Rut.parse("12..345")
for err in res.errores:
    print(err.codigo, err.severidad, err.hint)
```

| Código | Severidad | Descripción |
|--------|-----------|-------------|
| `ERROR_TIPO` | error | Tipo inválido |
| `RUT_VACIO` | error | Entrada vacía |
| `CARACTERES_INVALIDOS` | error | Caracteres no permitidos |
| `FORMATO_PUNTOS` | error | Separadores de miles inválidos |
| `FORMATO_GUION` | error | Guion inválido |
| `LONGITUD_MINIMA` | error | Longitud mínima no alcanzada |
| `LONGITUD_MAXIMA` | error | Longitud máxima excedida |
| `DV_INVALIDO` | error | Dígito verificador inválido |
| `DV_DISCORDANTE` | error | DV no coincide |
| `ESTADO_ENMASCARADO` | error | Enmascarado en estado no válido |
| `CLAVE_TOKEN_REQUERIDA` | error | Falta clave de tokenización |
| `NORMALIZACION_ESPACIOS` | warning | Espacios eliminados |
| `NORMALIZACION_GUION` | warning | Guion normalizado |
| `NORMALIZACION_PUNTOS` | warning | Puntos eliminados |
| `NORMALIZACION_DV` | warning | DV en minúscula |
| `CEROS_IZQUIERDA` | warning | Ceros a la izquierda eliminados |

## Registro y depuración

```python
import logging
from rutificador import configurar_registro

configurar_registro(level=logging.DEBUG)
```

Con handler personalizado:

```python
import logging
import json
from rutificador import configurar_registro

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({"nivel": record.levelname, "mensaje": record.getMessage()})

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
configurar_registro(level=logging.INFO, handler=handler)
```

## API de referencia

### Acceder a metadatos de validación

```python
from rutificador import ProcesadorLotesRut

procesador = ProcesadorLotesRut()
resultado = procesador.validar_lista_ruts(["12.345.678-5"], paralelo=False)

detalle = resultado.detalles_validos[0]
print(detalle.valor)           # 12345678-5
print(detalle.validador_modo)  # estricto/flexible
print(detalle.duracion)        # segundos consumidos en la validación

# Errores con código estructurado
resultado_error = procesador.validar_lista_ruts(["12345678-9"])
problema = resultado_error.ruts_invalidos[0]
print(problema.rut, problema.codigo, problema.mensaje)
```

### Evaluar rendimiento

```python
from rutificador import evaluar_rendimiento

resultados = evaluar_rendimiento(num_ruts=1000)
print(resultados['tasa_exito'])
```

### Registrar un formateador personalizado

```python
from rutificador.formatter import FormateadorRut, FabricaFormateadorRut

class FormateadorLista(FormateadorRut):
    def formatear(self, ruts):
        return ','.join(ruts)

FabricaFormateadorRut.registrar_formateador('lista', FormateadorLista)
```

## Desarrollo

### Configuración del entorno

```bash
git clone https://github.com/cortega26/rutificador.git
cd rutificador
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
pre-commit install
```

### Calidad

```bash
pytest -W error::DeprecationWarning   # Tests sin deprecaciones
mypy rutificador/                     # Tipado estático
ruff check .                          # Lint
ruff format . --check                 # Formato
bandit -r rutificador/                # Seguridad
```

Las contribuciones son bienvenidas. Revisa [`CONTRIBUTING.md`](CONTRIBUTING.md) para las directrices completas.

## Alcance y limitaciones

Rutificador **no** verifica la existencia del RUT en registros oficiales ni realiza enriquecimiento de identidad. Su alcance es la validación sintáctica, normalización y formateo según las reglas locales del RUT chileno.

## Licencia

MIT © Carlos Ortega González. Ver [LICENSE](LICENSE).

## Créditos

Este proyecto se inspiró en [rut-chile](https://github.com/gevalenz/rut-chile) de [gevalenz](https://github.com/gevalenz).
