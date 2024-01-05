"""Test some custom API methods of the icat.client.Client class.

Note that the basic functionality of the Client class is used
throughout all the tests and thus is implicitly tested, not only in
this module.
"""

from collections.abc import Iterable, Callable, Sequence
import datetime
import pytest
import icat
import icat.config
import icat.exception
from icat.query import Query
from conftest import getConfig, tmpSessionId


@pytest.fixture(scope="module")
def client(setupicat):
    client, conf = getConfig()
    client.login(conf.auth, conf.credentials)
    return client


# Note: the number of objects returned in the queries and their
# attributes obviously depend on the content of the ICAT and need to
# be kept in sync with the reference input used in the setupicat
# fixture.


# ======================== test logout() ===========================

def test_logout_no_session_error(client):
    """Issue #43: logout() should silently ignore ICATSessionError.
    """
    with tmpSessionId(client, "-=- Invalid -=-"):
        client.logout()

# ========================== test new() ============================

def test_new_obj_instance(client):
    """Pass an instance object to new.
    """
    entity = client.assertedSearch("Facility")[0]
    obj = client.new(entity.instance)
    assert obj == entity

@pytest.mark.parametrize(("typename", "beanname"), [
    ("investigation", "Investigation"),
    ("Investigation", "Investigation"),
    ("INVESTIGATION", "Investigation"),
    ("investigationUser", "InvestigationUser"),
    ("InvestigationUser", "InvestigationUser"),
    ("INVESTIGATIONUSER", "InvestigationUser"),
])
def test_new_obj_name(client, typename, beanname):
    """Pass the name of the object type to new.

    In earlier versions, this name was case sensitive and needed to be
    spelled as indicated in the WSDL downloaded from icat.server.  In
    #104, this has been changed, so that the type name is case
    insensitive now.  As result, the type can now be spelled as in the
    ICAT schema.
    """
    obj = client.new(typename)
    assert obj.BeanName == beanname

def test_new_obj_none(client):
    """Pass None to new.
    """
    assert client.new(None) is None

# ======================== test search() ===========================

cet = datetime.timezone(datetime.timedelta(hours=1))
cest = datetime.timezone(datetime.timedelta(hours=2))

@pytest.mark.parametrize(("query", "result"), [
    pytest.param(
        "SELECT o.name, o.title, o.startDate FROM Investigation o",
        [("08100122-EF", "Durol single crystal",
          datetime.datetime(2008, 3, 13, 11, 39, 42, tzinfo=cet)),
         ("10100601-ST", "Ni-Mn-Ga flat cone",
          datetime.datetime(2010, 9, 30, 12, 27, 24, tzinfo=cest)),
         ("12100409-ST", "NiO SC OF1 JUH HHL",
          datetime.datetime(2012, 7, 26, 17, 44, 24, tzinfo=cest))],
        id="inv_attrs"
    ),
    pytest.param(
        "SELECT i.name, ds.name FROM Dataset ds JOIN ds.investigation AS i "
        "WHERE i.startDate < '2011-01-01'",
        [("08100122-EF", "e201215"),
         ("08100122-EF", "e201216"),
         ("10100601-ST", "e208339"),
         ("10100601-ST", "e208341"),
         ("10100601-ST", "e208342")],
        id="inv_ds_name"
    ),
])
def test_search_mulitple_fields(client, query, result):
    """Search for mutliple fields.

    Newer versions of icat.server allow to select multiple fields in a
    search expression (added in icatproject/icat.server#246).  Test
    client side support for this.
    """
    if not client._has_wsdl_type('fieldSet'):
        pytest.skip("search for multiple fields not supported by this server")
    r = client.search(query)
    assert r == result

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

def test_assertedSearch_range_indefinite(client):
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

def test_assertedSearch_unique_mulitple_fields(client):
    """Search for some attributes of a unique object with assertedSearch().
    """
    if not client._has_wsdl_type('fieldSet'):
        pytest.skip("search for multiple fields not supported by this server")
    query = ("SELECT i.name, i.title, i.startDate FROM Investigation i "
             "WHERE i.name = '08100122-EF'")
    result = ("08100122-EF", "Durol single crystal",
              datetime.datetime(2008, 3, 13, 11, 39, 42, tzinfo=cet))
    r = client.assertedSearch(query)[0]
    assert isinstance(r, Sequence)
    assert r == result

# ===================== test searchChunked() =======================

