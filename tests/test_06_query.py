"""Test the icat.query module.
"""

import datetime
import re
import warnings
import pytest
import icat
import icat.config
from icat.query import Query
from conftest import getConfig, icat_version, require_icat_version, UtcTimezone


@pytest.fixture(scope="module")
def client(setupicat):
    client, conf = getConfig()
    client.login(conf.auth, conf.credentials)
    return client


# Note: the number of objects returned in the queries and their
# attributes obviously depend on the content of the ICAT and need to
# be kept in sync with the reference input used in the setupicat
# fixture.  This content also depends on the version of ICAT server we
# are talking to and the ICAT schema this server provides.
#
# Note: the exact query string is considered an implementation detail
# that is deliberately not tested here.  We limit the tests to check
# the presence of some key fragments in the various clauses of the
# queries.

investigation = None
tzinfo = UtcTimezone() if UtcTimezone else None

# The the actual number of rules in the test data differs with the
# ICAT version.
have_icat_5 = 0 if icat_version < "5.0" else 1
all_rules = 111 + 48*have_icat_5
grp_rules = 51 + 30*have_icat_5

@pytest.mark.dependency(name='get_investigation')
def test_query_simple(client):
    """A simple query for an investigation by name.
    """
    # The investigation is reused in other tests.
    global investigation
    name = "10100601-ST"
    query = Query(client, "Investigation", conditions={"name":"= '%s'" % name})
    print(str(query))
    assert "Investigation" in query.select_clause
    assert query.join_clause is None
    assert "name" in query.where_clause
    assert query.order_clause is None
    assert query.include_clause is None
    assert query.limit_clause is None
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
    assert "Datafile" in query.select_clause
    assert "investigation" in query.join_clause
    assert dfdata['investigation'] in query.where_clause
    assert query.order_clause is None
    assert query.include_clause is None
    assert query.limit_clause is None
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
    assert "Investigation" in query.select_clause
    assert query.join_clause is None
    assert "id" in query.where_clause
    assert "investigationInstruments" in query.include_clause
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
    assert "Instrument" in query.select_clause
    assert "investigation" in query.join_clause
    assert "id" in query.where_clause
    assert "name" in query.order_clause
    assert "instrumentScientists" in query.include_clause
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
    assert "Datafile" in query.select_clause
    assert "investigation" in query.join_clause
    assert "id" in query.where_clause
    assert "datafileFormat" in query.include_clause
    res = client.search(query)
    assert len(res) == 4

def test_query_relateddatafile(client):
    """RelatedDatafile is the entity type with the most complicated
    natural order.
    """
    query = Query(client, "RelatedDatafile", order=True)
    print(str(query))
    assert "RelatedDatafile" in query.select_clause
    assert query.where_clause is None
    assert query.order_clause is not None
    assert query.include_clause is None
    assert query.limit_clause is None
    res = client.search(query)
    assert len(res) == 1

def test_query_datacollection(client):
    """There is no sensible order for DataCollection, fall back to id.
    """
    query = Query(client, "DataCollection", order=True)
    print(str(query))
    assert "DataCollection" in query.select_clause
    assert query.join_clause is None
    assert query.where_clause is None
    assert "id" in query.order_clause
    assert query.include_clause is None
    assert query.limit_clause is None
    res = client.search(query)
    assert len(res) == 3 + 2*have_icat_5

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
    assert "Datafile" in query.select_clause
    assert "datafileFormat" in query.join_clause
    assert query.where_clause is None
    assert query.order_clause is not None
    assert query.include_clause is None
    assert query.limit_clause is None
    res = client.search(query)
    assert len(res) == 10 + have_icat_5

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
    assert "Datafile" in query.select_clause
    assert "investigation" in query.join_clause
    assert "id" in query.where_clause
    assert "name" in query.order_clause
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
    assert "Datafile" in query.select_clause
    assert "dataset" in query.join_clause
    assert query.where_clause is None
    assert "name" in query.order_clause
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
    assert "Datafile" in query.select_clause
    assert query.join_clause is None
    assert "datafileCreateTime" in query.where_clause
    res = client.search(query)
    assert len(res) == 4 + have_icat_5
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
    assert "Datafile" in query.select_clause
    assert query.join_clause is None
    assert "datafileCreateTime" in query.where_clause
    qstr = str(query)
    res = client.search(query)
    assert len(res) == 3 + have_icat_5

    # The last example also works by adding the conditions separately.
    query = Query(client, "Datafile")
    query.addConditions({"datafileCreateTime": ">= '2012-01-01'"})
    query.addConditions({"datafileCreateTime": "< '2013-01-01'"})
    print(str(query))
    assert str(query) == qstr
    res = client.search(query)
    assert len(res) == 3 + have_icat_5

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_in_operator(client):
    """Using "id in (i)" rather than "id = i" also works.
    (This may be needed to work around ICAT Issue 128.)
    """
    query = Query(client, "Investigation",
                  conditions={"id": "in (%d)" % investigation.id})
    print(str(query))
    assert "Investigation" in query.select_clause
    assert query.join_clause is None
    assert "in" in query.where_clause
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
    assert "Rule" in query.select_clause
    res = client.search(query)
    assert len(res) == all_rules - grp_rules

