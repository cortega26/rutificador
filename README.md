<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/rutificador.svg)](https://pypi.org/project/rutificador/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![Downloads](https://img.shields.io/pypi/dm/rutificador)](https://pypi.org/project/rutificador/)
[![Licencia](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Estilo de código](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)
[![Integración continua](https://github.com/cortega26/rutificador/actions/workflows/ci.yml/badge.svg)](https://github.com/cortega26/rutificador/actions/workflows/ci.yml)

</div>

# Rutificador

Biblioteca Python para validar, calcular y formatear el Rol Unico Tributario (RUT) chileno. **Sin dependencias externas**, tipado estatico completo, y soporte para procesamiento por lotes, streaming, CLI, e integraciones opcionales con Pydantic v2, FastAPI, pandas y polars.

```python
from rutificador import Rut

rut = Rut("12.345.678-5")
print(rut.formatear(separador_miles=True))  # 12.345.678-5

resultado = Rut.parse("12.345.678-9")
print(resultado.estado, resultado.codigo_error)  # invalido DV_DISCORDANTE
```

## Tabla de Contenidos

- [Caracteristicas](#caracteristicas)
- [Instalacion](#instalacion)
- [Uso basico](#uso-basico)
  - [Validacion y parseo](#validacion-y-parseo)
  - [Formateo](#formateo)
  - [Digito verificador](#calculo-del-digito-verificador)
  - [Enmascaramiento](#enmascaramiento)
  - [Sugerencias y autocorreccion](#sugerencias-y-autocorreccion)
- [Linea de comandos](#linea-de-comandos)
- [Procesamiento por lotes](#procesamiento-por-lotes)
- [Integraciones](#integraciones)
  - [Pydantic v2](#pydantic-v2)
  - [FastAPI](#fastapi)
  - [pandas](#pandas)
  - [polars](#polars)
- [Validacion avanzada](#validacion-avanzada)
- [Referencia de errores](#referencia-de-errores)
- [Registro y depuracion](#registro-y-depuracion)
- [API de referencia](#api-de-referencia)
- [Desarrollo](#desarrollo)
- [Licencia](#licencia)

---

## Caracteristicas

- **Cero dependencias base** — solo estandar de Python. Instalacion liviana y segura.
- **Validacion completa** — formato, digito verificador, longitud configurable, modos de rigor.
- **Formateo flexible** — separador de miles, mayusculas en DV, separador personalizado.
- **Streaming y lotes** — archivos de millones de lineas sin cargar todo en memoria.
- **Procesamiento en paralelo** — motor por procesos (CPU-bound) o hilos (I/O-bound).
- **Parseo seguro** — `Rut.parse()` nunca lanza excepcion, siempre retorna resultado estructurado.
- **Enmascaramiento y tokenizacion** — protege datos sensibles en logs, exports o pantallas.
- **Motor de sugerencias** — correccion fuzzy de errores tipograficos comunes.
- **Integraciones opcionales** — Pydantic v2, FastAPI, pandas, polars.
- **Tipado estatico** — `py.typed` (PEP 561), cobertura mypy completa.
- **CLI profesional** — salida en text, JSON, JSONL, CSV y XML.

## Instalacion

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

## Uso basico

### Validacion y parseo

```python
from rutificador import Rut

# Creacion directa — valida en el constructor (lanza excepcion si es invalido)
rut = Rut("12.345.678-5")

# Parseo seguro — nunca lanza excepcion, siempre retorna resultado estructurado
resultado = Rut.parse("12.345.678-5")
print(resultado.estado)       # valido
print(resultado.normalizado)  # 12345678-5

resultado = Rut.parse("12.345.678-9")
print(resultado.estado)        # invalido
print(resultado.codigo_error)  # DV_DISCORDANTE

# Capturar error en validacion directa
from rutificador.exceptions import ErrorValidacionRut

try:
    Rut("12.345.678-9")
except ErrorValidacionRut as e:
    print(e.codigo_error)  # DV_DISCORDANTE
```

### Formateo

```python
rut = Rut("12345678-5")

print(rut.formatear())                             # 12345678-5
print(rut.formatear(separador_miles=True))         # 12.345.678-5
print(rut.formatear(mayusculas=True))              # 12345678-5
print(rut.formatear(separador_miles=True, mayusculas=True))  # 12.345.678-5

# Con DV en 'k'
rut_k = Rut("12345670-k")
print(rut_k.formatear(separador_miles=True, mayusculas=True))  # 12.345.670-K
```

### Calculo del digito verificador

```python
from rutificador import calcular_digito_verificador

dv = calcular_digito_verificador("12345678")
print(dv)  # 5
```

### Enmascaramiento

```python
from rutificador import Rut

# Ofuscar parcialmente
print(Rut.enmascarar("12.345.678-5", mantener=3, caracter="X"))  # XXXXX678-5
print(Rut.enmascarar("12.345.678-5", mantener=4))                 # ****5678-5

# Tokenizacion
print(Rut.enmascarar("12.345.678-5", modo="token", clave="mi-clave"))  # tok_abc123...
```

### Sugerencias y autocorreccion

```python
from rutificador import Rut

# Sugerir correcciones para un RUT con error tipografico
sugerencias = Rut.sugerir("12.345.687-5")
print(sugerencias)  # ['12345678-5', ...]

# Autocorreccion inteligente
mejor_opcion = Rut.mejorar("12a345678-k")
print(mejor_opcion)  # 12345678-5
```

---

## Linea de comandos

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

# Autocorreccion + sugerencias
rutificador validar sucia_db.txt --mejorar --sugerir

# Informacion del sistema
rutificador info
```

### Comandos

| Comando | Descripcion |
|---------|-------------|
| `validar` | Valida RUTs desde archivo o stdin |
| `formatear` | Valida y formatea RUTs con opciones de salida |
| `enmascarar` | Ofusca/tokeniza RUTs para proteger datos sensibles |
| `info` | Muestra version, entorno y funcionalidades |

### Formatos de salida

| Formato | Descripcion |
|---------|-------------|
| `text` | Legible por humanos con resumen de auditoria en stderr |
| `json` | Array JSON estandar (OOM-Safe via streaming) |
| `jsonl` | Una linea por registro — ideal para Big Data |
| `csv` | Hoja de calculo con cabecera |
| `xml` | Estructura incremental para integraciones legacy |

---

## Procesamiento por lotes

```python
from rutificador import ProcesadorLotesRut

ruts = ['12.345.678-5', '98.765.432-1', '1-9']
procesador = ProcesadorLotesRut()

resultado = procesador.validar_lista_ruts(ruts)
print(len(resultado.detalles_validos))    # 2
print(len(resultado.detalles_invalidos))  # 1

# Formatear a JSON, CSV o XML
csv = procesador.formatear_lista_ruts(ruts, formato="csv")
print(csv)
# rut
# 12345678-5
# ...

# Paralelismo explicito
procesador = ProcesadorLotesRut(motor_paralelo="process")
resultado = procesador.validar_lista_ruts(ruts, paralelo=True)
```

### Streaming (archivos grandes)

```python
from rutificador import validar_flujo_ruts, formatear_flujo_ruts

# Validar millones de RUTs sin cargar todo en memoria
ruts = (linea.strip() for linea in open("muy_grande.txt"))
for es_valido, resultado in validar_flujo_ruts(ruts):
    if es_valido:
        print(resultado.valor)
```

---

## Integraciones

### Pydantic v2

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

# Formato especifico
RutConPuntos = rut_str_annotated(formato="miles-con-guion")

class UsuarioV2(BaseModel):
    rut: RutConPuntos

u2 = UsuarioV2(rut="12.345.678-5")
print(u2.rut)  # 12.345.678-5
```

### FastAPI

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

Los errores de validacion retornan **422 Unprocessable Entity** con codigo estructurado (`DV_DISCORDANTE`, `CARACTERES_INVALIDOS`, etc.).

### pandas

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

### polars

```sh
pip install rutificador[polars]
```

```python
import polars as pl
import rutificador.polars  # activa el namespace .rut

df = pl.DataFrame({"rut": ["12.345.678-5", "12.345.678-9", "invalid"]})
print(df.with_columns(pl.col("rut").rut.es_valido()))
```

---

## Validacion avanzada

```python
from rutificador import Rut, ValidadorRut
from rutificador.config import RigorValidacion, ConfiguracionRut

# Modo flexible: tolera espacios, guiones extra, etc.
validador = ValidadorRut(modo=RigorValidacion.FLEXIBLE)
rut = Rut('12 345 678-5', validador=validador)

# Configuracion avanzada
config = ConfiguracionRut(max_digitos=10)
validador = ValidadorRut(configuracion=config)

# Normalizacion con rigor flexible
normalizado, errores, advertencias = Rut.normalizar(
    "12 345 678-5", modo=RigorValidacion.FLEXIBLE
)
print(normalizado)  # 12345678-5
```

---

## Referencia de errores

Todos los errores tienen codigos estables y severidad explicita:

```python
from rutificador import Rut

res = Rut.parse("12..345")
for err in res.errores:
    print(err.codigo, err.severidad, err.hint)
```

### Errores

| Codigo | Descripcion |
|--------|-------------|
| `ERROR_TIPO` | Tipo invalido |
| `RUT_VACIO` | Entrada vacia |
| `CARACTERES_INVALIDOS` | Caracteres no permitidos |
| `FORMATO_PUNTOS` | Separadores de miles invalidos |
| `FORMATO_GUION` | Guion invalido |
| `LONGITUD_MINIMA` | Longitud minima no alcanzada |
| `LONGITUD_MAXIMA` | Longitud maxima excedida |
| `DV_INVALIDO` | Digito verificador invalido |
| `DV_DISCORDANTE` | DV no coincide |
| `ESTADO_ENMASCARADO` | Enmascarado en estado no valido |
| `CLAVE_TOKEN_REQUERIDA` | Falta clave de tokenizacion |

### Advertencias

| Codigo | Descripcion |
|--------|-------------|
| `NORMALIZACION_ESPACIOS` | Espacios eliminados |
| `NORMALIZACION_GUION` | Guion normalizado |
| `NORMALIZACION_PUNTOS` | Puntos eliminados |
| `NORMALIZACION_DV` | DV en minuscula |
| `CEROS_IZQUIERDA` | Ceros a la izquierda eliminados |

---

## Registro y depuracion

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

---

## API de referencia

### Metadatos de validacion

```python
from rutificador import ProcesadorLotesRut

procesador = ProcesadorLotesRut()
resultado = procesador.validar_lista_ruts(["12.345.678-5"], paralelo=False)

detalle = resultado.detalles_validos[0]
print(detalle.valor)           # 12345678-5
print(detalle.validador_modo)  # estricto/flexible
print(detalle.duracion)        # segundos consumidos en la validacion

# Errores con codigo estructurado
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

### Formateador personalizado

```python
from rutificador.formatter import FormateadorRut, FabricaFormateadorRut

class FormateadorLista(FormateadorRut):
    def formatear(self, ruts):
        return ','.join(ruts)

FabricaFormateadorRut.registrar_formateador('lista', FormateadorLista)
```

---

## Desarrollo

### Entorno

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
mypy rutificador/                     # Tipado estatico
ruff check .                          # Lint
ruff format . --check                 # Formato
bandit -r rutificador/                # Seguridad
```

Las contribuciones son bienvenidas. Revisa [`CONTRIBUTING.md`](CONTRIBUTING.md) para las directrices completas.

### Alcance

Rutificador **no** verifica la existencia del RUT en registros oficiales ni realiza enriquecimiento de identidad. Su alcance es la validacion sintactica, normalizacion y formateo segun las reglas locales del RUT chileno.

---

## Licencia

MIT &copy; Carlos Ortega Gonzalez. Ver [LICENSE](LICENSE).

## Creditos

Este proyecto se inspiro en [rut-chile](https://github.com/gevalenz/rut-chile) de [gevalenz](https://github.com/gevalenz).
