"""Test upload and download of files to and from IDS.
"""

from __future__ import print_function
import os
import os.path
import zipfile
import filecmp
import datetime
import pytest
import icat
import icat.config
from icat.query import Query
from icat.ids import DataSelection
from conftest import DummyDatafile, UtcTimezone
from conftest import require_icat_version, getConfig, callscript
from conftest import tmpSessionId


@pytest.fixture(scope="module")
def client(setupicat, request):
    conf = getConfig(ids="mandatory")
    client = icat.Client(conf.url, **conf.client_kwargs)
    client.login(conf.auth, conf.credentials)
    def cleanup():
        query = "SELECT df FROM Datafile df WHERE df.location IS NOT NULL"
        client.deleteData(client.search(query))
    request.addfinalizer(cleanup)
    return client


# ============================ testdata ============================

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
for ds in testdatasets:
    ds['dfs'] = [ df for df in testdatafiles if df['dsname'] == ds['dsname'] ]

# Enriched versions of testdatafiles and testdatasets, decorated
# with appropriate dependency markers, such that the datasets
# depend on the datafiles they contain.
markeddatafiles = [
    pytest.mark.dependency(name=df['dfname'])(df) for df in testdatafiles
]
markeddatasets = [
    pytest.mark.dependency(depends=[df['dfname'] for df in ds['dfs']])(ds)
    for ds in testdatasets
]


# ============================= tests ==============================

@pytest.mark.parametrize(("case"), markeddatafiles)
def test_upload(tmpdirsec, client, case):
    f = DummyDatafile(tmpdirsec.dir, 
                      case['dfname'], case['size'], case['mtime'])
    print("\nUpload file %s" % case['dfname'])
    conf = getConfig(confSection=case['uluser'])
    args = conf.cmdargs + [case['invname'], case['dsname'], 
                           case['dfformat'], f.fname]
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

@pytest.mark.parametrize(("case"), markeddatasets)
def test_download(tmpdirsec, client, case, method):
    conf = getConfig(confSection=case['dluser'])
    if len(case['dfs']) > 1:
        zfname = os.path.join(tmpdirsec.dir, "%s.zip" % case['dsname'])
        print("\nDownload %s to file %s" % (case['dsname'], zfname))
        args = conf.cmdargs + [ '--outputfile', zfname, 
                                case['invname'], case['dsname'], method ]
        callscript("downloaddata.py", args)
        zf = zipfile.ZipFile(zfname, 'r')
        zinfos = zf.infolist()
        assert len(zinfos) == len(case['dfs'])
        for df in case['dfs']:
            zi = None
            for i in zinfos:
                if i.filename.endswith(df['dfname']):
                    zi = i
                    break
            assert zi is not None
            assert "%x" % (zi.CRC & 0xffffffff) == df['testfile'].crc32
            assert zi.file_size == df['testfile'].size
    elif len(case['dfs']) == 1:
        df = case['dfs'][0]
        dfname = os.path.join(tmpdirsec.dir, "dl_%s" % df['dfname'])
        print("\nDownload %s to file %s" % (case['dsname'], dfname))
        args = conf.cmdargs + [ '--outputfile', dfname, 
                                case['invname'], case['dsname'], method ]
        callscript("downloaddata.py", args)
        assert filecmp.cmp(df['testfile'].fname, dfname)
    else:
        raise RuntimeError("No datafiles for dataset %s" % case['dsname'])

@pytest.mark.parametrize(("case"), markeddatasets)
def test_getinfo(client, case):
    """Call getStatus() and getSize() to get some informations on a dataset.
    """
    query = Query(client, "Dataset", conditions={
        "name": "= '%s'" % case['dsname'],
        "investigation.name": "= '%s'" % case['invname'],
    })
    selection = DataSelection(client.assertedSearch(query))
    size = client.ids.getSize(selection)
    print("Size of dataset %s: %d" % (case['dsname'], size))
    assert size == sum(f['size'] for f in case['dfs'])
    status = client.ids.getStatus(selection)
    print("Status of dataset %s: %s" % (case['dsname'], status))
    assert status in {"ONLINE", "RESTORING", "ARCHIVED"}

@pytest.mark.parametrize(("case"), markeddatasets)
def test_status_no_sessionId(client, case):
    """Call getStatus() while logged out.

    IDS 1.5.0 and newer allow the sessionId to be omitted from the
    getStatus() call.
    """
    if client.ids.apiversion < '1.5.0':
        pytest.skip("IDS %s is too old, need 1.5.0 or newer" 
                    % client.ids.apiversion)
    query = Query(client, "Dataset", conditions={
        "name": "= '%s'" % case['dsname'],
        "investigation.name": "= '%s'" % case['invname'],
    })
    selection = DataSelection(client.assertedSearch(query))
    with tmpSessionId(client, None):
        status = client.ids.getStatus(selection)
    print("Status of dataset %s: %s" % (case['dsname'], status))
    assert status in {"ONLINE", "RESTORING", "ARCHIVED"}

@pytest.mark.parametrize(("case"), markeddatasets)
def test_getDatafileIds(client, case):
    """Call getDatafileIds() to get the Datafile ids from a dataset.
    """
    if client.ids.apiversion < '1.5.0':
        pytest.skip("IDS %s is too old, need 1.5.0 or newer" 
                    % client.ids.apiversion)
    query = Query(client, "Dataset", conditions={
        "name": "= '%s'" % case['dsname'],
        "investigation.name": "= '%s'" % case['invname'],
    })
    ds = client.assertedSearch(query)[0]
    selection = DataSelection([ds])
    dfids = client.ids.getDatafileIds(selection)
    print("Datafile ids of dataset %s: %s" % (case['dsname'], str(dfids)))
    query = "Datafile.id <-> Dataset [id=%d]" % ds.id
    assert set(dfids) == set(client.search(query))

