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
4. DataCollections.
5. One last chunk with all remaining stuff (Study, RelatedDatafile,
   Job).

The functions defined in this module each return a list of queries
needed to fetch all objects to be included in one of these chunks.
"""

import icat
from icat.query import Query

__all__ = [ 'getAuthQueries', 'getStaticQueries',
            'getInvestigationQueries', 'getDataCollectionQueries',
            'getOtherQueries' ]


def getAuthQueries(client):
    """Return the queries to fetch all objects related to authorization.
    """
    return [
        Query(client, "User", order=True),
        Query(client, "Grouping", order=True,
              includes={"userGroups", "userGroups.user"}),
        Query(client, "Rule", order=["grouping.name", "what", "id"],
              includes={"grouping"}, join_specs={"grouping": "LEFT JOIN"}),
        Query(client, "PublicStep", order=True)
    ]

def getStaticQueries(client):
    """Return the queries to fetch all static objects.
    """
    # Compatibility between ICAT versions:
    # - ICAT 5.0.0 added Technique.
    queries = [
        Query(client, "Facility", order=True),
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
              includes={"facility"})
    ]
    if 'technique' in client.typemap:
        # ICAT >= 5.0.0
        queries.append( Query(client, "Technique", order=True) )
    return queries

def getInvestigationQueries(client, invid):
    """Return the queries to fetch all objects related to an investigation.
    """
    # Compatibility between ICAT versions:
    # - ICAT 4.4.0 added InvestigationGroups.
    # - ICAT 4.10.0 added relation between Shift and Instrument.
    # - ICAT 5.0.0 added DatasetInstrument and DatasetTechnique.
    inv_includes = {
        "facility", "type.facility", "investigationInstruments",
        "investigationInstruments.instrument.facility", "shifts", "keywords",
        "publications", "investigationUsers", "investigationUsers.user",
        "parameters", "parameters.type.facility"
    }
    if 'investigationGroup' in client.typemap:
        # ICAT >= 4.4.0
        inv_includes |= { "investigationGroups",
                          "investigationGroups.grouping" }
    if 'instrument' in client.typemap['shift'].InstRel:
        # ICAT >= 4.10.0
        inv_includes |= { "shifts.instrument.facility" }
    ds_includes = { "investigation", "type.facility", "sample",
                    "parameters.type.facility" }
    if 'datasetInstruments' in client.typemap['dataset'].InstMRel:
        # ICAT >= 5.0.0
        ds_includes |= { "datasetInstruments.instrument.facility" }
    if 'datasetTechniques' in client.typemap['dataset'].InstMRel:
        # ICAT >= 5.0.0
        ds_includes |= { "datasetTechniques" }

    return [
        Query(client, "Investigation",
              conditions={"id": "= %d" % invid}, includes=inv_includes),
        Query(client, "Sample", order=["name"],
              conditions={"investigation.id": "= %d" % invid},
              includes={"investigation", "type.facility",
                        "parameters", "parameters.type.facility"}),
        Query(client, "Dataset", order=["name"],
              conditions={"investigation.id": "= %d" % invid},
              includes=ds_includes),
        Query(client, "Datafile", order=["dataset.name", "name"],
              conditions={"dataset.investigation.id": "= %d" % invid},
              includes={"dataset", "datafileFormat.facility",
                        "parameters.type.facility"})
    ]

def getDataCollectionQueries(client):
    """Return the queries to fetch all DataCollections.
    """
    # Compatibility ICAT 4.3.0 vs. ICAT 4.3.1 and later: name of the
    # parameters relation in DataCollection.
    dc_includes = {
        "dataCollectionDatasets.dataset.investigation.facility",
        "dataCollectionDatafiles.datafile.dataset.investigation.facility",
    }
    if 'parameters' in client.typemap['dataCollection'].InstMRel:
        # ICAT >= 4.3.1
        dc_includes |= { "parameters.type.facility" }
    else:
        # ICAT == 4.3.0
        dc_includes |= { "dataCollectionParameters.type.facility" }
    return [
        Query(client, "DataCollection", order=True,
              includes=dc_includes),
    ]

def getOtherQueries(client):
    """Return the queries to fetch all other objects,
    e.g. not static and not directly related to an investigation.
    """
    return [
        Query(client, "Study", order=True,
              includes={"user", "studyInvestigations",
                        "studyInvestigations.investigation.facility"}),
        Query(client, "RelatedDatafile", order=True,
              includes={"sourceDatafile.dataset.investigation.facility",
                        "destDatafile.dataset.investigation.facility"}),
        Query(client, "Job", order=True,
              includes={"application.facility",
                        "inputDataCollection", "outputDataCollection"})
    ]
