# Línea de comandos

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

# Gate de calidad en CI (falla solo si más del 1 % es inválido)
rutificador validar ruts.txt --max-tasa-error 0.01 --quiet || echo "gate fallido"
```

## Comandos

| Comando | Descripción |
|---------|-------------|
| `validar` | Valida RUTs desde archivo o stdin |
| `formatear` | Valida y formatea RUTs con opciones de salida |
| `enmascarar` | Ofusca/tokeniza RUTs para proteger datos sensibles |
| `info` | Muestra versión, entorno y funcionalidades |

## Formatos de salida

| Formato | Descripción |
|---------|-------------|
| `text` | Legible por humanos con resumen de auditoría en stderr |
| `json` | Array JSON estándar |
| `jsonl` | Una línea por registro — ideal para Big Data |
| `csv` | Hoja de cálculo con cabecera |
| `xml` | Estructura para integraciones legacy |

## Gate de calidad (`validar --max-tasa-error`)

El flag `--max-tasa-error <0.0-1.0>` define la tasa máxima tolerada de
RUTs inválidos. Si la tasa de error supera el umbral, `validar` retorna
`2` e informa `Tasa de error X% supera el máximo tolerado Y% (n/m)` por
stderr. El resumen de auditoría incluye siempre `tasa_error`.

| Exit code | Significado |
|-----------|-------------|
| `0` | Todo válido, o tasa de error dentro del umbral (`--max-tasa-error`) |
| `1` | Hay RUTs inválidos (sin flag `--max-tasa-error`) |
| `2` | Tasa de error supera el umbral, o uso inválido (incluye errores de argparse) |

```bash
# Falla solo si más del 1 % de las filas es inválido
rutificador validar ruts.txt --max-tasa-error 0.01 --quiet || echo "gate fallido"
```