def test_query_condition_jpql_function(client):
    """Functions may be applied to field names of conditions.
    This test also applies `UPPER()` on the data to mitigate instances
    of Oracle databases which are case sensitive.
    """
    conditions = {
        "UPPER(title)": "like UPPER('%Ni-Mn-Ga flat cone%')",
        "UPPER(datasets.name)": "like UPPER('%e208341%')",
    }
    query = Query(client, "Investigation", conditions=conditions)
    print(str(query))
    assert "Investigation" in query.select_clause
    assert "datasets" in query.join_clause
    assert "UPPER" in query.where_clause
    res = client.search(query)
    assert len(res) == 1

def test_query_condition_jpql_function_namelen(client):
    """Functions may be applied to field names of conditions.
    Similar to last test, but picking another example where the effect
    of the JPQL function in the condition is easier to verify in the
    result.
    """
    conditions = { "name": "LIKE 'db/%'",
                   "LENGTH(fullName)": "> 11" }
    query = Query(client, "User", conditions=conditions)
    print(str(query))
    assert "User" in query.select_clause
    assert query.join_clause is None
    assert "LENGTH" in query.where_clause
    res = client.search(query)
    assert len(res) == 4

def test_query_condition_jpql_function_mixed(client):
    """Mix conditions with and without JPQL function on the same attribute.
    This test case failed for an early implementation of JPQL
    functions, see discussion in #89.
    """
    conditions = { "name": "LIKE 'db/%'",
                   "LENGTH(fullName)": "> 11", "fullName": "> 'C'" }
    query = Query(client, "User", conditions=conditions)
    print(str(query))
    assert "User" in query.select_clause
    assert query.join_clause is None
    assert "LENGTH" in query.where_clause
    res = client.search(query)
    assert len(res) == 3

def test_query_order_jpql_function(client):
    """Functions may be applied to attribute names in order.

    As an example, search for the User having the third longest
    fullName.  (In the example data, the longest and second longest
    fullName is somewhat ambiguous due to character encoding issues.)
    """
    query = Query(client, "User", conditions={ "name": "LIKE 'db/%'" },
                  order=[("LENGTH(fullName)", "DESC")], limit=(2,1))
    print(str(query))
    assert "User" in query.select_clause
    assert query.join_clause is None
    assert "LENGTH" in query.order_clause
    assert query.limit_clause is not None
    res = client.search(query)
    assert len(res) == 1
    assert res[0].fullName == "Nicolas Bourbaki"

def test_query_rule_order(client):
    """Rule does not have a constraint, id is included in the natural order.
    """
    query = Query(client, "Rule", order=True)
    print(str(query))
    assert "Rule" in query.select_clause
    assert query.join_clause is None
    assert query.where_clause is None
    assert "id" in query.order_clause
    res = client.search(query)
    assert len(res) == all_rules

