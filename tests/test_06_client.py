"""Test some custom API methods of the icat.client.Client class.

Note that the basic functionality of the Client class is used
throughout all the tests and thus is implicitly tested, not only in
this module.
"""

from __future__ import print_function
from collections import Iterable
import pytest
import icat
import icat.config
import icat.exception
from icat.query import Query


# Note: the number of objects returned in the queries and their
# attributes obviously depend on the content of the ICAT and need to
# be kept in sync with the reference input used in the setupicat
# fixture.


# ==================== test assertedSearch() =======================

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

# ===================== test searchChunked() =======================

def test_searchChunked_simple(client):
    """A simple search with searchChunked().
    """
    query = "User"
    # Do a normal search as a reference first, the result from
    # searchChunked() should be the same.
    users = client.search(query)
    res = client.searchChunked(query)
    # Note that searchChunked() returns a generator, not a list.  Be
    # somewhat less specific in the test, only assume the result to
    # be iterable.
    assert isinstance(res, Iterable)
    # turn it to a list so we can inspect the acual search result.
    objs = list(res)
    assert objs == users

def test_searchChunked_simple_jpql(client):
    """Same as test_searchChunked_simple, but using JPQL style query.
    """
    query = "SELECT o FROM User o"
    users = client.search(query)
    res = client.searchChunked(query)
    assert isinstance(res, Iterable)
    objs = list(res)
    assert objs == users

def test_searchChunked_simple_query(client):
    """Same as test_searchChunked_simple, but using a Query object.
    """
    query = Query(client, "User")
    users = client.search(query)
    res = client.searchChunked(query)
    assert isinstance(res, Iterable)
    objs = list(res)
    assert objs == users

def test_searchChunked_chunksize(client):
    """Same as test_searchChunked_simple, but setting a chunksize now.
    """
    # chunksize is an internal tuning parameter in searchChunked()
    # that should not have any visible impact on the result.  So we
    # may test the same assumptions as above.  We choose the
    # chunksize small enough such that that the result cannot be
    # fetched at once and thus force searchChunked() to repeat the
    # search internally.
    query = "User"
    users = client.search(query)
    chunksize = int(len(users)/2)
    if chunksize < 1:
        pytest.skip("too few objects for this test")
    res = client.searchChunked(query, chunksize=chunksize)
    assert isinstance(res, Iterable)
    objs = list(res)
    assert objs == users

def test_searchChunked_limit(client):
    """Same as test_searchChunked_simple, but adding a limit.
    """
    query = "User"
    users = client.search(query)
    s = 2
    c = 4
    res = client.searchChunked(query, skip=s, count=c)
    assert isinstance(res, Iterable)
    objs = list(res)
    assert objs == users[s:s+c]

def test_searchChunked_limit_toomany(client):
    """Same as test_searchChunked_limit, but choose an exceedingly large count.
    """
    query = "User"
    users = client.search(query)
    # Searching for len(users) after having skipped two is always
    # two more then available.
    s = 2
    c = len(users)
    res = client.searchChunked(query, skip=s, count=c)
    assert isinstance(res, Iterable)
    objs = list(res)
    assert objs == users[s:]

def test_searchChunked_limit_chunked(client):
    """Same as test_searchChunked_limit, but additionally setting a chunksize.
    """
    query = "User"
    users = client.search(query)
    s = 2
    c = 4
    res = client.searchChunked(query, skip=s, count=c, chunksize=3)
    assert isinstance(res, Iterable)
    objs = list(res)
    assert objs == users[s:s+c]
