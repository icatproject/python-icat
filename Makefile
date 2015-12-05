PYTHON   = python


sdist: init.py python2_6.patch doc-html
	$(PYTHON) setup.py sdist

init.py: icat/__init__.py

doc-html: init.py
	$(MAKE) -C doc html

doc-pdf: init.py
	$(MAKE) -C doc latexpdf

test: init.py
	$(PYTHON) setup.py test


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
	rm -f python2_6.patch
	rm -rf dist
	$(MAKE) -C doc distclean


icat/__init__.py: icatinfo.py icatinit.py gitversion
	(sed -e '/__copyright__/ r COPYING' icatinfo.py; \
	echo "__revision__  = \"`git describe --always --dirty`\""; \
	cat icatinit.py) > icat/__init__.py

# Dummy target to force icat/__init__.py
gitversion:

python2_6.patch:
	git diff `git merge-base master python2_6` python2_6 > $@


.PHONY: sdist init.py doc-html doc-pdf test clean distclean gitversion
