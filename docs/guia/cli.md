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
