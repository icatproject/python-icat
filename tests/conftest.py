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
import icat.dumpfile
from icat.query import Query
try:
    import icat.dumpfile_xml
except ImportError:
    pass
try:
    import icat.dumpfile_yaml
except ImportError:
    pass
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
testdatadir = testdir / "data"

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
    confFile = testdatadir / "icat.cfg"
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
    fname = testdatadir / fname
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

def require_dumpfile_backend(backend):
    if backend not in icat.dumpfile.Backends.keys():
        _skip("need %s backend for icat.dumpfile" % (backend))


def get_icatdata_schema():
    if icat_version < "4.4":
        fname = "icatdata-4.3.xsd"
    elif icat_version < "4.7":
        fname = "icatdata-4.4.xsd"
    elif icat_version < "4.10":
        fname = "icatdata-4.7.xsd"
    elif icat_version < "5.0":
        fname = "icatdata-4.10.xsd"
    else:
        fname = "icatdata-5.0.xsd"
    return gettestdata(fname)


def get_reference_dumpfile(ext = "yaml"):
    require_icat_version("4.4.0", "oldest available set of test data")
    if icat_version < "4.7":
        fname = "icatdump-4.4.%s" % ext
    elif icat_version < "4.10":
        fname = "icatdump-4.7.%s" % ext
    elif icat_version < "5.0":
        fname = "icatdump-4.10.%s" % ext
    else:
        fname = "icatdump-5.0.%s" % ext
    return gettestdata(fname)


def get_reference_summary():
    if icat_version < "5.0":
        version_suffix = "4"
    else:
        version_suffix = "5"
    users = [ "acord", "ahau", "jbotu", "jdoe", "nbour", "rbeck" ]
    refsummary = { "root": gettestdata("summary-%s" % version_suffix) }
    for u in users:
        refsummary[u] = gettestdata("summary-%s.%s" % (version_suffix, u))
    return refsummary


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
    require_dumpfile_backend("YAML")
    testcontent = get_reference_dumpfile()
    callscript("wipeicat.py", standardCmdArgs)
    args = standardCmdArgs + ["-f", "YAML", "-i", str(testcontent)]
    callscript("icatingest.py", args)

@pytest.fixture(scope="session")
def rootclient(setupicat):
    client, conf = getConfig(confSection="root", ids="optional")
    client.login(conf.auth, conf.credentials)
    return client

@pytest.fixture(scope="function")
def cleanup_objs(rootclient):
    """Delete some objects (that may or may not have been) created during
    a test
    """
    obj_list = []
    yield obj_list
    for obj in obj_list:
        try:
            if not obj.id:
                obj = rootclient.searchMatching(obj)
        except icat.SearchResultError:
            # obj not found, maybe the test failed, nothing to do on
            # this object then.
            pass
        else:
            if rootclient.ids and obj.BeanName == "Dataset":
                # obj is a dataset.  If any related datafile has been
                # uploaded (i.e. the location is not NULL), need to
                # delete it from IDS first.
                query = Query(rootclient, "Datafile",
                              conditions={"dataset.id": "= %d" % obj.id,
                                          "location": "IS NOT NULL"})
                rootclient.deleteData(rootclient.search(query))
            rootclient.delete(obj)

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

