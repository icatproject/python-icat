"""Define queries needed to dump the full ICAT content.

.. note::
   This module is mostly intended as a helper for the icatdump script.
   Most users will not need to use it directly or even care about it.

ICAT data files are written in chunks.  The partition used here is the
following:

1. One chunk with all objects that define authorization (User, Group,
   Rule, PublicStep).
2. All static content in one chunk, e.g. all objects not related to
   individual investigations and that need to be present, before we
   can add investigations.
3. FundingReferences.
4. The investigation data.  All content related to individual
   investigations.  Each investigation with all its data in one single
   chunk on its own.
5. DataCollections.
6. DataPublications.  All content related to individual data
   publications, each one in one chunk on its own respectively.
7. One last chunk with all remaining stuff (Study, RelatedDatafile,
   Job).

The functions defined in this module each return a list of queries
needed to fetch the objects to be included in one of these chunks.
The queries are adapted to the ICAT server version the client is
connected to.

.. versionchanged:: 1.0.0
    review the partition to take the schema extensions in ICAT 5.0
    into account and include the new entity types.
"""

from .query import Query

__all__ = [ 'getAuthQueries', 'getStaticQueries', 'getFundingQueries',
            'getInvestigationQueries', 'getDataCollectionQueries',
            'getDataPublicationQueries', 'getOtherQueries' ]


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

    .. versionchanged:: 1.0.0
        include queries for ``Technique`` and ``DataPublicationType``.
    """
    # Compatibility between ICAT versions:
    # - ICAT 5.0.0 added DataPublicationType and Technique.
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
    if 'dataPublicationType' in client.typemap:
        # ICAT >= 5.0.0
        queries.insert(3, Query(client, "DataPublicationType", order=True,
                                includes={"facility"}) )
    if 'technique' in client.typemap:
        # ICAT >= 5.0.0
        queries.insert(0, Query(client, "Technique", order=True) )
    return queries

def getFundingQueries(client):
    """Return the queries to fetch all FundingReferences.

    .. versionadded:: 1.0.0
    """
    # Compatibility between ICAT versions:
    # - ICAT 5.0.0 added FundingReference.
    if 'fundingReference' in client.typemap:
        return [ Query(client, "FundingReference", order=True), ]
    else:
        return []

def getInvestigationQueries(client, invid):
    """Return the queries to fetch all objects related to an investigation.

    .. versionchanged:: 1.0.0
        add include clauses for ``investigationFacilityCycles`` and
        ``fundingReferences`` into query for ``Investigation``, add
        include clauses for ``datasetInstruments`` and
        ``datasetTechniques`` into query for ``Dataset``.
    """
    # Compatibility between ICAT versions:
    # - ICAT 4.4.0 added InvestigationGroups.
    # - ICAT 4.10.0 added relation between Shift and Instrument.
    # - ICAT 5.0.0 added InvestigationFunding and InvestigationFacilityCycle.
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
    if 'investigationFacilityCycle' in client.typemap:
        # ICAT >= 5.0.0
        inv_includes |= { "investigationFacilityCycles.facilityCycle.facility" }
    if 'investigationFunding' in client.typemap:
        # ICAT >= 5.0.0
        inv_includes |= { "fundingReferences.funding" }
    ds_includes = { "investigation", "type.facility", "sample",
                    "parameters.type.facility" }
    if 'datasetInstruments' in client.typemap['dataset'].InstMRel:
        # ICAT >= 5.0.0
        ds_includes |= { "datasetInstruments.instrument.facility" }
    if 'datasetTechniques' in client.typemap['dataset'].InstMRel:
        # ICAT >= 5.0.0
        ds_includes |= { "datasetTechniques.technique" }

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

    .. versionadded:: 1.0.0
    """
    # Compatibility between ICAT versions:
    # - ICAT 4.3.0 vs. ICAT 4.3.1 and later: name of the parameters
    #   relation in DataCollection.
    # - ICAT 5.0.0 added DataCollectionInvestigation.
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
    if 'dataCollectionInvestigation' in client.typemap:
        # ICAT >= 5.0.0
        dc_includes |= { "dataCollectionInvestigations.investigation.facility" }
    return [
        Query(client, "DataCollection", order=True,
              includes=dc_includes),
    ]

def getDataPublicationQueries(client, pubid):
    """Return the queries to fetch all objects related to a data publication.

    .. versionadded:: 1.0.0

    .. versionchanged:: 1.1.0
        return an empty list if the ICAT server is older than 5.0
        rather than raising :exc:`~icat.exception.EntityTypeError`.
    """
    # Compatibility between ICAT versions:
    # - ICAT 5.0.0 added DataPublication and related classes.
    if 'dataPublication' in client.typemap:
        # ICAT >= 5.0.0
        return [
            Query(client, "DataPublication", order=True,
                  conditions={"id": "= %d" % pubid},
                  includes={"facility", "content", "type.facility", "dates",
                            "fundingReferences.funding", "relatedItems"}),
            Query(client, "DataPublicationUser", order=True,
                  conditions={"publication.id": "= %d" % pubid},
                  includes={"publication", "user", "affiliations"}),
        ]
    else:
        return []

def getOtherQueries(client):
    """Return the queries to fetch all other objects,
    e.g. not static and not directly related to an investigation.

    .. versionchanged:: 1.0.0
        drop query for ``DataCollection``, now in a separate function
        :func:`getDataCollectionQueries`.
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
