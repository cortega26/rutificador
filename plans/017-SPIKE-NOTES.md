# Spike 017: Notas — extensión nativa PyO3 para cálculo de DV

**Fecha**: 2026-07-14 | **Commit base**: 6b61e0e | **Decisión**: **No-go**

---

## 1. Setup

| Componente | Versión |
|-----------|---------|
| Rust | 1.97.0 |
| PyO3 | 0.29.0 |
| maturin | latest |
| Python | 3.13 |
| Plataforma | Linux x86_64 |

## 2. Implementación

Se implementó `calcular_dv_rust(base: &str) -> String` en Rust/PyO3 replicando
el algoritmo de módulo 11 con factores (2,3,4,5,6,7) cíclicos, idéntico al de
`rutificador/utils.py:calcular_digito_verificador`.

Se creó también una variante batch `calcular_dv_lote_rust(bases: Vec<String>) -> Vec<String>`
que procesa múltiples bases en una sola llamada FFI para amortizar el overhead.

## 3. Validación

Los 12 test vectors canónicos de `tests/vectors/conformance.json` pasan
correctamente. La implementación Rust produce resultados idénticos a la Python.

## 4. Resultados del benchmark

### DV individual (13 bases × 100,000 iteraciones)

| Implementación | Tiempo | us/llamada |
|---------------|--------|------------|
| Python | 0.0323s | 0.3 |
| Rust | 0.0560s | 0.6 |
| **Speedup** | **0.6×** | — |

### Lote de 13 bases × 10,000 iteraciones

| Implementación | Tiempo | us/lote |
|---------------|--------|---------|
| Python | 0.0039s | 0.4 |
| Rust | 0.0096s | 1.0 |
| **Speedup** | **0.4×** | — |

### Lote de 1,000 bases × 500 iteraciones

| Implementación | Tiempo |
|---------------|--------|
| Python | 0.0169s |
| Rust | 0.0418s |
| **Speedup** | **0.4×** |


## 5. Factores de la decisión

**A favor de adoptar PyO3:**
- Validación idéntica a Python (test vectors pasan)
- Habilitante para WASM/TypeScript (el código Rust es portable a `wasm-pack`)
- Eliminaría overhead de serialización inter-proceso en modo paralelo si se
  portara el pipeline completo

**En contra:**
- **Speedup consistentemente <1×**: el cálculo de DV es aritmética entera
  pura que Python ejecuta en C (`int.__mul__` → CPython). El overhead FFI
  (allocación de strings Python → Rust, serialización de retorno) domina
  completamente para operaciones tan triviales.
- **El cuello de botella real no es el DV**: el perfil de `Rut.parse()` muestra
  que el tiempo se gasta en regex (`_validar_caracteres_base`), normalización
  de strings, y construcción de `ValidacionResultado`. El DV es ~5% del total.
- **Toolchain adicional**: Rust + maturin + CI de compilación de wheels
  multiplataforma (manylinux, musllinux, macOS, Windows) para un solo
  maintainer.
- **Dependencia runtime de facto**: aunque el wheel es autocontenido, rompe
  la promesa de "cero dependencias base" del proyecto.

## 6. Recomendación: No-go

**No adoptar PyO3 para el cálculo de DV.** El speedup es consistentemente
<1× porque el overhead FFI supera cualquier ganancia en una operación tan
trivial como la aritmética de módulo 11.

Si en el futuro se decide portar la validación completa (formato, normalización,
DV) a Rust/WASM para el ecosistema TypeScript, el código de este spike sirve
como punto de partida. Pero como optimización de rendimiento para el paquete
Python, no tiene sentido.

### Qué sí optimizaría el rendimiento real

Si el rendimiento de procesamiento por lotes es una preocupación, las opciones
con mejor ROI son:

1. **Cython/PyPy**: si los usuarios pueden usar PyPy, el JIT optimiza bucles
   de validación automáticamente sin cambiar código.
2. **Vectorización con numpy**: procesar columnas de RUTs como arrays numpy
   para paralelismo SIMD (útil en el accessor pandas).
3. **Mejorar el pipeline de normalización**: reducir alocaciones de strings
   en `_limpiar_entrada`, `_normalizar_puntos`, `_normalizar_ceros` — estas
   son las operaciones más costosas, no el cálculo de DV.
