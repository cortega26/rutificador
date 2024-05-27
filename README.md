[![PyPI version](https://img.shields.io/pypi/v/rutificador.svg)](https://pypi.org/project/rutificador/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Continuous Integration](https://github.com/cortega26/rutificador/actions/workflows/ci.yml/badge.svg)](https://github.com/cortega26/rutificador/actions/workflows/ci.yml)
[![CodeQL](https://github.com/cortega26/rutificador/actions/workflows/codeql.yml/badge.svg)](https://github.com/cortega26/rutificador/actions/workflows/codeql.yml)
[![Coverage Status](https://coveralls.io/repos/github/cortega26/rutificador/badge.svg)](https://coveralls.io/github/cortega26/rutificador)

# Rutificador

Una biblioteca Python para validar y formatear RUTs (Rol Único Tributario) chilenos.

## Características

- Validación del formato del RUT.
- Cálculo del dígito verificador del RUT.
- Formateo del RUT con diferentes opciones (separador de miles, mayúsculas, formato de salida).
- Validación y formateo de listas de RUTs.
- Manejo de excepciones personalizadas.
- **Procesamiento de lotes de RUTs:** Permite procesar lotes de RUTs en lugar de hacerlo individualmente, lo que agiliza el trabajo con grandes cantidades de datos.
- **Separación de resultados:** Los resultados de los lotes se entregan por separado, mostrando RUTs válidos e inválidos, y pueden exportarse en varios formatos, incluidos CSV, XML y JSON.

## Instalación

Puedes instalar la librería utilizando pip:

```python
pip install rutificador
```

## Uso

### Importar la clase Rut

```python
from rutificador import Rut
```

### Crear Un Objeto

```python
rut1 = Rut('12345678-5')
rut2 = Rut('12.345.670')
```

### Validar un RUT

La validación del RUT se realiza automáticamente al crear un objeto `Rut`. La clase 'Rut' acepta RUTs con y sin dígito verificador así como RUTs con y sin separador de miles. Si el RUT ingresado no es válido, se lanzará una excepción `RutInvalidoError`.

### Calcular el Dígito Verificador de un RUT

```python
from rutificador import RutDigitoVerificador

digito_verificador = RutDigitoVerificador('12345678').digito_verificador
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

### Validar y Formatear una lista de RUTs en diversos formatos

Al igual que con los RUTs individuales, al utilizar el método `formatear_lista_ruts` la validación se hace de forma automática cuando se trata de listas de RUTs, la diferencia es que en vez de mostrar una excepción `RutInvalidoError` separará los RUTs válidos de los inválidos. Veamos algunos ejemplos:

```python
# Sin formato
ruts = ['12345678-5', '12345670-k', '98765432-1']
print(Rut.formatear_lista_ruts(ruts, separador_miles=True, mayusculas=True, formato=None))
# Salida:
# RUTs válidos:
# 12.345.678-5
# 12.345.670-K

RUTs inválidos:
98765432-1 - El dígito verificador '1' no coincide con el dígito verificador calculado '5'.

# En formato csv
ruts = ['12.345.678', '9876543', '1.234.567-4', '18005183']
csv_ruts = Rut.formatear_lista_ruts(ruts, formato='csv')
print(csv_ruts)
# Salida
# RUTs válidos:
# rut
# 12345678-5
# 9876543-3
# 1234567-4
# 18005183-k

# En formato json
ruts = ['12.345.678', '9876543', '1.234.567-4', '18005183']
json_ruts = Rut.formatear_lista_ruts(ruts, formato='json')
print(json_ruts)
# Salida
# RUTs válidos:
# [{"rut": "12345678-5"}, {"rut": "9876543-3"}, {"rut": "1234567-4"}, {"rut": "18005183-k"}]

# En formato xml
ruts = ['12.345.678', '9876543', '1.234.567-4', '18005183']
xml_ruts = Rut.formatear_lista_ruts(ruts, formato='xml')
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

## Problemas o Requerimientos

¿Te gustaría reportar algún error, solicitar alguna modificación o característica adicional en esta librería? Solo debes abrir un 'issue' y describir tu petición de la forma más precisa y clara posible.

## Contribuciones

Las contribuciones son bienvenidas. Solo debes hacer un fork del repositorio, crear una rama nueva, hacer los cambios que consideres pertinentes con su respectiva documentación, y finalmente hacer push y abrir un pull request para migrar los cambios al 'master'.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT.

## Créditos

Este paquete fue creado por Carlos Ortega y se inspiró en el proyecto [rut-chile](https://github.com/gevalenz/rut-chile) de [gevalenz](https://github.com/gevalenz), que es un módulo Python que proporciona funcionalidades comunes relacionadas con el RUT chileno.
