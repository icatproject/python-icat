"""Test ingest metadata using the icatingest script.
"""

from subprocess import CalledProcessError
import pytest
import icat
import icat.config
from icat.query import Query
from conftest import (DummyDatafile, require_dumpfile_backend,
                      gettestdata, getConfig, callscript)


# Test input
ds_params = str(gettestdata("ingest-ds-params.xml"))
datafiles = str(gettestdata("ingest-datafiles.xml"))
sample_ds = str(gettestdata("ingest-sample-ds.xml"))

@pytest.fixture(scope="module")
def client(setupicat):
    client, conf = getConfig(confSection="acord", ids="optional")
    client.login(conf.auth, conf.credentials)
    return client

@pytest.fixture(scope="module")
def cmdargs(setupicat):
    require_dumpfile_backend("XML")
    _, conf = getConfig(confSection="acord", ids="optional")
    return conf.cmdargs + ["-f", "XML"]

@pytest.fixture(scope="function")
def dataset(client, cleanup_objs):
    """A dataset to be used in the test.

    The dataset is not created by the fixture, it is assumed that the
    test does it.  The dataset will be eventually be deleted after the
    test.
    """
    inv = client.assertedSearch("Investigation [name='10100601-ST']")[0]
    dstype = client.assertedSearch("DatasetType [name='raw']")[0]
    dataset = client.new("Dataset",
                         name="e208343", complete=False,
                         investigation=inv, type=dstype)
    cleanup_objs.append(dataset)
    return dataset


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


def verify_dataset_params(client, dataset, params):
    query = Query(client, "DatasetParameter", 
                  conditions={"dataset.id": "= %d" % dataset.id}, 
                  includes={"type"})
    ps = client.search(query)
    assert len(ps) == len(params)
    values = { (p.type.name, p.numericValue, p.type.units) for p in ps }
    assert values == params


def test_ingest_dataset_params(client, dataset, cmdargs):
    """Ingest a file setting some dataset parameters.
    """
    dataset.create()
    args = cmdargs + ["-i", ds_params]
    callscript("icatingest.py", args)
    verify_dataset_params(client, dataset, { 
        ("Magnetic field", 5.3, "T"), 
        ("Reactor power", 10.0, "MW"), 
        ("Sample temperature", 293.15, "K") 
    })


def test_ingest_duplicate_throw(client, dataset, cmdargs):
    """Ingest with a collision of a duplicate object.

    Same test as above, but now place a duplicate object in the way.
    """
    dataset.create()
    ptype = client.assertedSearch("ParameterType [name='Reactor power']")[0]
    p = client.new("DatasetParameter", numericValue=5.0,
                   dataset=dataset, type=ptype)
    p.create()
    args = cmdargs + ["-i", ds_params]
    # FIXME: should inspect stderr and verify ICATObjectExistsError.
    with pytest.raises(CalledProcessError) as err:
        callscript("icatingest.py", args)
    # Verify that the params have been set.  The exceptions should
    # have been raised while trying to ingest the second parameter.
    # The first one (Magnetic field) should have been created and
    # Reactor power should still have the value set above.
    verify_dataset_params(client, dataset, { 
        ("Magnetic field", 5.3, "T"), 
        ("Reactor power", 5.0, "MW") 
    })


def test_ingest_duplicate_ignore(client, dataset, cmdargs):
    """Ingest with a collision of a duplicate object.

    Same test as above, but now ignore the duplicate.
    """
    dataset.create()
    ptype = client.assertedSearch("ParameterType [name='Reactor power']")[0]
    p = client.new("DatasetParameter", numericValue=5.0,
                   dataset=dataset, type=ptype)
    p.create()
    args = cmdargs + ["-i", ds_params, "--duplicate", "IGNORE"]
    callscript("icatingest.py", args)
    verify_dataset_params(client, dataset, { 
        ("Magnetic field", 5.3, "T"), 
        ("Reactor power", 5.0, "MW"), 
        ("Sample temperature", 293.15, "K") 
    })


