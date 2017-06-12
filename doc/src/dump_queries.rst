:mod:`icat.dump_queries` --- Queries needed to dump the ICAT content
====================================================================

.. py:module:: icat.dump_queries

.. note::
   This module is mostly intended as a helper for the icatdump script.
   Most users will not need to use it directly or even care about.

The data icatdump is written in chunks, see the documentation of
:mod:`icat.dumpfile` for details why this is needed.  The partition
used here is the following:

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


.. autofunction:: icat.dump_queries.getAuthQueries

.. autofunction:: icat.dump_queries.getStaticQueries

.. autofunction:: icat.dump_queries.getInvestigationQueries

.. autofunction:: icat.dump_queries.getOtherQueries