def test_query_rule_order_group(client, recwarn):
    """Ordering rule on grouping implicitely adds a "grouping IS NOT NULL"
    condition, because it is internally implemented using an INNER
    JOIN between the tables.  The Query class emits a warning about
    this.
    """
    recwarn.clear()
    query = Query(client, "Rule", order=['grouping', 'what', 'id'])
    w = recwarn.pop(icat.QueryNullableOrderWarning)
    assert issubclass(w.category, icat.QueryNullableOrderWarning)
    assert "grouping" in str(w.message)
    print(str(query))
    assert "Rule" in query.select_clause
    assert "grouping" in query.join_clause
    assert query.where_clause is None
    assert "what" in query.order_clause
    res = client.search(query)
    assert len(res) == grp_rules

def test_query_rule_order_group_suppress_warn_cond(client, recwarn):
    """The warning can be suppressed by making the condition explicit.
    """
    recwarn.clear()
    query = Query(client, "Rule", order=['grouping', 'what', 'id'],
                  conditions={"grouping": "IS NOT NULL"})
    assert len(recwarn.list) == 0
    print(str(query))
    assert "Rule" in query.select_clause
    assert "grouping" in query.join_clause
    assert "grouping" in query.where_clause
    assert "what" in query.order_clause
    res = client.search(query)
    assert len(res) == grp_rules

def test_query_rule_order_group_suppress_warn_join(client, recwarn):
    """Another option to suppress the warning is to override the JOIN spec.
    By confirming the default INNER JOIN, we get the Rules having
    grouping NOT NULL.
    """
    recwarn.clear()
    query = Query(client, "Rule", order=['grouping', 'what', 'id'],
                  join_specs={"grouping": "INNER JOIN"})
    assert len(recwarn.list) == 0
    print(str(query))
    assert "Rule" in query.select_clause
    assert "INNER JOIN" in query.join_clause
    assert query.where_clause is None
    assert "what" in query.order_clause
    res = client.search(query)
    assert len(res) == grp_rules

def test_query_rule_order_group_left_join(client, recwarn):
    """Another option to suppress the warning is to override the JOIN spec.
    By chosing a LEFT JOIN, we get all Rules.
    """
    recwarn.clear()
    query = Query(client, "Rule", order=['grouping', 'what', 'id'],
                  join_specs={"grouping": "LEFT OUTER JOIN"})
    assert len(recwarn.list) == 0
    print(str(query))
    assert "Rule" in query.select_clause
    assert "LEFT OUTER JOIN" in query.join_clause
    assert query.where_clause is None
    assert "what" in query.order_clause
    res = client.search(query)
    assert len(res) == all_rules

def test_query_order_one_to_many(client, recwarn):
    """Sort on a related object in a one to many relation.
    This has been enabled in #84, but a warning is still emitted.
    """
    recwarn.clear()
    query = Query(client, "Investigation",
                  order=['investigationInstruments.instrument.fullName'])
    w = recwarn.pop(icat.QueryOneToManyOrderWarning)
    assert issubclass(w.category, icat.QueryOneToManyOrderWarning)
    assert "investigationInstruments" in str(w.message)
    print(str(query))
    assert "Investigation" in query.select_clause
    assert "instrument" in query.join_clause
    assert query.where_clause is None
    assert "fullName" in query.order_clause
    res = client.search(query)
    assert len(res) == 3

def test_query_order_one_to_many_warning_suppressed(client, recwarn):
    """Again, the warning can be suppressed by overriding the JOIN spec.
    """
    recwarn.clear()
    query = Query(client, "Investigation",
                  order=['investigationInstruments.instrument.fullName'],
                  join_specs={"investigationInstruments": "INNER JOIN"})
    assert len(recwarn.list) == 0
    print(str(query))
    assert "Investigation" in query.select_clause
    assert "INNER JOIN" in query.join_clause
    assert "instrument" in query.join_clause
    assert query.where_clause is None
    assert "fullName" in query.order_clause
    res = client.search(query)
    assert len(res) == 3

