# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) src

.PHONY: clean html latex latexpdf linkcheck doctest

clean:
	rm -rf doctrees html latex linkcheck doctest

html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) html

latex:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) latex

latexpdf:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) latex
	$(MAKE) -C latex all-pdf

linkcheck:
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) linkcheck

doctest:
	$(SPHINXBUILD) -b doctest $(ALLSPHINXOPTS) doctest
