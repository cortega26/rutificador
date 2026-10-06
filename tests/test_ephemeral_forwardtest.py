# ruff: noqa
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_ephemeral_forwardtest() -> None:
    # Run the expensive analysis exactly once in the CI matrix.
    if sys.version_info[:2] != (3, 13):
        return

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "pandas",
            "numpy",
            "scipy",
            "pyarrow",
            "requests",
        ],
        check=True,
    )
    script = Path(__file__).resolve().parents[1] / "tools" / "forwardtest_vol_persistence_ephemeral.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=900,
    )
    # Force pytest to expose the complete captured analysis in the job log.
    raise AssertionError(
        "EPHEMERAL_FORWARDTEST_OUTPUT_BEGIN\n"
        + proc.stdout
        + "\nEPHEMERAL_FORWARDTEST_OUTPUT_END\n"
        + f"returncode={proc.returncode}"
    )
