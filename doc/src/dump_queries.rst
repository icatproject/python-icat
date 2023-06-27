:mod:`icat.dump_queries` --- Queries needed to dump the ICAT content
====================================================================

.. py:module:: icat.dump_queries

.. note::
   This module is mostly intended as a helper for the :ref:`icatdump`
   script.  Most users will not need to use it directly or even care
   about it.

:ref:`ICAT-data-files` are written in chunks.  The partition used here
is the following:

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
    Review the partition to take the schema extensions in ICAT 5.0
    into account and include the new entity types.

.. autofunction:: icat.dump_queries.getAuthQueries

.. autofunction:: icat.dump_queries.getStaticQueries

.. autofunction:: icat.dump_queries.getFundingQueries

.. autofunction:: icat.dump_queries.getInvestigationQueries

.. autofunction:: icat.dump_queries.getDataCollectionQueries

.. autofunction:: icat.dump_queries.getDataPublicationQueries

.. autofunction:: icat.dump_queries.getOtherQueries
