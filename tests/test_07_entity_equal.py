"""Test the equality and hashing of entity objects.

Equality is defined by the __eq__() and __ne__() methods.  Hashing is
defined by the __hash__() method.
"""

import pytest
import icat
import icat.config
from conftest import getConfig


@pytest.fixture(scope="module")
def client():
    client, _ = getConfig(needlogin=False)
    return client


def test_equality_eq(client):
    """Verify that equal objects are equal.
    """
    u1 = client.new("User", id=42, name="u_a")
    u2 = client.new("User", id=42, name="u_b")
    # Of course, each object should be equal to itself.
    assert u1 is u1
    assert u1 == u1
    assert not (u1 != u1)
    # Equality is defined by object id.  Note that it doesn't matter
    # that the name attribute is still different.
    assert u1 is not u2
    assert u1 == u2
    assert not (u1 != u2)
    # Equal objects MUST have the same hash value.
    assert hash(u1) == hash(u2)

def test_equality_ne(client):
    """Consider distinct objects.
    """
    u1 = client.new("User", id=728, name="u_a")
    u2 = client.new("User", id=949, name="u_b")
    u3 = client.new("User", id=429, name="u_c")
    assert u1 != u2
    assert u1 != u3
    assert u2 != u3
    assert not (u1 == u2)
    assert not (u1 == u3)
    assert not (u2 == u3)

def test_equality_new(client):
    """Consider new (e.g. not yet created) objects.
    """
    u1 = client.new("User", name="u_a")
    u2 = client.new("User", name="u_a")
    # Note that we did not set the id.  New objects are always
    # unequal, although all their attributes are equal here.  But as
    # long as the id is not set, equality is defined as identity.
    assert u1 is not u2
    assert u1 != u2
    assert not (u1 == u2)

def test_equality_client(client):
    """Test that objects that belong to different clients are never equal.

    There used to be a bug such that the client was not taken into
    account, fixed in c9a1be6.
    """
    # Get a second client that is connected to the same server.
    client2, _ = getConfig(needlogin=False)
    u1 = client.new("User", id=728, name="u_a")
    u2 = client2.new("User", id=728, name="u_a")
    # u1 and u2 have all attributes, including the id the same.
    assert u1.id == u2.id
    assert u1.name == u2.name
    # But they belong to different client instances and thus, they are
    # still not equal.
    assert u1 != u2
    assert not (u1 == u2)

def test_equality_type(client):
    """Test that objects of different entity types are never equal.

    Note: for ICAT up to version 4.4 the id of an entity object was
    guaranteed to be globally unique.  There was no need to consider
    the object type when checking for equality, considering the id was
    sufficient.  This has been changed in ICAT 4.5.0: now object ids
    are only unique among all objects of the same type.  Objects must
    not be considered equal if they are of different type, even if
    they have the same id.  This test would fail for python-icat
    0.8.0.
    """
    # Have two objects with the same id but different type.
    o1 = client.new("DatafileFormat", id=42)
    o2 = client.new("InvestigationType", id=42)
    assert o1 != o2
    assert not (o1 == o2)

def test_hash(client):
    """Test that putting objects in a set works as expected.

    This implicitly tests the hashing of objects, as the
    implementation of set relies on the hashes.
    """
    # Create a few objects, some of them are equal, some not.  We have
    # six objects, all differ in the name attribute.  But still o1 ==
    # o6 and o2 == o3 and thus we have in fact only four different
    # objects.
    o1 = client.new("Investigation", name="Foo", id=42)
    o2 = client.new("Dataset", investigation=o1, name="Foo-Bar", id=43)
    o3 = client.new("Dataset", name="Bar", id=43)
    o4 = client.new("Datafile", dataset=o2, name="Foo-Bar-Baz", id=44)
    o5 = client.new("Investigation", name="Bla", id=45)
    o6 = client.new("Investigation", name="Blup", id=42)
    s = set([o1, o2, o3, o4, o5, o6])
    assert len(s) == 4
    assert s == set([o1, o2, o4, o5])
    assert s == set([o6, o3, o4, o5])

def test_hash_type(client):
    """Test that putting objects in a set works as expected.

    Same test as test_hash(), but this time, we have objects of
    different type with the same id.  These must be considered not
    equal.  Same note as for test_equality_type() applies.
    """
    # Create a few objects, some of them are equal, some not.  We have
    # six objects, all differ in the name attribute.  But still o1 ==
    # o6 and o2 == o3 and thus we have in fact only four different
    # objects.
    o1 = client.new("Investigation", name="Foo", id=42)
    o2 = client.new("Dataset", investigation=o1, name="Foo-Bar", id=42)
    o3 = client.new("Dataset", name="Bar", id=42)
    o4 = client.new("Datafile", dataset=o2, name="Foo-Bar-Baz", id=42)
    o5 = client.new("Investigation", name="Bla", id=43)
    o6 = client.new("Investigation", name="Blup", id=42)
    s = set([o1, o2, o3, o4, o5, o6])
    assert len(s) == 4
    assert s == set([o1, o2, o4, o5])
    assert s == set([o6, o3, o4, o5])

