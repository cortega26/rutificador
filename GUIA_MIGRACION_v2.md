# Guia de Migracion de rutificador v1.x a v2.0

> **Version**: 2.0.0 | **Fecha**: 2026-07-14

## Por que v2.0

v2.0 elimina 12 simbolos obsoletos que han estado emitiendo `DeprecationWarning`
desde v1.4.4–v1.6.0. La biblioteca adopta nombres en espanol consistentes
para todas las clases y funciones publicas, sin aliases en ingles.

## Que cambia

### Simbolos eliminados

| Simbolo obsoleto (v1.x) | Reemplazo (v2.0) | Deprecado desde |
|---|---|---|
| `RutConfig` | `ConfiguracionRut` | v1.5.0 |
| `RutValidator` | `ValidadorRut` | v1.5.0 |
| `Validador` (Protocol) | `ValidadorRut` | v1.5.0 |
| `RutInvalidoError` | `ErrorValidacionRut` | v1.5.0 |
| `RutError` | `ErrorRut` | v1.5.0 |
| `RutValidationError` | `ErrorValidacionRut` | v1.5.0 |
| `RutFormatError` | `ErrorFormatoRut` | v1.5.0 |
| `RutDigitError` | `ErrorDigitoRut` | v1.5.0 |
| `RutLengthError` | `ErrorLongitudRut` | v1.5.0 |
| `RutProcessingError` | `ErrorProcesamientoRut` | v1.5.0 |
| `ConsultaRut` | `consulta_rut` | v1.4.4 |
| `ParametroRut` | `parametro_rut` | v1.4.4 |

### `RigorValidacion` simplificado

`RigorValidacion.LEGADO` fue eliminado. Solo existen dos modos:

- `RigorValidacion.ESTRICTO` — rechaza variantes de formato no canonicas
- `RigorValidacion.FLEXIBLE` — normaliza variantes y emite advertencias

Si usabas `RigorValidacion.LEGADO`, reemplazalo por `RigorValidacion.FLEXIBLE`.

### `__init__.py` sin `__getattr__`

Los imports de simbolos obsoletos ya no funcionan. `from rutificador import RutConfig`
lanza `ImportError` en v2.0 en lugar de emitir `DeprecationWarning`.

## Como migrar

### Opcion 1: Script automatico (recomendado)

```bash
# Escanear tu proyecto (sin modificar)
python scripts/migrate.py --check mi_proyecto/

# Aplicar cambios automaticamente
python scripts/migrate.py --fix mi_proyecto/

# Ver que cambiaria sin modificar
python scripts/migrate.py --fix --dry-run mi_proyecto/
```

### Opcion 2: Busqueda manual

```bash
# Encontrar usos de simbolos obsoletos
grep -rn "RutConfig\|RutValidator\|RutInvalidoError\|RutError\b\|RutValidationError\|RutFormatError\|RutDigitError\|RutLengthError\|RutProcessingError\|ConsultaRut\|ParametroRut" mi_proyecto/

# Reemplazar manualmente segun la tabla de arriba
```

### Opcion 3: Detectar con DeprecationWarning (v1.9.x)

Si aun estas en v1.9.x, podes detectar todos los usos obsoletos con:

```bash
python -W error::DeprecationWarning -m pytest mi_proyecto/
```

Esto convertira los `DeprecationWarning` en errores, revelando exactamente
que lineas necesitan actualizarse.

## Verificacion post-migracion

```bash
# Asegurate de que no quedan referencias
grep -rn "RutConfig\|RutValidator\|RutInvalidoError" mi_proyecto/
# Debe retornar 0 resultados

# Ejecuta tus tests
python -m pytest mi_proyecto/
```

## Cambios en imports

### Antes (v1.x)

```python
from rutificador import Rut, RutConfig, RutValidator
from rutificador.exceptions import RutInvalidoError, RutError

try:
    rut = Rut("12345678-5")
except RutInvalidoError:
    ...
```

### Despues (v2.0)

```python
from rutificador import Rut, ConfiguracionRut, ValidadorRut
from rutificador.exceptions import ErrorValidacionRut, ErrorRut

try:
    rut = Rut("12345678-5")
except ErrorValidacionRut:
    ...
```

## FAQ

### Mi codigo deja de funcionar si no migro?

Si. v2.0 elimina los simbolos obsoletos. `from rutificador import RutConfig`
lanza `ImportError`.

### Puedo seguir usando v1.9.x?

Si, pero no recibira nuevas funcionalidades ni parches de seguridad despues del
release de v2.0.

### Cuanto tiempo tengo para migrar?

La guia de migracion se publica con al menos 6 meses de anticipacion al release
de v2.0 en PyPI.

### El script de migracion modifica mis archivos de forma segura?

El script usa `ast.parse` y `ast.unparse` del modulo ast de Python para
reescribir solo los imports afectados. El resto del codigo queda intacto.
Siempre ejecuta `--dry-run` primero y respalda tu codigo antes de ejecutar
`--fix`.
