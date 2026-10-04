#!/usr/bin/env python3
"""Fail CI when repository capability evidence or detectable coverage drifts.

Two independent checks run:
1. freshness: known claims must still match the exact Git blobs inspected;
2. coverage: deterministic project surfaces may not gain an undeclared
   capability (for example, adding an output format without format.<name>).

The coverage scan proposes nothing semantic: it only covers mechanically
observable surfaces. Broader capability discovery remains a separate review
loop.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from datetime import date
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SCHEMA_VERSION = "project-capabilities-v1"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe evidence path: {relative}")
    candidate = (root / rel).resolve()
    root = root.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"evidence escapes repository: {relative}")
    return candidate


def _declared_ids(caps: list[dict]) -> set[str]:
    return {str(cap.get("id")) for cap in caps if cap.get("id")}


def _declared_terms(caps: list[dict]) -> set[str]:
    terms: set[str] = set()
    for cap in caps:
        for term in cap.get("terms") or []:
            if isinstance(term, str):
                terms.add(term.strip().lower())
        cid = cap.get("id")
        if isinstance(cid, str):
            terms.update(part.lower() for part in re.split(r"[._-]+", cid) if part)
    return terms


def discover_output_formats(root: Path) -> set[str]:
    """Read the actual CLI strategy registry, never README prose."""

    tree = ast.parse((root / "rutificador" / "cli.py").read_text(encoding="utf-8"))
    for node in tree.body:
        target = None
        value = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        if (
            isinstance(target, ast.Name)
            and target.id == "_ESTRATEGIAS_FORMATO"
            and isinstance(value, ast.Dict)
        ):
            result: set[str] = set()
            for key in value.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    result.add(key.value.lower())
            return result
    raise ValueError("could not find _ESTRATEGIAS_FORMATO in rutificador/cli.py")


def discover_contrib_integrations(root: Path) -> set[str]:
    contrib = root / "rutificador" / "contrib"
    result: set[str] = set()
    if not contrib.is_dir():
        return result
    for path in contrib.iterdir():
        if path.name.startswith("_"):
            continue
        if path.is_file() and path.suffix == ".py" and path.stem != "__init__":
            result.add(path.stem.lower())
        elif path.is_dir() and (path / "__init__.py").is_file():
            result.add(path.name.lower())
    return result


def coverage_errors(caps: list[dict], root: Path) -> list[str]:
    ids = _declared_ids(caps)
    terms = _declared_terms(caps)
    errors: list[str] = []

    detected_formats = discover_output_formats(root)
    declared_formats = {
        cid.removeprefix("format.") for cid in ids if cid.startswith("format.")
    }
    missing_formats = sorted(detected_formats - declared_formats)
    if missing_formats:
        errors.append(
            "undeclared CLI output format(s): "
            + ", ".join(missing_formats)
            + " (add format.<name> with direct evidence)"
        )

    integrations = discover_contrib_integrations(root)
    missing_integrations = sorted(name for name in integrations if name not in terms)
    if missing_integrations:
        errors.append(
            "undeclared contrib integration(s): "
            + ", ".join(missing_integrations)
            + " (add evidence-backed capability/term)"
        )

    if (
        list((root / "schemas").glob("*.json"))
        or (root / "tests/vectors/schema.json").is_file()
    ):
        if "validation.json-schema" not in ids:
            errors.append(
                "JSON Schema files exist but validation.json-schema is undeclared"
            )

    if (
        root / "scripts/conformance.py"
    ).is_file() and "testing.conformance-harness" not in ids:
        errors.append(
            "scripts/conformance.py exists but testing.conformance-harness is undeclared"
        )

    if (
        root / "tests/vectors/conformance.json"
    ).is_file() and "testing.conformance-vectors" not in ids:
        errors.append(
            "tests/vectors/conformance.json exists but testing.conformance-vectors is undeclared"
        )

    if (root / ".github/workflows/ci.yml").is_file() and "ci.github-actions" not in ids:
        errors.append(
            ".github/workflows/ci.yml exists but ci.github-actions is undeclared"
        )

    return errors


def validate(manifest_path: Path, root: Path) -> tuple[list[str], list[str]]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    stale: list[str] = []

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")

    caps = data.get("capabilities")
    if not isinstance(caps, list) or not caps:
        errors.append("capabilities must be a non-empty list")
        return errors, stale

    ids: set[str] = set()
    for cap in caps:
        cid = cap.get("id")
        if not isinstance(cid, str) or not cid:
            errors.append("every capability needs a non-empty id")
            continue
        if cid in ids:
            errors.append(f"duplicate capability id: {cid}")
        ids.add(cid)
        if cap.get("verification") != "CODE_VERIFIED":
            errors.append(f"{cid}: project manifests v1 allow CODE_VERIFIED only")
        evidence = cap.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{cid}: evidence must be a non-empty list")
            continue
        for item in evidence:
            path = item.get("path")
            expected = item.get("blob_sha")
            if not isinstance(path, str) or not isinstance(expected, str):
                errors.append(f"{cid}: evidence requires path + blob_sha")
                continue
            if not SHA_RE.fullmatch(expected):
                errors.append(f"{cid}:{path}: invalid blob_sha")
                continue
            try:
                source = safe_path(root, path)
            except ValueError as exc:
                errors.append(f"{cid}: {exc}")
                continue
            if not source.is_file():
                stale.append(f"{cid}:{path}: INVALIDATED (missing)")
                continue
            actual = git_blob_sha(source)
            if actual != expected:
                stale.append(f"{cid}:{path}: STALE expected={expected} actual={actual}")

    try:
        errors.extend(coverage_errors(caps, root))
    except (OSError, SyntaxError, ValueError) as exc:
        errors.append(f"capability coverage discovery failed: {exc}")

    return errors, stale


def refresh(manifest_path: Path, root: Path) -> None:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for cap in data["capabilities"]:
        for item in cap["evidence"]:
            source = safe_path(root, item["path"])
            if not source.is_file():
                raise SystemExit(f"cannot refresh missing evidence: {item['path']}")
            item["blob_sha"] = git_blob_sha(source)

    try:
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
        if SHA_RE.fullmatch(head):
            data["verified_against"]["commit"] = head
    except (OSError, subprocess.CalledProcessError):
        pass
    data["verified_against"]["verified_at"] = date.today().isoformat()
    manifest_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=".career/capabilities.json", type=Path)
    parser.add_argument("--repo", default=".", type=Path)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="recompute evidence hashes after consciously re-auditing affected claims",
    )
    args = parser.parse_args()

    manifest = args.manifest
    root = args.repo
    if args.refresh:
        refresh(manifest, root)

    errors, stale = validate(manifest, root)
    for error in errors:
        print(f"ERROR {error}")
    for item in stale:
        print(item)

    if errors or stale:
        print(
            f"capability manifest FAILED: {len(errors)} schema/coverage error(s), "
            f"{len(stale)} stale/invalidated evidence item(s)"
        )
        return 2

    data = json.loads(manifest.read_text(encoding="utf-8"))
    print(
        f"capability manifest CURRENT: {len(data['capabilities'])} capability claim(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
