# Spike 006: Notas — unificación de parsers

**Fecha**: 2026-06-12 | **Commit base**: 278425b | **Decisión**: **No-go**

---

## 1. Inventario del contrato del constructor

| Entrada | Resultado | Excepción |
|---------|-----------|-----------|
| `"12345678-5"` | `Rut` válido | — |
| `"12.345.678-5"` | `Rut` válido (acepta puntos) | — |
| `"12345678"` (base sola) | `Rut` válido (calcula DV) | — |
| `int` (e.g. `12345678`) | `Rut` válido (calcula DV) | — |
| `"12 345678-5"` (espacio interno) | `Rut` válido (normaliza) | — |
| `"12345678-9"` (DV incorrecto) | — | `ErrorDigitoRut` |
| `"abc"` | — | `ErrorFormatoRut` |
| `""` / `"  "` | — | `ErrorValidacionRut` |

El constructor garantiza tres cosas que `parse()` no expresa hoy:
1. **Auto-DV**: acepta base sola (`"12345678"`) y calcula el DV; `parse()` devuelve `estado="posible"`.
2. **Normalización silenciosa**: limpia espacios, guiones alternativos, ceros; `parse(ESTRICTO)` rechaza esas entradas.
3. **Excepciones tipadas**: lanza `ErrorFormatoRut`, `ErrorDigitoRut`, `ErrorLongitudRut` con mensajes y `codigo_error` específicos que los tests afirman (`grep -rn "ErrorFormatoRut\|ErrorDigitoRut" tests/` → 12 sitios en test_rutificador.py).

## 2. Mapping `estado` → excepción del constructor

| `parse().estado` | `parse().errores[0].codigo` | Excepción del constructor |
|------------------|-----------------------------|---------------------------|
| `"invalido"` | `CARACTERES_INVALIDOS` | `ErrorFormatoRut` |
| `"invalido"` | `DV_DISCORDANTE` | `ErrorDigitoRut` |
| `"invalido"` | `LONGITUD_MAXIMA` / `LONGITUD_MINIMA` | `ErrorLongitudRut` |
| `"invalido"` | `DV_INVALIDO`, `FORMATO_GUION`, etc. | `ErrorFormatoRut` |
| `"incompleto"` | `RUT_VACIO` | `ErrorValidacionRut` |
| `"posible"` | — | constructor auto-completa el DV (divergencia de diseño) |

Un wrapper `Rut(s) → parse(s) → raise` preservaría los tipos de excepción mapeando `codigo_error`, pero la divergencia en `"posible"` exige lógica extra (calcular el DV y revalidar), lo que añade complejidad al camino crítico sin eliminar código: el cálculo de DV para auto-completar ya existe en `parse()` para el estado `"posible"`, pero la interfaz del wrapper sería más opaca que el código actual.

## 3. Factores de la decisión

**A favor de unificar:**
- Una sola implementación de la gramática → cualquier cambio de formato es una edición, no dos.
- Elimina la clase de divergencia F3 de raíz.

**En contra:**
- Los dos entry points tienen contratos documentados y distintos (plan 003, Opción A). Unificarlos requiere un wrapper que adapte `estado+errores` a excepciones tipadas — añade indirección sin claridad.
- Fuzz de 500k entradas encontró **cero** divergencia de cálculo de DV; la única clase de divergencia (whitespace) ya está documentada, testeada y controlada.
- 12 sitios en tests afirman tipos de excepción concretos del constructor. Cualquier cambio en esos tipos o mensajes es un cambio observable de la API pública.
- El código es `# SECURITY-CRITICAL`; el costo de un error aquí supera el beneficio de eliminar duplicación que ya está contenida.
- El contrato builder/classifier acordado en plan 003 es más profesional y legible con dos implementaciones explícitas que con un único core+adapter.

## 4. Recomendación: No-go

**Mantener los dos entry points con contratos explícitos.** La red de seguridad (plan 002, `tests/test_consistencia_parse.py`) detectará cualquier drift de gramática futuro. Si en una versión 2.0 se decidiera unificar, el camino correcto es:

1. Extender `parse()` para soportar auto-DV (nuevo estado `"autocompletado"` o parámetro `completar_dv=True`).
2. Hacer que el constructor delegue a ese `parse()` extendido.
3. Preservar los tipos de excepción tipados mapeando `codigo_error` → clase de excepción.
4. Bump a v2.0 con entrada en CHANGELOG.

Ese trabajo pertenece a una remodelación de API mayor, no a mantenimiento de v1.x.
