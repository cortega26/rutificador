# Lineamientos para agentes

Este repositorio utiliza las siguientes convenciones y prácticas:

- **Idioma:** Usa español en los nombres de archivos, funciones, variables y comentarios.
- **Principios de diseño:** Aplica SOLID, DRY y KISS; respeta PEP-8 y el Zen de Python.
- **Calidad del código:** Ejecuta pruebas y linters antes de realizar un commit.
- **Versionado:** Incrementa la versión en cada cambio.
  - Se sigue el esquema de versionado semántico `MAJOR.MINOR.PATCH`.
  - La versión se define en `pyproject.toml` (`tool.poetry.version`) y se expone en `rutificador/__init__.py` como `__version__`.
- **Comprobaciones:** Usa `pre-commit` para linting y `pytest` para las pruebas.
