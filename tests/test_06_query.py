"""Test the icat.query module.
"""

from __future__ import print_function
import sys
import pytest
import icat
import icat.config
from icat.query import Query
from conftest import getConfig


@pytest.fixture(scope="module")
def client(setupicat):
    conf = getConfig()
    client = icat.Client(conf.url, **conf.client_kwargs)
    client.login(conf.auth, conf.credentials)
    return client


# Note: the number of objects returned in the queries and their
# attributes obviously depend on the content of the ICAT and need to
# be kept in sync with the reference input used in the setupicat
# fixture.


investigation = None

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
    assert len(res) == 0

def test_query_datacollection(client):
    """There is no sensible order for DataCollection, fall back to id.
    """
    query = Query(client, "DataCollection", order=True)
    print(str(query))
    assert "id" in query.order
    res = client.search(query)
    assert len(res) == 0

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
    assert len(res) == 7

def test_query_condition_greaterthen(client):
    """Other relations then equal may be used in the conditions too.
    """
    condition = {"datafileCreateTime": ">= '2012-01-01'"}
    query = Query(client, "Datafile", conditions=condition)
    print(str(query))
    res = client.search(query)
    assert len(res) == 2
    condition = {"datafileCreateTime": "< '2012-01-01'"}
    query = Query(client, "Datafile", conditions=condition)
    print(str(query))
    res = client.search(query)
    assert len(res) == 5

def test_query_condition_list(client):
    """We may also add a list of conditions on a single attribute.
    """
    condition = {"datafileCreateTime": [">= '2012-01-01'", "< '2013-01-01'"]}
    query = Query(client, "Datafile", conditions=condition)
    print(str(query))
    qstr = str(query)
    res = client.search(query)
    assert len(res) == 1

    # The last example also works by adding the conditions separately.
    query = Query(client, "Datafile")
    query.addConditions({"datafileCreateTime": ">= '2012-01-01'"})
    query.addConditions({"datafileCreateTime": "< '2013-01-01'"})
    print(str(query))
    assert str(query) == qstr
    res = client.search(query)
    assert len(res) == 1

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

def test_query_rule_order(client):
    """Rule does not have a constraint, id is included in the natural order.
    """
    query = Query(client, "Rule", order=True)
    print(str(query))
    assert "id" in query.order
    res = client.search(query)
    assert len(res) == 102

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
