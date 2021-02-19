"""Test the icat.query module.
"""

from __future__ import print_function
import sys
import datetime
import pytest
import icat
import icat.config
from icat.query import Query
from conftest import getConfig, require_icat_version, UtcTimezone


@pytest.fixture(scope="module")
def client(setupicat):
    client, conf = getConfig()
    client.login(conf.auth, conf.credentials)
    return client


# Note: the number of objects returned in the queries and their
# attributes obviously depend on the content of the ICAT and need to
# be kept in sync with the reference input used in the setupicat
# fixture.


investigation = None
tzinfo = UtcTimezone() if UtcTimezone else None

@pytest.mark.dependency(name='get_investigation')
def test_query_simple(client):
    """A simple query for an investigation by name.
    """
    # The investigation is reused in other tests.
    global investigation
    name = "10100601-ST"
    query = Query(client, "Investigation", conditions={"name":"= '%s'" % name})
    print(str(query))
    res = client.search(query)
    assert len(res) == 1
    investigation = res[0]
    assert investigation.BeanName == "Investigation"
    assert investigation.name == name

def test_query_datafile(client):
    """Query a datafile by its name, dataset name, and investigation name.
    """
    dfdata = { 
        'name': "e208945.nxs", 
        'dataset': "e208945", 
        'investigation': "12100409-ST" 
    }
    conditions = { 
        "name": "= '%s'" % dfdata['name'],
        "dataset.name": "= '%s'" % dfdata['dataset'],
        "dataset.investigation.name": "= '%s'" % dfdata['investigation'],
    }
    query = Query(client, "Datafile", conditions=conditions)
    print(str(query))
    qstr = str(query)
    res = client.search(query)
    assert len(res) == 1
    df = res[0]
    assert df.BeanName == "Datafile"
    assert df.name == dfdata['name']

    # Same example, but use placeholders in the query string now.
    conditions = { 
        "name": "= '%(name)s'",
        "dataset.name": "= '%(dataset)s'",
        "dataset.investigation.name": "= '%(investigation)s'",
    }
    query = Query(client, "Datafile", conditions=conditions)
    print(str(query))
    print(str(query) % dfdata)
    assert str(query) % dfdata == qstr
    res = client.search(str(query) % dfdata)
    assert len(res) == 1
    assert res[0] == df

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_investigation_includes(client):
    """Query lots of information about one single investigation.
    """
    includes = { "facility", "type.facility", "investigationInstruments", 
                 "investigationInstruments.instrument.facility", "shifts", 
                 "keywords", "publications", "investigationUsers", 
                 "investigationUsers.user", "investigationGroups", 
                 "investigationGroups.grouping", "parameters", 
                 "parameters.type.facility" }
    query = Query(client, "Investigation", 
                  conditions={"id": "= %d" % investigation.id}, 
                  includes=includes)
    print(str(query))
    res = client.search(query)
    assert len(res) == 1
    inv = res[0]
    assert inv.BeanName == "Investigation"
    assert inv.id == investigation.id
    assert inv.name == investigation.name
    assert inv.facility.BeanName == "Facility"
    assert inv.type.facility.BeanName == "Facility"
    assert len(inv.investigationInstruments) > 0
    assert len(inv.investigationUsers) > 0
    assert len(inv.investigationGroups) > 0

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_instruments(client):
    """Query the instruments related to a given investigation.
    """
    query = Query(client, "Instrument", 
                  order=["name"], 
                  conditions={ "investigationInstruments.investigation.id":
                               "= %d" % investigation.id }, 
                  includes={"facility", "instrumentScientists.user"})
    print(str(query))
    res = client.search(query)
    assert len(res) == 1
    instr = res[0]
    assert instr.BeanName == "Instrument"
    assert instr.facility.BeanName == "Facility"

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_datafile_by_investigation(client):
    """The datafiles related to a given investigation in natural order.
    """
    query = Query(client, "Datafile", order=True, 
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id }, 
                  includes={"dataset", "datafileFormat.facility", 
                            "parameters.type.facility"})
    print(str(query))
    res = client.search(query)
    assert len(res) == 4

def test_query_relateddatafile(client):
    """RelatedDatafile is the entity type with the most complicated
    natural order.
    """
    query = Query(client, "RelatedDatafile", order=True)
    print(str(query))
    res = client.search(query)
    assert len(res) == 1

