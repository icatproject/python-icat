"""Test icatdump and icatingest.
"""

from __future__ import print_function
import os.path
import pytest
import icat
import icat.config
from icat.query import Query
from conftest import gettestdata, callscript


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


ds_params = gettestdata("ingest-ds-params.xml")

def test_ingest_dataset_params(client, icatconfigfile):
    """Ingest a file setting some dataset parameters.
    """
    args = ["-c", icatconfigfile, "-s", "acord", "-f", "XML", "-i", ds_params]
    callscript("icatingest.py", args)
    # Verify that the params have been set.
    conditions = {
        "name": "= 'e208341'", 
        "investigation.name": "= '10100601-ST'",  
        "investigation.visitId": "='1.1-N'"
    }
    query = Query(client, "Dataset", conditions=conditions)
    dataset = client.assertedSearch(query)[0]
    query = Query(client, "DatasetParameter", 
                  conditions={"dataset.id": "= %d" % dataset.id}, 
                  includes={"type"})
    params = client.search(query)
    assert len(params) == 3
    values = { (p.type.name, p.numericValue, p.type.units) for p in params }
    assert values == { ("Magnetic field", 5.3, "T"), 
                       ("Reactor power", 10.0, "MW"), 
                       ("Sample temperature", 293.15, "K") }
