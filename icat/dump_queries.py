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
needed to fetch all objects to be included in one of these chunks.
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
                   includes={"userGroups", "userGroups.user"}),
             Query(client, "Rule", order=["grouping.name", "what", "id"], 
                   includes={"grouping"},
                   join_specs={"grouping": "LEFT JOIN"}),
             Query(client, "PublicStep", order=True) ]

def getStaticQueries(client):
    """Return the queries to fetch all static objects.
    """
    return [ Query(client, "Facility", order=True), 
             Query(client, "Instrument", order=True, 
                   includes={"facility", "instrumentScientists.user"}), 
             Query(client, "ParameterType", order=True, 
                   includes={"facility", "permissibleStringValues"}), 
             Query(client, "InvestigationType", order=True, 
                   includes={"facility"}), 
             Query(client, "SampleType", order=True, 
                   includes={"facility"}), 
             Query(client, "DatasetType", order=True, 
                   includes={"facility"}), 
             Query(client, "DatafileFormat", order=True, 
                   includes={"facility"}), 
             Query(client, "FacilityCycle", order=True, 
                   includes={"facility"}), 
             Query(client, "Application", order=True, 
                   includes={"facility"}) ]

def getInvestigationQueries(client, invid):
    """Return the queries to fetch all objects related to an investigation.
    """
    # Compatibility between ICAT versions:
    # - ICAT 4.4.0 added InvestigationGroups.
    # - ICAT 4.10.0 added relation between Shift and Instrument.
    inv_includes = { "facility", "type.facility", "investigationInstruments", 
                     "investigationInstruments.instrument.facility", "shifts", 
                     "keywords", "publications", "investigationUsers", 
                     "investigationUsers.user", "parameters", 
                     "parameters.type.facility" }
    if 'investigationGroup' in client.typemap:
        # ICAT >= 4.4.0
        inv_includes |= { "investigationGroups", 
                          "investigationGroups.grouping" }
    if 'instrument' in client.typemap['shift'].InstRel:
        # ICAT >= 4.10.0
        inv_includes |= { "shifts.instrument.facility" }

    return [ Query(client, "Investigation", 
                   conditions={"id": "= %d" % invid}, 
                   includes=inv_includes), 
             Query(client, "Sample", order=["name"], 
                   conditions={"investigation.id": "= %d" % invid}, 
                   includes={"investigation", "type.facility", 
                             "parameters", "parameters.type.facility"}), 
             Query(client, "Dataset", order=["name"], 
                   conditions={"investigation.id": "= %d" % invid}, 
                   includes={"investigation", "type.facility", 
                             "sample", "parameters.type.facility"}), 
             Query(client, "Datafile", order=["dataset.name", "name"], 
                   conditions={"dataset.investigation.id": "= %d" % invid}, 
                   includes={"dataset", "datafileFormat.facility", 
                             "parameters.type.facility"}) ]

def getOtherQueries(client):
    """Return the queries to fetch all other objects, 
    e.g. not static and not directly related to an investigation.
    """
    # Compatibility ICAT 4.3.0 vs. ICAT 4.3.1 and later: name of the
    # parameters relation in DataCollection.
    if 'parameters' in client.typemap['dataCollection'].InstMRel:
        # ICAT >= 4.3.1
        datacolparamname = 'parameters'
    else:
        datacolparamname = 'dataCollectionParameters'

    return [ Query(client, "Study", order=True, 
                   includes={"user", "studyInvestigations", 
                             "studyInvestigations.investigation.facility"}), 
             Query(client, "RelatedDatafile", order=True, 
                   includes={"sourceDatafile.dataset.investigation.facility", 
                             "destDatafile.dataset.investigation.facility"}), 
             Query(client, "DataCollection", order=True, 
                   includes={("dataCollectionDatasets.dataset."
                              "investigation.facility"), 
                             ("dataCollectionDatafiles.datafile.dataset."
                              "investigation.facility"), 
                             "%s.type.facility" % datacolparamname}), 
             Query(client, "Job", order=True, 
                   includes={"application.facility", 
                             "inputDataCollection", "outputDataCollection"}) ]