def test_query_datacollection(client):
    """There is no sensible order for DataCollection, fall back to id.
    """
    query = Query(client, "DataCollection", order=True)
    print(str(query))
    assert ("id", None) in query.order
    res = client.search(query)
    assert len(res) == 2

def test_query_datafiles_datafileformat(client, recwarn):
    """Datafiles ordered by format.
    Note: this raises a QueryNullableOrderWarning, see below.
    """
    recwarn.clear()
    query = Query(client, "Datafile", 
                  order=['datafileFormat', 'dataset', 'name'])
    w = recwarn.pop(icat.QueryNullableOrderWarning)
    assert issubclass(w.category, icat.QueryNullableOrderWarning)
    assert "datafileFormat" in str(w.message)
    print(str(query))
    res = client.search(query)
    assert len(res) == 10

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_order_direction(client):
    """We may add an ordering direction qualifier.

    This has been added in Issue #48.
    """
    # Try without specifying the ordering direction first:
    query = Query(client, "Datafile", 
                  order=["name"], 
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id })
    print(str(query))
    res = client.search(query)
    assert len(res) == 4
    # Ascending order is the default, so we should get the same result:
    query = Query(client, "Datafile", 
                  order=[("name", "ASC")], 
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id })
    print(str(query))
    assert client.search(query) == res
    # Descending order should give the reverse result:
    query = Query(client, "Datafile", 
                  order=[("name", "DESC")], 
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id })
    print(str(query))
    assert list(reversed(client.search(query))) == res
    # We may even combine different ordering directions on multiple
    # attributes of the same query:
    query = Query(client, "Datafile", 
                  order=[("dataset.name", "DESC"), ("name", "ASC")], 
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id })
    print(str(query))
    assert sorted(client.search(query), key=lambda df: df.name) == res

def test_query_order_direction_relation(client):
    """An ordering direction qualifier on a many to one relation.

    The ordering direction qualifier has been added in Issue #48.
    """
    # As a reference to compare with, get all datasets with their
    # datafiles in their natural order:
    query = Query(client, "Dataset", order=True, includes=["datafiles"])
    dss = client.search(query)
    # Now, get all datafiles sorted by dataset in descending and name
    # in ascending order:
    query = Query(client, "Datafile", order=[("dataset", "DESC"), "name"])
    print(str(query))
    dff = client.search(query)
    # verify:
    offs = 0
    for ds in reversed(dss):
        # There is no guarantee on the order of the included datafiles
        dsdfs = sorted(ds.datafiles, key=icat.entity.Entity.__sortkey__)
        l = len(dsdfs)
        assert dff[offs:offs+l] == dsdfs
        offs += l

def test_query_condition_greaterthen(client):
    """Other relations then equal may be used in the conditions too.
    """
    condition = {"datafileCreateTime": ">= '2012-01-01'"}
    query = Query(client, "Datafile", conditions=condition)
    print(str(query))
    res = client.search(query)
    assert len(res) == 4
    condition = {"datafileCreateTime": "< '2012-01-01'"}
    query = Query(client, "Datafile", conditions=condition)
    print(str(query))
    res = client.search(query)
    assert len(res) == 6

def test_query_condition_list(client):
    """We may also add a list of conditions on a single attribute.
    """
    condition = {"datafileCreateTime": [">= '2012-01-01'", "< '2013-01-01'"]}
    query = Query(client, "Datafile", conditions=condition)
    print(str(query))
    qstr = str(query)
    res = client.search(query)
    assert len(res) == 3

    # The last example also works by adding the conditions separately.
    query = Query(client, "Datafile")
    query.addConditions({"datafileCreateTime": ">= '2012-01-01'"})
    query.addConditions({"datafileCreateTime": "< '2013-01-01'"})
    print(str(query))
    assert str(query) == qstr
    res = client.search(query)
    assert len(res) == 3

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_in_operator(client):
    """Using "id in (i)" rather then "id = i" also works.
    (This may be needed to work around ICAT Issue 128.)
    """
    query = Query(client, "Investigation", 
                  conditions={"id": "in (%d)" % investigation.id})
    print(str(query))
    res = client.search(query)
    assert len(res) == 1
    inv = res[0]
    assert inv.BeanName == "Investigation"
    assert inv.id == investigation.id
    assert inv.name == investigation.name