def test_query_order_one_to_many_duplicate(client, recwarn):
    """Note that sorting on a one to many relation may have surprising
    effects on the result list.  That is why class Query emits a
    warning.
    You may get duplicates in the result.
    """
    recwarn.clear()
    # The query without ORDER BY clause.
    query = Query(client, "Investigation")
    assert len(recwarn.list) == 0
    print(str(query))
    res = client.search(query)
    assert len(res) == 3
    reference = res
    # The same query adding a ORDER BY clause, we get two duplicates in
    # the result.
    recwarn.clear()
    query = Query(client, "Investigation", order=['investigationUsers.role'])
    w = recwarn.pop(icat.QueryOneToManyOrderWarning)
    assert issubclass(w.category, icat.QueryOneToManyOrderWarning)
    assert "investigationUsers" in str(w.message)
    print(str(query))
    res = client.search(query)
    assert len(res) > 3
    assert set(res) == set(reference)

def test_query_order_one_to_many_missing(client, recwarn):
    """Note that sorting on a one to many relation may have surprising
    effects on the result list.  That is why class Query emits a
    warning.
    You may get misses in the result.
    """
    recwarn.clear()
    # The query without ORDER BY clause.
    query = Query(client, "Sample")
    assert len(recwarn.list) == 0
    print(str(query))
    res = client.search(query)
    assert len(res) == 3
    reference = res
    # The same query adding a ORDER BY clause, one item, a sample
    # having no parameter with a string value, is missing from the result.
    recwarn.clear()
    query = Query(client, "Sample", order=['parameters.stringValue'])
    w = recwarn.pop(icat.QueryOneToManyOrderWarning)
    assert issubclass(w.category, icat.QueryOneToManyOrderWarning)
    assert "parameters" in str(w.message)
    print(str(query))
    res = client.search(query)
    assert len(res) == 2
    # We can fix it in this case using a LEFT JOIN.
    recwarn.clear()
    query = Query(client, "Sample",
                  order=['parameters.stringValue'],
                  join_specs={"parameters": "LEFT JOIN"})
    assert len(recwarn.list) == 0
    print(str(query))
    res = client.search(query)
    assert len(res) == 3
    assert set(res) == set(reference)

def test_query_order_suppress_warnings(client, recwarn):
    """Suppress all QueryWarnings.
    """
    recwarn.clear()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=icat.QueryWarning)
        query = Query(client, "Investigation",
                      order=['investigationInstruments.instrument.fullName'])
    assert len(recwarn.list) == 0
    print(str(query))
    res = client.search(query)
    assert len(res) == 3

def test_query_limit(client):
    """Add a LIMIT clause to an earlier example.
    """
    query = Query(client, "Rule", order=['grouping', 'what', 'id'],
                  conditions={"grouping":"IS NOT NULL"})
    query.setLimit( (0,10) )
    print(str(query))
    assert "Rule" in query.select_clause
    assert "grouping" in query.join_clause
    assert "grouping" in query.where_clause
    assert "what" in query.order_clause
    assert query.limit_clause is not None
    res = client.search(query)
    assert len(res) == 10

def test_query_limit_placeholder(client):
    """LIMIT clauses are particular useful with placeholders.
    """
    query = Query(client, "Rule", order=['grouping', 'what', 'id'],
                  conditions={"grouping":"IS NOT NULL"})
    query.setLimit( ("%d","%d") )
    chunksize = 45
    print(str(query))
    print(str(query) % (0,chunksize))
    assert "Rule" in query.select_clause
    assert "grouping" in query.join_clause
    assert "grouping" in query.where_clause
    assert "what" in query.order_clause
    assert query.limit_clause is not None
    res = client.search(str(query) % (0,chunksize))
    assert len(res) == chunksize
    print(str(query) % (chunksize,chunksize))
    res = client.search(str(query) % (chunksize,chunksize))
    assert len(res) == grp_rules - chunksize

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
    print(str(query))
    assert "User" in query.select_clause
    assert query.join_clause is None
    assert fullName in query.where_clause
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
    assert "Datafile" in query.select_clause
    assert "investigation" in query.join_clause
    assert "id" in query.where_clause
    assert "datafileFormat" in query.include_clause
    assert repr(query) == r

