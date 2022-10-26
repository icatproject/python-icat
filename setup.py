#! /usr/bin/python
"""Python interface to ICAT and IDS

This package provides a collection of modules for writing Python
programs that access an `ICAT`_ service using the SOAP interface.  It
is based on Suds and extends it with ICAT specific features.

.. _ICAT: https://icatproject.org/
"""

import setuptools
from setuptools import setup
import setuptools.command.build_py
import distutils.command.sdist
from distutils import log
from glob import glob
import os
import os.path
from pathlib import Path
import string
import sys
try:
    import distutils_pytest
    cmdclass = distutils_pytest.cmdclass
except (ImportError, AttributeError):
    cmdclass = dict()
try:
    import setuptools_scm
    version = setuptools_scm.get_version()
except (ImportError, LookupError):
    try:
        import _meta
        version = _meta.__version__
    except ImportError:
        log.warn("warning: cannot determine version number")
        version = "UNKNOWN"


if sys.version_info < (3, 4):
    log.warn("warning: Python %d.%d is not supported! "
             "This package requires Python 3.4 or newer."
             % sys.version_info[:2])


docstring = __doc__


class meta(setuptools.Command):

    description = "generate meta files"
    user_options = []
    init_template = '''"""%(doc)s"""

__version__ = "%(version)s"

#
# Default import
#

from icat.client import *
from icat.exception import *
'''
    meta_template = '''
__version__ = "%(version)s"
'''

    def initialize_options(self):
        self.package_dir = None

    def finalize_options(self):
        self.package_dir = {}
        if self.distribution.package_dir:
            for name, path in self.distribution.package_dir.items():
                self.package_dir[name] = convert_path(path)

    def run(self):
        values = {
            'version': self.distribution.get_version(),
            'doc': docstring
        }
        try:
            pkgname = self.distribution.packages[0]
        except IndexError:
            log.warn("warning: no package defined")
        else:
            pkgdir = Path(self.package_dir.get(pkgname, pkgname))
            if not pkgdir.is_dir():
                pkgdir.mkdir()
            with (pkgdir / "__init__.py").open("wt") as f:
                print(self.init_template % values, file=f)
        with Path("_meta.py").open("wt") as f:
            print(self.meta_template % values, file=f)


class build_test(setuptools.Command):
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
                        for ver in ("4.4", "4.7", "4.10", "5.0")
                        for ext in ("xml", "yaml")]
        files = ["example_data.yaml",
                 "ingest-datafiles.xml", "ingest-ds-params.xml"] + refdumpfiles
        for f in files:
            src = os.path.join("doc", "examples", f)
            dest = os.path.join(destdir, os.path.basename(f))
            self.copy_file(src, dest, preserve_mode=False)


# Note: Do not use setuptools for making the source distribution,
# rather use the good old distutils instead.
# Rationale: https://rhodesmill.org/brandon/2009/eby-magic/
class sdist(distutils.command.sdist.sdist):
    def run(self):
        self.run_command('meta')
        super().run()
        subst = {
            "version": self.distribution.get_version(),
            "url": self.distribution.get_url(),
            "description": docstring.split("\n")[0],
            "long_description": docstring.split("\n", maxsplit=2)[2].strip(),
        }
        for spec in glob("*.spec"):
            with Path(spec).open('rt') as inf:
                with Path(self.dist_dir, spec).open('wt') as outf:
                    outf.write(string.Template(inf.read()).substitute(subst))


class build_py(setuptools.command.build_py.build_py):
    def run(self):
        self.run_command('meta')
        super().run()


# There are several forks of the original suds package around, most of
# them short-lived.  Two of them have been evaluated with python-icat
# and found to work: suds-jurko and the more recent suds-community.
# The latter has been renamed to suds.  We don't want to force to use
# one particular suds clone.  Therefore, we first try if (any clone
# of) suds is already installed and only add suds to install_requires
# if not.
requires = ["packaging"]
try:
    import suds
except ImportError:
    requires.append("suds")

with Path("README.rst").open("rt", encoding="utf8") as f:
    readme = f.read()

setup(
    name = "python-icat",
    version = version,
    description = docstring.split("\n")[0],
    long_description = readme,
    url = "https://github.com/icatproject/python-icat",
    author = "Rolf Krahl",
    author_email = "rolf.krahl@helmholtz-berlin.de",
    license = "Apache-2.0",
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages = ["icat"],
    python_requires = ">=3.4",
    install_requires = requires,
    scripts = ["icatdump.py", "icatingest.py", "wipeicat.py"],
    cmdclass = dict(cmdclass,
                    meta=meta,
                    build_py=build_py,
                    build_test=build_test,
                    sdist=sdist),
)
