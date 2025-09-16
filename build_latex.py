#!/usr/bin/env python3
"""
Cross-platform LaTeX build helper.
- Reads a simple KEY=VALUE env file (default: ./latex.env)
- Runs: pdflatex (first pass) → bibtex → pdflatex (two final passes by default)
- Prints clean, step-by-step logs and exits with non-zero on failure.

Usage:
  python build_latex.py [--env latex.env] [--tex main.tex] [--bib main] [--passes 2]

If PDFLATEX/BIBTEX in env file are bare commands, they must be resolvable on PATH.
If they are absolute paths, they will be used directly.
"""
from __future__ import annotations
import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
import re

DEFAULT_ENV_FILE = "src/latex/latex.env"
DEFAULT_TEX = "src/latex/main.tex"
DEFAULT_BIB = "main"


class BuildError(RuntimeError):
    pass


def parse_env_file(path: Path) -> dict:
    env = {}
    if not path.exists():
        raise BuildError(f"Env file not found: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()
    return env


def which(cmd: str) -> str | None:
    # Honor absolute paths
    p = Path(cmd)
    if p.is_file():
        return str(p)
    # Search PATH in a cross-platform way
    from shutil import which as shutil_which
    return shutil_which(cmd)


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> int:
    print(f"→ Running: {' '.join(shlex.quote(c) for c in cmd)}")
    proc = subprocess.run(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    print(proc.stdout)
    return proc.returncode


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build LaTeX project")
    parser.add_argument("--env", default=DEFAULT_ENV_FILE, help="Env file path (default: latex.env)")
    parser.add_argument("--tex", default=DEFAULT_TEX, help="Main .tex file (default: main.tex)")
    parser.add_argument("--bib", default=DEFAULT_BIB, help="BibTeX base name (default: main)")
    parser.add_argument("--passes", type=int, default=None, help="Number of final pdflatex passes (default from env or 2)")
    parser.add_argument("--interaction", default=None, help="pdflatex interaction mode (default from env or nonstopmode)")
    parser.add_argument("--no-file-line-error", action="store_true", help="Disable -file-line-error flag")
    parser.add_argument("--outdir", default=None, help="Output directory for build artifacts (default from env or 'out')")
    args = parser.parse_args(argv)

    cwd = Path.cwd()
    env_path = Path(args.env)
    env = parse_env_file(env_path)

    pdflatex = env.get("PDFLATEX")
    bibtex = env.get("BIBTEX")
    if not pdflatex or not bibtex:
        raise BuildError("Env file must define PDFLATEX and BIBTEX")

    pdflatex_cmd = which(pdflatex)
    bibtex_cmd = which(bibtex)
    if not pdflatex_cmd:
        raise BuildError(f"pdflatex not found or not executable: {pdflatex}")
    if not bibtex_cmd:
        raise BuildError(f"bibtex not found or not executable: {bibtex}")

    # Options
    interaction = args.interaction or env.get("INTERACTION", "nonstopmode")
    file_line_error = env.get("FILE_LINE_ERROR", "true").lower() in ("1", "true", "yes", "on") and not args.no_file_line_error
    final_passes = args.passes if args.passes is not None else int(env.get("PDFLATEX_FINAL_PASSES", "2"))
    outdir = Path(args.outdir or env.get("OUTDIR", "out"))

    tex_file = Path(args.tex)
    bib_base = args.bib

    if not tex_file.exists():
        raise BuildError(f"Tex file not found: {tex_file}")

    # Ensure output directory exists
    outdir.mkdir(parents=True, exist_ok=True)

    # First pass (use -output-directory)
    cmd = [pdflatex_cmd, f"-interaction={interaction}", f"-output-directory={outdir}"]
    if file_line_error:
        cmd.append("-file-line-error")
    cmd.append(str(tex_file))
    code = run(cmd, cwd)
    if code != 0:
        raise BuildError("pdflatex first pass failed")

    # BibTeX (run in outdir against aux located there)
    # Ensure bib files are accessible: copy any referenced .bib files to outdir
    aux_path = outdir / tex_file.with_suffix('.aux').name
    if aux_path.exists():
        aux_text = aux_path.read_text(encoding="utf-8", errors="ignore")
        # Look for lines like: \bibdata{references} or \bibdata{src/latex/references}
        m = re.search(r"\\bibdata\{([^}]*)\}", aux_text)
        if m:
            biblist = [b.strip() for b in m.group(1).split(',') if b.strip()]
            for bibbase in biblist:
                # Accept absolute or relative bases, add .bib if missing
                if not bibbase.endswith('.bib'):
                    bibbase += '.bib'
                # Resolve from project root
                src_candidate = cwd / bibbase
                if not src_candidate.exists():
                    # Try relative to the main tex directory
                    src_candidate = tex_file.parent / bibbase
                if src_candidate.exists():
                    target = outdir / Path(bibbase).name
                    if not target.exists() or target.read_bytes() != src_candidate.read_bytes():
                        target.write_bytes(src_candidate.read_bytes())
                # else: leave to BIBINPUTS to find
    # Prepare env to help MiKTeX find bst/bib if still needed
    srcdir = tex_file.parent
    sep = ";" if os.name == "nt" else ":"
    child_env = os.environ.copy()
    child_env["BIBINPUTS"] = str(srcdir) + sep
    child_env["BSTINPUTS"] = str(srcdir) + sep
    code = run([bibtex_cmd, bib_base], outdir, env=child_env)
    if code != 0:
        raise BuildError("bibtex failed")

    # Final passes
    for i in range(final_passes):
        print(f"-- pdflatex final pass {i+1}/{final_passes} --")
        code = run(cmd, cwd)
        if code != 0:
            raise BuildError(f"pdflatex final pass {i+1} failed")

    pdf = outdir / tex_file.with_suffix('.pdf').name
    if not pdf.exists():
        raise BuildError("Build finished without producing PDF")

    size = pdf.stat().st_size
    print(f"✅ Built {pdf.name} ({size} bytes)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BuildError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
