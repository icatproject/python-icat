# Add hoc quick and dirty solution to prepare a source distribution.
# Should find the proper way to do this using the various versions of
# Python Distutils.

APIDOC_DIR        = doc/api
EXAMPLE_DIR       = doc/examples
EXAMPLE_FILES     = getversion.py login.py init-icat.py			\
		    create-investigation.py create-sampletype.py	\
		    add-investigation-data.py addfile.py add-job.py	\
		    downloaddata.py ldapsync.py				\
		    create-parametertypes.py check.py icatsummary.py	\
		    wipeicat.py

EXAMPLE_CGI_DIR   = $(EXAMPLE_DIR)/cgi
EXAMPLE_CGI_FILES = cgi/login.py cgi/logout.py cgi/session-status.py	\
		    cgi/instruments.py cgi/setcookie.py

sdist: sdist_prepare
	./setup.py sdist

clean:
	rm -f *~ icat/*~
	rm -rf build

distclean: apidoc_clean example_clean clean
	rm -f MANIFEST
	rm -rf python_icat.egg-info
	rm -f *.pyc icat/*.pyc
	rm -rf __pycache__ icat/__pycache__
	rm -f icat/__init__.py
	rm -rf dist

sdist_prepare: icat/__init__.py apidoc copy_examples

icat/__init__.py: icatinfo.py icatinit.py svnversion
	(cat icatinfo.py; \
	echo "__revision__  = \"`svnversion`\""; \
	cat icatinit.py) > icat/__init__.py

# Dummy target to force icat/__init__.py
svnversion:

apidoc: apidoc_clean
	epydoc --html --docformat=restructuredtext --output=$(APIDOC_DIR) icat

apidoc_clean:
	rm -rf $(APIDOC_DIR)

copy_examples:
	cp -p $(EXAMPLE_FILES) $(EXAMPLE_DIR)
	cp -p $(EXAMPLE_CGI_FILES) $(EXAMPLE_CGI_DIR)

example_clean:
	(cd $(EXAMPLE_DIR); rm -f $(EXAMPLE_FILES) $(EXAMPLE_CGI_FILES))
