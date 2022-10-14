all: build

build:
	latexmk -synctex=1 -interaction=nonstopmode -file-line-error -pdf observe.tex

clean:
	rm -f *.aux *.bbl *.bcf *.blg *.fdb_latexmk *.fls *.log *.notes *.out *.pdf *.run.xml *.toc parts/*.aux common/*.aux
