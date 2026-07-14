# Uso Básico

## Validación y parseo

```python
from rutificador import Rut

# Creación directa — valida en el constructor (lanza excepción si es inválido)
rut = Rut("12.345.678-5")

# Parseo seguro — nunca lanza excepción
resultado = Rut.parse("12.345.678-5")
print(resultado.estado)       # valido
print(resultado.normalizado)  # 12345678-5

resultado = Rut.parse("12.345.678-9")
print(resultado.estado)        # invalido
print(resultado.codigo_error)  # DV_DISCORDANTE
```

## Formateo

```python
rut = Rut("12345678-5")

print(rut.formatear())                             # 12345678-5
print(rut.formatear(separador_miles=True))         # 12.345.678-5
print(rut.formatear(mayusculas=True))              # 12345678-5
```

## Cálculo del dígito verificador

```python
from rutificador import calcular_digito_verificador

dv = calcular_digito_verificador("12345678")
print(dv)  # 5
```

## Enmascaramiento

```python
from rutificador import Rut

print(Rut.enmascarar("12.345.678-5", mantener=3, caracter="X"))  # XXXXX678-5
print(Rut.enmascarar("12.345.678-5", mantener=4))                 # ****5678-5

# Tokenización
print(Rut.enmascarar("12.345.678-5", modo="token", clave="mi-clave"))
```

## Sugerencias y autocorrección

```python
from rutificador import Rut

sugerencias = Rut.sugerir("12.345.687-5")
print(sugerencias)  # ['12345678-5', ...]

mejor_opcion = Rut.mejorar("12a345678-k")
print(mejor_opcion)  # 12345678-5
```
