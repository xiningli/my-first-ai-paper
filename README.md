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
- `latexmkrc`: Config for `latexmk` build (outputs to `out/`)

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

This repo includes a reusable Python script that reads `latex.env` to locate tools across OSes.

1) Configure tools in `latex.env` (already prefilled for your machine on Windows/MiKTeX):

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
python build_latex.py --env latex.env --tex src/latex/main.tex --bib main
```

Flags:
- `--passes N` to change final pdflatex passes (default 2)
- `--interaction=nonstopmode|batchmode|scrollmode|errorstopmode`
- `--no-file-line-error` to disable `-file-line-error`

The script runs: pdflatex → bibtex → pdflatex ×2 and emits clear logs. It exits non-zero on failure. Final PDF: `out/main.pdf`.

## Generate the example figure

Install Python dependencies and generate the plot image:

```powershell
pip install -r src/python/requirements.txt
python src/python/generate_plot.py
```

This writes `src/latex/figures/simple_plot.png`, which is included by `src/latex/main.tex`.
## Citing
Use `\citep{key}` for parenthetical citations and `\citet{key}` for textual citations (natbib). Add new entries in `references.bib`.

## Customize
- Update `\author{}`, `\title{}`, and date in `src/latex/main.tex`
- Add figures under `src/latex/figures/` and include with `\includegraphics{}`
- Switch bibliography style by editing `\bibliographystyle{}`

## License
MIT — see `LICENSE`.