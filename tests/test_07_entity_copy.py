"""Test the copy method of entity objects.

This method returns a shallow copy of the original entity object.

This has some subtile consequences: the returned object has all
attributes set to a copy of the corresponding values of original
object.  The relations are copied by reference, i.e. the original and
the copy refer to the same related object.
"""

import pytest
import icat
import icat.config
from conftest import getConfig


@pytest.fixture(scope="module")
def client():
    client, _ = getConfig(needlogin=False)
    return client


def test_copy_instattr(client):
    """Consider normal attributes of original and copy.
    """
    name1 = "Dataset X"
    name2 = "Dataset Y"
    ds = client.new("Dataset", id=541, name=name1)
    cds = ds.copy()
    assert cds == ds
    assert cds.id == ds.id
    assert cds.name == name1
    # Changing attributes of the copy does not affect the original.
    cds.name = name2
    assert ds.name == name1


def test_copy_instrel(client):
    """Consider many to one relationships of original and copy.
    """
    name1 = "Dataset X"
    name2 = "Dataset Y"
    invname1 = "Investigation A"
    invname2 = "Investigation B"
    inv = client.new("Investigation", id=82, name=invname1)
    ds = client.new("Dataset", id=541, investigation=inv, name=name1)
    cds = ds.copy()
    assert cds.investigation == ds.investigation
    assert cds.investigation.id == ds.investigation.id
    assert cds.investigation.name == invname1
    # The copy and the original refer to the same related objects.
    # Changing attributes of a related object of the copy does affect
    # the original.
    cds.investigation.name = invname2
    assert ds.investigation.name == invname2


def test_copy_instmrel(client):
    """Consider one to many relationships of original and copy.

    One to many relationships are stored in lists of objects.  The
    copy method creates shallow copies of these lists.
    """
    df1 = client.new("Datafile", id=568, name="df_a.dat")
    df2 = client.new("Datafile", id=450, name="df_b.dat")
    df3 = client.new("Datafile", id=141, name="df_c.dat")
    df4 = client.new("Datafile", id=593, name="df_d.dat")
    ds = client.new("Dataset", id=684, name="Dataset X")
    ds.datafiles = [ df1, df2, df3 ]
    cds = ds.copy()
    assert cds.datafiles == [ df1, df2, df3 ]
    # Modifying the object list in the copy does not affect the original.
    cds.datafiles.append(df4)
    assert cds.datafiles == [ df1, df2, df3, df4 ]
    assert ds.datafiles == [ df1, df2, df3 ]
    # Modifying an object in this list in the copy does affect the original.
    cds.datafiles[1].name = "df_b.txt"
    assert ds.datafiles[1].name == "df_b.txt"
