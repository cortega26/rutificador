# AGENTS.md · AI Delivery Playbook v4.1

> **Propósito** · Proveer instrucciones operativas actualizadas para asistentes de código que trabajen en entornos regulados. Este documento está dirigido exclusivamente a agentes de IA.

---

## 1. Principios de Ejecución
1. **Eficiencia dirigida** · Minimiza rondas generando la mejor propuesta viable en el primer intento.
2. **Contexto anclado** · Trabaja solo sobre artefactos confirmados; cualquier suposición debe declararse y ser reversible.
3. **Seguridad por defecto** · Adoptar librerías y patrones seguros sin esperar a la etapa final.
4. **Trazabilidad total** · Toda salida debe indicar modelo, semillas y supuestos clave.
5. **Idioma operativo** · Variables, comentarios y documentación en español salvo que el repositorio tenga un estándar explícito distinto.

---

## 2. Estrategia de Modelos
- **Capa principal** · `gpt-5.1-codex-max@2025-10-01` para arquitectura o migraciones críticas.  
- **Capa optimizada** · `claude-4.1-sonnet` para tareas de mantenimiento/lint.  
- **Capa de razonamiento** · Modelos O-series u homólogos cuando se requiera verificación formal.  

**Configuración obligatoria**
```yaml
model_profile:
  seed: 42
  temperature: 0.05        # 0 para código determinista, 0.1 para investigación ligera
  top_p: 0.95
  max_retries: 2
  fallback: ["gpt-5.1", "claude-4-haiku"]
```
> Registrar en cada entrega: modelo efectivo, temperatura y número de reintentos.

---

## 3. Protocolo de Compromiso
1. **Descubrimiento** · Leer `pyproject/requirements`, scripts de calidad y archivos modificados antes de proponer cambios.  
2. **Plan mínimo** · Si la tarea no es trivial, exponer 3‑5 pasos; mantener un solo paso “in_progress”.  
3. **Suposiciones** · Formato `ASUNTO · riesgo · mitigación`. Ej.: `Base de datos · esquema desconocido · asumir v1 y confirmar`.  
4. **Finalización** · Resumir cambios, archivos tocados y comandos ejecutados; sugerir próximos pasos if aplicable.

---

## 4. Seguridad y Cumplimiento
### Canal seguro de entrega
- **Entrada** · Validar siempre datos externos (CLI, archivos, HTTP).  
- **Salida** · Evitar registrar secretos; usar placeholders (`<TOKEN>`).  
- **Dependencias** · Preferir versiones fijadas; correr `pip-audit`/`npm audit` cuando se agreguen paquetes.

### Validación escalonada
| Etapa | Objetivo | Herramientas |
|-------|----------|--------------|
| S1 · Análisis | Identificar superficies sensibles y normativas aplicables (GDPR, HIPAA, PCI) | Checklist interno |
| S2 · Implementación | Incluir controles (Validaciones, RBAC, sanitización) | Librerías del stack |
| S3 · Revisión | Ejecutar SAST (CodeQL/semgrep) + pruebas de seguridad | Workflows CI |

> Marca cualquier módulo que trate datos personales con `# SECURITY-CRITICAL` y solicita revisión humana.

---

## 5. Estándares de Salida
### Bloque META obligatorio
```yaml
META:
  modelo: "gpt-5.1-codex-max@2025-10-01"
  seed: 42
  reintentos: 0
  complejidad: 0.6          # 0‑1
  supuestos:
    - "No existen migraciones pendientes"
  validaciones:
    - "pytest"
    - "ruff check"
  riesgos:
    - "Posible degradación en lotes >1e6 RUTs"
```

### Formatos soportados
1. **Unified diff enriquecido** (default).  
2. **JSON Edit Plan** (`edits[]`) cuando no se modifica código directamente.  
3. **Tabla de hallazgos** para auditorías o revisiones.  

Incluir siempre comandos reproducibles (`make lint`, `pytest`, etc.) y resaltar si no se ejecutaron por límite del entorno.

---

## 6. Validación Continua
### Pipeline mínimo
1. **Formato** · `ruff format --check .` o equivalente.  
2. **Lint** · `ruff check .` / `eslint .`.  
3. **Tipos** · `mypy --strict .` / `tsc --noEmit`.  
4. **Pruebas** · `pytest -q` / `npm test`.  
5. **Seguridad** · `bandit -r src/`, `safety check`, `npm audit`.  
6. **Cobertura** · ≥85 % en líneas tocadas.  
7. **Performance (si aplica)** · Benchmark del camino crítico, registrar comparativa.

