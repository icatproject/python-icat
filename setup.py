#! /usr/bin/python

import sys
import os.path
from glob import glob
from distutils.core import  Command, setup
try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    # Python 2.x
    from distutils.command.build_py import build_py
try:
    import distutils_pytest
except ImportError:
    pass
import icatinfo
import re

if sys.version_info < (2, 6):
    raise RuntimeError("Sorry, this Python version (%s) is too old to use "
                       "this package." % sys.version)

DOCLINES         = icatinfo.__doc__.split("\n")
DESCRIPTION      = DOCLINES[0]
LONG_DESCRIPTION = "\n".join(DOCLINES[2:])
VERSION          = icatinfo.__version__
AUTHOR           = icatinfo.__author__
URL              = "http://icatproject.org/user-documentation/python-icat/"
m = re.match(r"^(.*?)\s*<(.*)>$", AUTHOR)
(AUTHOR_NAME, AUTHOR_EMAIL) = m.groups() if m else (AUTHOR, None)


class build_test(Command):
    """Copy all stuff needed for the tests (example scripts, test data)
    into the test directory.
    """
    description = "set up test environment"
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        self.copy_test_scripts()
        self.copy_test_data()

    def copy_test_scripts(self):
        destdir = os.path.join("tests", "scripts")
        self.mkpath(destdir)
        scripts = []
        scripts += glob(os.path.join("doc", "examples", "*.py"))
        scripts += self.distribution.scripts
        for script in scripts:
            dest = os.path.join(destdir, os.path.basename(script))
            self.copy_file(script, dest, preserve_mode=False)

    def copy_test_data(self):
        destdir = os.path.join("tests", "data")
        self.mkpath(destdir)
        files = ["example_data.yaml", "icatdump.xml", "icatdump.yaml", 
                 "ingest-datafiles.xml", "ingest-ds-params.xml"]
        for f in files:
            src = os.path.join("doc", "examples", f)
            dest = os.path.join(destdir, os.path.basename(f))
            self.copy_file(src, dest, preserve_mode=False)


setup(
    name = "python-icat",
    version = VERSION,
    description = DESCRIPTION,
    long_description = LONG_DESCRIPTION,
    author = AUTHOR_NAME,
    author_email = AUTHOR_EMAIL,
    url = URL,
    license = "Apache-2.0",
    requires = ["suds"],
    packages = ["icat"],
    scripts = ["icatdump.py", "icatingest.py"],
    # I never tested Python 3.0, any feedback welcome.  Python 3.*
    # requires the jurko fork of Suds.
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    cmdclass = {'build_py': build_py, 'build_test': build_test},
)

