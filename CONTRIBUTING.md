# Guía de Contribución

Gracias por tu interés en contribuir a **rutificador**. Este documento describe cómo participar en el desarrollo del proyecto.

## Requisitos

- Python 3.10 o superior
- Entorno virtual (`venv` o similar)

## Configuración del Entorno de Desarrollo

```bash
# Clonar el repositorio
git clone https://github.com/cortega26/rutificador.git
cd rutificador

# Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Instalar el paquete en modo editable
pip install -e .

# Instalar hooks de pre-commit (opcional pero recomendado)
pre-commit install
```

## Calidad de Código

El proyecto mantiene **cero tolerancia** a errores en todas las herramientas de calidad. Antes de enviar un cambio, asegúrate de que todo pase:

```bash
# Tests (sin deprecation warnings)
pytest -W error::DeprecationWarning

# Cobertura (opcional)
pytest --cov=rutificador --cov-report=term

# Tipos
mypy rutificador/ tests/ --ignore-missing-imports

# Lint y formato
ruff check .
ruff format . --check

# Seguridad
bandit -r rutificador/

# Límites arquitectónicos
lint-imports

# Documentación
mkdocs build --strict

# Benchmarks de rendimiento
pytest tests/benchmarks/ tests/test_benchmark.py --benchmark-only
```


## Estilo de Código

- **Formato**: El proyecto usa [ruff](https://docs.astral.sh/ruff/) para formato y linting. No es necesario ejecutarlo manualmente si tienes instalado el pre-commit hook.
- **Tipos**: Todo el código nuevo debe incluir anotaciones de tipos (type hints). El proyecto sigue PEP 484.
- **Docstrings**: Usamos [Google-style](https://google.github.io/styleguide/pyguide.html#383-functions-and-methods) para docstrings, en español.

  ```python
  def ejemplo(param1: str, param2: int = 0) -> bool:
      """Descripción breve de la función.

      Args:
          param1: Descripción del primer parámetro.
          param2: Descripción del segundo (por defecto 0).

      Returns:
          Descripción del valor de retorno.

      Raises:
          ValueError: Si param1 está vacío.
      """
  ```

## Convenciones del Proyecto

- **Idioma**: Código, docstrings, mensajes de commit y documentación en **español**.
- **Commits**: Usar [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat:` — nueva funcionalidad
  - `fix:` — corrección de errores
  - `refactor:` — cambios que no agregan funcionalidad ni corrigen errores
  - `docs:` — cambios en documentación
  - `chore:` — tareas de mantenimiento
  - `release:` — nuevas versiones
- **Versiones**: [SemVer](https://semver.org/) (v1.x.x). Las versiones se publican vía CI al crear un tag `v*` en master.

## Estructura del Proyecto

```
rutificador/
├── rutificador/           # Código fuente
│   ├── config.py          # Configuración y modos de validación
│   ├── validador.py       # Validación de formato y DV
│   ├── rut.py             # Clase principal Rut
│   ├── procesador.py      # Procesamiento por lotes
│   ├── formatter.py       # Estrategias de formateo (CSV, JSON, XML)
│   ├── sugestor.py        # Motor de sugerencias fuzzy
│   ├── utils.py           # Utilidades (cálculo DV, limpieza)
│   ├── errores.py         # Catálogo de errores
│   ├── exceptions.py      # Jerarquía de excepciones
│   ├── cli.py             # Interfaz de línea de comandos
│   ├── contrib/           # Integraciones opcionales
│   │   ├── pydantic/      # Tipo RutStr para Pydantic v2
│   │   ├── fastapi.py     # Dependencia para FastAPI
│   │   ├── pandas.py      # Accessor para pandas
│   │   ├── polars.py      # Namespace para polars
│   │   └── _formato_comun.py
│   └── py.typed           # Marcador PEP 561
├── tests/                 # Tests
└── pyproject.toml         # Configuración del paquete
```

## Dependencias

- **Core**: Sin dependencias externas (solo stdlib de Python).
- **Extras opcionales**: `pydantic`, `fastapi`+`httpx`, `pandas`, `polars`.
- **Dev**: Ver `requirements-dev.txt`.

## Pull Requests

1. Crea una rama desde `master` con un nombre descriptivo (`fix/`, `feat/`, `docs/`).
2. Asegúrate de que todos los controles de calidad pasen (CI los ejecutará automáticamente).
3. La rama debe estar actualizada con `master` antes del merge.
4. Incluye una descripción clara de los cambios y su motivación.

## Reportar Problemas

Si encuentras un error, abre un issue en GitHub incluyendo:
- Versión de rutificador (`pip show rutificador`)
- Versión de Python
- Código mínimo para reproducir el problema
- Comportamiento esperado vs real

## Licencia

Al contribuir, aceptas que tus cambios se publiquen bajo la licencia MIT del proyecto.
