# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         = a4

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) src

html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) html

latex:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) latex

latexpdf: latex
	$(MAKE) -C latex all-pdf

linkcheck:
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) linkcheck

doctest:
	$(SPHINXBUILD) -b doctest $(ALLSPHINXOPTS) doctest

distclean:
	rm -rf doctrees html latex linkcheck doctest

.PHONY: html latex latexpdf linkcheck doctest distclean
