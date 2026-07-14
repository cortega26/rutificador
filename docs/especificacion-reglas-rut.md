# Especificación formal de validación de RUT chileno

> **Versión**: 1.0 — 2026-07-14  
> **Alcance**: validación sintáctica, formato, normalización y cálculo de dígito verificador  
> **Fuera de alcance**: verificación de existencia en registros oficiales (SRI)

---

## 1. Definición de RUT

Un Rol Único Tributario (RUT) chileno se compone de:

1. **Base numérica**: una secuencia de **1 a 9 dígitos** (`[0-9]`).
2. **Separador**: un guion (`-`).
3. **Dígito verificador (DV)**: exactamente 1 carácter, `[0-9kK]`.

Forma canónica: `<base>-<dv>` (ej: `12345678-5`).

El DV se calcula mediante el algoritmo de **módulo 11** descrito en §2.

---

## 2. Algoritmo de dígito verificador

### 2.1 Configuración

| Parámetro | Valor |
|-----------|-------|
| Factores de verificación | `(2, 3, 4, 5, 6, 7)` |
| Módulo | `11` |
| Aplicación | De derecha a izquierda, cíclica |

Implementado en `rutificador/config.py:14-16` y `rutificador/utils.py:159-164`.

### 2.2 Procedimiento

1. Invertir la base numérica.
2. Para cada dígito `dᵢ`, multiplicar por el factor correspondiente `fᵢ` (cíclico desde 2).
3. Sumar todos los productos: `S = Σ(dᵢ × fᵢ)`.
4. Calcular `M = S mod 11`.
5. El DV preliminar es `11 - M`.
6. Si el resultado es `11`, el DV es `0`.
7. Si el resultado es `10`, el DV es `K`.
8. En cualquier otro caso, el DV es el propio dígito (0-9).

### 2.3 Fórmula

```
dv_preliminar = 11 - (suma % 11)
dv = 0  si dv_preliminar == 11
dv = K  si dv_preliminar == 10
dv = dv_preliminar  en otro caso
```

### 2.4 Ejemplos

| Base | Cálculo | DV |
|------|---------|----|
| `12345678` | 8×2 + 7×3 + 6×4 + 5×5 + 4×6 + 3×7 + 2×2 + 1×3 = 16+21+24+25+24+21+4+3 = 138; 138 mod 11 = 6; 11−6 = **5** | `5` |
| `12345670` | 0×2 + 7×3 + 6×4 + 5×5 + 4×6 + 3×7 + 2×2 + 1×3 = 0+21+24+25+24+21+4+3 = 122; 122 mod 11 = 1; 11−1 = **10** | `k` |
| `1` | 1×2 = 2; 2 mod 11 = 2; 11−2 = **9** | `9` |

Referencia: test vectors canónicos en `tests/vectors/test_vectors_dv.json`.

---

## 3. Reglas de formato

### 3.1 Caracteres permitidos

- Dígitos: `[0-9]`
- Punto: `.` (solo como separador de miles en grupos de 3)
- Guion: `-` (exactamente uno, antes del DV)
- `k` o `K` (solo como dígito verificador)

Cualquier otro carácter produce el error `CARACTERES_INVALIDOS`.

### 3.2 Separadores de miles

Los puntos como separadores de miles deben formar **grupos exactos de 3 dígitos** (excepto el primer grupo a la izquierda, que puede tener 1-3 dígitos).

| Entrada | Válido | Motivo |
|---------|--------|--------|
| `12.345.678-5` | Sí | Grupos 3-3-2 desde la izquierda |
| `1.234.567-8` | Sí | Grupos 1-3-3 |
| `12.34.567-8` | No | Grupo central de 2 dígitos (`FORMATO_PUNTOS`) |
| `12345678-5` | Sí | Sin separadores |

Regex de validación: `^\d{1,3}(?:\.\d{3})*$` (`rutificador/utils.py:25`).

### 3.3 Guion

Exactamente un guion (`-`). Guiones alternativos (`_`, `–`, `—`, `−`) se normalizan en modo FLEXIBLE pero producen advertencia `NORMALIZACION_GUION`.

Dos o más guiones producen el error `FORMATO_GUION`.

### 3.4 Dígito verificador

Exactamente 1 carácter después del guion: `[0-9kK]`. En mayúscula o minúscula; la validación es case-insensitive.

---

## 4. Reglas de normalización

`Rut.normalizar()` (`rutificador/rut.py:232-288`) aplica 9 pasos secuenciales:

