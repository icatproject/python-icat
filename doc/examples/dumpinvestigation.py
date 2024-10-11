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

# ------------------------------------------------------------
# helper
# ------------------------------------------------------------

def get_investigation_id(client, invid):
    """Search the investigation id from name and optionally visitid."""
    query = Query(client, "Investigation", attributes=["id"])
    l = invid.split(':')
    query.addConditions({"name": "= '%s'" % l[0]})
    if len(l) == 2:
        # one colon, invid == name:visitId
        query.addConditions({"visitId": "= '%s'" % l[1]})
    else:
        # too many colons
        raise RuntimeError("Invalid investigation identifier '%s'" % invid)
    return client.assertedSearch(query)[0]

def mergesearch(client, queries):
    """Do many searches and merge the results in one list excluding dups."""
    objs = set()
    for se in queries:
        objs.update(client.search(se))
    return list(objs)

# The following helper functions control what ICAT objects are written
# in each of the dumpfile chunks.  There are three options for the
# items in each list: either queries expressed as Query objects, or
# queries expressed as string expressions, or lists of objects.  In
# the first two cases, the search results will be written, in the last
# case, the objects are written as provided.

def get_auth_types(client, invid):
    """Users and groups related to the investigation.
    """
    # We need the users related to our investigation via
    # InvestigationUser, the users member of one of the groups related
    # via InvestigationGroup, and the instrument scientists from the
    # instruments related to the investigations.  These are
    # independent searches, but the results are likely to overlap.  So
    # we need to search and merge results first.
    usersearch = [
        Query(client, "User", conditions={
            "investigationUsers."
            "investigation.id": "= %d" % invid,
        }),
        Query(client, "User", conditions={
            "userGroups.grouping.investigationGroups."
            "investigation.id": "= %d" % invid,
        }),
        Query(client, "User", conditions={
            "instrumentScientists.instrument.investigationInstruments."
            "investigation.id": "= %d" % invid,
        }),
    ]
    return [
        mergesearch(client, usersearch),
        Query(client, "Grouping", conditions={
            "investigationGroups.investigation.id": "= %d" % invid,
        }, includes=["userGroups.user"], aggregate="DISTINCT", order=True),
    ]

def get_static_types(client, invid):
    """Static stuff that exists independently of the investigation in ICAT.
    """
    # Similar situation for ParameterType as for User: need to merge
    # ParameterType used for InvestigationParameter, SampleParameter,
    # DatasetParameter, and DatafileParameter.
    ptsearch = [
        Query(client, "ParameterType", conditions={
            "investigationParameters."
            "investigation.id": "= %d" % invid,
        }, includes=["facility", "permissibleStringValues"]),
        Query(client, "ParameterType", conditions={
            "sampleParameters.sample."
            "investigation.id": "= %d" % invid,
        }, includes=["facility", "permissibleStringValues"]),
        Query(client, "ParameterType", conditions={
            "datasetParameters.dataset."
            "investigation.id": "= %d" % invid,
        }, includes=["facility", "permissibleStringValues"]),
        Query(client, "ParameterType", conditions={
            "datafileParameters.datafile.dataset."
            "investigation.id": "= %d" % invid,
        }, includes=["facility", "permissibleStringValues"]),
    ]
    return [
        Query(client, "Facility",
              conditions={
                  "investigations.id": "= %d" % invid,
              },
              order=True),
        Query(client, "Instrument",
              conditions={
                  "investigationInstruments.investigation.id": "= %d" % invid,
              },
              includes=["facility", "instrumentScientists.user"],
              order=True),
        mergesearch(client, ptsearch),
        Query(client, "InvestigationType",
              conditions={
                  "investigations.id": "= %d" % invid,
              },
              includes=["facility"],
              order=True),
        Query(client, "SampleType",
              conditions={
                  "samples.investigation.id": "= %d" % invid,
              },
              includes=["facility"],
              aggregate="DISTINCT",
              order=True),
        Query(client, "DatasetType",
              conditions={
                  "datasets.investigation.id": "= %d" % invid,
              },
              includes=["facility"],
              aggregate="DISTINCT",
              order=True),
        Query(client, "DatafileFormat",
              conditions={
                  "datafiles.dataset.investigation.id": "= %d" % invid,
              },
              includes=["facility"],
              aggregate="DISTINCT",
              order=True),
    ]

def get_investigation_types(client, invid):
    """The investigation and all the stuff that belongs to it.
    """
    # The set of objects to be included in the Investigation.
    inv_includes = {
        "facility", "type.facility", "investigationInstruments",
        "investigationInstruments.instrument.facility", "shifts",
        "keywords", "publications", "investigationUsers",
        "investigationUsers.user", "investigationGroups",
        "investigationGroups.grouping", "parameters",
        "parameters.type.facility"
    }
    return [
        Query(client, "Investigation",
              conditions={"id":"in (%d)" % invid},
              includes=inv_includes),
        Query(client, "Sample",
              conditions={"investigation.id":"= %d" % invid},
              includes={"investigation", "type.facility",
                        "parameters", "parameters.type.facility"},
              order=True),
        Query(client, "Dataset",
              conditions={"investigation.id":"= %d" % invid},
              includes={"investigation", "type.facility", "sample",
                        "parameters", "parameters.type.facility"},
              order=True),
        Query(client, "Datafile",
              conditions={"dataset.investigation.id":"= %d" % invid},
              includes={"dataset", "datafileFormat.facility",
                        "parameters", "parameters.type.facility"},
              order=True)
    ]

# ------------------------------------------------------------
# Do it
# ------------------------------------------------------------

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


invid = get_investigation_id(client, conf.investigation)

with open_dumpfile(client, conf.file, conf.format, 'w') as dumpfile:
    dumpfile.writedata(get_auth_types(client, invid))
    dumpfile.writedata(get_static_types(client, invid))
    dumpfile.writedata(get_investigation_types(client, invid))