def test_query_metaattr(client):
    """Test adding a condition on a meta attribute.  Issue #6
    """
    query = Query(client, "Datafile", conditions={ "modId": "= 'jdoe'" })
    print(str(query))
    assert "Datafile" in query.select_clause
    assert query.join_clause is None
    assert "modId" in query.where_clause
    res = client.search(query)
    assert len(res) == 0

def test_query_include_1(client):
    """Test adding an "INCLUDE 1" clause.
    """
    query = Query(client, "Investigation", includes="1")
    print(str(query))
    assert "Investigation" in query.select_clause
    assert query.join_clause is None
    assert query.where_clause is None
    assert "facility" in query.include_clause
    assert "type" in query.include_clause
    res = client.search(query)
    assert len(res) > 0
    inv = res[0]
    assert inv.BeanName == "Investigation"
    assert inv.facility.BeanName == "Facility"
    assert inv.type.BeanName == "InvestigationType"

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_attribute_datafile_name(client):
    """The datafiles names related to a given investigation in natural order.

    Querying attributes rather than entire objects is a new feature
    added in Issue #28.
    """
    query = Query(client, "Datafile", attributes="name", order=True,
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id })
    print(str(query))
    assert "name" in query.select_clause
    assert "investigation" in query.join_clause
    assert "id" in query.where_clause
    assert query.order_clause is not None
    res = client.search(query)
    assert len(res) == 4
    for n in res:
        assert not isinstance(n, icat.entity.Entity)

@pytest.mark.dependency(depends=['get_investigation'])
def test_query_attribute_datafile_name_list(client):
    """The datafiles names related to a given investigation in natural order.

    Same as last test, but pass the attribute as a list having one
    single element.
    """
    query = Query(client, "Datafile", attributes=["name"], order=True,
                  conditions={ "dataset.investigation.id":
                               "= %d" % investigation.id })
    print(str(query))
    assert "name" in query.select_clause
    assert "investigation" in query.join_clause
    assert "id" in query.where_clause
    assert query.order_clause is not None
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
    assert "name" in query.select_clause
    assert "datafileFormat" in query.join_clause
    assert "investigation" in query.join_clause
    assert "id" in query.where_clause
    res = client.search(query)
    assert len(res) == 4
    for n in res:
        assert n in ['other', 'NeXus']

def test_query_mulitple_attributes(client):
    """Query multiple attributes in the SELECT clause.
    """
    if not client._has_wsdl_type('fieldSet'):
        pytest.skip("search for multiple fields not supported by this server")

    results = [("08100122-EF", "Durol single crystal",
                datetime.datetime(2008, 3, 13, 10, 39, 42, tzinfo=tzinfo)),
               ("10100601-ST", "Ni-Mn-Ga flat cone",
                datetime.datetime(2010, 9, 30, 10, 27, 24, tzinfo=tzinfo)),
               ("12100409-ST", "NiO SC OF1 JUH HHL",
                datetime.datetime(2012, 7, 26, 15, 44, 24, tzinfo=tzinfo))]
    query = Query(client, "Investigation",
                  attributes=("name", "title", "startDate"), order=True)
    print(str(query))
    assert "name" in query.select_clause
    assert "title" in query.select_clause
    assert "startDate" in query.select_clause
    assert "facility" in query.join_clause
    assert query.order_clause is not None
    res = client.search(query)
    assert res == results

def test_query_mulitple_attributes_related_obj(client):
    """Query multiple attributes including attributes of related objects.
    """
    if not client._has_wsdl_type('fieldSet'):
        pytest.skip("search for multiple fields not supported by this server")

    results = [("08100122-EF", "e201215"),
               ("08100122-EF", "e201216"),
               ("10100601-ST", "e208339"),
               ("10100601-ST", "e208341"),
               ("10100601-ST", "e208342")]
    query = Query(client, "Dataset",
                  attributes=("investigation.name", "name"), order=True,
                  conditions={"investigation.startDate":  "< '2011-01-01'"})
    print(str(query))
    assert "name" in query.select_clause
    assert "investigation" in query.join_clause
    assert "startDate" in query.where_clause
    assert query.order_clause is not None
    res = client.search(query)
    assert res == results

