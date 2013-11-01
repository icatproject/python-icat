# Add hoc quick and dirty solution to prepare a source distribution.
# Should find the proper way to do this using the various versions of
# Python Distutils.

APIDOC_DIR        = doc/api
EXAMPLE_DIR       = doc/examples
EXAMPLE_FILES     = getversion.py login.py init-icat.py			\
		    create-investigation.py create-sampletype.py	\
		    add-investigation-data.py ldapsync.py		\
		    create-parametertypes.py check.py
EXAMPLE_CGI_DIR   = $(EXAMPLE_DIR)/cgi
EXAMPLE_CGI_FILES = cgi/login.py cgi/logout.py cgi/session-status.py	\
		    cgi/instruments.py cgi/setcookie.py

sdist: sdist_prepare
	./setup.py sdist

sdist_prepare:
	rm -rf $(APIDOC_DIR)
	epydoc --html --output=$(APIDOC_DIR) icat
	mkdir -p $(EXAMPLE_DIR)
	cp -p $(EXAMPLE_FILES) $(EXAMPLE_DIR)
	mkdir -p $(EXAMPLE_CGI_DIR)
	cp -p $(EXAMPLE_CGI_FILES) $(EXAMPLE_CGI_DIR)
