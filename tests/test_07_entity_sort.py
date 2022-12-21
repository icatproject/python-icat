"""Test sorting of entity objects.
"""

import pytest
import icat
import icat.config
from conftest import getConfig


@pytest.fixture(scope="module")
def client():
    client, _ = getConfig(needlogin=False)
    return client


def test_sort_users(client):
    """Sort Users.

    This is the most simple sorting example: Users are sorted by the
    name attribute.
    """
    u1 = client.new("User", id=728, name="u_a")
    u2 = client.new("User", id=949, name="u_c")
    u3 = client.new("User", id=429, name="u_b")
    users = [ u1, u2, u3 ]
    users.sort(key=icat.entity.Entity.__sortkey__)
    assert users == [ u1, u3, u2 ]


def test_sort_datafile_only(client):
    """Sort Datafiles with no Datasets.

    Datafiles having no relation to a Dataset are sorted by the name
    attribute.
    """
    df1 = client.new("Datafile", id=937, name="df_b")
    df2 = client.new("Datafile", id=391, name="df_d")
    df3 = client.new("Datafile", id=819, name="df_e")
    df4 = client.new("Datafile", id=805, name="df_b")
    df5 = client.new("Datafile", id=579, name="df_d")
    df6 = client.new("Datafile", id=652, name="df_a")
    df7 = client.new("Datafile", id=694, name="df_c")
    datafiles = [ df1, df2, df3, df4, df5, df6, df7 ]
    datafiles.sort(key=icat.entity.Entity.__sortkey__)
    # Note: this relies on the fact that list.sort() is guaranteed to
    # be stable (in Python 2.3 and newer), e.g. that df1 will be
    # before df4 and df2 before df5 in the result.
    assert datafiles == [ df6, df1, df4, df7, df2, df5, df3 ]


def test_sort_datafile_dataset(client):
    """Sort Datafiles with Datasets.

    Datafiles having a relation to a Dataset (not related to an
    investigation in turn) are sorted by (dataset.name, name).
    """
    ds1 = client.new("Dataset", id=592, name="ds_a")
    ds2 = client.new("Dataset", id=341, name="ds_b")
    df1 = client.new("Datafile", id=429, name="df_b", dataset=ds1)
    df2 = client.new("Datafile", id=229, name="df_d", dataset=ds2)
    df3 = client.new("Datafile", id=286, name="df_e", dataset=ds1)
    df4 = client.new("Datafile", id=584, name="df_b", dataset=ds2)
    df5 = client.new("Datafile", id=432, name="df_d", dataset=ds1)
    df6 = client.new("Datafile", id=477, name="df_a", dataset=ds2)
    df7 = client.new("Datafile", id=404, name="df_c", dataset=ds1)
    datafiles = [ df1, df2, df3, df4, df5, df6, df7 ]
    datafiles.sort(key=icat.entity.Entity.__sortkey__)
    assert datafiles == [ df1, df7, df5, df3, df6, df4, df2 ]
    # Now lets reverse the order of the datasets and try again.
    ds1.name = "ds_x"
    datafiles.sort(key=icat.entity.Entity.__sortkey__)
    assert datafiles == [ df6, df4, df2, df1, df7, df5, df3 ]


def test_sort_datafile_mix(client):
    """Sort Datafiles with and without Datasets.

    A mixture of Datafiles, some with and some without a Dataset.
    This sorts the ones without Dataset first.

    There used to be a bug in __sortkey__() that triggered a TypeError
    in Python 3 in this case, fixed in 8f33ae1.
    """
    ds1 = client.new("Dataset", id=550, name="ds_a")
    ds2 = client.new("Dataset", id=301, name="ds_b")
    df1 = client.new("Datafile", id=978, name="df_b", dataset=ds1)
    df2 = client.new("Datafile", id=736, name="df_d", dataset=ds2)
    df3 = client.new("Datafile", id=969, name="df_e", dataset=ds1)
    df4 = client.new("Datafile", id=127, name="df_b")
    df5 = client.new("Datafile", id=702, name="df_d")
    df6 = client.new("Datafile", id=631, name="df_a", dataset=ds2)
    df7 = client.new("Datafile", id=765, name="df_c")
    datafiles = [ df1, df2, df3, df4, df5, df6, df7 ]
    datafiles.sort(key=icat.entity.Entity.__sortkey__)
    assert datafiles == [ df4, df7, df5, df1, df3, df6, df2 ]
    # Now lets reverse the order of the datasets and try again.
    ds1.name = "ds_x"
    datafiles.sort(key=icat.entity.Entity.__sortkey__)
    assert datafiles == [ df4, df7, df5, df6, df2, df1, df3 ]