def test_ingest_duplicate_check_err(client, dataset, cmdargs):
    """Ingest with a collision of a duplicate object.

    Same test as above, but use CHECK which fails due to mismatch.
    """
    dataset.create()
    ptype = client.assertedSearch("ParameterType [name='Reactor power']")[0]
    p = client.new("DatasetParameter", numericValue=5.0,
                   dataset=dataset, type=ptype)
    p.create()
    args = cmdargs + ["-i", ds_params, "--duplicate", "CHECK"]
    # FIXME: should inspect stderr and verify ICATObjectExistsError.
    with pytest.raises(CalledProcessError) as err:
        callscript("icatingest.py", args)
    verify_dataset_params(client, dataset, { 
        ("Magnetic field", 5.3, "T"), 
        ("Reactor power", 5.0, "MW") 
    })


def test_ingest_duplicate_check_ok(client, dataset, cmdargs):
    """Ingest with a collision of a duplicate object.

    Same test as above, but now it matches, so CHECK should return ok.
    """
    dataset.create()
    ptype = client.assertedSearch("ParameterType [name='Reactor power']")[0]
    p = client.new("DatasetParameter", numericValue=10.0,
                   dataset=dataset, type=ptype)
    p.create()
    args = cmdargs + ["-i", ds_params, "--duplicate", "CHECK"]
    callscript("icatingest.py", args)
    verify_dataset_params(client, dataset, { 
        ("Magnetic field", 5.3, "T"), 
        ("Reactor power", 10.0, "MW"), 
        ("Sample temperature", 293.15, "K") 
    })


def test_ingest_duplicate_overwrite(client, dataset, cmdargs):
    """Ingest with a collision of a duplicate object.

    Same test as above, but now overwrite the old value.
    """
    dataset.create()
    ptype = client.assertedSearch("ParameterType [name='Reactor power']")[0]
    p = client.new("DatasetParameter", numericValue=5.0,
                   dataset=dataset, type=ptype)
    p.create()
    args = cmdargs + ["-i", ds_params, "--duplicate", "OVERWRITE"]
    callscript("icatingest.py", args)
    verify_dataset_params(client, dataset, { 
        ("Magnetic field", 5.3, "T"), 
        ("Reactor power", 10.0, "MW"), 
        ("Sample temperature", 293.15, "K") 
    })


# Minimal example, a Datafile featuring a string.
ingest_data_string = """<?xml version="1.0" encoding="utf-8"?>
<icatdata>
  <data>
    <datasetRef id="Dataset_001" 
		name="e208343" 
		investigation.name="10100601-ST" 
		investigation.visitId="1.1-N"/>
    <datafile>
      <name>dup_test_str.dat</name>
      <dataset ref="Dataset_001"/>
    </datafile>
  </data>
</icatdata>
"""
# A Datafile featuring an int.
ingest_data_int = """<?xml version="1.0" encoding="utf-8"?>
<icatdata>
  <data>
    <datasetRef id="Dataset_001" 
		name="e208343" 
		investigation.name="10100601-ST" 
		investigation.visitId="1.1-N"/>
    <datafile>
      <fileSize>42</fileSize>
      <name>dup_test_int.dat</name>
      <dataset ref="Dataset_001"/>
    </datafile>
  </data>
</icatdata>
"""
# A Dataset featuring a boolean.
ingest_data_boolean = """<?xml version="1.0" encoding="utf-8"?>
<icatdata>
  <data>
    <dataset id="Dataset_001">
      <complete>false</complete>
      <name>e208343</name>
      <investigation name="10100601-ST" visitId="1.1-N"/>
      <type name="raw"/>
    </dataset>
  </data>
</icatdata>
"""
# A DatasetParameter featuring a float.
ingest_data_float = """<?xml version="1.0" encoding="utf-8"?>
<icatdata>
  <data>
    <datasetRef id="Dataset_001" 
		name="e208343" 
		investigation.name="10100601-ST" 
		investigation.visitId="1.1-N"/>
    <datasetParameter>
      <numericValue>5.3</numericValue>
      <dataset ref="Dataset_001"/>
      <type name="Magnetic field" units="T"/>
    </datasetParameter>
  </data>
</icatdata>
"""
# A Datafile featuring a date.
ingest_data_date = """<?xml version="1.0" encoding="utf-8"?>
<icatdata>
  <data>
    <datasetRef id="Dataset_001" 
		name="e208343" 
		investigation.name="10100601-ST" 
		investigation.visitId="1.1-N"/>
    <datafile>
      <datafileCreateTime>2008-06-18T09:31:11+02:00</datafileCreateTime>
      <name>dup_test_date.dat</name>
      <dataset ref="Dataset_001"/>
    </datafile>
  </data>
</icatdata>
"""

