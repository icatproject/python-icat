PYTHON = python3


build:
	$(PYTHON) setup.py build

test:
	$(PYTHON) setup.py test

sdist: doc-man
	$(PYTHON) setup.py sdist

doc-html: build
	$(MAKE) -C doc html

doc-man: build
	$(MAKE) -C doc man

clean:
	rm -rf build
	rm -rf __pycache__
	rm -rf tests/data/example_data.yaml
	rm -rf tests/data/icatdata-*.xsd
	rm -rf tests/data/icatdump-* tests/data/ingest-*.xml
	rm -rf tests/data/ingest-*.xsd tests/data/ingest.xslt
	rm -rf tests/data/metadata-*-inl.xml tests/data/metadata-*-sep.xml
	rm -rf tests/data/metadata-sample.xml
	rm -rf tests/scripts

distclean: clean
	rm -f MANIFEST _meta.py
	rm -rf dist
	rm -rf tests/.pytest_cache
	$(MAKE) -C doc distclean

meta:
	$(PYTHON) setup.py meta


.PHONY: build test sdist doc-html doc-man clean distclean meta
