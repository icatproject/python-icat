"""Test icatdump and icatingest.
"""

from __future__ import print_function
import os.path
import pytest
from subprocess import CalledProcessError
import icat
import icat.config
from icat.query import Query
from conftest import DummyDatafile, gettestdata, callscript


# The ICAT session as a fixture to be shared among all tests in this
# module.  The user needs appropriate read permissions.
user = "root"

@pytest.fixture(scope="module")
def client(setupicat, icatconfigfile):
    args = ["-c", icatconfigfile, "-s", user]
    conf = icat.config.Config().getconfig(args)
    client = icat.Client(conf.url, **conf.client_kwargs)
    client.login(conf.auth, conf.credentials)
    return client


# Test input
ds_params = gettestdata("ingest-ds-params.xml")
datafiles = gettestdata("ingest-datafiles.xml")

@pytest.fixture(scope="function")
def dataset(client):
    """Get the dataset to be used for ingest tests.

    The ingest-ds-params.xml test input uses a Dataset that is assumed
    to exist in the ICAT content as set up by the setupicat fixture.
    This fixture retrieves this dataset from ICAT and deletes all
    DatasetParameters related to it.
    """
    conditions = {
        "name": "= 'e208341'", 
        "investigation.name": "= '10100601-ST'",  
        "investigation.visitId": "='1.1-N'"
    }
    query = Query(client, "Dataset", conditions=conditions)
    ds = client.assertedSearch(query)[0]
    query = Query(client, "DatasetParameter", 
                  conditions={"dataset.id": "= %d" % ds.id})
    client.deleteMany(client.search(query))
    return ds


# Test datafiles to be created by test_ingest_datafiles:
testdatafiles = [
    {
        'dfname': "e208343.dat",
        'size': 394,
        'mtime': 1286600400,
    },
    {
        'dfname': "e208343.nxs",
        'size': 52857,
        'mtime': 1286600400,
    },
]


def test_ingest_dataset_params(dataset, client, icatconfigfile):
    """Ingest a file setting some dataset parameters.
    """
    args = ["-c", icatconfigfile, "-s", "acord", "-f", "XML", "-i", ds_params]
    callscript("icatingest.py", args)
    # Verify that the params have been set.
    query = Query(client, "DatasetParameter", 
                  conditions={"dataset.id": "= %d" % dataset.id}, 
                  includes={"type"})
    params = client.search(query)
    assert len(params) == 3
    values = { (p.type.name, p.numericValue, p.type.units) for p in params }
    assert values == { ("Magnetic field", 5.3, "T"), 
                       ("Reactor power", 10.0, "MW"), 
                       ("Sample temperature", 293.15, "K") }


def test_ingest_duplicate_throw(dataset, client, icatconfigfile):
    """Ingest with a collision of a duplicate object.

    Same test as above, but now place a duplicate object in the way.
    """
    ptype = client.assertedSearch("ParameterType [name='Reactor power']")[0]
    p = client.new("datasetParameter", numericValue=5.0, 
                   dataset=dataset, type=ptype)
    p.create()
    args = ["-c", icatconfigfile, "-s", "acord", "-f", "XML", "-i", ds_params]
    # FIXME: should inspect stderr and verify ICATObjectExistsError.
    with pytest.raises(CalledProcessError) as err:
        callscript("icatingest.py", args)
    # Verify that the params have been set.  The exceptions should
    # have been raised while trying to ingest the second parameter.
    # The first one (Maegnetic field) should have been created and
    # Reactor power should still have the value set above.
    query = Query(client, "DatasetParameter", 
                  conditions={"dataset.id": "= %d" % dataset.id}, 
                  includes={"type"})
    params = client.search(query)
    assert len(params) == 2
    values = { (p.type.name, p.numericValue, p.type.units) for p in params }
    assert values == { ("Magnetic field", 5.3, "T"), 
                       ("Reactor power", 5.0, "MW") }


def test_ingest_duplicate_ignore(dataset, client, icatconfigfile):
    """Ingest with a collision of a duplicate object.

    Same test as above, but now ignore the duplicate.
    """
    ptype = client.assertedSearch("ParameterType [name='Reactor power']")[0]
    p = client.new("datasetParameter", numericValue=5.0, 
                   dataset=dataset, type=ptype)
    p.create()
    args = ["-c", icatconfigfile, "-s", "acord", "-f", "XML", "-i", ds_params, 
            "--duplicate", "IGNORE"]
    callscript("icatingest.py", args)
    # Verify that the params have been set.
    query = Query(client, "DatasetParameter", 
                  conditions={"dataset.id": "= %d" % dataset.id}, 
                  includes={"type"})
    params = client.search(query)
    assert len(params) == 3
    values = { (p.type.name, p.numericValue, p.type.units) for p in params }
    assert values == { ("Magnetic field", 5.3, "T"), 
                       ("Reactor power", 5.0, "MW"), 
                       ("Sample temperature", 293.15, "K") }