@pytest.mark.parametrize("inputdata", [
    pytest.param(ingest_data_string, id="ingest_data_string"),
    pytest.param(ingest_data_int, id="ingest_data_int"),
    pytest.param(ingest_data_boolean, id="ingest_data_boolean"),
    pytest.param(ingest_data_float, id="ingest_data_float"),
    pytest.param(ingest_data_date, id="ingest_data_date"),
])
def test_ingest_duplicate_check_types(tmpdirsec, dataset, cmdargs, inputdata):
    """Ingest with a collision of a duplicate object.

    Similar to test_ingest_duplicate_check_ok(), but trying several
    input datasets that test different data types.  Issue #9.
    """
    # Most input data create a datafile or a dataset parameter related
    # to dataset and thus assume the dataset to already exist.  Only
    # ingest_data_boolean creates the dataset itself.
    if inputdata is not ingest_data_boolean:
        dataset.create()
    # We simply ingest twice the same data, using duplicate=CHECK the
    # second time.  This obviously leads to matching duplicates.
    inpfile = tmpdirsec / "ingest.xml"
    with inpfile.open("wt") as f:
        f.write(inputdata)
    args = cmdargs + ["-i", str(inpfile)]
    callscript("icatingest.py", args)
    callscript("icatingest.py", args + ["--duplicate", "CHECK"])


def test_ingest_datafiles(tmpdirsec, client, dataset, cmdargs):
    """Ingest a dataset with some datafiles.
    """
    dummyfiles = [ f['dfname'] for f in testdatafiles ]
    args = cmdargs + ["-i", datafiles]
    callscript("icatingest.py", args)
    # Verify that the datafiles have been created but not uploaded.
    dataset = client.searchMatching(dataset)
    for fname in dummyfiles:
        query = Query(client, "Datafile", conditions={
            "name": "= '%s'" % fname,
            "dataset.id": "= %d" % dataset.id,
        })
        df = client.assertedSearch(query)[0]
        assert df.location is None


def test_ingest_datafiles_upload(tmpdirsec, client, dataset, cmdargs):
    """Upload datafiles to IDS from icatingest.

    Same as last test, but set the --upload-datafiles flag so that
    icatingest will not create the datafiles as objects in the ICAT,
    but upload the files to IDS instead.
    """
    if not client.ids:
        pytest.skip("no IDS configured")
    dummyfiles = [ DummyDatafile(tmpdirsec, f['dfname'], f['size'], f['mtime'])
                   for f in testdatafiles ]
    args = cmdargs + ["-i", datafiles, "--upload-datafiles", 
                      "--datafile-dir", str(tmpdirsec)]
    callscript("icatingest.py", args)
    # Verify that the datafiles have been uploaded.
    dataset = client.searchMatching(dataset)
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


def test_ingest_dataset_samples(client, cleanup_objs, cmdargs):
    """Ingest some datasets that are releated to samples.
    """
    ds_sample_map = {
        "e209001": "ab3465",
        "e209002": "ab3465",
        "e209003": "ab3466",
        "e209004": None,
    }
    inv = client.assertedSearch("Investigation [name='10100601-ST']")[0]
    query = Query(client, "SampleType", conditions={"name": "= 'NiMnGa'"})
    sample_type = client.assertedSearch(query)[0]
    ds_type = client.assertedSearch("DatasetType [name='raw']")[0]
    for name in ds_sample_map.keys():
        # the datasets are supposed to be created by the imgest file
        dataset = client.new("Dataset",
                             name=name, complete=False,
                             investigation=inv, type=ds_type)
        cleanup_objs.append(dataset)
    for name in {v for v in ds_sample_map.values() if v}:
        # the samples are referenced from the ingest file, but are are
        # assumed to already exist, so we need to create them here.
        sample = client.new("Sample",
                            name=name, investigation=inv, type=sample_type)
        sample.create()
        cleanup_objs.append(sample)
    args = cmdargs + ["-i", sample_ds]
    callscript("icatingest.py", args)
    for ds_name, sample_name in ds_sample_map.items():
        query = Query(client, "Dataset", conditions={
            "investigation.id": "= %d" % inv.id,
            "name": "= '%s'" % ds_name,
        }, includes=["sample"])
        ds = client.assertedSearch(query)[0]
        if sample_name:
            assert ds.sample
            assert ds.sample.name == sample_name
        else:
            assert not ds.sample