> Documentar cualquier paso omitido con razón y mitigación.

---

## 7. Marcos de Pruebas
- **Unitarias** · Independientes, rápidas, sin IO externo.
- **Property-based** · Hypothesis / fast-check para validar invariantes numéricas o de formato.
- **Integración** · Cubrir interacción entre CLI, validadores y formateadores.
- **Seguridad** · Pruebas negativas: RUTs malformados, entradas maliciosas, ataques de tamaño.
- **Rendimiento** · Ensayar lotes grandes usando generadores; registrar tiempos y memoria.

### Plantilla de caso
```python
@pytest.mark.parametrize("entrada, esperado", [...])
def test_validacion_rut(entrada, esperado):
    with caplog.at_level(logging.DEBUG):
        if esperado.exito:
            assert Rut(entrada).formatear() == esperado.valor
        else:
            with pytest.raises(RutInvalidoError):
                Rut(entrada)
```

---

## 8. Perfiles por Stack
| Stack | Lint/Tipo | Tests | Seguridad | Notas |
|-------|-----------|-------|-----------|-------|
| **Python ≥3.11** | `ruff`, `mypy --strict` | `pytest --cov=rutificador` | `bandit`, `safety` | Usar `pathlib`, `Protocol`, dataclasses. |
| **TypeScript (Node LTS)** | `prettier`, `eslint`, `tsc --noEmit` | `vitest --run` | `npm audit` | Evitar `any`, usar `zod` para validar entradas. |
| **Go ≥1.22** | `gofmt`, `golangci-lint` | `go test -race -cover ./...` | `gosec ./...` | Respetar contextos y devolver errores envueltos. |
| **Rust stable** | `cargo fmt --check`, `cargo clippy -D warnings` | `cargo test` | `cargo audit` | Preferir `Result` con thiserror. |

---

## 9. Documentación y Control de Cambios
- Actualizar `README` o guías si se añaden flags, scripts o procesos.
- Siempre que se libere o se suban cambios de código, incrementar la versión en `rutificador/version.py`; el CI de PyPI rechaza publicar versiones repetidas.
- Las entradas de `CHANGELOG.md` deben incluir etiquetas `[SECURITY]`, `[PERF]`, `[BREAKING]` según corresponda.
- Para decisiones arquitectónicas, crear/editar ADR con: contexto, opciones, decisión, consecuencias.
- Mantener referencias a requisitos regulatorios cumplidos (ej. “Cumple GDPR Art. 32 mediante cifrado at-rest”).  

---

## 10. Colaboración Humano‑IA
1. **Transparencia** · Marcar bloques generados por IA en docstrings o comentarios solo si la política del repo lo solicita.
2. **Revisión requerida** · Señalar explícitamente las zonas que exigen revisión humana (ex. “Lógica de autenticación”).  
3. **Feedback loop** · Registrar correcciones recibidas para limitar repeticiones: `LEARNED: preferir pathlib sobre os.path`.  
4. **CI asistida** · Referenciar el workflow `ai-generated-validation.yml` cuando se creen archivos `*AI-GENERATED*`.  

---

## 11. Plantillas rápidas
### Respuesta estándar
```
META: {...}
PLAN:
- Paso 1 · estado
- Paso 2 · estado
SECURITY: Riesgos identificados + mitigación
PERFORMANCE: Consideraciones o pruebas
COMMANDS: ["pytest -q"]
RESULTS: Resumen de cambios + archivos
NEXT: Pasos sugeridos (opcional)
```

### JSON Edit Plan
```json
{
  "edits": [
    {
      "path": "rutificador/rut.py",
      "action": "modify",
      "rationale": "Propagar validador personalizado",
      "impact": "compatible",
      "review_required": true
    }
  ],
  "meta": {
    "modelo": "gpt-5.1-codex-max",
    "seed": 42,
    "seguridad": "validada"
  }
}
```

---

**Fin · AI Delivery Playbook v4.1**

*Este documento unifica selección de modelos, rigor de seguridad y colaboración humana para acelerar entregas sin perder trazabilidad.*
