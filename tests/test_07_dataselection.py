"""Test the DataSelection class from icat.ids.
"""

import pytest
import icat
import icat.config
from icat.ids import DataSelection

# the user to use by the client fixture.
client_user = "root"


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
    assert selection.invIds == invIds
    assert selection.dsIds == dsIds
    assert selection.dfIds == dfIds


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
    invIds = [ o.id for o in objs if o.BeanName == "Investigation" ]
    dsIds = [ o.id for o in objs if o.BeanName == "Dataset" ]
    dfIds = [ o.id for o in objs if o.BeanName == "Datafile" ]
    selection = DataSelection(objs)
    assert selection.invIds == invIds
    assert selection.dsIds == dsIds
    assert selection.dfIds == dfIds


def test_selection():
    """Initialize a DataSelection from another DataSelection.
    """
    invIds = [42]
    dsIds = [47,11]
    dfIds = [6,666,66]
    objs = {
        'investigationIds': invIds,
        'datasetIds': dsIds,
        'datafileIds': dfIds
    }
    sel1 = DataSelection(objs)
    assert sel1.invIds == invIds
    assert sel1.dsIds == dsIds
    assert sel1.dfIds == dfIds
    sel2 = DataSelection(sel1)
    assert sel2.invIds == invIds
    assert sel2.dsIds == dsIds
    assert sel2.dfIds == dfIds
