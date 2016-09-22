"""pytest configuration.
"""

from __future__ import print_function
import sys
import os.path
import datetime
import re
from random import getrandbits
import zlib
import subprocess
import shutil
import tempfile
import logging
from distutils.version import StrictVersion as Version
import pytest
import icat
import icat.config
try:
    from suds.sax.date import UtcTimezone
except ImportError:
    UtcTimezone = None


# Note that pytest captures stderr, so we won't see any logging by
# default.  But since Suds uses logging, it's better to still have
# a well defined basic logging configuration in place.
logging.basicConfig(level=logging.INFO)

testdir = os.path.dirname(__file__)


# ============================= helper ===============================

if sys.version_info < (3, 0):
    def buf(seq):
        return buffer(bytearray(seq))
else:
    def buf(seq):
        return bytearray(seq)

class DummyDatafile(object):
    """A dummy file with random content to be used for test upload.
    """
    def __init__(self, directory, name, size, date=None):
        if date is not None:
            date = (date, date)
        self.name = name
        self.fname = os.path.join(directory, name)
        chunksize = 8192
        crc32 = 0
        with open(self.fname, 'wb') as f:
            while size > 0:
                if chunksize > size:
                    chunksize = size
                chunk = buf(getrandbits(8) for _ in range(chunksize))
                size -= chunksize
                crc32 = zlib.crc32(chunk, crc32)
                f.write(chunk)
        if date:
            os.utime(self.fname, date)
        self.crc32 = "%x" % (crc32 & 0xffffffff)
        self.stat = os.stat(self.fname)
        self.size = self.stat.st_size
        if UtcTimezone:
            mtime = int(self.stat.st_mtime)
            self.mtime = datetime.datetime.fromtimestamp(mtime, UtcTimezone())
        else:
            self.mtime = None

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

class tmpLogin:
    """Temporarily login as another user in an ICAT client.
    """
    def __init__(self, client, auth, credentials):
        self.client = client
        self.saveSessionId = client.sessionId
        self.auth = auth
        self.credentials = credentials
    def __enter__(self):
        self.client.sessionId = None
        self.client.login(self.auth, self.credentials)
        return self.client
    def __exit__(self, type, value, tb):
        self.client.logout()
        self.client.sessionId = self.saveSessionId


def gettestdata(fname):
    fname = os.path.join(testdir, "data", fname)
    assert os.path.isfile(fname)
    return fname


def getConfig(confSection="root", **confArgs):
    """Get the configuration, skip on ConfigError.
    """
    confFile = os.path.join(testdir, "data", "icat.cfg")
    if not os.path.isfile(confFile):
        pytest.skip("no test ICAT server configured")
    try:
        args = ["-c", confFile, "-s", confSection]
        conf = icat.config.Config(**confArgs).getconfig(args)
        conf.cmdargs = ["-c", conf.configFile[0], "-s", conf.configSection]
        return conf
    except icat.ConfigError as err:
        pytest.skip(err.message)


def get_icat_version():
    conf = getConfig(needlogin=False)
    client = icat.Client(conf.url, **conf.client_kwargs)
    return client.apiversion

# ICAT server version we talk to.  Ignore any errors from
# get_icat_version(), if something fails (e.g. no server is configured
# at all), set a dummy zero version number.
try:
    icat_version = get_icat_version()
except:
    icat_version = Version("0.0")

def require_icat_version(minversion, reason):
    if icat_version < minversion:
        pytest.skip("need ICAT server version %s or newer: %s" 
                    % (minversion, reason))


def callscript(scriptname, args, stdin=None, stdout=None, stderr=None):
    script = os.path.join(testdir, "scripts", scriptname)
    cmd = [sys.executable, script] + args
    print("\n>", *cmd)
    subprocess.check_call(cmd, stdin=stdin, stdout=stdout, stderr=stderr)


yaml_filter = (re.compile(r"^# (Date|Service|ICAT-API|Generator): .*$"),
               r"# \1: ###")
xml_filter = (re.compile(r"^\s*<(date|service|apiversion|generator)>.*</\1>$"),
              r"  <\1>###</\1>")

def filter_file(infile, outfile, pattern, repl):
    """Filter a text file.

    This may be needed to compare some test output file with
    predefined results, because some information in the file might not
    depend on the actual test but rather dynamically change with each
    call.  Such as the header of a dump file that contains date and
    ICAT version.
    """
    with open(infile, 'rt') as inf, open(outfile, 'wt') as outf:
        while True:
            l = inf.readline()
            if not l:
                break
            l = re.sub(pattern, repl, l)
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
def standardConfig():
    return getConfig()


testcontent = gettestdata("icatdump.yaml")

@pytest.fixture(scope="session")
def setupicat(standardConfig):
    require_icat_version("4.4.0", "need InvestigationGroup")
    callscript("wipeicat.py", standardConfig.cmdargs)
    args = standardConfig.cmdargs + ["-f", "YAML", "-i", testcontent]
    callscript("icatingest.py", args)


# ============================= hooks ================================

class DependencyItemStatus(object):
    """Status of a test item in a dependency manager.
    """

    Phases = ('setup', 'call', 'teardown')

    def __init__(self):
        self.results = { w:None for w in self.Phases }

    def __str__(self):
        l = ["%s: %s" % (w, self.results[w]) for w in self.Phases]
        return "Status(%s)" % ", ".join(l)

    def addResult(self, rep):
        self.results[rep.when] = rep.outcome

    def isSuccess(self):
        return list(self.results.values()) == ['passed', 'passed', 'passed']

class DependencyManager(object):
    """Dependency manager, stores the results of tests.
    """

    ScopeCls = {'module':pytest.Module, 'session':pytest.Session}

    @classmethod
    def getManager(cls, item, scope='module'):
        """Get the DependencyManager object from the node at scope level.
        Create it, if not yet present.
        """
        node = item.getparent(cls.ScopeCls[scope])
        if not hasattr(node, 'dependencyManager'):
            node.dependencyManager = cls()
        return node.dependencyManager

    def __init__(self):
        self.results = {}

    def addResult(self, item, marker, rep):
        name = marker.kwargs.get('name')
        if not name:
            name = item.name
        status = self.results.setdefault(name, DependencyItemStatus())
        status.addResult(rep)

    def checkDepend(self, depends):
        for i in depends:
            if not(i in self.results and self.results[i].isSuccess()):
                pytest.skip("depends on %s" % i)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store the test outcome if this item is marked "dependency".
    """
    outcome = yield
    marker = item.get_marker("dependency")
    if marker is not None:
        rep = outcome.get_result()
        manager = DependencyManager.getManager(item)
        manager.addResult(item, marker, rep)


def pytest_runtest_setup(item):
    """Check dependencies if this item is marked "dependency".
    Skip if any of the dependencies has not been run successfully.
    """
    marker = item.get_marker("dependency")
    if marker is not None:
        depends = marker.kwargs.get('depends')
        if depends:
            manager = DependencyManager.getManager(item)
            manager.checkDepend(depends)


def require_servertest():
    if not pytest.config.getoption("--servertests"):
        pytest.skip("need --servertests option to run")

def pytest_addoption(parser):
    parser.addoption("--servertests", action="store_true",
                     help="run tests for testing the server.")


def pytest_report_header(config):
    """Add information on the icat package used in the tests.
    """
    modpath = os.path.dirname(os.path.abspath(icat.__file__))
    if icat_version > "0.0":
        server = icat_version
    else:
        server = "-"
    return [ "python-icat: %s (%s)" % (icat.__version__, icat.__revision__), 
             "             %s" % (modpath),
             "icat.server: %s" % server]