def test_sort_mixed_objects(client):
    """Sort some objects of various different entity types.

    Objects of different types are sorted by type and then according
    to the type specific order within a given type.
    """
    u1 = client.new("User", id=79, name="a")
    u2 = client.new("User", id=711, name="b")
    u3 = client.new("User", id=554, name="c")
    inv1 = client.new("Investigation", id=14, name="a")
    ds1 = client.new("Dataset", id=982, name="a")
    ds2 = client.new("Dataset", id=652, name="c")
    ds3 = client.new("Dataset", id=150, name="b", investigation=inv1)
    df1 = client.new("Datafile", id=809, name="b")
    df2 = client.new("Datafile", id=161, name="c")
    df3 = client.new("Datafile", id=634, name="d")
    df4 = client.new("Datafile", id=98, name="b", dataset=ds1)
    df5 = client.new("Datafile", id=935, name="e", dataset=ds1)
    df6 = client.new("Datafile", id=226, name="a", dataset=ds2)
    df7 = client.new("Datafile", id=988, name="d", dataset=ds2)
    objects = [ df3, u2, u3, ds2, ds1, inv1, df5, 
                df4, df6, df7, ds3, df2, u1, df1 ]
    objects.sort(key=icat.entity.Entity.__sortkey__)
    assert objects == [ df1, df2, df3, df4, df5, df6, df7, 
                        ds1, ds2, ds3, inv1, u1, u2, u3 ]


def test_sort_datacollection_datafile(client):
    """Sort DataCollections with Datafiles.

    DataCollection does not have any attributes or many to one
    relationships.  The only criterion that could be used for sorting
    are one to many relationships.  DataCollections are sorted by
    Datasets first and then by Datafiles.

    There used to be a bug in the code such that __sortkey__() was
    thoroughly broken in this case, fixed in 0df5832.
    """
    # First test with only Datafiles.
    df1 = client.new("Datafile", id=143, name="df_a")
    df2 = client.new("Datafile", id=306, name="df_b")
    df3 = client.new("Datafile", id=765, name="df_c")
    df4 = client.new("Datafile", id=871, name="df_d")
    dcdf1 = client.new("DataCollectionDatafile", id=790, datafile=df1)
    dcdf2 = client.new("DataCollectionDatafile", id=895, datafile=df2)
    dcdf3 = client.new("DataCollectionDatafile", id=611, datafile=df3)
    dcdf4 = client.new("DataCollectionDatafile", id=28, datafile=df4)
    dc1 = client.new("DataCollection", id=658)
    dc1.dataCollectionDatafiles=[ dcdf3 ]
    dc2 = client.new("DataCollection", id=424)
    dc2.dataCollectionDatafiles=[ dcdf2, dcdf4 ]
    dc3 = client.new("DataCollection", id=172)
    dc3.dataCollectionDatafiles=[ dcdf1 ]
    dc4 = client.new("DataCollection", id=796)
    dc4.dataCollectionDatafiles=[ dcdf4 ]
    dc5 = client.new("DataCollection", id=797)
    dc5.dataCollectionDatafiles=[ dcdf2 ]
    dc6 = client.new("DataCollection", id=607)
    dc6.dataCollectionDatafiles=[]
    dc7 = client.new("DataCollection", id=485)
    dc7.dataCollectionDatafiles=[ dcdf2, dcdf3, dcdf4 ]
    dataCollections = [ dc1, dc2, dc3, dc4, dc5, dc6, dc7 ]
    dataCollections.sort(key=icat.entity.Entity.__sortkey__)
    assert dataCollections == [ dc6, dc3, dc5, dc7, dc2, dc1, dc4 ]
    # Now, add a few Datasets.
    ds1 = client.new("Dataset", id=508, name="ds_a")
    ds2 = client.new("Dataset", id=673, name="ds_b")
    dcds1 = client.new("DataCollectionDataset", id=184, dataset=ds1)
    dcds2 = client.new("DataCollectionDataset", id=361, dataset=ds2)
    dc4.dataCollectionDatasets=[ dcds1, dcds2 ]
    dc5.dataCollectionDatasets=[ dcds1 ]
    dc6.dataCollectionDatasets=[ dcds1, dcds2 ]
    dc7.dataCollectionDatasets=[ dcds1 ]
    dataCollections.sort(key=icat.entity.Entity.__sortkey__)
    assert dataCollections == [ dc3, dc2, dc1, dc5, dc7, dc6, dc4 ]