def test_ingest_duplicate_check_err(dataset, client, icatconfigfile):
    """Ingest with a collision of a duplicate object.

    Same test as above, but use CHECK which fails due to mismatch.
    """
    ptype = client.assertedSearch("ParameterType [name='Reactor power']")[0]
    p = client.new("datasetParameter", numericValue=5.0, 
                   dataset=dataset, type=ptype)
    p.create()
    args = ["-c", icatconfigfile, "-s", "acord", "-f", "XML", "-i", ds_params, 
            "--duplicate", "CHECK"]
    # FIXME: should inspect stderr and verify ICATObjectExistsError.
    with pytest.raises(CalledProcessError) as err:
        callscript("icatingest.py", args)
    # Verify that the params have been set.
    query = Query(client, "DatasetParameter", 
                  conditions={"dataset.id": "= %d" % dataset.id}, 
                  includes={"type"})
    params = client.search(query)
    assert len(params) == 2
    values = { (p.type.name, p.numericValue, p.type.units) for p in params }
    assert values == { ("Magnetic field", 5.3, "T"), 
                       ("Reactor power", 5.0, "MW") }


def test_ingest_duplicate_check_ok(dataset, client, icatconfigfile):
    """Ingest with a collision of a duplicate object.

    Same test as above, but now it matches, so CHECK should return ok.
    """
    ptype = client.assertedSearch("ParameterType [name='Reactor power']")[0]
    p = client.new("datasetParameter", numericValue=10.0, 
                   dataset=dataset, type=ptype)
    p.create()
    args = ["-c", icatconfigfile, "-s", "acord", "-f", "XML", "-i", ds_params, 
            "--duplicate", "CHECK"]
    callscript("icatingest.py", args)
    # Verify that the params have been set.
    query = Query(client, "DatasetParameter", 
                  conditions={"dataset.id": "= %d" % dataset.id}, 
                  includes={"type"})
    params = client.search(query)
    assert len(params) == 3
    values = { (p.type.name, p.numericValue, p.type.units) for p in params }
    assert values == { ("Magnetic field", 5.3, "T"), 
                       ("Reactor power", 10.0, "MW"), 
                       ("Sample temperature", 293.15, "K") }


def test_ingest_duplicate_overwrite(dataset, client, icatconfigfile):
    """Ingest with a collision of a duplicate object.

    Same test as above, but now overwrite the old value.
    """
    ptype = client.assertedSearch("ParameterType [name='Reactor power']")[0]
    p = client.new("datasetParameter", numericValue=5.0, 
                   dataset=dataset, type=ptype)
    p.create()
    args = ["-c", icatconfigfile, "-s", "acord", "-f", "XML", "-i", ds_params, 
            "--duplicate", "OVERWRITE"]
    callscript("icatingest.py", args)
    # Verify that the params have been set.
    query = Query(client, "DatasetParameter", 
                  conditions={"dataset.id": "= %d" % dataset.id}, 
                  includes={"type"})
    params = client.search(query)
    assert len(params) == 3
    values = { (p.type.name, p.numericValue, p.type.units) for p in params }
    assert values == { ("Magnetic field", 5.3, "T"), 
                       ("Reactor power", 10.0, "MW"), 
                       ("Sample temperature", 293.15, "K") }


def test_ingest_datafiles(tmpdirsec, client, icatconfigfile):
    """Ingest a dataset with some datafiles.
    """
    dummyfiles = [ f['dfname'] for f in testdatafiles ]
    args = ["-c", icatconfigfile, "-s", "acord", "-f", "XML", "-i", datafiles]
    callscript("icatingest.py", args)
    # Verify that the datafiles have been uploaded.
    conditions = {
        "name": "= 'e208343'", 
        "investigation.name": "= '10100601-ST'",  
        "investigation.visitId": "='1.1-N'"
    }
    query = Query(client, "Dataset", conditions=conditions)
    dataset = client.assertedSearch(query)[0]
    for fname in dummyfiles:
        query = Query(client, "Datafile", conditions={
            "name": "= '%s'" % fname,
            "dataset.id": "= %d" % dataset.id,
        })
        df = client.assertedSearch(query)[0]
        assert df.location is None
    # Delete the dataset together with the datafiles so that the next
    # test gets a chance to creste them again.
    client.delete(dataset)


def test_ingest_datafiles_upload(tmpdirsec, client, icatconfigfile):
    """Upload datafiles to IDS from icatingest.

    Same as last test, but set the --upload-datafiles flag so that
    icatingest will not create the datafiles as objects in the ICAT,
    but upload the files to IDS instead.
    """
    dummyfiles = [ DummyDatafile(tmpdirsec.dir, 
                                 f['dfname'], f['size'], f['mtime'])
                   for f in testdatafiles ]
    args = ["-c", icatconfigfile, "-s", "acord", "-f", "XML", "-i", datafiles, 
            "--upload-datafiles", "--datafile-dir", tmpdirsec.dir]
    callscript("icatingest.py", args)
    # Verify that the datafiles have been uploaded.
    conditions = {
        "name": "= 'e208343'", 
        "investigation.name": "= '10100601-ST'",  
        "investigation.visitId": "='1.1-N'"
    }
    query = Query(client, "Dataset", conditions=conditions)
    dataset = client.assertedSearch(query)[0]
    for f in dummyfiles:
        query = Query(client, "Datafile", conditions={
            "name": "= '%s'" % f.name,
            "dataset.id": "= %d" % dataset.id,
        })
        df = client.assertedSearch(query)[0]
        assert df.location is not None
        assert df.fileSize == f.size
        assert df.checksum == f.crc32
        if f.mtime:
            assert df.datafileModTime == f.mtime
