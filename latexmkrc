# latexmk configuration for this project
$pdf_mode = 1;          # pdflatex
$interaction = 'nonstopmode';
$bibtex_use = 2;        # use bibtex automatically when needed
$pdflatex = 'pdflatex -synctex=1 -interaction=nonstopmode %O %S';
$bibtex = 'bibtex %O %B';
@default_files = ('src/latex/main.tex');
 
 # Place all outputs under ./out/ to separate src and build artifacts
 $out_dir = 'out';
 $aux_dir = 'out/aux';
 
 # Ensure directories exist before running
 add_cus_dep('','ensure_dirs',0,'do_nothing');
 sub do_nothing {}