def test_query_condition_obj(client):
    """We may place conditions on related objects.
    This is in particular useful to test whether a relation is null.
    """
    query = Query(client, "Rule", conditions={"grouping": "IS NULL"})
    print(str(query))
    res = client.search(query)
    assert len(res) == 60

def test_query_rule_order(client):
    """Rule does not have a constraint, id is included in the natural order.
    """
    query = Query(client, "Rule", order=True)
    print(str(query))
    assert ("id", None) in query.order
    res = client.search(query)
    assert len(res) == 104

def test_query_nullable_warning(client, recwarn):
    """Ordering on nullable relations emits a warning.
    """
    recwarn.clear()
    query = Query(client, "Rule", order=['grouping', 'what', 'id'])
    w = recwarn.pop(icat.QueryNullableOrderWarning)
    assert issubclass(w.category, icat.QueryNullableOrderWarning)
    assert "grouping" in str(w.message)
    print(str(query))
    res = client.search(query)
    assert len(res) == 44

def test_query_nullable_warning_suppressed(client, recwarn):
    """The warning can be suppressed by making the condition explicit.
    """
    recwarn.clear()
    query = Query(client, "Rule", order=['grouping', 'what', 'id'], 
                  conditions={"grouping":"IS NOT NULL"})
    assert len(recwarn.list) == 0
    print(str(query))
    res = client.search(query)
    assert len(res) == 44

def test_query_limit(client):
    """Add a LIMIT clause to the last example.
    """
    query = Query(client, "Rule", order=['grouping', 'what', 'id'], 
                  conditions={"grouping":"IS NOT NULL"})
    query.setLimit( (0,10) )
    print(str(query))
    res = client.search(query)
    assert len(res) == 10

def test_query_limit_placeholder(client):
    """LIMIT clauses are particular useful with placeholders.
    """
    query = Query(client, "Rule", order=['grouping', 'what', 'id'], 
                  conditions={"grouping":"IS NOT NULL"})
    query.setLimit( ("%d","%d") )
    print(str(query))
    print(str(query) % (0,30))
    res = client.search(str(query) % (0,30))
    assert len(res) == 30
    print(str(query) % (30,30))
    res = client.search(str(query) % (30,30))
    assert len(res) == 14

def test_query_non_ascii(client):
    """Test if query strings with non-ascii characters work.

    There was a bug that forced query strings to be all ascii.  The
    bug only occured with Python 2.  It was fixed in change 8d5132d.
    """
    # String literal with unicode characters that will be understood
    # by both Python 2 and Python 3.
    fullName = b'Rudolph Beck-D\xc3\xbclmen'.decode('utf8')
    query = Query(client, "User", 
                  conditions={ "fullName": "= '%s'" % fullName })
    if sys.version_info < (3, 0):
        print(unicode(query))
    else:
        print(str(query))
    res = client.search(query)
    assert len(res) == 1

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_str(client):
    """Test the __str__() operator.  It should have no side effects.

    The __str__() operator was modifying the query object under
    certain conditions (if a1.a2 was in includes but a1 not, a1 was
    added).  While this modification was most likely harmless and in
    particular did not cause any semantic change of the query, it was
    still a bug because a __str__() operator should not have any side
    effects at all.  It was fixed in changes 4688517 and 905dd8c.
    """
    query = Query(client, "Datafile", order=True, 
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id }, 
                  includes={"dataset", "datafileFormat.facility", 
                            "parameters.type.facility"})
    r = repr(query)
    print(str(query))
    assert repr(query) == r

def test_query_metaattr(client):
    """Test adding a condition on a meta attribute.  Issue #6
    """
    query = Query(client, "Datafile", conditions={ "modId": "= 'jdoe'" })
    print(str(query))
    res = client.search(query)
    assert len(res) == 0

