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
import distutils.dist
from distutils import log
from pathlib import Path
import string
try:
    import distutils_pytest
    cmdclass = distutils_pytest.cmdclass
except (ImportError, AttributeError):
    cmdclass = dict()
try:
    import gitprops
    release = str(gitprops.get_last_release())
    version = str(gitprops.get_version())
except (ImportError, LookupError):
    try:
        from _meta import release, version
    except ImportError:
        log.warn("warning: cannot determine version number")
        release = version = "UNKNOWN"

docstring = __doc__


# Enforcing of PEP 625 has been added in setuptools 69.3.0.  We don't
# want this, we want to keep control on the name of the sdist
# ourselves.  Disable it.
def _fixed_get_fullname(self):
    return "%s-%s" % (self.get_name(), self.get_version())

distutils.dist.DistributionMetadata.get_fullname = _fixed_get_fullname


class meta(setuptools.Command):

    description = "generate meta files"
    user_options = []
    meta_template = '''
release = "%(release)s"
version = "%(version)s"
'''

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        version = self.distribution.get_version()
        log.info("version: %s", version)
        values = {
            'release': release,
            'version': version,
        }
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
        destdir = Path("tests", "scripts")
        self.mkpath(str(destdir))
        scripts = []
        scripts += Path("doc", "examples").glob("*.py")
        scripts += (Path(s) for s in self.distribution.scripts)
        for script in scripts:
            dest = destdir / script.name
            self.copy_file(str(script), str(dest), preserve_mode=False)

    def copy_test_data(self):
        destdir = Path("tests", "data")
        self.mkpath(str(destdir))
        etc = Path("etc")
        doc = Path("doc")
        examples = doc / "examples"
        files = []
        files += ( examples / f
                   for f in ("example_data.yaml",
                             "ingest-datafiles.xml", "ingest-ds-params.xml",
                             "ingest-sample-ds.xml") )
        files += ( examples / ("icatdump-%s.%s" % (ver, ext))
                   for ver in ("4.4", "4.7", "4.10", "5.0")
                   for ext in ("xml", "yaml") )
        files += doc.glob("icatdata-*.xsd")
        files += examples.glob("metadata-*.xml")
        files += ( etc / f
                   for f in ("ingest-10.xsd", "ingest-11.xsd", "ingest.xslt") )
        for f in files:
            dest = destdir / f.name
            self.copy_file(str(f), str(dest), preserve_mode=False)


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
        for spec in Path().glob("*.spec"):
            with spec.open('rt') as inf:
                with Path(self.dist_dir, spec).open('wt') as outf:
                    outf.write(string.Template(inf.read()).substitute(subst))


class build_py(setuptools.command.build_py.build_py):
    def run(self):
        self.run_command('meta')
        super().run()
        package = self.distribution.packages[0].split('.')
        outfile = self.get_module_outfile(self.build_lib, package, "_meta")
        self.copy_file("_meta.py", outfile, preserve_mode=0)


# There are several forks of the original suds package around, most of
# them short-lived.  Two of them have been evaluated with python-icat
# and found to work: suds-jurko and the more recent suds-community.
# The latter has been renamed to suds.  We don't want to force to use
# one particular suds clone.  Therefore, we first try if (any clone
# of) suds is already installed and only add suds to install_requires
# if not.
requires = ["setuptools", "lxml", "packaging"]
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
    long_description_content_type = "text/x-rst",
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
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    project_urls = dict(
        Documentation="https://python-icat.readthedocs.io/",
        Source="https://github.com/icatproject/python-icat/",
        Download=("https://github.com/icatproject/python-icat/releases/%s/"
                  % release),
        Changes=("https://python-icat.readthedocs.io/en/stable"
                 "/changelog.html#changes-%s" % release.replace('.', '-')),
    ),
    packages = ["icat"],
    package_dir = {"": "src"},
    python_requires = ">=3.4",
    install_requires = requires,
    scripts = [
        "src/scripts/icatdump.py",
        "src/scripts/icatingest.py",
        "src/scripts/wipeicat.py"
    ],
    cmdclass = dict(cmdclass,
                    meta=meta,
                    build_py=build_py,
                    build_test=build_test,
                    sdist=sdist),
)
