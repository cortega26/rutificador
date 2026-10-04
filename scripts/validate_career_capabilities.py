#!/usr/bin/env python3
"""Fail CI when a repository-owned capability claim loses its evidence.

The manifest's evidence blob hashes are authoritative. Unrelated repository
changes do not make capabilities stale; a changed or deleted evidence file does.
"""

from __future__ import annotations

import argparse
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
                stale.append(
                    f"{cid}:{path}: STALE expected={expected} actual={actual}"
                )

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
    parser.add_argument(
        "--manifest", default=".career/capabilities.json", type=Path
    )
    parser.add_argument("--repo", default=".", type=Path)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="recompute evidence blob hashes after consciously re-auditing affected claims",
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
            f"capability manifest FAILED: {len(errors)} schema error(s), "
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
