from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from rutificador.contrib.fastapi import ParametroRut
from rutificador.rut import Rut

app = FastAPI()


@app.get("/validar")
def validar_rut(rut: Rut = Depends(ParametroRut)):
    return {
        "valido": True,
        "formateado": rut.formatear(separador_miles=True),
        "base": str(rut.base),
        "dv": rut.digito_verificador,
    }


client = TestClient(app)


def test_fastapi_dependency_valida():
    response = client.get("/validar", params={"rut": "12.345.678-5"})
    assert response.status_code == 200
    assert response.json()["formateado"] == "12.345.678-5"
    assert response.json()["base"] == "12345678"


def test_fastapi_dependency_invalida():
    response = client.get("/validar", params={"rut": "12.345.678-k"})
    assert response.status_code == 422
    # El detalle debe seguir el formato estándar de FastAPI
    detail = response.json()["detail"]
    assert detail[0]["type"] == "DV_DISCORDANTE"
    assert "loc" in detail[0]


def test_fastapi_dependency_normalizacion():
    # 12345678 -> 12345678-5
    response = client.get("/validar", params={"rut": "12345678"})
    assert response.status_code == 200
    assert response.json()["formateado"] == "12.345.678-5"
