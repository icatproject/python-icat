"""Implement 'test' command.

This module is imported by setup.py.  It implements the 'test' command
that may optionally be run after 'build' and before 'install'.
"""

import sys
import os.path
from distutils.core import Command
from distutils import log
from distutils.spawn import spawn


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


class runtests(Command):

    description = "\"test\" the distribution by running the tests"
    user_options = [
        ('build-lib=', 'd', "directory to \"build\" (copy) to"),
        ('skip-build', None,
         "skip rebuilding everything (for testing/debugging)"),
    ]
    boolean_options = ['skip-build']

    def initialize_options(self):
        self.build_lib = None
        self.skip_build = 0

    def finalize_options(self):
        self.set_undefined_options('build', ('build_lib', 'build_lib'))

    def run(self):
        self.run_command('check')
        if not self.skip_build:
            self.run_command('build_py')

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
        with tmpchdir("tests"):
            spawn([sys.executable, "-m", "pytest", "."])
