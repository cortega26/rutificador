<!-- markdownlint-disable MD041 -->
[![PyPI version](https://img.shields.io/pypi/v/rutificador.svg)](https://pypi.org/project/rutificador/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Continuous Integration](https://github.com/cortega26/rutificador/actions/workflows/ci.yml/badge.svg)](https://github.com/cortega26/rutificador/actions/workflows/ci.yml)
[![CodeQL](https://github.com/cortega26/rutificador/actions/workflows/codeql.yml/badge.svg)](https://github.com/cortega26/rutificador/actions/workflows/codeql.yml)
[![Coverage Status](https://coveralls.io/repos/github/cortega26/rutificador/badge.svg)](https://coveralls.io/github/cortega26/rutificador)

# Rutificador

Biblioteca en Python para validar, calcular y formatear RUTs (Rol Único Tributario) chilenos de forma eficiente.

## Tabla de Contenidos

- [Rutificador](#rutificador)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [Características](#características)
  - [Instalación](#instalación)
  - [Uso](#uso)
    - [Importar la clase Rut](#importar-la-clase-rut)
    - [Crear Un Objeto](#crear-un-objeto)
    - [Validar un RUT](#validar-un-rut)
    - [Calcular el Dígito Verificador de un RUT](#calcular-el-dígito-verificador-de-un-rut)
    - [Formatear un RUT](#formatear-un-rut)
    - [Validar y Formatear una lista de RUTs en diversos formatos](#validar-y-formatear-una-lista-de-ruts-en-diversos-formatos)
  - [Desarrollo](#desarrollo)
    - [Configuración del Entorno](#configuración-del-entorno)
    - [Ejecutar Pruebas](#ejecutar-pruebas)
  - [Problemas o Requerimientos](#problemas-o-requerimientos)
  - [Contribuciones](#contribuciones)
  - [Licencia](#licencia)
  - [Créditos](#créditos)

## Características

- Validación del formato del RUT.
- Cálculo del dígito verificador del RUT.
- Formateo del RUT con diferentes opciones (separador de miles, mayúsculas, formato de salida).
- Validación y formateo de listas de RUTs.
- Manejo de excepciones personalizadas.
- **Procesamiento de lotes de RUTs:** Permite procesar lotes de RUTs en lugar de hacerlo individualmente, lo que agiliza el trabajo con grandes cantidades de datos.
- **Separación de resultados:** Los resultados de los lotes se entregan por separado, mostrando RUTs válidos e inválidos, y pueden exportarse en varios formatos, incluidos CSV, XML y JSON.
- Compatibilidad con Python 3.9 o superior.

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
processor = ProcesadorLotesRut()
resultado = processor.formatear_lista_ruts(ruts, formato='json')
print(resultado)
```

### Registro y depuración

```python
import logging
from rutificador import configurar_registro

configurar_registro(level=logging.DEBUG)
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

El paquete incluye un comando de consola llamado `rutificador` con dos subcomandos:

- `rutificador validar [archivo]`: valida RUTs recibidos por `stdin` o desde un archivo.
- `rutificador formatear [archivo]`: valida y formatea los RUTs; acepta las opciones `--separador-miles` y `--mayusculas`.

Ejemplos:

```bash
$ echo "12345678-5" | rutificador validar
12345678-5

$ echo "12345678-5" | rutificador formatear --separador-miles
12.345.678-5
```

## Desarrollo

### Configuración del Entorno

1. Clonar el repositorio:
   git clone [https://github.com/cortega26/rutificador.git](https://github.com/cortega26/rutificador.git)
   cd rutificador

2. Crear un entorno virtual:
   python -m venv venv
   source venv/bin/activate  # En Windows use venv\Scripts\activate

3. Instalar las dependencias de desarrollo:
   pip install -r requirements-dev.txt

4. Instalar los ganchos de pre-commit:
   pre-commit install

### Ejecutar pruebas y linters

Antes de enviar tus cambios, verifica la calidad del código con:

pre-commit run --files <archivos>
pytest

## Problemas o Requerimientos

¿Te gustaría reportar algún error, solicitar alguna modificación o característica adicional en esta librería? Solo debes abrir un `issue` y describir tu petición de la forma más precisa y clara posible.

## Contribuciones

Las contribuciones son bienvenidas. Antes de comenzar, revisa las directrices en [AGENTS.md](AGENTS.md). Haz un fork del repositorio, crea una rama nueva, documenta tus cambios y finalmente haz push para abrir un pull request hacia la rama principal.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

## Créditos

Este paquete fue creado por Carlos Ortega y se inspiró en el proyecto [rut-chile](https://github.com/gevalenz/rut-chile) de [gevalenz](https://github.com/gevalenz), que es un módulo Python que proporciona funcionalidades comunes relacionadas con el RUT chileno.
