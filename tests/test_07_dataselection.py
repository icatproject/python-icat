"""Test the DataSelection class from icat.ids.
"""

import pytest
import icat
import icat.config
from icat.ids import DataSelection
from conftest import getConfig


@pytest.fixture(scope="module")
def client(setupicat):
    client, conf = getConfig()
    client.login(conf.auth, conf.credentials)
    return client

# parameter lists
param_ids = [
    ([42], [], []),
    ([], [47,11], []),
    ([], [], [6,666,66]),
    ([42], [47,11], [6,666,66]),
]
param_queries = [
    pytest.param(
        "Investigation [name = '10100601-ST']",
        id="investigations"
    ),
    pytest.param(
        "Dataset <-> Investigation [name = '10100601-ST']",
        id="datasets"
    ),
    pytest.param(
        "Datafile <-> Dataset <-> Investigation [name = '10100601-ST']",
        id="datafiles"
    ),
    pytest.param(
        "SELECT dc FROM DataCollection dc "
        "INCLUDE dc.dataCollectionDatafiles AS dcdf, dcdf.datafile, "
        "dc.dataCollectionDatasets AS dcds, dcds.dataset",
        id="dataCollections"
    ),
]

def get_obj_ids(objs):
    """Return a tuple (invIds, dsIds, dfIds) from a list of objects.
    """
    invIds = set()
    dsIds = set()
    dfIds = set()
    for o in objs:
        if o.BeanName == "Investigation":
            invIds.add(o.id)
        elif o.BeanName == "Dataset":
            dsIds.add(o.id)
        elif o.BeanName == "Datafile":
            dfIds.add(o.id)
        elif o.BeanName == "DataCollection":
            for dcds in o.dataCollectionDatasets:
                if dcds.dataset:
                    dsIds.add(dcds.dataset.id)
            for dcdf in o.dataCollectionDatafiles:
                if dcdf.datafile:
                    dfIds.add(dcdf.datafile.id)
        else:
            raise ValueError("Invalid object <%r>" % o)
    return (invIds, dsIds, dfIds)


@pytest.mark.parametrize(("invIds", "dsIds", "dfIds"), param_ids)
def test_id_dict(invIds, dsIds, dfIds):
    """Initialize a DataSelection from a dict with object ids.
    """
    objs = {
        'investigationIds': invIds,
        'datasetIds': dsIds,
        'datafileIds': dfIds
    }
    selection = DataSelection(objs)
    assert selection.invIds == set(invIds)
    assert selection.dsIds == set(dsIds)
    assert selection.dfIds == set(dfIds)


@pytest.mark.parametrize(("query"), param_queries)
def test_objlist(client, query):
    """Initialize a DataSelection from a list of objects.
    """
    objs = client.search(query)
    invIds, dsIds, dfIds = get_obj_ids(objs)
    selection = DataSelection(objs)
    assert selection.invIds == invIds
    assert selection.dsIds == dsIds
    assert selection.dfIds == dfIds


def test_entitylist(client):
    """Initialize a DataSelection from an EntityList.

    The constructor of DataSelection used to be overly strict such
    that only lists of objects have been accepted, but other sequence
    types such as an EntityList have been rejected.  (Fixed in
    957b0c0.)
    """
    query = "Investigation INCLUDE Dataset [name = '10100601-ST']"
    inv = client.assertedSearch(query)[0]
    objs = inv.datasets
    assert not isinstance(objs, list)
    invIds, dsIds, dfIds = get_obj_ids(objs)
    selection = DataSelection(objs)
    assert selection.invIds == invIds
    assert selection.dsIds == dsIds
    assert selection.dfIds == dfIds


@pytest.mark.parametrize(("query"), param_queries)
def test_set(client, query):
    """Initialize a DataSelection from a set of objects.

    Newer versions of python-icat allow a DataSelection to be created
    from any iterator of objects (not from a Mapping though), in
    particular from a set.
    """
    objs = client.search(query)
    invIds, dsIds, dfIds = get_obj_ids(objs)
    s = set(objs)
    selection = DataSelection(s)
    assert selection.invIds == invIds
    assert selection.dsIds == dsIds
    assert selection.dfIds == dfIds


@pytest.mark.parametrize(("query"), param_queries)
def test_generator(client, query):
    """Initialize a DataSelection from a generator of objects.

    Newer versions of python-icat allow a DataSelection to be created
    from any iterator of objects (not from a Mapping though), in
    particular from a generator.
    """
    def objgenerator(it):
        """Admittedly stupid example for a generator function.
        """
        for o in it:
            yield o
    objs = client.search(query)
    invIds, dsIds, dfIds = get_obj_ids(objs)
    g = objgenerator(objs)
    selection = DataSelection(g)
    assert selection.invIds == invIds
    assert selection.dsIds == dsIds
    assert selection.dfIds == dfIds


@pytest.mark.parametrize(("invIds", "dsIds", "dfIds"), param_ids)
def test_selection(invIds, dsIds, dfIds):
    """Initialize a DataSelection from another DataSelection.
    """
    objs = {
        'investigationIds': invIds,
        'datasetIds': dsIds,
        'datafileIds': dfIds
    }
    sel1 = DataSelection(objs)
    assert sel1.invIds == set(invIds)
    assert sel1.dsIds == set(dsIds)
    assert sel1.dfIds == set(dfIds)
    sel2 = DataSelection(sel1)
    assert sel2.invIds == set(invIds)
    assert sel2.dsIds == set(dsIds)
    assert sel2.dfIds == set(dfIds)
