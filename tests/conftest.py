"""pytest configuration.
"""

from __future__ import print_function
import sys
import os.path
import re
import subprocess
import shutil
import tempfile
import logging
import pytest
import icat
import icat.config


# Note that pytest captures stderr, so we won't see any logging by
# default.  But since Suds uses logging, it's better to still have
# a well defined basic logging configuration in place.
logging.basicConfig(level=logging.INFO)

testdir = os.path.dirname(__file__)


# ============================= helper ===============================

class tmpSessionId:
    """Temporarily switch to another sessionId in an ICAT client.
    """
    def __init__(self, client, sessionId):
        self.client = client
        self.saveSessionId = client.sessionId
        self.sessionId = sessionId
    def __enter__(self):
        self.client.sessionId = self.sessionId
        return self.client
    def __exit__(self, type, value, tb):
        self.client.sessionId = self.saveSessionId


def gettestdata(fname):
    fname = os.path.join(testdir, "data", fname)
    assert os.path.isfile(fname)
    return fname


def get_icat_version():
    fname = os.path.join(testdir, "data", "icat.cfg")
    args = ["-c", fname, "-s", "root"]
    conf = icat.config.Config(needlogin=False).getconfig(args)
    client = icat.Client(conf.url, **conf.client_kwargs)
    return client.apiversion

# ICAT server version we talk to.  Ignore any errors from
# get_icat_version(), if something fails (e.g. no server is configured
# at all), set a dummy zero version number.
try:
    icat_version = get_icat_version()
except:
    icat_version = "0"

def require_icat_version(minversion):
    if icat_version < minversion:
        pytest.skip("need ICAT server version %s or newer" % minversion)


def callscript(scriptname, args, stdin=None, stdout=None, stderr=None):
    script = os.path.join(testdir, "scripts", scriptname)
    cmd = [sys.executable, script] + args
    print("\n>", *cmd)
    subprocess.check_call(cmd, stdin=stdin, stdout=stdout, stderr=stderr)


def filter_yaml_dump(infile, outfile):
    """Strip the header information from a YAML dump file.

    We need this because we want to compare the content of dump
    files.  But the header information is supposed to change
    independently of the content.
    """
    substre = re.compile(r"^# (Date|Service|ICAT-API|Generator): .*$")
    with open(infile, 'rt') as inf:
        with open(outfile, 'wt') as outf:
            while True:
                l = inf.readline()
                if not l:
                    break
                l = re.sub(substre, r"# \1: ###", l)
                outf.write(l)


def filter_xml_dump(infile, outfile):
    """Strip the header information from a XML dump file.

    We need this because we want to compare the content of dump
    files.  But the header information is supposed to change
    independently of the content.
    """
    substre = re.compile(r"^\s*<(date|service|apiversion|generator)>.*</\1>$")
    with open(infile, 'rt') as inf:
        with open(outfile, 'wt') as outf:
            while True:
                l = inf.readline()
                if not l:
                    break
                l = re.sub(substre, r"  <\1>###</\1>", l)
                outf.write(l)


# ============================ fixtures ==============================

# Deliberately not using the 'tmpdir' fixture provided by pytest,
# because it seem to use a predictable directory name in /tmp wich is
# insecure.

class TmpDir(object):
    """Provide a temporary directory.
    """
    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="python-icat-test-")
    def __del__(self):
        self.cleanup()
    def cleanup(self):
        if self.dir:
            shutil.rmtree(self.dir)
        self.dir = None

@pytest.fixture(scope="session")
def tmpdirsec(request):
    tmpdir = TmpDir()
    request.addfinalizer(tmpdir.cleanup)
    return tmpdir


@pytest.fixture(scope="session")
def icatconfigfile():
    fname = os.path.join(testdir, "data", "icat.cfg")
    if not os.path.isfile(fname):
        pytest.skip("no test ICAT server configured")
    return fname


@pytest.fixture(scope="module")
def wipeicat(icatconfigfile):
    # wipeicat uses JPQL search syntax.
    require_icat_version("4.3.0")
    callscript("wipeicat.py", ["-c", icatconfigfile, "-s", "root"])


testcontent = gettestdata("icatdump.yaml")

@pytest.fixture(scope="module")
def setupicat(wipeicat, icatconfigfile):
    # testcontent has InvestigationGroup objects.
    require_icat_version("4.4.0")
    args = ["-c", icatconfigfile, "-s", "root", 
            "-f", "YAML", "-i", testcontent]
    callscript("icatrestore.py", args)


# ============================= hooks ================================

def pytest_report_header(config):
    """Add information on the icat package used in the tests.
    """
    modpath = os.path.dirname(os.path.abspath(icat.__file__))
    return [ "python-icat: %s (%s)" % (icat.__version__, icat.__revision__), 
             "             %s" % (modpath) ]
