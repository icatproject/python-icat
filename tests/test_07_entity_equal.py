"""Test the equality and hashing of entity objects.

Equality is defined by the __eq__() and __ne__() methods.  Hashing is
defined by the __hash__() method.
"""

import pytest
import icat
import icat.config

user = "root"

@pytest.fixture(scope="module")
def client(setupicat, icatconfigfile):
    args = ["-c", icatconfigfile, "-s", user]
    conf = icat.config.Config().getconfig(args)
    client = icat.Client(conf.url, **conf.client_kwargs)
    client.login(conf.auth, conf.credentials)
    return client


def test_equality_fetched_ne(client):
    """Fetch a few distinct objects and test that indeed they are not equal.
    """
    (u1, u2, u3) = client.assertedSearch("0,3 User", assertmin=3, assertmax=3)
    # Since theses real objects from the ICAT, they are guaranteed to
    # be different.
    assert u1 != u2
    assert u1 != u3
    assert u2 != u3
    assert not (u1 == u2)
    assert not (u1 == u3)
    assert not (u2 == u3)

def test_equality_fetched_eq(client):
    """Verify that equal objects are equal.
    """
    (u1, u2) = client.assertedSearch("0,2 User", assertmin=2, assertmax=2)
    # Same as above.
    assert u1 != u2
    assert not (u1 == u2)
    # Of course, each object should be equal to itself.
    assert u1 is u1
    assert u1 == u1
    assert not (u1 != u1)
    # Now make them look equal, equality is defined by object id.
    u2.id = u1.id
    assert u1 == u2
    assert not (u1 != u2)
    # Equal objects MUST have the same hash value.
    assert hash(u1) == hash(u2)
    # Note that it doesn't matter that the name attribute is still different.
    assert u1.name != u2.name

def test_equality_new(client):
    """Create a few objects qith new and test for equality.
    """
    u1 = client.new("user")
    u2 = client.new("user")
    # Newly created objects are always unequal, although all their
    # attributes are equal here.  But as long as the id is not set,
    # equality is defined as identity.
    assert u1 != u2
    assert not (u1 == u2)
    # if the id is set to the same value, they become equal.
    u1.id = u2.id = 42
    assert u1 == u2
    assert not (u1 != u2)
    assert hash(u1) == hash(u2)
    # Again, other attributes do not matter.
    u1.name = "foo"
    u2.name = "Bar"
    assert u1 == u2
    assert not (u1 != u2)
    assert hash(u1) == hash(u2)

def test_equality_client(client, icatconfigfile):
    """Test that objects that belong to different clients are never equal.

    There used to be a bug such that the client was not taken into
    account, fixed in c9a1be6.
    """
    # Get a second client that is connected as the same user to the
    # same server and even shares the same ICAT session.
    args = ["-c", icatconfigfile, "-s", user]
    conf = icat.config.Config().getconfig(args)
    client2 = icat.Client(conf.url, **conf.client_kwargs)
    client2.sessionId = client.sessionId
    u1 = client.assertedSearch("0,1 User")[0]
    u2 = client2.assertedSearch("User [id=%d]" % u1.id)[0]
    # u1 and u2 correspond to the same user at the ICAT server and
    # thus have all attributes, including the id the same.
    assert u1.id == u2.id
    assert u1.name == u2.name
    assert u1.fullName == u2.fullName
    # But they belong to different client instances and thus, they are
    # still not equal.
    assert u1 != u2
    assert not (u1 == u2)
    # Both clients share the same session, make sure they do not log
    # out twice.
    client2.sessionId = None

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
    o1 = client.new("datafileFormat")
    o1.id = 42
    o2 = client.new("investigationType")
    o2.id = 42
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
    o1 = client.new("investigation", name="Foo", id=42)
    o2 = client.new("dataset", investigation=o1, name="Foo-Bar", id=43)
    o3 = client.new("dataset", name="Bar", id=43)
    o4 = client.new("datafile", dataset=o2, name="Foo-Bar-Baz", id=44)
    o5 = client.new("investigation", name="Bla", id=45)
    o6 = client.new("investigation", name="Blup", id=42)
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
    o1 = client.new("investigation", name="Foo", id=42)
    o2 = client.new("dataset", investigation=o1, name="Foo-Bar", id=42)
    o3 = client.new("dataset", name="Bar", id=42)
    o4 = client.new("datafile", dataset=o2, name="Foo-Bar-Baz", id=42)
    o5 = client.new("investigation", name="Bla", id=43)
    o6 = client.new("investigation", name="Blup", id=42)
    s = set([o1, o2, o3, o4, o5, o6])
    assert len(s) == 4
    assert s == set([o1, o2, o4, o5])
    assert s == set([o6, o3, o4, o5])