| # | Paso | Descripción | Error si falla |
|---|------|-------------|----------------|
| 1 | Validar tipo | `str` o `int` | `ERROR_TIPO` |
| 2 | Verificar espacios | Solo permitidos en FLEXIBLE | `CARACTERES_INVALIDOS` (ESTRICTO) / `NORMALIZACION_ESPACIOS` (FLEXIBLE) |
| 3 | Verificar guiones alternativos | `_`, `–`, `—`, `−` → `-` | `NORMALIZACION_GUION` (advertencia) |
| 4 | Validar caracteres base | Solo `[0-9kK.-]`; al menos un dígito; máx. 1 guion | `RUT_VACIO`, `CARACTERES_INVALIDOS`, `FORMATO_GUION` |
| 5 | Separar base y DV | División por el guion | `FORMATO_GUION` |
| 6 | Normalizar puntos | Grupos de 3 dígitos → eliminar puntos | `FORMATO_PUNTOS` |
| 7 | Normalizar ceros | `lstrip("0")`; si queda vacío → `"0"` | `CEROS_IZQUIERDA` (advertencia) |
| 8 | Normalizar DV | `[0-9kK]` → lowercase | `DV_INVALIDO` |
| 9 | Reconstruir | `f"{base}-{dv}"` o `f"{base}-"` si falta DV | — |

---

## 5. Modos de rigor

Definidos en `rutificador/config.py:41-61` (`RigorValidacion`):

### 5.1 `ESTRICTO` (default)

- Rechaza espacios internos → `CARACTERES_INVALIDOS`
- Requiere formato canónico: sin guiones alternativos, sin espacios
- DV debe coincidir exactamente

### 5.2 `FLEXIBLE`

- Acepta y normaliza espacios → advertencia `NORMALIZACION_ESPACIOS`
- Acepta guiones alternativos → advertencia `NORMALIZACION_GUION`
- Acepta separadores de miles y ceros a la izquierda (con advertencias)
- La validación del DV es igual de estricta

### 5.3 `LEGADO` (obsoleto)

Alias de `FLEXIBLE`. Emite `DeprecationWarning`. Se eliminará en v2.0.

---

## 6. Casos límite

| Entrada | Modo | Estado esperado | Nota |
|---------|------|-----------------|------|
| `0-0` | Estricto | válido | RUT con base "0" |
| `12345678` | Estricto | posible | Base sin DV; se puede calcular |
| `1-9` | Flexible | válido | RUT de 1 dígito |
| `123456789-2` | Estricto | válido | RUT de 9 dígitos |
| `12345670-k` | Estricto | válido | DV=K en minúscula |
| `12345670-K` | Estricto | válido | DV=K en mayúscula |
| `000012345678-5` | Flexible | válido | Ceros a la izquierda normalizados |
| `12 345 678-5` | Flexible | válido | Espacios normalizados |
| `12 345 678-5` | Estricto | inválido | Espacios rechazados |
| `` (vacío) | Estricto | incompleto | `RUT_VACIO` |
| `abc` | Estricto | inválido | `CARACTERES_INVALIDOS` |
| `12.34.567-8` | Estricto | inválido | `FORMATO_PUNTOS` |
| `1234567890-?` | Estricto | inválido | `LONGITUD_MAXIMA` + `DV_INVALIDO` |

---

## 7. Trazabilidad con el código fuente

| Concepto | Archivo | Líneas |
|----------|---------|--------|
| Configuración (factores, módulo, límites) | `rutificador/config.py` | 10-17 |
| Algoritmo DV | `rutificador/utils.py` | 123-164 |
| Regex de formato RUT | `rutificador/validador.py` | 32 |
| Regex de puntos | `rutificador/utils.py` | 25-26 |
| Normalización (9 pasos) | `rutificador/rut.py` | 232-288 |
| Classifier (`Rut.parse`) | `rutificador/rut.py` | 291-387 |
| Catálogo de errores | `rutificador/errores.py` | 21-118 |
| Modos de rigor | `rutificador/config.py` | 41-61 |

---

## 8. Test vectors

Los test vectors canónicos están en `tests/vectors/`:

- `test_vectors_dv.json` — cálculo de dígito verificador (≥10 casos)
- `test_vectors_validacion.json` — validación completa (≥12 casos)

Estos archivos JSON están diseñados para ser legibles por cualquier lenguaje
(Rust, TypeScript, Go) y sirven como fixtures cross-platform para ports futuros.

---

*Última actualización: 2026-07-14 · v1.6.1*
