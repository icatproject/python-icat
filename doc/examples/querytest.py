#! /usr/bin/python
"""Provide some examples on how to use the query module.
"""

import logging
import sys
import yaml
import icat
import icat.config
from icat.query import Query

logging.basicConfig(level=logging.INFO)

config = icat.config.Config()
config.add_variable('datafile', ("datafile",),
                    dict(metavar="inputdata.yaml",
                         help="name of the input datafile"))
client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)


# ------------------------------------------------------------
# Read input data
# ------------------------------------------------------------

if conf.datafile == "-":
    f = sys.stdin
else:
    f = open(conf.datafile, 'r')
data = yaml.safe_load(f)
f.close()


# ------------------------------------------------------------
# Query examples
# ------------------------------------------------------------

# To simplify things, we take search values from the example data job.
inp = data['jobs']['job1']['input']

print("\nA simple query for an investigation by name.")
name = inp['datasets'][0]['investigation']
q = Query(client, "Investigation", conditions={"name":"= '%s'" % name})
print(str(q))
res = client.search(q)
print("%d result(s)" % len(res))
# keep the investigation id for a later example
if len(res) > 0:
    invid = res[0].id
else:
    # No result, use a bogus id instead
    invid = 4711

print("\nUse investigation id: %d" % invid)

print("\nQuery a datafile by its name, dataset name, and investigation name:")
df = inp['datafiles'][0]
conditions = {
    "name":"= '%s'" % df['name'],
    "dataset.name":"= '%s'" % df['dataset'],
    "dataset.investigation.name":"= '%s'" % df['investigation'],
}
q = Query(client, "Datafile", conditions=conditions)
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nSame example, but use placeholders in the query string now:")
df = inp['datafiles'][0]
conditions = {
    "name":"= '%(name)s'",
    "dataset.name":"= '%(dataset)s'",
    "dataset.investigation.name":"= '%(investigation)s'",
}
q = Query(client, "Datafile", conditions=conditions)
print(str(q))
print(str(q) % df)
print("%d result(s)" % len(client.search(str(q) % df)))

print("\nQuery lots of information about one single investigation.")
includes = { "facility", "type.facility", "investigationInstruments",
             "investigationInstruments.instrument.facility", "shifts",
             "keywords", "publications", "investigationUsers",
             "investigationUsers.user", "investigationGroups",
             "investigationGroups.grouping", "parameters",
             "parameters.type.facility" }
q = Query(client, "Investigation",
          conditions={"id":"= %d" % invid}, includes=includes)
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nQuery the instruments related to a given investigation.")
q = Query(client, "Instrument",
          order=["name"],
          conditions={ "investigationInstruments.investigation.id":
                       "= %d" % invid },
          includes={"facility", "instrumentScientists.user"})
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nThe datafiles related to a given investigation in natural order.")
q = Query(client, "Datafile", order=True,
          conditions={ "dataset.investigation.id":"= %d" % invid },
          includes={"dataset", "datafileFormat.facility",
                    "parameters.type.facility"})
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nSame example, but skip the investigation in the order.")
q = Query(client, "Datafile", order=['dataset.name', 'name'],
          conditions={ "dataset.investigation.id":"= %d" % invid },
          includes={"dataset", "datafileFormat.facility",
                    "parameters.type.facility"})
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nRelatedDatafile is the entity type with the most complicated "
      "natural order.")
q = Query(client, "RelatedDatafile", order=True)
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nThere is no sensible order for DataCollection, fall back to id.")
q = Query(client, "DataCollection", order=True)
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nDatafiles ordered by format.")
print("(Note: this raises a QueryNullableOrderWarning, see below.)")
q = Query(client, "Datafile", order=['datafileFormat', 'dataset', 'name'])
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nOther relations then equal may be used in the conditions too.")
condition = {"datafileCreateTime":">= '2012-01-01'"}
q = Query(client, "Datafile", conditions=condition)
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nWe may also add a list of conditions on a single attribute.")
condition = {"datafileCreateTime":[">= '2012-01-01'", "< '2013-01-01'"]}
q = Query(client, "Datafile", conditions=condition)
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nThe last example also works by adding the conditions separately.")
q = Query(client, "Datafile")
q.addConditions({"datafileCreateTime":">= '2012-01-01'"})
q.addConditions({"datafileCreateTime":"< '2013-01-01'"})
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nUsing \"id in (i)\" rather than \"id = i\" also works.")
print("(This may be needed to work around ICAT Issue 149.)")
q = Query(client, "Investigation", conditions={"id":"in (%d)" % invid})
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nRule does not have a constraint, id is included in the natural order.")
q = Query(client, "Rule", order=True)
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nOrdering on nullable relations emits a warning.")
q = Query(client, "Rule", order=['grouping', 'what', 'id'])
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nThe warning can be suppressed by making the condition explicit.")
q = Query(client, "Rule", order=['grouping', 'what', 'id'],
          conditions={"grouping":"IS NOT NULL"})
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nAdd a LIMIT clause to the last example.")
q.setLimit( (0,10) )
print(str(q))
print("%d result(s)" % len(client.search(q)))

print("\nLIMIT clauses are particular useful with placeholders.")
q.setLimit( ("%d","%d") )
print(str(q))
print(str(q) % (0,30))
print("%d result(s)" % len(client.search(str(q) % (0,30))))
print(str(q) % (30,30))
print("%d result(s)" % len(client.search(str(q) % (30,30))))
