"""pytest configuration.
"""

import datetime
import locale
import logging
import os
from pathlib import Path
from random import getrandbits
import re
import shutil
import subprocess
import sys
import tempfile
import zlib
import pytest
import icat
import icat.config
from icat.helper import Version
try:
    from suds.sax.date import UtcTimezone
except ImportError:
    UtcTimezone = None

# There are tests that depend on being able to read utf8-encoded text
# files, Issue #54.
os.environ["LANG"] = "en_US.UTF-8"
locale.setlocale(locale.LC_CTYPE, "en_US.UTF-8")

# Note that pytest captures stderr, so we won't see any logging by
# default.  But since Suds uses logging, it's better to still have
# a well defined basic logging configuration in place.
logging.basicConfig(level=logging.INFO)
# Newer pytest versions show the logs at level DEBUG in case of an
# error.  The problem is that suds is rather chatty, so it will
# clutter the output to an extent that we wont be able to see
# anything.  Silence it.
logging.getLogger('suds.client').setLevel(logging.CRITICAL)
logging.getLogger('suds').setLevel(logging.ERROR)

testdir = Path(__file__).resolve().parent


def _skip(reason):
    if Version(pytest.__version__) >= '3.3.0':
        pytest.skip(reason, allow_module_level=True)
    else:
        raise pytest.skip.Exception(reason, allow_module_level=True)


# ============================= helper ===============================

class DummyDatafile():
    """A dummy file with random content to be used for test upload.
    """
    def __init__(self, directory, name, size, date=None):
        if date is not None:
            date = (date, date)
        self.name = name
        self.fname = directory / name
        chunksize = 8192
        crc32 = 0
        with self.fname.open('wb') as f:
            while size > 0:
                if chunksize > size:
                    chunksize = size
                chunk = bytearray(getrandbits(8) for _ in range(chunksize))
                size -= chunksize
                crc32 = zlib.crc32(chunk, crc32)
                f.write(chunk)
        if date:
            os.utime(str(self.fname), date)
        self.crc32 = "%x" % (crc32 & 0xffffffff)
        self.stat = self.fname.stat()
        self.size = self.stat.st_size
        if UtcTimezone:
            mtime = int(self.stat.st_mtime)
            self.mtime = datetime.datetime.fromtimestamp(mtime, UtcTimezone())
        else:
            self.mtime = None


def getConfig(confSection="root", **confArgs):
    """Get the configuration, skip on ConfigError.
    """
    confFile = testdir / "data" / "icat.cfg"
    if not confFile.is_file():
        _skip("no test ICAT server configured")
    try:
        confArgs['args'] = ["-c", str(confFile), "-s", confSection]
        client, conf = icat.config.Config(**confArgs).getconfig()
        conf.cmdargs = ["-c", str(conf.configFile[0]), "-s", conf.configSection]
        return (client, conf)
    except icat.ConfigError as err:
        _skip(str(err))


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

class tmpClient:
    """A temporary client using an own configuration,
    such as login as another user.
    """
    def __init__(self, **confArgs):
        (self.client, self.conf) = getConfig(**confArgs)
    def __enter__(self):
        self.client.login(self.conf.auth, self.conf.credentials)
        return self.client
    def __exit__(self, type, value, tb):
        self.client.logout()


def gettestdata(fname):
    fname = testdir / "data" / fname
    assert fname.is_file()
    return fname


def get_icat_version():
    client, _ = getConfig(needlogin=False)
    ids_version = client.ids.apiversion if client.ids else Version("0.0")
    return client.apiversion, ids_version

# ICAT server version we talk to.  Ignore any errors from
# get_icat_version(), if something fails (e.g. no server is configured
# at all), set a dummy zero version number.
try:
    icat_version, ids_version = get_icat_version()
except:
    icat_version, ids_version = Version("0.0"), Version("0.0")

def require_icat_version(minversion, reason):
    if icat_version < minversion:
        _skip("need ICAT server version %s or newer: %s" % (minversion, reason))


def get_reference_dumpfile(ext = "yaml"):
    require_icat_version("4.4.0", "oldest available set of test data")
    if icat_version < "4.7":
        fname = "icatdump-4.4.%s" % ext
    elif icat_version < "4.10":
        fname = "icatdump-4.7.%s" % ext
    else:
        fname = "icatdump-4.10.%s" % ext
    return gettestdata(fname)


def callscript(scriptname, args, stdin=None, stdout=None, stderr=None):
    script = testdir / "scripts" / scriptname
    cmd = [sys.executable, str(script)] + args
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
    with infile.open('rt') as inf, outfile.open('wt') as outf:
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

@pytest.fixture(scope="session")
def tmpdirsec(request):
    tmpdir = tempfile.mkdtemp(prefix="python-icat-test-")
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture(scope="session")
def standardCmdArgs():
    _, conf = getConfig()
    return conf.cmdargs


@pytest.fixture(scope="session")
def setupicat(standardCmdArgs):
    testcontent = get_reference_dumpfile()
    callscript("wipeicat.py", standardCmdArgs)
    args = standardCmdArgs + ["-f", "YAML", "-i", str(testcontent)]
    callscript("icatingest.py", args)

# ============================= hooks ================================

def pytest_report_header(config):
    """Add information on the icat package used in the tests.
    """
    modpath = Path(icat.__file__).resolve().parent
    if icat_version > "0.0":
        icatserver = icat_version
    else:
        icatserver = "-"
    if ids_version > "0.0":
        idsserver = ids_version
    else:
        idsserver = "-"
    return [ "python-icat: %s" % (icat.__version__), 
             "             %s" % (modpath),
             "icat.server: %s, ids.server: %s" % (icatserver, idsserver)]