def test_query_mulitple_attributes_oldicat_valueerror(client):
    """Query class should raise ValueError if multiple attributes are
    requested, but the ICAT server is too old to support this.
    """
    if client._has_wsdl_type('fieldSet'):
        pytest.skip("search for multiple fields is supported by this server")

    with pytest.raises(ValueError) as err:
        query = Query(client, "Investigation", attributes=("name", "title"))
    err_pattern = r"\bICAT server\b.*\bnot support\b.*\bmultiple attributes\b"
    assert re.search(err_pattern, str(err.value))

def test_query_mulitple_attributes_distinct(client):
    """Combine DISTINCT with a query for multiple attributes.

    This requires a special handling due to some quirks in the
    icat.server query parser.  Support for this has been added in
    #81.
    """
    if not client._has_wsdl_type('fieldSet'):
        pytest.skip("search for multiple fields not supported by this server")

    # Try the query without DISTINCT first so that we can verify the effect.
    query = Query(client, "InvestigationUser",
                  attributes=("investigation.name", "role"),
                  conditions={"investigation.name": "= '08100122-EF'"})
    print(str(query))
    res = client.search(query)
    query = Query(client, "InvestigationUser",
                  attributes=("investigation.name", "role"),
                  conditions={"investigation.name": "= '08100122-EF'"},
                  aggregate="DISTINCT")
    print(str(query))
    assert "DISTINCT" in query.select_clause
    assert "role" in query.select_clause
    assert "investigation" in query.join_clause
    assert "name" in query.where_clause
    res_dist = client.search(query)
    # The search with DISTINCT yields less items, but if we eliminate
    # duplicates, the result set is the same:
    assert len(res) > len(res_dist)
    assert set(res) == set(res_dist)

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
    assert "DISTINCT" in query.select_clause
    assert "name" in query.select_clause
    assert "datafileFormat" in query.join_clause
    assert "id" in query.where_clause
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
    assert "DISTINCT" in query.select_clause
    assert "datafileFormat" in query.select_clause
    assert "investigation" in query.join_clause
    assert "id" in query.where_clause
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
    # two.  Therefore we may assume the float representation of an
    # average of integers is exact, so we may even dare to compare the
    # float value for equality.
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
    if ':' not in aggregate:
        assert aggregate in query.select_clause
    if attribute is not None and '.' not in attribute:
        assert attribute in query.select_clause
    assert "investigation" in query.join_clause
    assert "id" in query.where_clause
    res = client.search(query)
    assert len(res) == 1
    assert res[0] == expected

@pytest.mark.parametrize(("entity", "kwargs"), [
    ("Datafile", dict(attributes="name", order=True)),
    ("InvestigationUser",
     dict(attributes=("investigation.name", "role"),
          conditions={"investigation.name": "= '08100122-EF'"},
          aggregate="DISTINCT")),
    ("Datafile", dict(order=[("name", "ASC")])),
    ("Datafile", dict(conditions={
        "name": "= 'e208945.nxs'",
        "dataset.name": "= 'e208945'",
        "dataset.investigation.name": "= '12100409-ST'",
    })),
    ("Instrument", dict(order=["name"],
                        includes={"facility", "instrumentScientists.user"})),
    ("Rule", dict(order=['grouping', 'what', 'id'],
                  conditions={"grouping":"IS NOT NULL"},
                  limit=(0,10))),
    ("Rule", dict(order=['grouping', 'what', 'id'],
                  join_specs={"grouping": "LEFT OUTER JOIN"})),
])
def test_query_copy(client, entity, kwargs):
    """Test the Query.copy() method.

    Very basic test: verify that Query.copy() yields an equivalent
    query for various Query() constructor argument sets.
    """
    if ('attributes' in kwargs and len(kwargs['attributes']) > 1 and
        not client._has_wsdl_type('fieldSet')):
        pytest.skip("search for multiple fields not supported by this server")
    query = Query(client, entity, **kwargs)
    clone = query.copy()
    assert str(clone) == str(query)
    assert entity in clone.select_clause
