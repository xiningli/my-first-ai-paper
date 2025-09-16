# Small AI Paper Sample (LaTeX + BibTeX)

This is a minimal academic paper template for AI research, set up with LaTeX and BibTeX. It includes common sections and seminal citations.

## Contents
- `src/latex/`: LaTeX sources (canonical entry: `src/latex/main.tex`)
	- `sections/`: Introduction, Related Work, Method, Experiments, Conclusion
	- `figures/`: Generated figures (e.g., `simple_plot.png`)
	- `references.bib`: Sample BibTeX entries
- `src/python/`: helper scripts and Python deps
	- `generate_plot.py`: generates `src/latex/figures/simple_plot.png`
	- `requirements.txt`: Python dependencies (matplotlib, numpy)
- `out/` (generated): build artifacts and final PDF (git-ignored)
- `.gitattributes`, `.editorconfig`: LF + UTF-8 normalization
- `src/latex/latexmkrc`: Config for `latexmk` build (outputs to `out/`)

## Line endings and encoding
This project standardizes on:
- Line endings: LF (Unix) via `.gitattributes` and `.editorconfig`
- Encoding: UTF-8

On Windows, Git will normalize line endings to LF in the repo automatically. If you previously committed files with CRLF, you can re-normalize:

```powershell
git rm --cached -r .
git reset --hard
```

## Build outputs go to `out/`
We keep sources clean and send all LaTeX build artifacts to `out/` (aux files in `out/aux`).

Tools configured to use `out/`:
- `latexmk` via `latexmkrc`
- `build_latex.py` via `OUTDIR` in `latex.env` (default `out`)

## Build (Windows PowerShell)

Quick compile with latexmk (recommended):
```powershell
latexmk -pdf -interaction=nonstopmode src/latex/main.tex
```
Artifacts will be in `out/`; final PDF is `out/main.pdf`.

Clean build artifacts:
```powershell
latexmk -C
Remove-Item -Recurse -Force .\out -ErrorAction SilentlyContinue
```

## Cross-platform Python build (recommended)

This repo includes a reusable Python script that reads `src/latex/latex.env` to locate tools across OSes.

1) Configure tools in `src/latex/latex.env` (already prefilled for your machine on Windows/MiKTeX):

```
PDFLATEX=C:\\Users\\<you>\\AppData\\Local\\Programs\\MiKTeX\\miktex\\bin\\x64\\pdflatex.exe
BIBTEX=C:\\Users\\<you>\\AppData\\Local\\Programs\\MiKTeX\\miktex\\bin\\x64\\bibtex.exe
```

On macOS/Linux, you can just set:

```
PDFLATEX=pdflatex
BIBTEX=bibtex
```

2) Build with Python (outputs to `out/`):

```
python build_latex.py --env src/latex/latex.env --tex src/latex/main.tex --bib main
```

Flags:
- `--passes N` to change final pdflatex passes (default 2)
- `--interaction=nonstopmode|batchmode|scrollmode|errorstopmode`
- `--no-file-line-error` to disable `-file-line-error`

The script runs: pdflatex → bibtex → pdflatex ×2 and emits clear logs. It exits non-zero on failure. Final PDF: `out/main.pdf`.

## Poetry (recommended, Maven-like)

Use Poetry for dependency management and an in-project virtual environment (like Maven for Java):

1) Install Poetry (Windows PowerShell):
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
$env:Path = "$env:APPDATA\Python\Scripts;$env:LOCALAPPDATA\pypoetry\Cache\Scripts;$env:Path"
poetry --version
```

2) Configure Poetry to create venv in the project and install deps:
```powershell
poetry config virtualenvs.in-project true
poetry install
```

3) Generate the plot and build the PDF:
```powershell
poetry run python src/python/generate_plot.py
poetry run python build_latex.py --env src/latex/latex.env --tex src/latex/main.tex --bib main
```

VS Code tasks provided:
- `poetry: ensure in-project venv` → `poetry: install` → `poetry: plot` → `poetry: build pdf`

### Alternative: plain venv + pip

If you prefer not to install Poetry, you can still use a local venv:

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install matplotlib numpy
python src/python/generate_plot.py
python build_latex.py --env src/latex/latex.env --tex src/latex/main.tex --bib main
```

The generated figure `src/latex/figures/simple_plot.png` is included by `src/latex/main.tex`.
## Citing
Use `\citep{key}` for parenthetical citations and `\citet{key}` for textual citations (natbib). Add new entries in `references.bib`.

## Customize
- Update `\author{}`, `\title{}`, and date in `src/latex/main.tex`
- Add figures under `src/latex/figures/` and include with `\includegraphics{}`
- Switch bibliography style by editing `\bibliographystyle{}`

## License
MIT — see `LICENSE`.