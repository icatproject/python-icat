PYTHON   = python


build: init.py
	$(PYTHON) setup.py build

test: init.py
	$(PYTHON) setup.py test

sdist: init.py doc-html
	$(PYTHON) setup.py sdist

init.py: icat/__init__.py

doc-html: init.py
	$(MAKE) -C doc html

doc-pdf: init.py
	$(MAKE) -C doc latexpdf


clean:
	rm -f *~ icat/*~ tests/*~ doc/*~ doc/examples/*~
	rm -rf build
	rm -rf tests/data/example_data.yaml
	rm -rf tests/data/icatdump.* tests/data/ingest-*.xml
	rm -rf tests/scripts

distclean: clean
	rm -rf tests/.cache
	rm -f MANIFEST
	rm -rf python_icat.egg-info
	rm -f *.pyc icat/*.pyc tests/*.pyc
	rm -rf __pycache__ icat/__pycache__ tests/__pycache__
	rm -f icat/__init__.py
	rm -rf dist
	$(MAKE) -C doc distclean


icat/__init__.py: icatinfo.py icatinit.py gitversion
	(cat icatinfo.py; \
	echo "__revision__  = \"`git describe --always --dirty`\""; \
	cat icatinit.py) > icat/__init__.py

# Dummy target to force icat/__init__.py
gitversion:


.PHONY: build test sdist init.py doc-html doc-pdf clean distclean gitversion
