# latexmk configuration for this project
$pdf_mode = 1;          # pdflatex
$interaction = 'nonstopmode';
$bibtex_use = 2;        # use bibtex automatically when needed
$pdflatex = 'pdflatex -synctex=1 -interaction=nonstopmode %O %S';
$bibtex = 'bibtex %O %B';
@default_files = ('main.tex');