# Try different type of queries: query strings using concise syntax,
# query strings using JPQL style syntax, Query objects.  For each
# type, try both, simple and complex queries.
@pytest.mark.parametrize(("query",), [
    pytest.param("User", id="legacy_user"),
    pytest.param(
        "User <-> UserGroup <-> Grouping <-> "
        "InvestigationGroup [role='writer'] <-> "
        "Investigation [name='08100122-EF']",
        id="legacy_writer"
    ),
    pytest.param("SELECT u FROM User u", id="jpql_user"),
    pytest.param(
        "SELECT u FROM User u "
        "JOIN u.userGroups AS ug JOIN ug.grouping AS g "
        "JOIN g.investigationGroups AS ig JOIN ig.investigation AS i "
        "WHERE i.name ='08100122-EF' AND ig.role = 'writer' "
        "ORDER BY u.name",
        id="jpql_writer"
    ),
    pytest.param(lambda client: Query(client, "User"), id="query_user"),
    pytest.param(
        lambda client: Query(client, "User", order=True, conditions={
            "userGroups.grouping.investigationGroups.role": "= 'writer'",
            "userGroups.grouping.investigationGroups.investigation.name":
                "= '08100122-EF'"
        }),
        id="query_writer"
    ),
])
def test_searchChunked_simple(client, query):
    """A simple search with searchChunked().
    """
    # Hack: the parametrize marker above cannot access client,
    # must defer the constructor call to here.
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
    # may test the same assumptions as above.  We choose the chunksize
    # small enough such that the result cannot be fetched at once and
    # thus force searchChunked() to repeat the search internally.
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
    pytest.param("User [name LIKE 'j%']", id="legacy"),
    pytest.param(
        "SELECT u FROM User u WHERE u.name LIKE 'j%' ORDER BY u.name",
        id="jpql"
    ),
    pytest.param(
        lambda client: Query(client, "User", order=True, conditions={
            "name": "LIKE 'j%'",
        }),
        id="query"
    ),
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

@pytest.mark.parametrize(("query",), [
    pytest.param(
        "SELECT o FROM Investigation o WHERE o.id = %d",
        id="id_equal"
    ),
    pytest.param(
        "SELECT o FROM Investigation o WHERE o.id in (%d)",
        id="id_in"
    ),
])
def test_searchChunked_id(client, query):
    """Search by id with searchChunked().

    There is a bug in some versions of icat.server causing the LIMIT
    clause in a query to have no effect when searching by id
    (icatproject/icat.server#125).  This used to break searchChunked()
    that fully relies on the LIMIT clause.  It can be worked around
    reformulating the query, see the second version of the query.
    Now, there is an improvement version of searchChunked() that also
    works around this for the standard formulation of the query
    (9901ec6).
    """
    refq = Query(client, "Investigation", attributes="id", limit=(0,1),
                 conditions={"name": "= '08100122-EF'"})
    id = client.assertedSearch(refq)[0]
    # The search by id must return exactly one result.  The broken
    # version returns the same object over and over again in an
    # endless loop.
    count = 0
    for obj in client.searchChunked(str(query) % id):
        count += 1
        assert count == 1

def test_searchChunked_limit_bug(client):
    """See Issue icatproject/icat.server#128.

    This bug in icat.server used to cause searchChunked() to
    repeatedly yield the same object in an endless loop.
    """
    facility = client.assertedSearch("Facility")[0]
    query = Query(client, "Facility", conditions={"id": "= %d" % facility.id})
    count = 0
    for f in client.searchChunked(query):
        count += 1
        # This search should yield only one result, so the loop should
        # have only one iteration.
        assert count == 1
    assert count == 1

def test_searchChunked_limit_bug_chunksize(client):
    """See Issue icatproject/icat.server#128.

    Same as test_searchChunked_limit_bug(), but now set an explicit
    chunksize.  Ref. #57.
    """
    facility = client.assertedSearch("Facility")[0]
    query = Query(client, "Facility", conditions={"id": "= %d" % facility.id})
    count = 0
    for f in client.searchChunked(query, chunksize=1):
        count += 1
        # This search should yield only one result, so the loop should
        # have only one iteration.
        assert count == 1
    assert count == 1

