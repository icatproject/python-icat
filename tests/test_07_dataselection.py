"""Test the DataSelection class from icat.ids.
"""

import pytest
import icat
import icat.config
from icat.ids import DataSelection
from conftest import getConfig


@pytest.fixture(scope="module")
def client(setupicat):
    client, conf = getConfig(confSection="nbour")
    client.login(conf.auth, conf.credentials)
    return client


@pytest.mark.parametrize(("invIds", "dsIds", "dfIds"), [
    ([42], [], []),
    ([], [47,11], []),
    ([], [], [6,666,66]),
    ([42], [47,11], [6,666,66]),
])
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


@pytest.mark.parametrize(("query"), [
    ("Investigation [name = '10100601-ST']"),
    ("Dataset <-> Investigation [name = '10100601-ST']"),
    ("Datafile <-> Dataset <-> Investigation [name = '10100601-ST']"),
])
def test_objlist(client, query):
    """Initialize a DataSelection from a list of objects.
    """
    objs = client.search(query)
    invIds = [ o.id for o in objs if o.BeanName == "Investigation" ]
    dsIds = [ o.id for o in objs if o.BeanName == "Dataset" ]
    dfIds = [ o.id for o in objs if o.BeanName == "Datafile" ]
    selection = DataSelection(objs)
    assert selection.invIds == set(invIds)
    assert selection.dsIds == set(dsIds)
    assert selection.dfIds == set(dfIds)


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
    invIds = [ o.id for o in objs if o.BeanName == "Investigation" ]
    dsIds = [ o.id for o in objs if o.BeanName == "Dataset" ]
    dfIds = [ o.id for o in objs if o.BeanName == "Datafile" ]
    selection = DataSelection(objs)
    assert selection.invIds == set(invIds)
    assert selection.dsIds == set(dsIds)
    assert selection.dfIds == set(dfIds)


@pytest.mark.parametrize(("query"), [
    ("Investigation [name = '10100601-ST']"),
    ("Dataset <-> Investigation [name = '10100601-ST']"),
    ("Datafile <-> Dataset <-> Investigation [name = '10100601-ST']"),
])
def test_set(client, query):
    """Initialize a DataSelection from a set of objects.

    Newer versions of python-icat allow a DataSelection to be created
    from any iterator of objects (not from a Mapping though), in
    particular from a set.
    """
    objs = client.search(query)
    invIds = [ o.id for o in objs if o.BeanName == "Investigation" ]
    dsIds = [ o.id for o in objs if o.BeanName == "Dataset" ]
    dfIds = [ o.id for o in objs if o.BeanName == "Datafile" ]
    s = set(objs)
    selection = DataSelection(s)
    assert selection.invIds == set(invIds)
    assert selection.dsIds == set(dsIds)
    assert selection.dfIds == set(dfIds)


@pytest.mark.parametrize(("query"), [
    ("Investigation [name = '10100601-ST']"),
    ("Dataset <-> Investigation [name = '10100601-ST']"),
    ("Datafile <-> Dataset <-> Investigation [name = '10100601-ST']"),
])
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
    invIds = [ o.id for o in objs if o.BeanName == "Investigation" ]
    dsIds = [ o.id for o in objs if o.BeanName == "Dataset" ]
    dfIds = [ o.id for o in objs if o.BeanName == "Datafile" ]
    g = objgenerator(objs)
    selection = DataSelection(g)
    assert selection.invIds == set(invIds)
    assert selection.dsIds == set(dsIds)
    assert selection.dfIds == set(dfIds)


@pytest.mark.parametrize(("invIds", "dsIds", "dfIds"), [
    ([42], [], []),
    ([], [47,11], []),
    ([], [], [6,666,66]),
    ([42], [47,11], [6,666,66]),
])
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
