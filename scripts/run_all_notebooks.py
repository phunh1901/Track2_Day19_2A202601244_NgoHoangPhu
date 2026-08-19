"""Execute all 8 notebooks sequentially headless, preserving output and verifying zero errors."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


def main() -> int:
    notebooks = sorted((ROOT / "notebooks").glob("[0-9]*.ipynb"))
    if not notebooks:
        print("No notebooks found! Syncing from jupytext py files...")
        import subprocess

        subprocess.run(["jupytext", "--to", "notebook", "notebooks/[0-9]*.py"], cwd=str(ROOT), check=True)
        notebooks = sorted((ROOT / "notebooks").glob("[0-9]*.ipynb"))

    print("=" * 70)
    print(f"Executing {len(notebooks)} notebooks with nbconvert (grader simulation)")
    print("=" * 70)

    ep = ExecutePreprocessor(timeout=900, kernel_name="venv_lab19")
    failures = []

    for nb_path in notebooks:
        print(f"\n---> Running: {nb_path.name} ... ", end="", flush=True)
        t0 = time.perf_counter()
        try:
            with open(nb_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)

            ep.preprocess(nb, {"metadata": {"path": str(ROOT / "notebooks")}})

            with open(nb_path, "w", encoding="utf-8") as f:
                nbformat.write(nb, f)

            duration = time.perf_counter() - t0
            print(f"PASS ({duration:.1f}s)")
        except Exception as e:
            duration = time.perf_counter() - t0
            print(f"FAIL ({duration:.1f}s)")
            print(f"Error: {e}")
            failures.append((nb_path.name, str(e)))

    print("\n" + "=" * 70)
    if not failures:
        print(f"ALL {len(notebooks)} NOTEBOOKS EXECUTED SUCCESSFULLY WITHOUT ERRORS!")
        print("=" * 70)
        return 0
    else:
        print(f"FAILED {len(failures)}/{len(notebooks)} NOTEBOOKS:")
        for name, err in failures:
            print(f"  - {name}: {err[:150]}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
