# Integraciones

## Pydantic v2

```sh
pip install rutificador[pydantic]
```

```python
from pydantic import BaseModel
from rutificador.contrib.pydantic import RutStr

class Usuario(BaseModel):
    rut: RutStr

u = Usuario(rut="12.345.678-5")
print(u.rut)  # 12345678-5
```

## FastAPI

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

## pandas

```sh
pip install rutificador[pandas]
```

```python
import pandas as pd
import rutificador.pandas

s = pd.Series(["12.345.678-5", "12.345.678-9", "invalid"])
print(s.rut.es_valido())
print(s.rut.formatear(formato="miles"))
```

## polars

```sh
pip install rutificador[polars]
```

```python
import polars as pl
import rutificador.polars

df = pl.DataFrame({"rut": ["12.345.678-5", "12.345.678-9", "invalid"]})
print(df.with_columns(pl.col("rut").rut.es_valido()))
```