def test_sort_datacollection_datafile_order_mrel(client):
    """Sort DataCollections with Datafiles.

    The order of the DataCollectionDatafiles in DataCollection should
    not matter for the sort key.  This used to be broken, fixed in
    baac4b2.
    """
    df1 = client.new("Datafile", id=62, name="df_a")
    df2 = client.new("Datafile", id=471, name="df_b")
    df3 = client.new("Datafile", id=113, name="df_c")
    df4 = client.new("Datafile", id=810, name="df_d")
    dcdf1 = client.new("DataCollectionDatafile", id=850, datafile=df1)
    dcdf2 = client.new("DataCollectionDatafile", id=741, datafile=df2)
    dcdf3 = client.new("DataCollectionDatafile", id=18, datafile=df3)
    dcdf4 = client.new("DataCollectionDatafile", id=888, datafile=df4)
    dc1 = client.new("DataCollection", id=861)
    dc1.dataCollectionDatafiles=[ dcdf3 ]
    dc2 = client.new("DataCollection", id=859)
    dc2.dataCollectionDatafiles=[ dcdf2, dcdf4 ]
    dc3 = client.new("DataCollection", id=402)
    dc3.dataCollectionDatafiles=[ dcdf1 ]
    dc4 = client.new("DataCollection", id=190)
    dc4.dataCollectionDatafiles=[ dcdf4 ]
    dc5 = client.new("DataCollection", id=687)
    dc5.dataCollectionDatafiles=[ dcdf2 ]
    dc6 = client.new("DataCollection", id=230)
    dc6.dataCollectionDatafiles=[]
    dc7 = client.new("DataCollection", id=701)
    dc7.dataCollectionDatafiles=[ dcdf3, dcdf4, dcdf2 ]
    dc8 = client.new("DataCollection", id=747)
    dc8.dataCollectionDatafiles=[ dcdf4, dcdf2, dcdf3 ]
    dc9 = client.new("DataCollection", id=501)
    dc9.dataCollectionDatafiles=[ dcdf2, dcdf4, dcdf3 ]
    dataCollections = [ dc1, dc2, dc3, dc4, dc5, dc6, dc7, dc8, dc9 ]
    # Note that dc7, dc8, and dc9 are all equal and sort before dc2.
    dataCollections.sort(key=icat.entity.Entity.__sortkey__)
    assert dataCollections == [ dc6, dc3, dc5, dc7, dc8, dc9, dc2, dc1, dc4 ]


def test_datacollection_sortkey_max_recursion(client):
    """Entity.__sortkey__() may enter in an infinite recursion.  Issue #14.
    """
    df1 = client.new("Datafile", name="df_a")
    dc1 = client.new("DataCollection")
    dcdf1 = client.new("DataCollectionDatafile",
                       datafile=df1, dataCollection=dc1)
    dc1.dataCollectionDatafiles.append(dcdf1)
    df1.dataCollectionDatafiles.append(dcdf1)
    print(dc1.__sortkey__())


def test_sortattrs_dependencies(client):
    """Check that there are no circular dependencies for sort attributes.

    The cause for Bug #14 was that DataCollections were sorted by
    Datasets and Datafiles via DataCollectionDatafile and
    DataCollectionDataset respectively and that sorting of the latter
    was by DataCollection.  The fix was to break this circular
    dependency.

    This test verifies that there are no further circular dependencies
    for sort attributes in the entity object classes.
    """
    def checkSortDependency(cls, recursionList=()):
        """Helper function."""
        if cls.BeanName in recursionList:
            raise RuntimeError("Circular sorting dependency detected: %s" 
                               % " -> ".join(recursionList))
        rl = list(recursionList)
        rl.append(cls.BeanName)
        deplist = []
        sortAttrs = cls.SortAttrs or cls.Constraint
        for a in sortAttrs:
            if a in cls.InstRel or a in cls.InstMRel:
                rname = cls.getAttrInfo(client, a).type
                deplist.append(rname)
                rcls = client.getEntityClass(rname)
                deplist.extend(checkSortDependency(rcls, rl))
        return deplist

    for cls in client.typemap.values():
        if cls.BeanName is None:
            continue
        deplist = checkSortDependency(cls)
        print("%s: %s" % (cls.BeanName, ", ".join(deplist)))
