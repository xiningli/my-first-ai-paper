# Small AI Paper Sample (LaTeX + BibTeX)

This is a minimal academic paper template for AI research, set up with LaTeX and BibTeX. It includes common sections and seminal citations.

## Contents
- `main.tex`: Entry point; includes sections and bibliography
- `sections/`: Introduction, Related Work, Method, Experiments, Conclusion
- `references.bib`: Sample BibTeX entries (Perceptron, Backprop, LeNet, AlexNet, Transformer, BERT, GPT-3)
- `.gitignore`: Ignore LaTeX build artifacts and `.vscode`
- `latexmkrc`: Config for `latexmk` build

## Build (Windows PowerShell)
Prerequisites:

 Quick compile with latexmk (recommended):
```powershell
latexmk -pdf -interaction=nonstopmode main.tex
```
Artifacts will be in the project root; output `main.pdf` is git-ignored by default. To commit PDFs, remove `*.pdf` from `.gitignore`.

Clean build artifacts:
```powershell
latexmk -C
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

2) Build with Python:

```
python build_latex.py --env latex.env --tex main.tex --bib main
```

Flags:
- `--passes N` to change final pdflatex passes (default 2)
- `--interaction=nonstopmode|batchmode|scrollmode|errorstopmode`
- `--no-file-line-error` to disable `-file-line-error`

The script runs: pdflatex → bibtex → pdflatex ×2 and emits clear logs. It exits non-zero on failure.
## Citing
Use `\citep{key}` for parenthetical citations and `\citet{key}` for textual citations (natbib). Add new entries in `references.bib`.

## Customize
- Update `\author{}`, `\title{}`, and date in `main.tex`
- Add figures under a `figures/` folder and include with `\includegraphics{}`
- Switch bibliography style by editing `\bibliographystyle{}`

## License
MIT — see `LICENSE`.
