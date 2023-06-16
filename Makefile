PYTHON = python3


build:
	$(PYTHON) setup.py build

test:
	$(PYTHON) setup.py test

sdist: doc-man
	$(PYTHON) setup.py sdist

doc-html: meta
	$(MAKE) -C doc html PYTHONPATH=$(CURDIR)

doc-man: meta
	$(MAKE) -C doc man PYTHONPATH=$(CURDIR)

clean:
	rm -rf build
	rm -rf __pycache__
	rm -rf tests/data/example_data.yaml
	rm -rf tests/data/icatdump-* tests/data/ingest-*.xml
	rm -rf tests/data/ingest.xsd tests/data/ingest.xslt
	rm -rf tests/scripts

distclean: clean
	rm -f MANIFEST _meta.py
	rm -f icat/__init__.py
	rm -rf dist
	rm -rf tests/.pytest_cache
	$(MAKE) -C doc distclean

meta:
	$(PYTHON) setup.py meta


.PHONY: build test sdist doc-html doc-man clean distclean meta
