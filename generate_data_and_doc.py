#!/usr/bin/env python3
"""
One-step: generate data (figures) with Poetry env and build the LaTeX PDF.
Runs:
  - poetry run python src/python/main.py
  - python src/latex/build_latex.py --env src/latex/latex.env --tex src/latex/main.tex --bib main
"""
from __future__ import annotations
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str], cwd: Path | None = None, env_extra: dict | None = None) -> int:
    print("→", " ".join(cmd))
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    try:
        return subprocess.call(cmd, cwd=str(cwd) if cwd else None, env=env)
    except FileNotFoundError:
        return 127


def ensure_data_with_poetry_or_fallback() -> int:
    pyproj_dir = ROOT / "src" / "python"
    # Try Poetry path first
    cfg = run(["poetry", "config", "virtualenvs.in-project", "true"], cwd=pyproj_dir)
    inst = run(["poetry", "install"], cwd=pyproj_dir) if cfg == 0 else 1
    if cfg == 0 and inst == 0:
        # Poetry env ready - enforce headless MPL backend
        return run(["poetry", "run", "python", "../python/run.py"], cwd=pyproj_dir, env_extra={"MPLBACKEND": "Agg"})

    # Fallback: use system Python, install minimal deps, then run
    print("WARN: Poetry unavailable; falling back to system Python (pip install matplotlib numpy).")
    pip_cmd = [sys.executable, "-m", "pip", "install", "matplotlib", "numpy"]
    if run(pip_cmd, cwd=ROOT) != 0:
        return 1
    return run([sys.executable, str(ROOT / "src/python/run.py")], cwd=ROOT, env_extra={"MPLBACKEND": "Agg"})


def build_latex() -> int:
    latex_script = ROOT / "src" / "latex" / "build_latex.py"
    if not latex_script.exists():
        print(f"ERROR: Missing {latex_script}")
        return 1
    return run(
        [
            sys.executable,
            str(latex_script),
            "--env",
            str(ROOT / "src/latex/latex.env"),
            "--tex",
            str(ROOT / "src/latex/main.tex"),
            "--bib",
            "main",
        ],
        cwd=ROOT,
    )


def main() -> int:
    if ensure_data_with_poetry_or_fallback() != 0:
        print("ERROR: Generating figure failed.")
        return 1
    return build_latex()

if __name__ == "__main__":
    raise SystemExit(main())
