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
- Install TeX distribution (MiKTeX or TeX Live)
- Optional: VS Code + LaTeX Workshop extension

Quick compile with latexmk (recommended):
```powershell
latexmk -pdf -interaction=nonstopmode main.tex
```
Artifacts will be in the project root; output `main.pdf` is git-ignored by default. To commit PDFs, remove `*.pdf` from `.gitignore`.

Clean build artifacts:
```powershell
latexmk -C
```

## Citing
Use `\citep{key}` for parenthetical citations and `\citet{key}` for textual citations (natbib). Add new entries in `references.bib`.

## Customize
- Update `\author{}`, `\title{}`, and date in `main.tex`
- Add figures under a `figures/` folder and include with `\includegraphics{}`
- Switch bibliography style by editing `\bibliographystyle{}`

## License
MIT — see `LICENSE`.
