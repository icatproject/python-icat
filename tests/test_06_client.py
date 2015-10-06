"""Test some custom API methods of the icat.client.Client class.

Note that the basic functionality of the Client class is used
throughout all the tests and thus is implicitly tested, not only in
this module.
"""

from __future__ import print_function
from collections import Iterable, Callable
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

# Try different type of queries: query strings using concise syntax,
# query strings using JPQL style syntax, Query objects.  For each
# type, try both, simple and complex queries.
@pytest.mark.parametrize(("query",), [
    ("User",),
    ("User <-> UserGroup <-> Grouping <-> "
     "InvestigationGroup [role='writer'] <-> "
     "Investigation [name='08100122-EF']",),
    ("SELECT u FROM User u",),
    ("SELECT u FROM User u "
     "JOIN u.userGroups AS ug JOIN ug.grouping AS g "
     "JOIN g.investigationGroups AS ig JOIN ig.investigation AS i "
     "WHERE i.name ='08100122-EF' AND ig.role = 'writer' "
     "ORDER BY u.name",),
    (lambda client: Query(client, "User"),),
    (lambda client: Query(client, "User", order=True, conditions={
        "userGroups.grouping.investigationGroups.role": "= 'writer'", 
        "userGroups.grouping.investigationGroups.investigation.name": "= '08100122-EF'"
    }),),
])
def test_searchChunked_simple(client, query):
    """A simple search with searchChunked().
    """
    # Hack: the parametrize marker above cannot access client,
    # must defer the constrictor call to here.
    if isinstance(query, Callable):
        query = query(client)
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

@pytest.mark.parametrize(("skip", "count", "chunksize"), [
    (0,4,100),
    (2,4,100),
    (2,500,100),
    (2,4,3),
])
def test_searchChunked_limit(client, skip, count, chunksize):
    """Same as test_searchChunked_simple, but adding a limit.
    """
    query = "User"
    users = client.search(query)
    res = client.searchChunked(query, skip=skip, count=count, 
                               chunksize=chunksize)
    assert isinstance(res, Iterable)
    objs = list(res)
    assert objs == users[skip:skip+count]

@pytest.mark.parametrize(("query",), [
    ("User [name LIKE 'j%']",),
    ("SELECT u FROM User u WHERE u.name LIKE 'j%' ORDER BY u.name",),
    (lambda client: Query(client, "User", order=True, conditions={
        "name": "LIKE 'j%'", 
    }),),
])
def test_searchChunked_percent(client, query):
    """Search with searchChunked() with a percent character in the query.
    Issue #13.
    """
    if isinstance(query, Callable):
        query = query(client)
    users = client.search(query)
    res = client.searchChunked(query)
    assert isinstance(res, Iterable)
    objs = list(res)
    assert objs == users

# ==================== test searchUniqueKey() ======================

@pytest.mark.parametrize(("key", "attrs"), [
    ("Facility_name-ESNF", {"name": "ESNF"}),
    ("Investigation_facility-(name-ESNF)_name-12100409=2DST_visitId-1=2E1=2DP", 
     {"name": "12100409-ST", "visitId": "1.1-P"}),
])
def test_searchUniqueKey_simple(client, key, attrs):
    """Search a few objects by their unique key.
    """
    obj = client.searchUniqueKey(key)
    assert obj.BeanName == key.split('_', 1)[0]
    assert obj.id
    for k in attrs:
        assert getattr(obj, k) == attrs[k]

@pytest.mark.parametrize(("key", "relobjs"), [
    ("Dataset_investigation-(facility-(name-ESNF)_name-12100409=2DST_visitId-1=2E1=2DP)_name-e208945", [
        ("investigation", "Investigation_facility-(name-ESNF)_name-12100409=2DST_visitId-1=2E1=2DP"),
        ("investigation.facility", "Facility_name-ESNF"),
    ]),
])
def test_searchUniqueKey_objindex(client, key, relobjs):
    """Test caching of objects in the objindex.
    """
    objindex = {}
    obj = client.searchUniqueKey(key, objindex=objindex)
    assert obj.BeanName == key.split('_', 1)[0]
    assert obj.id
    assert objindex[key] == obj
    for (a, k) in relobjs:
        assert k in objindex
        assert objindex[k].BeanName == k.split('_', 1)[0]
        assert objindex[k].id
        # Reestablish the relation
        o = obj
        for ac in a.split('.')[:-1]:
            o = getattr(o, ac)
        setattr(o, a.rsplit('.',1)[-1], objindex[k])
    assert obj.getUniqueKey() == key

def test_searchUniqueKey_objindex_preset(client):
    """Test presetting the objindex.

    Objects may be added to the objindex beforehand and will then
    not be searched from the server.
    """
    ds = client.assertedSearch("Dataset [name='e208945']")[0]
    # Deliberately choose a key that would not be found otherwise.
    dskey = "Dataset_foo"
    objindex = {dskey : ds}
    obj = client.searchUniqueKey(dskey, objindex=objindex)
    assert obj == ds