def test_searchChunked_mulitple_fields(client):
    """A simple search with searchChunked().
    """
    if not client._has_wsdl_type('fieldSet'):
        pytest.skip("search for multiple fields not supported by this server")
    query = "SELECT u.name, u.fullName, u.email from User u"
    # Do a normal search as a reference first, the result from
    # searchChunked() should be the same.
    user_attrs = client.search(query)
    res_gen = client.searchChunked(query)
    # Note that searchChunked() returns a generator, not a list.  Be
    # somewhat less specific in the test, only assume the result to
    # be iterable.
    assert isinstance(res_gen, Iterable)
    # turn it to a list so we can inspect the acual search result.
    res = list(res_gen)
    assert isinstance(res[0], Sequence)
    assert res == user_attrs


# ==================== test searchUniqueKey() ======================

@pytest.mark.parametrize(("key", "attrs"), [
    pytest.param("Facility_name-ESNF", {"name": "ESNF"}, id="facility"),
    pytest.param(
        "Investigation_facility-(name-ESNF)"
        "_name-12100409=2DST_visitId-1=2E1=2DP",
        {"name": "12100409-ST", "visitId": "1.1-P"},
        id="investigation"
    ),
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
    pytest.param(
        "Dataset_investigation-(facility-(name-ESNF)"
        "_name-12100409=2DST_visitId-1=2E1=2DP)_name-e208945",
        [
            ("investigation",
             "Investigation_facility-(name-ESNF)"
             "_name-12100409=2DST_visitId-1=2E1=2DP"),
            ("investigation.facility", "Facility_name-ESNF"),
        ],
        id="dataset"
    ),
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

# ==================== test searchMatching() =======================
# searchMatching() is pretty much straight forward.  There are not
# too much features that could be tested.

def test_searchMatching_simple(client):
    """Search a few objects with searchMatching()
    """
    facility = client.new("Facility", name="ESNF")
    obj = client.searchMatching(facility)
    assert obj.BeanName == "Facility"
    assert obj.id
    assert obj.name == "ESNF"
    facility = obj
    investigation = client.new("Investigation",
                               name="12100409-ST", visitId="1.1-P",
                               facility=facility)
    obj = client.searchMatching(investigation)
    assert obj.BeanName == "Investigation"
    assert obj.id
    assert obj.name == "12100409-ST"
    assert obj.visitId == "1.1-P"
    investigation = obj
    dataset = client.new("Dataset", name="e208945",
                         investigation=investigation)
    obj = client.searchMatching(dataset)
    assert obj.BeanName == "Dataset"
    assert obj.id
    assert obj.name == "e208945"
    dataset = obj

def test_searchMatching_include(client):
    """Set an include clause with searchMatching()
    """
    facility = client.new("Facility", name="ESNF")
    obj = client.searchMatching(facility)
    assert obj.BeanName == "Facility"
    assert obj.id
    assert obj.name == "ESNF"
    facility = obj
    investigation = client.new("Investigation",
                               name="12100409-ST", visitId="1.1-P",
                               facility=facility)
    obj = client.searchMatching(investigation, includes="1")
    assert obj.BeanName == "Investigation"
    assert obj.id
    assert obj.name == "12100409-ST"
    assert obj.visitId == "1.1-P"
    assert obj.type.id
    assert obj.facility.id
    investigation = obj
    dataset = client.new("Dataset", name="e208945",
                         investigation=investigation)
    obj = client.searchMatching(dataset, includes=["datafiles"])
    assert obj.BeanName == "Dataset"
    assert obj.id
    assert obj.name == "e208945"
    assert len(obj.datafiles) > 0

def test_searchMatching_error_attribute_missing(client):
    """Test error handling with searchMatching():
    leaving out a required attribute
    """
    facility = client.assertedSearch("Facility")[0]
    # Neglect to set visitId
    investigation = client.new("Investigation",
                               name="12100409-ST",
                               facility=facility)
    with pytest.raises(ValueError):
        obj = client.searchMatching(investigation)

def test_searchMatching_error_relation_missing(client):
    """Test error handling with searchMatching():
    leaving out a required many-to-one relation
    """
    facility = client.assertedSearch("Facility")[0]
    # Neglect to set facility
    investigation = client.new("Investigation",
                               name="12100409-ST", visitId="1.1-P")
    with pytest.raises(ValueError):
        obj = client.searchMatching(investigation)

def test_searchMatching_error_relation_id_missing(client):
    """Test error handling with searchMatching():
    a required many-to-one relation has no id
    """
    facility = client.assertedSearch("Facility")[0]
    fac = client.new("Facility", name=str(facility.name))
    investigation = client.new("Investigation",
                               name="12100409-ST", visitId="1.1-P",
                               facility=fac)
    with pytest.raises(ValueError):
        obj = client.searchMatching(investigation)
