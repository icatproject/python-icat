PYTHON = python3


build:
	$(PYTHON) setup.py build

test:
	$(PYTHON) setup.py test

sdist: doc-html
	$(PYTHON) setup.py sdist

doc-html: init_py
	$(MAKE) -C doc html


clean:
	rm -f *~ icat/*~ tests/*~ doc/*~ doc/examples/*~
	rm -rf build
	rm -rf tests/data/example_data.yaml
	rm -rf tests/data/icatdump.* tests/data/ingest-*.xml
	rm -rf tests/scripts

distclean: clean
	rm -rf tests/.cache
	rm -f MANIFEST .version
	rm -rf python_icat.egg-info
	rm -f *.pyc icat/*.pyc tests/*.pyc
	rm -rf __pycache__ icat/__pycache__ tests/__pycache__
	rm -f icat/__init__.py
	rm -rf dist
	$(MAKE) -C doc distclean


init_py:
	$(PYTHON) setup.py init_py


.PHONY: build test sdist doc-html clean distclean init_py
