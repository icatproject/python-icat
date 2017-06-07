"""Define queries needed to dump the full ICAT content.

.. note::
   This module is mostly intended as a helper for the icatdump script.
   Most users will not need to use it directly or even care about it.

The data icatdump is written in chunks, see the documentation of
icat.dumpfile for details why this is needed.  The partition used
here is the following:

1. One chunk with all objects that define authorization (User, Group,
   Rule, PublicStep).
2. All static content in one chunk, e.g. all objects not related to
   individual investigations and that need to be present, before we
   can add investigations.
3. The investigation data.  All content related to individual
   investigations.  Each investigation with all its data in one single
   chunk on its own.
4. One last chunk with all remaining stuff (RelatedDatafile,
   DataCollection, Job).

The functions defined in this module each return a list of queries
needed to fetch all objects to be included in one of these chunkes.
"""

import icat
from icat.query import Query

__all__ = [ 'getAuthQueries', 'getStaticQueries', 
            'getInvestigationQueries', 'getOtherQueries' ]


def getAuthQueries(client):
    """Return the queries to fetch all objects related to authorization.
    """
    return [ Query(client, "User", order=True), 
             Query(client, "Grouping", order=True, 
                   includes=set(["userGroups", "userGroups.user"])),
             Query(client, "Rule", order=["what", "id"], 
                   conditions={"grouping": "IS NULL"}), 
             Query(client, "Rule", order=["grouping.name", "what", "id"], 
                   conditions={"grouping": "IS NOT NULL"}, 
                   includes=set(["grouping"])), 
             Query(client, "PublicStep", order=True) ]

def getStaticQueries(client):
    """Return the queries to fetch all static objects.
    """
    return [ Query(client, "Facility", order=True), 
             Query(client, "Instrument", order=True, 
                   includes=set(["facility", "instrumentScientists.user"])), 
             Query(client, "ParameterType", order=True, 
                   includes=set(["facility", "permissibleStringValues"])), 
             Query(client, "InvestigationType", order=True, 
                   includes=set(["facility"])), 
             Query(client, "SampleType", order=True, 
                   includes=set(["facility"])), 
             Query(client, "DatasetType", order=True, 
                   includes=set(["facility"])), 
             Query(client, "DatafileFormat", order=True, 
                   includes=set(["facility"])), 
             Query(client, "FacilityCycle", order=True, 
                   includes=set(["facility"])), 
             Query(client, "Application", order=True, 
                   includes=set(["facility"])) ]

def getInvestigationQueries(client, invid):
    """Return the queries to fetch all objects related to an investigation.
    """
    # Compatibility ICAT 4.3.* vs. ICAT 4.4.0 and later: include
    # InvestigationGroups.
    inv_includes = set([ "facility", "type.facility", "investigationInstruments", 
                         "investigationInstruments.instrument.facility", "shifts", 
                         "keywords", "publications", "investigationUsers", 
                         "investigationUsers.user", "parameters", 
                         "parameters.type.facility" ])
    if client.apiversion > '4.3.99':
        inv_includes |= set([ "investigationGroups", 
                              "investigationGroups.grouping" ])

    return [ Query(client, "Investigation", 
                   conditions={"id": "= %d" % invid}, 
                   includes=inv_includes), 
             Query(client, "Sample", order=["name"], 
                   conditions={"investigation.id": "= %d" % invid}, 
                   includes=set(["investigation", "type.facility", 
                                 "parameters", "parameters.type.facility"])), 
             Query(client, "Dataset", order=["name"], 
                   conditions={"investigation.id": "= %d" % invid}, 
                   includes=set(["investigation", "type.facility", 
                                 "sample", "parameters.type.facility"])), 
             Query(client, "Datafile", order=["dataset.name", "name"], 
                   conditions={"dataset.investigation.id": "= %d" % invid}, 
                   includes=set(["dataset", "datafileFormat.facility", 
                                 "parameters.type.facility"])) ]

def getOtherQueries(client):
    """Return the queries to fetch all other objects, 
    e.g. not static and not directly related to an investigation.
    """
    # Compatibility ICAT 4.3.0 vs. ICAT 4.3.1 and later: name of the
    # parameters relation in DataCollection.
    if client.apiversion < '4.3.1':
        datacolparamname = 'dataCollectionParameters'
    else:
        datacolparamname = 'parameters'

    return [ Query(client, "Study", order=True, 
                   includes=set(["user", "studyInvestigations", 
                                 "studyInvestigations.investigation.facility"])), 
             Query(client, "RelatedDatafile", order=True, 
                   includes=set(["sourceDatafile.dataset.investigation.facility", 
                                 "destDatafile.dataset.investigation.facility"])), 
             Query(client, "DataCollection", order=True, 
                   includes=set([("dataCollectionDatasets.dataset."
                                  "investigation.facility"), 
                                 ("dataCollectionDatafiles.datafile.dataset."
                                  "investigation.facility"), 
                                 "%s.type.facility" % datacolparamname])), 
             Query(client, "Job", order=True, 
                   includes=set(["application.facility", 
                                 "inputDataCollection", "outputDataCollection"])) ]
