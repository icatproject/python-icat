#! /usr/bin/python

import sys
from distutils.core import setup
try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    # Python 2.x
    from distutils.command.build_py import build_py
import icat
import re

if sys.version_info < (2, 6):
    raise RuntimeError("Sorry, this Python version (%s) is too old to use "
                       "this package." % sys.version)

DOCLINES         = icat.__doc__.split("\n")
DESCRIPTION      = DOCLINES[0]
LONG_DESCRIPTION = "\n".join(DOCLINES[2:])
VERSION          = icat.__version__
AUTHOR           = icat.__author__
URL              = "http://code.google.com/p/icatproject/wiki/PythonIcat"
m = re.match(r"^(.*?)\s*<(.*)>$", AUTHOR)
(AUTHOR_NAME, AUTHOR_EMAIL) = m.groups() if m else (AUTHOR, None)

setup(
    name = "python-icat",
    version = VERSION,
    description = DESCRIPTION,
    long_description = LONG_DESCRIPTION,
    author = AUTHOR_NAME,
    author_email = AUTHOR_EMAIL,
    url = URL,
    license = "BSD-2-Clause",
    requires = ["suds"],
    packages = ["icat"],
    # Minimum required Python version is 2.6.  Python 3.* should work,
    # I guess, but I only tested 3.2.  Python 3 requires the jurko
    # fork of Suds.
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    cmdclass = {'build_py': build_py},
)