def test_query_include_1(client):
    """Test adding an "INCLUDE 1" clause.
    """
    query = Query(client, "Investigation", includes="1")
    print(str(query))
    res = client.search(query)
    assert len(res) > 0
    inv = res[0]
    assert inv.BeanName == "Investigation"
    assert inv.facility.BeanName == "Facility"
    assert inv.type.BeanName == "InvestigationType"

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_attribute_datafile_name(client):
    """The datafiles names related to a given investigation in natural order.

    Querying attributes rather then entire objects is a new feature
    added in Issue #28.
    """
    query = Query(client, "Datafile", attributes="name", order=True,
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id })
    print(str(query))
    res = client.search(query)
    assert len(res) == 4
    for n in res:
        assert not isinstance(n, icat.entity.Entity)

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_related_obj_attribute(client):
    """We may query attributes of related objects in the SELECT clause.

    This requires icat.server 4.5 or newer to work.
    """
    require_icat_version("4.5.0", "SELECT related object's attribute")
    query = Query(client, "Datafile", attributes="datafileFormat.name",
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id })
    print(str(query))
    res = client.search(query)
    assert len(res) == 4
    for n in res:
        assert n in ['other', 'NeXus']

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_aggregate_distinct_attribute(client):
    """Test DISTINCT on an attribute in the search result.

    Support for adding aggregate functions has been added in
    Issue #32.
    """
    require_icat_version("4.7.0", "SELECT DISTINCT in queries")
    query = Query(client, "Datafile", 
                  attributes="datafileFormat.name",
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id })
    print(str(query))
    res = client.search(query)
    assert sorted(res) == ["NeXus", "NeXus", "other", "other"]
    query.setAggregate("DISTINCT")
    print(str(query))
    res = client.search(query)
    assert sorted(res) == ["NeXus", "other"]

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_aggregate_distinct_related_obj(client):
    """Test DISTINCT on a related object in the search result.

    Support for adding aggregate functions has been added in
    Issue #32.
    """
    require_icat_version("4.7.0", "SELECT DISTINCT in queries")
    query = Query(client, "Datafile", 
                  attributes="datafileFormat",
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id })
    print(str(query))
    res = client.search(query)
    assert len(res) == 4
    for n in res:
        assert isinstance(n, icat.entity.Entity)
    query.setAggregate("DISTINCT")
    print(str(query))
    res = client.search(query)
    assert len(res) == 2
    for n in res:
        assert isinstance(n, icat.entity.Entity)

@pytest.mark.dependency(depends=['get_investigation'])
@pytest.mark.parametrize(("attribute", "aggregate", "expected"), [
    (None, "COUNT", 4),
    (None, "COUNT:DISTINCT", 4),
    ("datafileFormat", "COUNT", 4),
    ("datafileFormat", "COUNT:DISTINCT", 2),
    ("datafileFormat.name", "COUNT", 4),
    ("datafileFormat.name", "COUNT:DISTINCT", 2),
    ("fileSize", "MAX", 73428),
    ("fileSize", "MIN", 394),
    ("fileSize", "SUM", 127125),
    # Note that the number of datafiles is four which is a power of
    # two.  Therefore we may assume the double representation of an
    # average of integers is exact, so we may even dare to compare
    # the double value for equality.
    ("fileSize", "AVG", 31781.25),
    ("name", "MAX", "e208341.nxs"),
    ("name", "MIN", "e208339.dat"),
    pytest.param("datafileCreateTime", "MIN",
                 datetime.datetime(2010, 10, 1, 6, 17, 48, tzinfo=tzinfo),
                 marks=pytest.mark.skipif("tzinfo is None")),
    pytest.param("datafileCreateTime", "MAX",
                 datetime.datetime(2010, 10, 5, 9, 31, 53, tzinfo=tzinfo),
                 marks=pytest.mark.skipif("tzinfo is None"))
])
def test_query_aggregate_misc(client, attribute, aggregate, expected):
    """Try some working aggregate results for the datafiles.

    Support for adding aggregate functions has been added in
    Issue #32.
    """
    if attribute is not None and "." in attribute:
        require_icat_version("4.5.0", "SELECT related object's attribute")
    if "DISTINCT" in aggregate:
        require_icat_version("4.7.0", "SELECT DISTINCT in queries")
    query = Query(client, "Datafile",
                  attributes=attribute, aggregate=aggregate,
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id })
    print(str(query))
    res = client.search(query)
    assert len(res) == 1
    assert res[0] == expected

