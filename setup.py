#! /usr/bin/python
"""Python interface to ICAT and IDS

This package provides a collection of modules for writing Python
programs that access an `ICAT`_ service using the SOAP interface.  It
is based on Suds and extends it with ICAT specific features.

.. _ICAT: https://icatproject.org/
"""

from __future__ import print_function
try:
    from distutils.command.build_py import build_py_2to3 as du_build_py
except ImportError:
    # Python 2.x
    from distutils.command.build_py import build_py as du_build_py
import distutils.command.sdist
import distutils.core
from distutils.core import setup
import distutils.log
from glob import glob
import os
import os.path
import string
import sys
try:
    import distutils_pytest
except ImportError:
    pass
try:
    import setuptools_scm
    version = setuptools_scm.get_version()
    with open(".version", "wt") as f:
        f.write(version)
except (ImportError, LookupError):
    try:
        with open(".version", "rt") as f:
            version = f.read()
    except (OSError, IOError):
        distutils.log.warn("warning: cannot determine version number")
        version = "UNKNOWN"


if sys.version_info < (3, 4):
    distutils.log.warn("warning: support for Python versions older then 3.4 "
                       "is deprecated and will be removed in Version 1.0")


doclines = __doc__.strip().split("\n")


class init_py(distutils.core.Command):

    description = "generate the main __init__.py file"
    user_options = []
    init_template = '''"""%s"""

import sys
import warnings

if sys.version_info < (3, 4):
    warnings.warn("Support for Python versions older then 3.4 is deprecated  "
                  "and will be removed in python-icat 1.0", DeprecationWarning)

__version__ = "%s"

#
# Default import
#

from icat.client import *
from icat.exception import *
'''

    def initialize_options(self):
        self.package_dir = None

    def finalize_options(self):
        self.package_dir = {}
        if self.distribution.package_dir:
            for name, path in self.distribution.package_dir.items():
                self.package_dir[name] = convert_path(path)

    def run(self):
        try:
            pkgname = self.distribution.packages[0]
        except IndexError:
            distutils.log.warn("warning: no package defined")
        else:
            pkgdir = self.package_dir.get(pkgname, pkgname)
            ver = self.distribution.get_version()
            if not os.path.isdir(pkgdir):
                os.mkdir(pkgdir)
            with open(os.path.join(pkgdir, "__init__.py"), "wt") as f:
                print(self.init_template % (__doc__, ver), file=f)


class build_test(distutils.core.Command):
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
        refdumpfiles = ["icatdump-%s.%s" % (ver, ext)
                        for ver in ("4.4", "4.7", "4.10")
                        for ext in ("xml", "yaml")]
        files = ["example_data.yaml",
                 "ingest-datafiles.xml", "ingest-ds-params.xml"] + refdumpfiles
        for f in files:
            src = os.path.join("doc", "examples", f)
            dest = os.path.join(destdir, os.path.basename(f))
            self.copy_file(src, dest, preserve_mode=False)


class sdist(distutils.command.sdist.sdist):
    def run(self):
        self.run_command('init_py')
        distutils.command.sdist.sdist.run(self)
        subst = {
            "version": self.distribution.get_version(),
            "url": self.distribution.get_url(),
            "description": self.distribution.get_description(),
            "long_description": self.distribution.get_long_description(),
        }
        for spec in glob("*.spec"):
            with open(spec, "rt") as inf:
                with open(os.path.join(self.dist_dir, spec), "wt") as outf:
                    outf.write(string.Template(inf.read()).substitute(subst))


class build_py(du_build_py):
    def run(self):
        self.run_command('init_py')
        du_build_py.run(self)


setup(
    name = "python-icat",
    version = version,
    description = doclines[0],
    long_description = "\n".join(doclines[2:]),
    author = "Rolf Krahl",
    author_email = "rolf.krahl@helmholtz-berlin.de",
    url = "https://github.com/icatproject/python-icat",
    license = "Apache-2.0",
    requires = ["suds"],
    packages = ["icat"],
    scripts = ["icatdump.py", "icatingest.py", "wipeicat.py"],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    cmdclass = {
        'build_py': build_py,
        'build_test': build_test,
        'init_py': init_py,
        'sdist': sdist,
    },
)