def test_putData_datafileCreateTime(tmpdirsec, client):
    """Call client.putData() with a datafile having datafileCreateTime set.
    Issue #10.
    """
    case = testdatafiles[0]
    query = Query(client, "Dataset", conditions={
        "name": "= '%s'" % case['dsname'], 
        "investigation.name": "= '%s'" % case['invname'], 
    })
    dataset = client.assertedSearch(query)[0]
    datafileformat = client.assertedSearch("DatafileFormat [name='raw']")[0]
    tzinfo = UtcTimezone() if UtcTimezone else None
    createTime = datetime.datetime(2008, 6, 18, 9, 31, 11, tzinfo=tzinfo)
    dfname = "test_datafileCreateTime_dt.dat"
    f = DummyDatafile(tmpdirsec.dir, dfname, case['size'])
    datafile = client.new("datafile", name=f.name, 
                          dataset=dataset, datafileFormat=datafileformat)
    datafile.datafileCreateTime = createTime
    client.putData(f.fname, datafile)
    query = Query(client, "Datafile", conditions={
        "name": "= '%s'" % dfname,
        "dataset.name": "= '%s'" % case['dsname'],
        "dataset.investigation.name": "= '%s'" % case['invname'],
    })
    df = client.assertedSearch(query)[0]
    assert df.datafileCreateTime is not None
    # The handling of date value in original Suds is buggy, so we
    # cannot expect to be able to reliably compare date values.  If
    # UtcTimezone is set, we have the jurko fork and then this bug in
    # Suds is fixed.
    if tzinfo is not None:
        assert df.datafileCreateTime == createTime

    # Now try the same again with datafileCreateTime set to a string.
    dfname = "test_datafileCreateTime_str.dat"
    f = DummyDatafile(tmpdirsec.dir, dfname, case['size'])
    datafile = client.new("datafile", name=f.name, 
                          dataset=dataset, datafileFormat=datafileformat)
    datafile.datafileCreateTime = createTime.isoformat()
    client.putData(f.fname, datafile)
    query = Query(client, "Datafile", conditions={
        "name": "= '%s'" % dfname,
        "dataset.name": "= '%s'" % case['dsname'],
        "dataset.investigation.name": "= '%s'" % case['invname'],
    })
    df = client.assertedSearch(query)[0]
    assert df.datafileCreateTime is not None
    if tzinfo is not None:
        assert df.datafileCreateTime == createTime

@pytest.mark.parametrize(("case"), markeddatasets)
def test_archive(client, case):
    """Call archive() on a dataset.
    """
    if not client.ids.isTwoLevel():
        pytest.skip("This IDS does not use two levels of data storage")
    query = Query(client, "Dataset", conditions={
        "name": "= '%s'" % case['dsname'],
        "investigation.name": "= '%s'" % case['invname'],
    })
    selection = DataSelection(client.assertedSearch(query))
    status = client.ids.getStatus(selection)
    print("Status of dataset %s is %s" % (case['dsname'], status))
    print("Request archive of dataset %s" % (case['dsname']))
    client.ids.archive(selection)
    status = client.ids.getStatus(selection)
    # Do not assert status == "ARCHIVED" because the archive could be
    # deferred by the server or an other operation on the same dataset
    # could intervene.  So, there is no guarantee whatsoever on the
    # outcome of the archive() call.
    print("Status of dataset %s is now %s" % (case['dsname'], status))

@pytest.mark.parametrize(("case"), markeddatasets)
def test_restore(client, case):
    """Call restore() on a dataset.
    """
    if not client.ids.isTwoLevel():
        pytest.skip("This IDS does not use two levels of data storage")
    query = Query(client, "Dataset", conditions={
        "name": "= '%s'" % case['dsname'],
        "investigation.name": "= '%s'" % case['invname'],
    })
    selection = DataSelection(client.assertedSearch(query))
    status = client.ids.getStatus(selection)
    print("Status of dataset %s is %s" % (case['dsname'], status))
    print("Request restore of dataset %s" % (case['dsname']))
    client.ids.restore(selection)
    status = client.ids.getStatus(selection)
    # Do not assert status == "RESTORING" because same remark as for
    # archive() applies: there is no guarantee whatsoever on the
    # outcome of the restore() call.
    print("Status of dataset %s is now %s" % (case['dsname'], status))

@pytest.mark.parametrize(("case"), markeddatasets)
def test_reset(client, case):
    """Call reset() on a dataset.

    Note that we just test if we can make the call without an error.
    We do not test whether the call has any effect.  This call resets
    the internal state of the data after an error in ids.server.  This
    is out of scope of testing the client.
    """
    if client.ids.apiversion < '1.6.0':
        pytest.skip("IDS %s is too old, need 1.6.0 or newer" 
                    % client.ids.apiversion)
    if not client.ids.isTwoLevel():
        pytest.skip("This IDS does not use two levels of data storage")
    query = Query(client, "Dataset", conditions={
        "name": "= '%s'" % case['dsname'],
        "investigation.name": "= '%s'" % case['invname'],
    })
    selection = DataSelection(client.assertedSearch(query))
    print("Request reset of dataset %s" % (case['dsname']))
    client.ids.reset(selection)
    status = client.ids.getStatus(selection)
    print("Status of dataset %s is now %s" % (case['dsname'], status))
