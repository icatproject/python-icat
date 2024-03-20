File formats
============

Some components of python-icat read input files or write output files:

The :ref:`icatdump` command line script fetches content from an ICAT
server and writes it to a file.  The :ref:`icatingest` command line
script reads those files and restores the content in an ICAT server.
The ICAT data file format written and read by these scripts
respectively corresponds directly to the ICAT schema.  It is rather
generic and may encode any ICAT content.

The metadata ingest file format is basically a restricted version of
the ICAT data file format.  It is read by class
:class:`icat.ingest.IngestReader` for the purpose of ingesting
metadata created by experiments into ICAT.

See the following sections for a detailed description of these file
formats:

.. toctree::
   :maxdepth: 1

   file-icatdata
   file-icatingest
