#! /usr/bin/python

import os
from distutils.core import setup
import icat
import re

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
)

