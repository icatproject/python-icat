
PYTHON = python

DOCTESTS     = icat/helper.doctest icat/listproxy.doctest

APIDOC_DIR   = doc/api

sdist: init.py python2_6.patch apidoc
	$(PYTHON) setup.py sdist

init.py: icat/__init__.py

apidoc: apidoc_clean init.py
	epydoc --html --docformat=restructuredtext --output=$(APIDOC_DIR) icat


test: init.py
	$(PYTHON) setup.py test

doctest: $(DOCTESTS)


clean:
	rm -f *~ icat/*~ tests/*~ doc/*~ doc/examples/*~
	rm -rf build
	rm -rf tests/data/example_data.yaml tests/data/icatdump.*
	rm -rf tests/scripts

apidoc_clean:
	rm -rf $(APIDOC_DIR)

distclean: apidoc_clean clean
	rm -f MANIFEST
	rm -rf python_icat.egg-info
	rm -f *.pyc icat/*.pyc tests/*.pyc
	rm -rf __pycache__ icat/__pycache__ tests/__pycache__
	rm -f icat/__init__.py
	rm -f python2_6.patch
	rm -rf dist


icat/__init__.py: icatinfo.py icatinit.py gitversion
	(sed -e '/__copyright__/ r COPYING' icatinfo.py; \
	echo "__revision__  = \"`git describe --always --dirty`\""; \
	cat icatinit.py) > icat/__init__.py

# Dummy target to force icat/__init__.py
gitversion:

python2_6.patch:
	git diff master python2_6 > $@


%.doctest: %.py
	$(PYTHON) -m doctest $<


.PHONY: sdist init.py apidoc test doctest \
	clean apidoc_clean distclean gitversion
