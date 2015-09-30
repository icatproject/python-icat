"""Test some custom API methods of the icat.client.Client class.
"""

from __future__ import print_function
import pytest
import icat
import icat.config
import icat.exception
from icat.query import Query


# Note: the number of objects returned in the queries and their
# attributes obviously depend on the content of the ICAT and need to
# be kept in sync with the reference input used in the setupicat
# fixture.


def test_assertedSearch_unique(client):
    """Search for a unique object with assertedSearch().
    """
    facility = client.assertedSearch("Facility [name='ESNF']")[0]
    assert facility.BeanName == "Facility"
    assert facility.name == "ESNF"

def test_assertedSearch_fail_not_exist(client):
    """Get an error from assertedSearch() because the object does not exist.
    """
    with pytest.raises(icat.exception.SearchAssertionError) as err:
        facility = client.assertedSearch("Facility [name='FOO']")[0]

def test_assertedSearch_fail_not_unique(client):
    """Get an error from assertedSearch() because the object is not unique.
    """
    with pytest.raises(icat.exception.SearchAssertionError) as err:
        investigation = client.assertedSearch("Investigation")[0]

def test_assertedSearch_range(client):
    """Search for range of objects.
    """
    objs = client.assertedSearch("0,3 User", assertmin=1, assertmax=10)
    assert 1 <= len(objs) <= 10
    assert objs[0].BeanName == "User"

def test_assertedSearch_range_exact(client):
    """Search for known number of objects.
    """
    objs = client.assertedSearch("0,3 User", assertmin=3, assertmax=3)
    assert len(objs) == 3
    assert objs[0].BeanName == "User"

def test_assertedSearch_range_empty(client):
    """Search for range of objects, allowing zero objects to be found.
    """
    objs = client.assertedSearch("Facility [name='FOO']", 
                                 assertmin=0, assertmax=10)
    assert len(objs) <= 10

def test_assertedSearch_range_empty(client):
    """Search for indefinite number of objects.
    """
    objs = client.assertedSearch("Datafile", assertmin=1, assertmax=None)
    assert len(objs) >= 1
    assert objs[0].BeanName == "Datafile"

def test_assertedSearch_range_exact_query(client):
    """Check that Query objects also work with assertedSearch().
    """
    query = Query(client, "User", limit=(0,3))
    objs = client.assertedSearch(query, assertmin=3, assertmax=3)
    assert len(objs) == 3
    assert objs[0].BeanName == "User"

