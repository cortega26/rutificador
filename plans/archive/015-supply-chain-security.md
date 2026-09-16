# Plan 015: Endurecimiento de seguridad en cadena de suministro — attestación de procedencia e integridad de releases

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 6b61e0e..HEAD -- .github/workflows/publish-package.yml .github/workflows/security.yml .github/workflows/ci.yml`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `6b61e0e`, 2026-07-14

## Why this matters

rutificador ya usa PyPI Trusted Publishing (`id-token: write` en `publish-package.yml:22`) y genera SBOM CycloneDX en CI. Pero hay tres brechas de seguridad en la cadena de suministro: (1) los artifacts de release no tienen attestación de procedencia verificable, (2) el SBOM CycloneDX no se adjunta a los GitHub Releases, y (3) los pasos del workflow de publicación pueden beneficiarse de un environment con reglas de protección. Cerrar estas brechas es señal de madurez para una librería usada en producción con datos personales (RUTs), sin modificar una línea de código de la librería.

## Current state

- `.github/workflows/publish-package.yml` — ya usa `id-token: write` y PyPI Trusted Publishing (`pypa/gh-action-pypi-publish@release/v1`). Construye con `python -m build` y verifica con `twine check`. NO genera attestación de procedencia.
- `.github/workflows/security.yml` — ejecuta `bandit`, `safety check`, `pip-audit`, genera SBOM con `cyclonedx-py`. NO sube el SBOM como artifact de release.
- `.github/workflows/ci.yml` — tests + calidad. Sin cambios necesarios.
- GitHub Actions permissions are well-scoped: `id-token: write`, `contents: read`.

Repo conventions: YAML workflow files, all comments in Spanish, existing workflows follow consistent structure with `uses:`, `with:`, `run:`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Build package | `.venv/bin/python -m build` | exit 0, `dist/` populated |
| SBOM generation | `.venv/bin/cyclonedx-py environment -o sbom.json` | exit 0, `sbom.json` created |
| Twine check | `.venv/bin/python -m twine check dist/*` | exit 0 |
| Verify attestation | `gh attestation verify dist/*.whl --repo cortega26/rutificador` | exit 0 (after this plan) |

## Scope

**In scope** (files you may modify):
- `.github/workflows/publish-package.yml` — add provenance attestation, SBOM upload, environment protection rules
- `.github/workflows/security.yml` — optionally upload SBOM as artifact

**Out of scope** (do NOT touch):
- Any Python source code in `rutificador/`
- `pyproject.toml` (build configuration is already correct)
- `requirements-dev.txt`
- CI test/lint/type workflows

## Git workflow

- Branch: `advisor/015-supply-chain-security`
- Commit message style: `chore(ci): <description>`
- Example: `chore(ci): agregar attestación de procedencia al workflow de publicación`
- Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Agregar attestación de procedencia al workflow de publicación

Editar `.github/workflows/publish-package.yml`. Después del paso "Construir paquete" (línea 43) y antes de "Verificar paquete" (línea 46), agregar attestación de artifact de GitHub:

```yaml
      - name: Generar attestación de procedencia
        uses: actions/attest-build-provenance@v2
        with:
          subject-path: dist/*
```

Esto genera una attestación SLSA v1.0 verificable que vincula el artifact con el commit exacto y el workflow que lo produjo. Los consumidores pueden verificarlo con:

```bash
gh attestation verify dist/rutificador-*.whl --repo cortega26/rutificador
```

También actualizar los permisos del job para incluir el permiso necesario:

```yaml
    permissions:
      id-token: write
      contents: read
      attestations: write  # NUEVO: requerido por actions/attest-build-provenance
```

**Verify**: el workflow debe ser sintácticamente válido. Revisar con `yamllint` o validación manual del schema de GitHub Actions. No hay comando local para probar — la verificación real ocurre en el próximo release.

### Step 2: Adjuntar SBOM CycloneDX a los GitHub Releases

Hay dos opciones. **Opción A (recomendada)**: generar el SBOM en el workflow de publicación como paso adicional. **Opción B**: subir el SBOM generado en `security.yml` como artifact y referenciarlo desde el release.

Implementar Opción A — agregar al workflow `publish-package.yml`, después del paso de construcción:

```yaml
      - name: Generar SBOM CycloneDX
        run: |
          python -m pip install cyclonedx-bom
          cyclonedx-py environment -o sbom.json

      - name: Subir SBOM como artifact del release
        uses: actions/upload-artifact@v7
        with:
          name: sbom
          path: sbom.json
```

Y en el paso `pypa/gh-action-pypi-publish`, asegurar que la URL de attestación esté activa si PyPI la soporta en ese momento.

Para que el SBOM se adjunte automáticamente al GitHub Release, se puede usar `softprops/action-gh-release` si el trigger es `release: [published]`, pero dado que el workflow actual se dispara con tags (`push: tags: ["v*"]`), una alternativa es usar `gh release upload` en un paso condicional:

```yaml
      - name: Adjuntar SBOM al release
        if: startsWith(github.ref, 'refs/tags/')
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh release upload ${GITHUB_REF#refs/tags/} sbom.json
```

**Verify**: revisar que `gh release upload` está disponible en el runner (`ubuntu-latest` lo incluye).

### Step 3: Agregar protección de environment (opcional pero recomendado)

El workflow ya declara un environment `release` (línea 19). Agregar reglas de protección en GitHub Settings → Environments → release:

- **Required reviewers**: al menos 1 (el maintainer)
- **Wait timer**: 0 (no necesario)
- **Deployment branches**: `master`

Esto no es un cambio de código — es una configuración en la UI de GitHub. Documentarlo en el plan para que el maintainer lo configure manualmente.

### Step 4: Verificación de integridad del flujo existente

Confirmar que nada se rompió:

```bash
# Verificar que el paquete sigue construyéndose
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*

# Verificar que el SBOM se genera
.venv/bin/cyclonedx-py environment -o sbom.json
test -f sbom.json && echo "SBOM OK"
```

### Step 5: Documentar la verificación de attestación en el README

Agregar una sección corta al README (o a `SECURITY.md`) explicando cómo los consumidores pueden verificar la integridad del paquete:

```markdown
### Verificación de integridad

Cada release de rutificador incluye una attestación de procedencia SLSA v1.0
generada por GitHub Actions. Los consumidores pueden verificar que el paquete
fue construido desde el commit oficial:

```bash
gh attestation verify dist/rutificador-*.whl --repo cortega26/rutificador
```

El SBOM CycloneDX está disponible en los assets del release en GitHub.
```

**Verify**: el README no debe tener errores de markdown. `mkdocs build --strict` debe pasar si se modifica `docs/`.

## Test plan

No hay tests automatizables localmente para cambios de CI — la verificación ocurre en el próximo release tag. Sin embargo:

1. Probar sintaxis YAML: copiar el workflow modificado y validarlo contra el schema de GitHub Actions (el editor de GitHub Actions en la UI lo valida automáticamente al hacer push)
2. Probar `gh attestation verify` en el próximo release manual

## Done criteria

- [ ] `publish-package.yml` incluye `actions/attest-build-provenance@v2`
- [ ] `publish-package.yml` incluye generación y upload de SBOM CycloneDX
- [ ] Los permisos del job incluyen `attestations: write`
- [ ] El SBOM se adjunta al GitHub Release (o como artifact del workflow)
- [ ] `python -m build && python -m twine check dist/*` sigue funcionando
- [ ] `cyclonedx-py environment -o sbom.json` se ejecuta exitosamente
- [ ] Documentación de verificación agregada a README o SECURITY.md
- [ ] `plans/README.md` status row updated

## STOP conditions

- Si `actions/attest-build-provenance@v2` no está disponible en el runner de GitHub Actions (poco probable, es un action oficial de GitHub), usar `gh attestation` CLI directamente como alternativa
- Si agregar `attestations: write` causa un error de permisos porque el repositorio no tiene habilitada la feature de attestations, documentar que requiere habilitación en Settings → Actions → General → "Allow GitHub to create and publish attestations"
- Si `cyclonedx-py` falla en el runner de publicación (requiere `pip install cyclonedx-bom` como paso adicional), documentar el paso y verificar que `requirements-dev.txt` lo incluye

## Maintenance notes

- GitHub Attestations es una feature relativamente nueva. Si GitHub cambia la API o el action, este plan debe revisarse.
- La generación de SBOM en el workflow de publicación es redundante con `security.yml`, pero intencional: el SBOM debe generarse en el mismo pipeline que produce el artifact para garantizar que corresponde exactamente a esa build.
- PyPI está implementando PEP 740 (attestation verification). Cuando esté disponible, se puede agregar un paso de verificación de attestations en el propio workflow de publicación.
- Las reglas de protección del environment `release` se configuran manualmente en GitHub UI y no son versionables en el repo. Este plan las documenta pero no las aplica automáticamente.
