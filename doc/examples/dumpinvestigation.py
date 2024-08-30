#! /usr/bin/python
#
# Dump the objects related to a single investigation to a file or to
# stdout.
#
# This is intended to demonstrate the dumpfile API.  The result
# should be a subset of the dumpfile created by icatdump.
#

import logging
import icat
import icat.config
from icat.query import Query
from icat.dumpfile import open_dumpfile
import icat.dumpfile_xml
import icat.dumpfile_yaml

logging.basicConfig(level=logging.INFO)

formats = icat.dumpfile.Backends.keys()
config = icat.config.Config()
config.add_variable('file', ("-o", "--outputfile"),
                    dict(help="output file name or '-' for stdout"),
                    default='-')
config.add_variable('format', ("-f", "--format"),
                    dict(help="output file format", choices=formats),
                    default='YAML')
config.add_variable('investigation', ("investigation",),
                    dict(help="name and optionally visit id "
                         "(separated by a colon) of the investigation"))
client, conf = config.getconfig()

if client.apiversion < '4.4':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.4.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


# ------------------------------------------------------------
# helper
# ------------------------------------------------------------

def getinvestigation(invid):
    """Search the investigation id from name and optionally visitid."""
    l = invid.split(':')
    if len(l) == 1:
        # No colon, invid == name
        searchexp = "Investigation.id [name='%s']" % tuple(l)
    elif len(l) == 2:
        # one colon, invid == name:visitId
        searchexp = "Investigation.id [name='%s' AND visitId='%s']" % tuple(l)
    else:
        # too many colons
        raise RuntimeError("Invalid investigation identifier '%s'" % invid)
    return (client.assertedSearch(searchexp)[0])

def mergesearch(sexps):
    """Do many searches and merge the results in one list excluding dups."""
    objs = set()
    for se in sexps:
        objs.update(client.search(se))
    return list(objs)


# ------------------------------------------------------------
# Do it
# ------------------------------------------------------------

invid = getinvestigation(conf.investigation)


# We need the users related to our investigation via
# InvestigationUser, the users member of one of the groups related via
# InvestigationGroup, and the instrument scientists from the
# instruments related to the investigations.  These are independent
# searches, but the results are likely to overlap.  So we need to
# search and merge results first.  Similar situation for ParameterType.
usersearch = [
    Query(client, "User", conditions=[
        ("investigationUsers.investigation.id", "= %d")
    ]),
    Query(client, "User", conditions=[
        ("userGroups.grouping.investigationGroups.investigation.id", "= %d")
    ]),
    Query(client, "User", conditions=[
        ("instrumentScientists.instrument.investigationInstruments."
         "investigation.id", "= %d")
    ]),
]
ptsearch = [
    Query(client, "ParameterType", conditions=[
        ("investigationParameters.investigation.id", "= %d")
    ], includes=["facility", "permissibleStringValues"]),
    Query(client, "ParameterType", conditions=[
        ("sampleParameters.sample.investigation.id", "= %d")
    ], includes=["facility", "permissibleStringValues"]),
    Query(client, "ParameterType", conditions=[
        ("datasetParameters.dataset.investigation.id", "= %d")
    ], includes=["facility", "permissibleStringValues"]),
    Query(client, "ParameterType", conditions=[
        ("datafileParameters.datafile.dataset.investigation.id", "= %d")
    ], includes=["facility", "permissibleStringValues"]),
]

# The set of objects to be included in the Investigation.
inv_includes = { "facility", "type.facility", "investigationInstruments",
                 "investigationInstruments.instrument.facility", "shifts",
                 "keywords", "publications", "investigationUsers",
                 "investigationUsers.user", "investigationGroups",
                 "investigationGroups.grouping", "parameters",
                 "parameters.type.facility" }

# The following lists control what ICAT objects are written in each of
# the dumpfile chunks.  There are three options for the items in each
# list: either queries expressed as Query objects, or queries
# expressed as string expressions, or lists of objects.  In the first
# two cases, the seacrh results will be written, in the last case, the
# objects are written as provided.
authtypes = [
    mergesearch([str(s) % invid for s in usersearch]),
    Query(client, "Grouping", conditions=[
        ("investigationGroups.investigation.id", "= %d" % invid)
    ], order=["name"], includes=["userGroups.user"])
]
statictypes = [
    Query(client, "Facility", order=True),
    Query(client, "Instrument", conditions=[
        ("investigationInstruments.investigation.id", "= %d" % invid)
    ], order=True, includes=["facility", "instrumentScientists.user"]),
    mergesearch([str(s) % invid for s in ptsearch]),
    Query(client, "InvestigationType", conditions=[
        ("investigations.id", "= %d" % invid)
    ], order=True, includes=["facility"]),
    Query(client, "SampleType", conditions=[
        ("samples.investigation.id", "= %d" % invid)
    ], order=True, includes=["facility"]),
    Query(client, "DatasetType", conditions=[
        ("datasets.investigation.id", "= %d" % invid)
    ], order=True, includes=["facility"]),
    Query(client, "DatafileFormat", conditions=[
        ("datafiles.dataset.investigation.id", "= %d" % invid)
    ], order=True, includes=["facility"]),
]
investtypes = [
    Query(client, "Investigation",
          conditions=[("id", "in (%d)" % invid)],
          includes=inv_includes),
    Query(client, "Sample", order=["name"],
          conditions=[("investigation.id", "= %d" % invid)],
          includes={"investigation", "type.facility",
                    "parameters", "parameters.type.facility"}),
    Query(client, "Dataset", order=["name"],
          conditions=[("investigation.id", "= %d" % invid)],
          includes={"investigation", "type.facility", "sample",
                    "parameters", "parameters.type.facility"}),
    Query(client, "Datafile", order=["dataset.name", "name"],
          conditions=[("dataset.investigation.id", "= %d" % invid)],
          includes={"dataset", "datafileFormat.facility",
                    "parameters", "parameters.type.facility"})
]

with open_dumpfile(client, conf.file, conf.format, 'w') as dumpfile:
    dumpfile.writedata(authtypes)
    dumpfile.writedata(statictypes)
    dumpfile.writedata(investtypes)
