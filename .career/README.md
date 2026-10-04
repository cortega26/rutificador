# Career capability manifest

`.career/capabilities.json` is a machine-readable inventory of capabilities
that this repository can prove directly from code.

It is **not** a marketing profile and it is not maintained by date. Each claim
points to one or more repository files plus the exact Git blob id that was
inspected.

CI runs:

```bash
python scripts/validate_career_capabilities.py
```

on every pull request and push to `master`. If evidence for a known claim
changes or disappears, the corresponding capability becomes stale and CI
fails until the claim is consciously re-audited.

After reviewing an intentional evidence change:

```bash
python scripts/validate_career_capabilities.py --refresh
python scripts/validate_career_capabilities.py
```

The refresh command only updates evidence hashes. It does **not** discover or
approve new capabilities automatically.

This file is designed for downstream career/application tooling. New
capabilities are added only with concrete code evidence; a job description is
never accepted as evidence about this repository.
