"""Test upload and download of files to and from IDS.
"""

import datetime
import filecmp
import time
import zipfile
import pytest
import icat
import icat.config
from icat.ids import DataSelection
from icat.query import Query
from conftest import DummyDatafile, UtcTimezone
from conftest import getConfig, tmpSessionId, tmpClient


@pytest.fixture(scope="module")
def client(setupicat):
    client, conf = getConfig(ids="mandatory")
    client.login(conf.auth, conf.credentials)
    yield client
    query = "SELECT df FROM Datafile df WHERE df.location IS NOT NULL"
    while True:
        try:
            client.deleteData(client.search(query))
        except icat.IDSDataNotOnlineError:
            time.sleep(10)
        else:
            break


# ============================ testdata ============================

testdatafiles = [
    {
        'uluser': "rbeck",
        'invname': "08100122-EF",
        'dsname': "e201216",
        'dfformat': "NeXus",
        'dfname': "e201216.nxs",
        'size': 368369,
        'mtime': 1213774271,
        'testfile': None,
    },
    {
        'uluser': "acord",
        'invname': "10100601-ST",
        'dsname': "e208342",
        'dfformat': "other",
        'dfname': "e208342.dat",
        'size': 394,
        'mtime': 1286600400,
        'testfile': None,
    },
    {
        'uluser': "ahau",
        'invname': "10100601-ST",
        'dsname': "e208342",
        'dfformat': "NeXus",
        'dfname': "e208342.nxs",
        'size': 52857,
        'mtime': 1286600400,
        'testfile': None,
    },
    {
        'uluser': "nbour",
        'invname': "12100409-ST",
        'dsname': "e208946",
        'dfformat': "other",
        'dfname': "e208946.dat",
        'size': 459,
        'mtime': 1343610608,
        'testfile': None,
    },
    {
        'uluser': "nbour",
        'invname': "12100409-ST",
        'dsname': "e208946",
        'dfformat': "NeXus",
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
    pytest.param(df, marks=pytest.mark.dependency(name=df['dfname']))
    for df in testdatafiles
]
markeddatasets = [
    pytest.param(ds, marks=pytest.mark.dependency(
        depends=[df['dfname'] for df in ds['dfs']]
    )) for ds in testdatasets
]

# ============================= helper =============================

def getDataset(client, case):
    query = Query(client, "Dataset", conditions={
        "investigation.name": "= '%s'" % case['invname'],
        "name": "= '%s'" % case['dsname'],
    })
    return (client.assertedSearch(query)[0])

def getDatafileFormat(client, case):
    l = case['dfformat'].split(':')
    query = Query(client, "DatafileFormat", conditions={
        "name": "= '%s'" % l[0],
    })
    if len(l) > 1:
        query.addConditions({"version": "= '%s'" % l[1]})
    return (client.assertedSearch(query)[0])

def getDatafile(client, case, dfname=None):
    if dfname is None:
        dfname = case['dfname']
    query = Query(client, "Datafile", conditions={
        "name": "= '%s'" % dfname,
        "dataset.name": "= '%s'" % case['dsname'],
        "dataset.investigation.name": "= '%s'" % case['invname'],
    })
    return (client.assertedSearch(query)[0])

def copyfile(infile, outfile, chunksize=8192):
    """Read all data from infile and write them to outfile.
    """
    while True:
        chunk = infile.read(chunksize)
        if not chunk:
            break
        outfile.write(chunk)

# ============================= tests ==============================

@pytest.mark.parametrize(("case"), markeddatafiles)
def test_upload(tmpdirsec, client, case):
    f = DummyDatafile(tmpdirsec, case['dfname'], case['size'], case['mtime'])
    print("\nUpload file %s" % case['dfname'])
    with tmpClient(confSection=case['uluser'], ids="mandatory") as tclient:
        username = tclient.getUserName()
        dataset = getDataset(tclient, case)
        datafileformat = getDatafileFormat(tclient, case)
        datafile = tclient.new("Datafile", name=f.fname.name,
                               dataset=dataset, datafileFormat=datafileformat)
        tclient.putData(f.fname, datafile)
        df = getDatafile(tclient, case)
        assert df.location is not None
        assert df.fileSize == f.size
        assert df.checksum == f.crc32
        if f.mtime:
            assert df.datafileModTime == f.mtime
        assert df.createId == username
        assert df.modId == username
        case['testfile'] = f

@pytest.fixture(scope='function', params=["getData", "getPreparedData"])
def method(request):
    return request.param

@pytest.mark.parametrize(("case"), markeddatasets)
def test_download(tmpdirsec, client, case, method):
    with tmpClient(confSection=case['dluser'], ids="mandatory") as tclient:
        if len(case['dfs']) > 1:
            zfname = tmpdirsec / ("%s.zip" % case['dsname'])
            print("\nDownload %s to file %s" % (case['dsname'], zfname))
            dataset = getDataset(tclient, case)
            query = "Datafile <-> Dataset [id=%d]" % dataset.id
            datafiles = tclient.search(query)
            if method == 'getData':
                response = tclient.getData(datafiles)
            elif method == 'getPreparedData':
                prepid = tclient.prepareData(datafiles)
                while not tclient.isDataPrepared(prepid):
                    time.sleep(5)
                response = tclient.getData(prepid)
            with zfname.open('wb') as f:
                copyfile(response, f)
            zf = zipfile.ZipFile(str(zfname), 'r')
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
            dfname = tmpdirsec / ("dl_%s" % df['dfname'])
            print("\nDownload %s to file %s" % (case['dsname'], dfname))
            dataset = getDataset(tclient, case)
            query = "Datafile <-> Dataset [id=%d]" % dataset.id
            datafiles = tclient.search(query)
            if method == 'getData':
                response = tclient.getData(datafiles)
            elif method == 'getPreparedData':
                prepid = tclient.prepareData(datafiles)
                while not tclient.isDataPrepared(prepid):
                    time.sleep(5)
                response = tclient.getData(prepid)
            with dfname.open('wb') as f:
                copyfile(response, f)
            assert filecmp.cmp(str(df['testfile'].fname), str(dfname))
        else:
            raise RuntimeError("No datafiles for dataset %s" % case['dsname'])

@pytest.mark.parametrize(("case"), markeddatasets)
def test_getinfo(client, case, method):
    """Call getStatus() and getSize() to get some informations on a dataset.
    """
    selection = DataSelection([getDataset(client, case)])
    if method == 'getPreparedData':
        if client.ids.apiversion < '1.11.0':
            pytest.skip("IDS %s is too old, need 1.11.0 or newer" 
                        % client.ids.apiversion)
        prepid = client.prepareData(selection)
        while not client.isDataPrepared(prepid):
            time.sleep(5)
        selection = prepid
    size = client.ids.getSize(selection)
    print("Size of dataset %s: %d" % (case['dsname'], size))
    assert size == sum(f['size'] for f in case['dfs'])
    status = client.ids.getStatus(selection)
    print("Status of dataset %s: %s" % (case['dsname'], status))
    assert status in {"ONLINE", "RESTORING", "ARCHIVED"}

@pytest.mark.parametrize(("case"), markeddatasets)
def test_getstatus_versionerror(client, case):
    """The call of getStatus() with a preparedID should throw an error if
    talking to an old ids.server not supporting it.
    """
    selection = DataSelection([getDataset(client, case)])
    if client.ids.apiversion >= '1.11.0':
        pytest.skip("This test is for IDS versions older then 1.11.0 only, "
                    "found ids.server %s" % client.ids.apiversion)
    prepid = client.prepareData(selection)
    while not client.isDataPrepared(prepid):
        time.sleep(5)
    with pytest.raises(icat.VersionMethodError):
        size = client.ids.getSize(prepid)

@pytest.mark.parametrize(("case"), markeddatasets)
def test_status_no_sessionId(client, case):
    """Call getStatus() while logged out.

    IDS 1.5.0 and newer allow the sessionId to be omitted from the
    getStatus() call.
    """
    if client.ids.apiversion < '1.5.0':
        pytest.skip("IDS %s is too old, need 1.5.0 or newer" 
                    % client.ids.apiversion)
    selection = DataSelection([getDataset(client, case)])
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
    ds = getDataset(client, case)
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
    dataset = getDataset(client, case)
    datafileformat = client.assertedSearch("DatafileFormat [name='other']")[0]
    tzinfo = UtcTimezone() if UtcTimezone else None
    createTime = datetime.datetime(2008, 6, 18, 9, 31, 11, tzinfo=tzinfo)
    dfname = "test_datafileCreateTime_dt.dat"
    f = DummyDatafile(tmpdirsec, dfname, case['size'])
    datafile = client.new("Datafile", name=f.name,
                          dataset=dataset, datafileFormat=datafileformat)
    datafile.datafileCreateTime = createTime
    client.putData(f.fname, datafile)
    df = getDatafile(client, case, dfname)
    assert df.datafileCreateTime is not None
    # The handling of date value in original Suds is buggy, so we
    # cannot expect to be able to reliably compare date values.  If
    # UtcTimezone is set, we have the jurko fork and then this bug in
    # Suds is fixed.
    if tzinfo is not None:
        assert df.datafileCreateTime == createTime

    # Now try the same again with datafileCreateTime set to a string.
    dfname = "test_datafileCreateTime_str.dat"
    f = DummyDatafile(tmpdirsec, dfname, case['size'])
    datafile = client.new("Datafile", name=f.name,
                          dataset=dataset, datafileFormat=datafileformat)
    datafile.datafileCreateTime = createTime.isoformat()
    client.putData(f.fname, datafile)
    df = getDatafile(client, case, dfname)
    assert df.datafileCreateTime is not None
    if tzinfo is not None:
        assert df.datafileCreateTime == createTime

@pytest.mark.parametrize(("case"), markeddatasets)
def test_write(client, case):
    """Call write() on a dataset.
    """
    if client.ids.apiversion < '1.9.0':
        pytest.skip("IDS %s is too old, need 1.9.0 or newer" 
                    % client.ids.apiversion)
    if not client.ids.isTwoLevel():
        pytest.skip("This IDS does not use two levels of data storage")
    selection = DataSelection([getDataset(client, case)])
    status = client.ids.getStatus(selection)
    print("Status of dataset %s is %s" % (case['dsname'], status))
    if status != "ONLINE":
        pytest.skip("Dataset %s is not ONLINE" % (case['dsname']))
    print("Request write of dataset %s" % (case['dsname']))
    # Note that there is no effect whatsoever of the write request
    # visible at the client side.  The only thing that we can test
    # here is that IDS did accept the call without raising an error.
    # Note however, that the write call may be disabled in the IDS
    # server configuration.  In this case, IDS will raise a
    # NotImplementedError.  So we must even ignore this error.
    try:
        client.ids.write(selection)
    except icat.IDSNotImplementedError:
        pass

@pytest.mark.parametrize(("case"), markeddatasets)
def test_archive(client, case):
    """Call archive() on a dataset.
    """
    if not client.ids.isTwoLevel():
        pytest.skip("This IDS does not use two levels of data storage")
    selection = DataSelection([getDataset(client, case)])
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
    selection = DataSelection([getDataset(client, case)])
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
    selection = DataSelection([getDataset(client, case)])
    print("Request reset of dataset %s" % (case['dsname']))
    client.ids.reset(selection)
    status = client.ids.getStatus(selection)
    print("Status of dataset %s is now %s" % (case['dsname'], status))
