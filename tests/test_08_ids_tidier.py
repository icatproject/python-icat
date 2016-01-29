"""Stress the IDS Tidier.

If the uploads are large enough, one upload will trigger automatical
archiving of former uploads.  This tests are mainly useful to test the
IDS server, in particular the Tidier, rather then to test the client.
That is why they are disabled by default.  Consequently, there are no
assert statements to test success.  The relevant outcome of the test
can only be verified checking the server logs.

The size of the test data has been adjusted such the effect is visible
for an IDS server having

  startArchivingLevel1024bytes = 250000 (= 244.14 MiB) and 
  stopArchivingLevel1024bytes =  200000 (= 195.31 MiB)

in the ids.properties.
"""

from __future__ import print_function
import os.path
import time
import pytest
import icat
import icat.config
from icat.ids import DataSelection
from icat.exception import IDSDataNotOnlineError
from conftest import DummyDatafile, getConfig, require_servertest


# Skip unless server tests requested.
require_servertest()

@pytest.fixture(scope="module")
def client(setupicat, request):
    conf = getConfig(ids="mandatory")
    client = icat.Client(conf.url, **conf.client_kwargs)
    client.login(conf.auth, conf.credentials)
    def cleanup():
        query = ("SELECT ds FROM Dataset ds "
                 "WHERE ds.name LIKE 'test_idsVolume_%'")
        while True:
            datasets = client.search(query)
            if not datasets:
                break
            restore = False
            for ds in datasets:
                try:
                    client.deleteData([ds])
                    client.delete(ds)
                except IDSDataNotOnlineError:
                    restore = True
            if restore:
                time.sleep(30)
    request.addfinalizer(cleanup)
    return client


KiB = 1024
MiB = 1024*KiB
df_size = 30*MiB
ds_sizes = [3, 2, 1, 4, 2, 2, 5 ]
testdatasets = []

# ============================= helper =============================

def printStatus(client, objs):
    for o in objs:
        selection = DataSelection([o])
        status = client.ids.getStatus(selection)
        print("Status of %s: %s" % (o.name, status))
        assert status in {"ONLINE", "RESTORING", "ARCHIVED"}

# ============================= tests ==============================

@pytest.mark.dependency(name='upload')
def test_upload(tmpdirsec, client):
    inv = client.assertedSearch("Investigation [name='12100409-ST']")[0]
    datasetType = client.assertedSearch("DatasetType [name='raw']")[0]
    datafileFormat = client.assertedSearch("DatafileFormat [name='raw']")[0]
    print("Start uploading.")
    for i, n in enumerate(ds_sizes, start=1):
        dataset = client.new("dataset", type=datasetType, investigation=inv)
        dataset.name = "test_idsVolume_%02d" % i
        dataset.create()
        for j in range(1,n+1):
            f = DummyDatafile(tmpdirsec.dir, "file%02d.dat" % j, df_size)
            datafile = client.new("datafile", name=os.path.basename(f.fname), 
                                  dataset=dataset, 
                                  datafileFormat=datafileFormat)
            datafile = client.putData(f.fname, datafile)
            dataset.datafiles.append(datafile)
        print("Dataset %s created." % dataset.name)
        testdatasets.append(dataset)
        printStatus(client, testdatasets)
