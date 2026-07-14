# Procesamiento por Lotes

## Lotes en memoria

```python
from rutificador import ProcesadorLotesRut

ruts = ['12.345.678-5', '98.765.432-1', '1-9']
procesador = ProcesadorLotesRut()

resultado = procesador.validar_lista_ruts(ruts)
print(len(resultado.detalles_validos))    # 2
print(len(resultado.detalles_invalidos))  # 1

csv = procesador.formatear_lista_ruts(ruts, formato="csv")
```

## Paralelismo

```python
procesador = ProcesadorLotesRut(motor_paralelo="process")
resultado = procesador.validar_lista_ruts(ruts, paralelo=True)
```

## Streaming (archivos grandes)

```python
from rutificador import validar_flujo_ruts

ruts = (linea.strip() for linea in open("muy_grande.txt"))
for es_valido, resultado in validar_flujo_ruts(ruts):
    if es_valido:
        print(resultado.valor)
```
