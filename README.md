<!-- markdownlint-disable MD041 -->
[![PyPI version](https://img.shields.io/pypi/v/rutificador.svg)](https://pypi.org/project/rutificador/)
[![Python](https://img.shields.io/badge/Python-3.9--3.14-blue)](https://www.python.org/)
[![Licencia](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Estilo de código](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Integración continua](https://github.com/cortega26/rutificador/actions/workflows/ci.yml/badge.svg)](https://github.com/cortega26/rutificador/actions/workflows/ci.yml)
[![CodeQL](https://github.com/cortega26/rutificador/actions/workflows/codeql.yml/badge.svg)](https://github.com/cortega26/rutificador/actions/workflows/codeql.yml)
[![Estado de cobertura](https://coveralls.io/repos/github/cortega26/rutificador/badge.svg)](https://coveralls.io/github/cortega26/rutificador)

# Rutificador

Biblioteca en Python para validar, calcular y formatear RUTs (Rol Único Tributario) chilenos de forma eficiente.

## Tabla de Contenidos

- [Rutificador](#rutificador)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [Características](#caracteristicas)
  - [Alcance y limitaciones](#alcance-y-limitaciones)
  - [Instalación](#instalacion)
  - [Uso](#uso)
    - [Importar la clase Rut](#importar-la-clase-rut)
    - [Crear un objeto](#crear-un-objeto)
    - [Validar un RUT](#validar-un-rut)
    - [Calcular el Dígito Verificador de un RUT](#calcular-el-digito-verificador-de-un-rut)
    - [Formatear un RUT](#formatear-un-rut)
    - [Parseo incremental y normalización](#parseo-incremental-y-normalizacion)
    - [Motor de sugerencias (Fuzzy Matching)](#motor-de-sugerencias-fuzzy-matching)
    - [Pydantic v2](#pydantic-v2)
    - [Enmascarado y tokenización](#enmascarado-y-tokenizacion)
    - [Streaming con resultados estructurados](#streaming-con-resultados-estructurados)
    - [Validar y Formatear una lista de RUTs en diversos formatos](#validar-y-formatear-una-lista-de-ruts-en-diversos-formatos)
    - [Personalizar la validación](#personalizar-la-validacion)
    - [Procesamiento en lotes](#procesamiento-en-lotes)
    - [CLI con archivos grandes](#cli-con-archivos-grandes)
    - [Registro y depuración](#registro-y-depuracion)
    - [Información de versión](#informacion-de-version)
    - [Acceder a metadatos de validación](#acceder-a-metadatos-de-validacion)
    - [Política de errores](#politica-de-errores)
    - [Evaluar rendimiento](#evaluar-rendimiento)
    - [Registrar un formateador personalizado](#registrar-un-formateador-personalizado)
    - [Uso desde la línea de comandos](#uso-desde-la-linea-de-comandos)
  - [Desarrollo](#desarrollo)
    - [Configuración del Entorno](#configuracion-del-entorno)
    - [Ejecutar pruebas y linters](#ejecutar-pruebas-y-linters)
  - [Problemas o Requerimientos](#problemas-o-requerimientos)
  - [Contribuciones](#contribuciones)
  - [Licencia](#licencia)
  - [Créditos](#creditos)

## Características

- Validación de formato y cálculo de dígito verificador.
- Formateo configurable (separador de miles, mayúsculas, separador personalizado).
- Procesamiento por lotes con separación de válidos/ inválidos y salida en CSV, XML o JSON.
- Validación configurable por instancia: cada `Rut` reutiliza el `ValidadorRut` inyectado.
- Metadatos enriquecidos: cada validación genera un `RutProcesado` con duración y modo de rigurosidad.
- Paralelismo adaptable en la API (`motor_paralelo` por procesos o hilos); la CLI usa el backend predeterminado.
- Compatibilidad con Python >=3.9 y <4.0.

## Alcance y limitaciones

Rutificador **no** verifica la existencia del RUT en registros oficiales ni realiza
enriquecimiento de identidad. El alcance es validación, normalización y formateo
según reglas locales.

## Instalación

Puedes instalar la librería utilizando pip:

```sh
pip install rutificador
```

## Uso

### Importar la clase Rut

```python
from rutificador import Rut
```

### Crear un objeto

```python
rut1 = Rut('12345678-5')
rut2 = Rut('12.345.670')
```

### Validar un RUT

La validación del RUT se realiza automáticamente al crear un objeto `Rut`. La clase `Rut` acepta RUTs con y sin dígito verificador, así como RUTs con y sin separador de miles. Si el RUT ingresado no es válido, se lanzará una excepción `RutInvalidoError`.

### Calcular el Dígito Verificador de un RUT

```python
from rutificador import calcular_digito_verificador

digito_verificador = calcular_digito_verificador("12345678")
print(digito_verificador)  # Salida: 5
```

### Formatear un RUT

```python
# Formato predeterminado
print(rut1.formatear())  # Salida: 12345678-5

# Con separador de miles
print(rut1.formatear(separador_miles=True))  # Salida: 12.345.678-5

# Formato predeterminado (Rut con dígito verificador = 'k')
print(rut2.formatear())  # Salida: 12345670-k

# Con separador de miles y en mayúsculas
print(rut2.formatear(separador_miles=True, mayusculas=True))  # Salida: 12.345.670-K
```

### Parseo incremental y normalización

```python
from rutificador import Rut
from rutificador.config import RigorValidacion

resultado = Rut.parse("12.345.678-5")
print(resultado.estado)       # valido
print(resultado.normalizado)  # 12345678-5

normalizado, errores, advertencias = Rut.normalizar(
    "12 345 678-5", modo=RigorValidacion.FLEXIBLE
)
print(normalizado)  # 12345678-5
```

### Pydantic v2 (extra opcional; se instala explícitamente)

Instalación:

```bash
pip install rutificador[pydantic]
```

Uso con Pydantic v2:

```python
from pydantic import BaseModel
from rutificador.contrib.pydantic import RutStr, rut_str_annotated

# Para validación simple (formato base-dv por defecto)
class Modelo(BaseModel):
    rut: RutStr

# Para formatos específicos (ej: con puntos)
RutConPuntos = rut_str_annotated(formato="miles-con-guion")

class ModeloAvanzado(BaseModel):
    rut: RutConPuntos

m = Modelo(rut="12.345.678-5")
print(m.rut)  # 12345678-5
```

Advertencia:

> RutStr valida y normaliza identificadores. NO verifica identidad ni existencia.

Anti-ejemplos:

- No uses `RutStr` para autocorregir entradas de usuario de forma silenciosa.
- No trates la normalización como verificación de identidad.

### FastAPI (extra opcional)

Instalación:

```bash
pip install rutificador[fastapi]
```

Uso mediante Inyección de Dependencias:

```python
from fastapi import FastAPI, Depends
from rutificador import Rut
from rutificador.contrib.fastapi import parametro_rut

app = FastAPI()

@app.get("/usuario/{rut}")
def obtener_usuario(rut: Rut = Depends(parametro_rut)):
    # 'rut' ya es un objeto Rut validado y tipado
    return {"rut_normalizado": str(rut), "dv": rut.digito_verificador}
```

La dependencia `parametro_rut` (anteriormente `ParametroRut`) maneja automáticamente los errores de validación, devolviendo un error **422 Unprocessable Entity** con el detalle del error detectado (`DV_DISCORDANTE`, `CARACTERES_INVALIDOS`, etc.) compatible con el formato estándar de FastAPI/Pydantic.

### Enmascarado y tokenización

```python
from rutificador import Rut

print(Rut.enmascarar("12.345.678-5", mantener=3, caracter="X"))  # XXXXX678-5
print(Rut.enmascarar("12.345.678-5", modo="token", clave="<CLAVE>"))  # tok_...
```

### Motor de sugerencias (Fuzzy Matching)

Ideal para interfaces de usuario que necesitan corregir errores tipográficos comunes en tiempo real.

```python
from rutificador import Rut

# Sugerir correcciones para un RUT con transposición o DV erróneo
sugerencias = Rut.sugerir("12.345.687-5")
print(sugerencias)  # ['12345678-5', ...]

# Intentar mejorar/corregir automáticamente la entrada
mejor_opcion = Rut.mejorar("12a345678-k")
print(mejor_opcion)  # 12345678-5
```

### Streaming con resultados estructurados

```python
from rutificador import ProcesadorLotesRut

ruts = ["12.345.678-5", "12.345.678-1", "abc"]
for resultado in flujo(ruts):
    print(resultado.estado, resultado.normalizado)
```

### Validar y formatear una lista de RUTs en diversos formatos

Al igual que con los RUTs individuales, el uso de `formatear_lista_ruts` realiza la validación de forma automática cuando se trabaja con secuencias de RUTs. En lugar de lanzar una excepción `RutInvalidoError`, separará los RUTs válidos de los inválidos. Veamos algunos ejemplos:

```python
from rutificador import formatear_lista_ruts

# Sin formato
ruts = ["12345678-5", "12345670-k", "98765432-1"]
print(formatear_lista_ruts(ruts, separador_miles=True, mayusculas=True, formato=None))
# Salida:
# RUTs válidos:
# 12.345.678-5
# 12.345.670-K

RUTs inválidos:
98765432-1 - El dígito verificador '1' no coincide con el dígito verificador calculado '5'.

# En formato csv
ruts = ["12.345.678", "9876543", "1.234.567-4", "18005183"]
csv_ruts = formatear_lista_ruts(ruts, formato="csv")
print(csv_ruts)
# Salida
# RUTs válidos:
# rut
# 12345678-5
# 9876543-3
# 1234567-4
# 18005183-k

# En formato json
ruts = ["12.345.678", "9876543", "1.234.567-4", "18005183"]
json_ruts = formatear_lista_ruts(ruts, formato="json")
print(json_ruts)
# Salida
# RUTs válidos:
# [{"rut": "12345678-5"}, {"rut": "9876543-3"}, {"rut": "1234567-4"}, {"rut": "18005183-k"}]

# En formato xml
ruts = ["12.345.678", "9876543", "1.234.567-4", "18005183"]
xml_ruts = formatear_lista_ruts(ruts, formato="xml")
print(xml_ruts)
# Salida
# RUTs válidos:
# <root>
#     <rut>12345678-5</rut>
#     <rut>9876543-3</rut>
#     <rut>1234567-4</rut>
#     <rut>18005183-k</rut>
# </root>
```

### Personalizar la validación

```python
from rutificador import Rut, ValidadorRut, RigorValidacion

validador = ValidadorRut(modo=RigorValidacion.FLEXIBLE)
rut = Rut('12.345.678-5', validador=validador)
print(rut)
```

### Procesamiento en lotes

```python
from rutificador import ProcesadorLotesRut

ruts = ['12.345.678-5', '98.765.432-1', '1-9']
procesador = ProcesadorLotesRut(motor_paralelo="process")
resultado = procesador.formatear_lista_ruts(ruts, formato='json')
print(resultado)
```

Todas las operaciones en lote reutilizan las instancias de `Rut` generadas durante la validación, evitando recalcular cada entrada al momento de formatear o transmitir resultados por flujo. Esto mantiene la coherencia con los validadores personalizados y mejora el rendimiento en conjuntos grandes. Para cargas masivas puedes alternar entre `motor_paralelo="thread"` (compatible con I/O intensivo) o `motor_paralelo="process"` (ideal para CPU-bound).

### CLI con archivos grandes

```bash
# Procesa un archivo gigantesco mediante streaming
$ rutificador validar datos/ruts_masivos.txt > ruts_validos.txt
```

La herramienta lee línea a línea y usa el motor por defecto; si necesitas seleccionar explícitamente hilos o procesos, hazlo mediante la API (`motor_paralelo`) y combina el resultado con tus scripts para generar informes especializados.

### Registro y depuración

```python
import logging
from rutificador import configurar_registro

configurar_registro(level=logging.DEBUG)
```

`configurar_registro` prepara un logger dedicado (`rutificador`) sin alterar la configuración global del proyecto que lo consume. Si ya cuentas con tu propio esquema de logging puedes pasar cualquier `logging.Handler` personalizado (JSON, Syslog, etc.) mediante el parámetro `handler`, y la función se encargará de integrarlo sin tocar los handlers existentes de tu aplicación:

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

### Información de versión

La versión del paquete se define en `rutificador/version.py` y puede consultarse directamente:

```python
from rutificador import __version__

print(__version__)
```

También puedes obtener metadatos adicionales:

```python
from rutificador import obtener_informacion_version

info = obtener_informacion_version()
print(info['version'])
```

### Acceder a metadatos de validación

```python
from rutificador import ProcesadorLotesRut

procesador = ProcesadorLotesRut()
resultado = procesador.validar_lista_ruts(["12.345.678-5"], paralelo=False)

detalle = resultado.detalles_validos[0]
print(detalle.valor)           # 12345678-5
print(detalle.validador_modo)  # estricto/flexible
print(detalle.duracion)        # segundos consumidos en la validación

# Errores con código y mensaje
resultado_error = procesador.validar_lista_ruts(["12345678-9"])
if resultado_error.ruts_invalidos:
    problema = resultado_error.ruts_invalidos[0]
    print(problema.rut, problema.codigo, problema.mensaje)
```

Los objetos `RutProcesado` permiten instrumentar dashboards o auditorías sin volver a recorrer el lote original.

### Política de errores

Los errores y advertencias tienen códigos estables y severidad explícita:

```python
from rutificador import Rut

res = Rut.parse("12..345")
for err in res.errores:
    print(err.codigo, err.severidad, err.hint)
```

Resumen de códigos (v1.x):

| Código | Severidad | Descripción |
| --- | --- | --- |
| ERROR_TIPO | error | Tipo inválido |
| RUT_VACIO | error | Entrada vacía |
| CARACTERES_INVALIDOS | error | Caracteres no permitidos |
| FORMATO_PUNTOS | error | Separadores de miles inválidos |
| FORMATO_GUION | error | Guion inválido |
| LONGITUD_MINIMA | error | Longitud mínima no alcanzada |
| LONGITUD_MAXIMA | error | Longitud máxima excedida |
| DV_INVALIDO | error | DV inválido |
| DV_DISCORDANTE | error | DV no coincide |
| ESTADO_ENMASCARADO | error | Enmascarado en estado no válido |
| CLAVE_TOKEN_REQUERIDA | error | Falta clave de tokenización |
| NORMALIZACION_ESPACIOS | warning | Espacios eliminados |
| NORMALIZACION_GUION | warning | Guion normalizado |
| NORMALIZACION_PUNTOS | warning | Puntos eliminados |
| NORMALIZACION_DV | warning | DV en minúscula |
| CEROS_IZQUIERDA | warning | Ceros a la izquierda eliminados |

### Evaluar rendimiento

```python
from rutificador import evaluar_rendimiento

resultados = evaluar_rendimiento(num_ruts=1000)
print(resultados['tasa_exito'])
```

### Registrar un formateador personalizado

```python
from rutificador import FormateadorRut, FabricaFormateadorRut

class FormateadorLista(FormateadorRut):
    def formatear(self, ruts):
        return ','.join(ruts)

FabricaFormateadorRut.registrar_formateador('lista', FormateadorLista)
```

### Uso desde la línea de comandos

El paquete incluye la herramienta `rutificador` optimizada para el procesamiento de archivos a gran escala y auditoría de datos.

#### Comandos Principales

- `rutificador validar [archivo]`: Valida RUTs (desde archivo o `stdin`).
- `rutificador formatear [archivo]`: Valida y formatea RUTs.
- `rutificador enmascarar [archivo]`: Protege datos sensibles mediante enmascaramiento.

#### Características Avanzadas (v1.4.0)

```bash
# Procesamiento paralelo en todos los núcleos para máxima velocidad
rutificador validar ruts_pesados.txt --paralelo --format jsonl > resultados.jsonl

# Auto-corrección inteligente: limpia y valida en un solo paso
rutificador validar sucia_db.txt --mejorar --format csv > limpia_db.csv

# Auditoría con salida estructurada y resumen en STDERR
rutificador formatear datos.txt --format json --separador-miles
```

#### Formatos de Salida

- `text`: Humano-legible con resumen de auditoría detallado.
- `json`: Array JSON estándar (OOM-Safe mediante streaming).
- `jsonl`: Una línea por registro (ideal para Big Data).
- `csv`: Formato de hoja de cálculo con cabecera.
- `xml`: Estructura incremental compatible con integraciones legacy.

#### Reporte de Auditoría

Todas las operaciones masivas generan un bloque de metadatos (en el footer o STDERR) con la versión del sistema, tasa de éxito y tiempo exacto de ejecución, facilitando el cumplimiento de normativas de trazabilidad.

## Desarrollo

### Configuración del Entorno

1. Clonar el repositorio:
   git clone [https://github.com/cortega26/rutificador.git](https://github.com/cortega26/rutificador.git)
   cd rutificador

2. Crear un entorno virtual:
   python -m venv venv
   source venv/bin/activate  # En Windows use venv\Scripts\activate

3. Actualizar pip a una versión segura y luego instalar las dependencias de desarrollo:
   python -m pip install --upgrade "pip>=25.2"
   pip install -r requirements-dev.txt

4. Instalar los ganchos de pre-commit:
   pre-commit install

### Ejecutar pruebas y linters

Antes de enviar tus cambios, verifica la calidad del código con:

pre-commit run --files `<archivos>`
pytest

### Notas de validación y seguridad

- La suite incluye pruebas que aseguran el soporte de configuraciones
  personalizadas de `ConfiguracionRut`, incluyendo bases de hasta 9 dígitos,
  tanto para entradas con como sin dígito verificador. Esto evita regresiones
  en escenarios donde se amplía `max_digitos` para integraciones externas.
- Para detalles del flujo de escaneo y de la gestión temporal del aviso
  GHSA-4xh5-x5gv-qwph, consulta `SECURITY_SCANNING_NOTES.md`.

## Problemas o Requerimientos

¿Te gustaría reportar algún error, solicitar alguna modificación o característica adicional en esta librería? Solo debes abrir un `issue` y describir tu petición de la forma más precisa y clara posible.

## Contribuciones

Las contribuciones son bienvenidas. Antes de comenzar, revisa las directrices en [AGENTS.md](AGENTS.md). Haz un fork del repositorio, crea una rama nueva, documenta tus cambios y finalmente haz push para abrir un pull request hacia la rama principal.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

## Créditos

Este paquete fue creado por Carlos Ortega y se inspiró en el proyecto [rut-chile](https://github.com/gevalenz/rut-chile) de [gevalenz](https://github.com/gevalenz), que es un módulo Python que proporciona funcionalidades comunes relacionadas con el RUT chileno.
