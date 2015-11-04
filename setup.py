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
from distutils import log
from distutils.spawn import spawn
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


class tmpchdir:
    """Temporarily change the working directory.
    """
    def __init__(self, wdir):
        self.savedir = os.getcwd()
        self.wdir = wdir
    def __enter__(self):
        os.chdir(self.wdir)
        return os.getcwd()
    def __exit__(self, type, value, tb):
        os.chdir(self.savedir)


class test(Command):

    description = "run the tests"
    user_options = [
        ('build-lib=', 'd', "directory to \"build\" (copy) to"),
        ('skip-build', None,
         "skip rebuilding everything (for testing/debugging)"),
        ('test-args=', None, "extra arguments to pass to pytest"),
    ]
    boolean_options = ['skip-build']

    def initialize_options(self):
        self.build_lib = None
        self.skip_build = 0
        self.test_args = None

    def finalize_options(self):
        self.set_undefined_options('build', ('build_lib', 'build_lib'))

    def run(self):
        if not self.skip_build:
            self.run_command('build_py')

        self.copy_test_scripts()
        self.copy_test_data()

        # Add build_lib to the module search path to make sure the
        # built package can be imported by the tests.  Manipulate
        # both, sys.path to affect the current running Python, and
        # os.environ['PYTHONPATH'] to affect subprocesses spawned by
        # the tests.
        build_lib = os.path.abspath(self.build_lib)
        sys.path.insert(0,build_lib)
        try:
            # if PYTHONPATH is already set, prepend build_lib.
            os.environ['PYTHONPATH'] = "%s:%s" % (build_lib,
                                                  os.environ['PYTHONPATH'])
        except KeyError:
            # no, PYTHONPATH was not set.
            os.environ['PYTHONPATH'] = build_lib

        # Do not create byte code during test.
        sys.dont_write_bytecode = True
        os.environ['PYTHONDONTWRITEBYTECODE'] = "1"

        import icat
        log.info("Version: python-icat %s (%s)", 
                 icat.__version__, icat.__revision__)

        # Must change the directory, otherwise the icat package in the
        # cwd would override the one from build_lib.  Alas, there seem
        # to be no way to tell Python not to put the cwd in front of
        # $PYTHONPATH in sys.path.
        testcmd = [sys.executable, "-m", "pytest"]
        if self.test_args:
            testcmd.extend(self.test_args.split())
        if self.dry_run:
            testcmd.append("--collect-only")
        with tmpchdir("tests"):
            spawn(testcmd)

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
    license = "BSD-2-Clause",
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
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    cmdclass = {'build_py': build_py, 'test': test},
)

