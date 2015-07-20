"""Test upload and download of files to and from IDS.
"""

from __future__ import print_function
import sys
import os
import os.path
from random import getrandbits
import datetime
import zlib
import zipfile
import filecmp
import pytest
import icat
import icat.config
from icat.query import Query
from conftest import gettestdata, callscript
try:
    from suds.sax.date import UtcTimezone
except ImportError:
    UtcTimezone = None

# ============================= helper =============================

user = "root"

@pytest.fixture(scope="module")
def client(setupicat, icatconfigfile):
    args = ["-c", icatconfigfile, "-s", user]
    conf = icat.config.Config().getconfig(args)
    client = icat.Client(conf.url, **conf.client_kwargs)
    client.login(conf.auth, conf.credentials)
    return client

# Create a test file with random content.

if sys.version_info < (3, 0):
    def buf(seq):
        return buffer(bytearray(seq))
else:
    def buf(seq):
        return bytearray(seq)

class Testfile(object):
    def __init__(self, directory, name, size, date=None):
        if date is not None:
            date = (date, date)
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


# ============================= tests ==============================

testdatafiles = [
    {
        'uluser': "rbeck",
        'invname': "08100122-EF",
        'dsname': "e201216",
        'dfformat': "NeXus:4.0.0",
        'dfname': "e201216.nxs",
        'size': 368369,
        'mtime': 1213774271,
        'testfile': None,
    },
    {
        'uluser': "acord",
        'invname': "10100601-ST",
        'dsname': "e208342",
        'dfformat': "raw",
        'dfname': "e208342.dat",
        'size': 394,
        'mtime': 1286600400,
        'testfile': None,
    },
    {
        'uluser': "ahau",
        'invname': "10100601-ST",
        'dsname': "e208342",
        'dfformat': "NeXus:4.0.0",
        'dfname': "e208342.nxs",
        'size': 52857,
        'mtime': 1286600400,
        'testfile': None,
    },
    {
        'uluser': "nbour",
        'invname': "12100409-ST",
        'dsname': "e208946",
        'dfformat': "raw",
        'dfname': "e208946.dat",
        'size': 459,
        'mtime': 1343610608,
        'testfile': None,
    },
    {
        'uluser': "nbour",
        'invname': "12100409-ST",
        'dsname': "e208946",
        'dfformat': "NeXus:4.2.1",
        'dfname': "e208946.nxs",
        'size': 396430,
        'mtime': 1370254963,
        'testfile': None,
    },
]
testdatasets = [
    {
        'dluser': "jdoe",
        'invname': "08100122-EF",
        'dsname': "e201216",
    },
    {
        'dluser': "ahau",
        'invname': "10100601-ST",
        'dsname': "e208342",
    },
    {
        'dluser': "nbour",
        'invname': "12100409-ST",
        'dsname': "e208946",
    },
]

@pytest.mark.parametrize(("case"), testdatafiles)
def test_upload(tmpdirsec, icatconfigfile, client, case):
    f = Testfile(tmpdirsec.dir, case['dfname'], case['size'], case['mtime'])
    print("\nUpload file %s" % case['dfname'])
    args = ["-c", icatconfigfile, "-s", case['uluser'], 
            case['invname'], case['dsname'], case['dfformat'], f.fname]
    callscript("addfile.py", args)
    query = Query(client, "Datafile", conditions={
        "name": "= '%s'" % case['dfname'],
        "dataset.name": "= '%s'" % case['dsname'],
        "dataset.investigation.name": "= '%s'" % case['invname'],
    })
    df = client.assertedSearch(query)[0]
    assert df.location is not None
    assert df.fileSize == f.size
    assert df.checksum == f.crc32
    if f.mtime:
        assert df.datafileModTime == f.mtime
    case['testfile'] = f

@pytest.fixture(scope='function', params=["getData", "getPreparedData"])
def method(request):
    return request.param

@pytest.mark.parametrize(("case"), testdatasets)
def test_download(tmpdirsec, icatconfigfile, case, method):
    dfs = [ c for c in testdatafiles if c['dsname'] == case['dsname'] ]
    if len(dfs) > 1:
        zfname = os.path.join(tmpdirsec.dir, "%s.zip" % case['dsname'])
        print("\nDownload %s to file %s" % (case['dsname'], zfname))
        args = ["-c", icatconfigfile, "-s", case['dluser'], 
                '--outputfile', zfname, case['invname'], case['dsname'], 
                method]
        callscript("downloaddata.py", args)
        zf = zipfile.ZipFile(zfname, 'r')
        zinfos = zf.infolist()
        assert len(zinfos) == len(dfs)
        for df in dfs:
            zi = None
            for i in zinfos:
                if i.filename.endswith(df['dfname']):
                    zi = i
                    break
            assert zi is not None
            assert "%x" % (zi.CRC & 0xffffffff) == df['testfile'].crc32
            assert zi.file_size == df['testfile'].size
    elif len(dfs) == 1:
        dfname = os.path.join(tmpdirsec.dir, "dl_%s" % dfs[0]['dfname'])
        print("\nDownload %s to file %s" % (case['dsname'], dfname))
        args = ["-c", icatconfigfile, "-s", case['dluser'], 
                '--outputfile', dfname, case['invname'], case['dsname'], 
                method]
        callscript("downloaddata.py", args)
        assert filecmp.cmp(dfs[0]['testfile'].fname, dfname)
    else:
        raise RuntimeError("No datafiles for dataset %s" % case['dsname'])
