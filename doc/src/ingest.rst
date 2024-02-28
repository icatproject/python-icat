:mod:`icat.ingest` --- Ingest metadata into ICAT
================================================

.. py:module:: icat.ingest

.. versionadded:: 1.1.0

.. note::
   The status of this module in the current version is still
   experimental.  There may be incompatible changes in the future
   even in minor releases of python-icat.

This module provides class :class:`icat.ingest.IngestReader` that
reads :ref:`ICAT-ingest-files` to add them to ICAT.  It is designed
for the use case of ingesting metadata for datasets created during
experiments.

The :class:`~icat.ingest.IngestReader` is based on the general purpose
class :class:`~icat.dumpfile_xml.XMLDumpFileReader`.  It differs from
that base class in restricting the vocabular of the input file: only
objects that need to be created during ingestion from the experiment
may appear in the input.  This restriction is enforced by first
validating the input against an XML Schema Definition (XSD).  In a
second step, the input is transformed into generic :ref:`ICAT data XML
file format <ICAT-data-xml-files>` using an XSL Transformation (XSLT)
and then fed into :class:`~icat.dumpfile_xml.XMLDumpFileReader`.  The
format of the input files may be customized to some extent by
providing custom versions of XSD and XSLT files, see
:ref:`ingest-customize` below.

The ``Dataset`` objects in the input will not be created by
:class:`~icat.ingest.IngestReader`, because it is assumed that a
separate workflow in the caller will copy the content of datafiles to
the storage managed by IDS and create the corresponding ``Dataset``
and ``Datafile`` objects in ICAT at the same time.  But the attributes
of the datasets will be read from the input file and set in the
``Dataset`` objects by :class:`~icat.ingest.IngestReader`.
:class:`~icat.ingest.IngestReader` will also create the related
``DatasetTechnique``, ``DatasetInstrument`` and ``DatasetParameter``
objects read from the input file in ICAT.

.. autoclass:: icat.ingest.IngestReader
    :members:
    :show-inheritance:


.. _ingest-process:

Ingest process
--------------

The processing of ingest files during the instantiation of an
:class:`~icat.ingest.IngestReader` object may be summarized with the
following steps:

1. Read the metadata and parse the :class:`lxml.etree._ElementTree`.

2. Call :meth:`~icat.ingest.IngestReader.get_xsd` to get the
   appropriate XSD file and validate the metadata against that schema.

3. Inject an ``_environment`` element as first child of the ``data``
   element, see below.

4. Call :meth:`~icat.ingest.IngestReader.get_xslt` to get the
   appropriate XSLT file and transform the metadata into generic ICAT
   data XML file format.

5. Feed the result of the transformation into the parent class
   :class:`~icat.dumpfile_xml.XMLDumpFileReader`.

Once this initialization is done,
:meth:`~icat.ingest.IngestReader.ingest` may be called to read the
individual objects defined in the metadata.


.. _ingest-environment:

The environment element
-----------------------

During the processing of ingest files, an ``_environment`` element
will be injected as the first child of the ``data`` element.  In the
current version of python-icat, this ``_environment`` element has the
following attributes:

  `icat_version`
    Version of the ICAT server this client connects to, e.g. the
    :attr:`icat.client.Client.apiversion` attribute of the `client`
    object being used by this :class:`~icat.ingest.IngestReader`.

More attributes may be added in future versions.  This
``_environment`` element may be used by the XSLT in order to adapt the
result of the transformation to the environment, in particular to
adapt the output to the ICAT schema version it is supposed to conform
to.


.. _ingest-example:

Ingest example
--------------

It is assumed that the XSD and XSLT files (`ingest-*.xsd`,
`ingest.xslt`) provided with the python-icat source distribution are
installed in the directory pointed to by the class attribute
:attr:`~icat.ingest.IngestReader.SchemaDir` of
:class:`~icat.ingest.IngestReader`.  The core of an ingest script
might then look like::

  from pathlib import Path
  include icat
  from icat.ingest include IngestReader

  # prerequisite: search the investigation object to ingest into from
  # ICAT and collect a list of dataset objects that should be ingested
  # from the data collected at the experiment.  The datasets should be
  # instantiated (client.new('Dataset')) and include their respective
  # datafiles, but not yet created at this point:
  # investigation = client.assertedSearch(...)[0]
  # datasets = [...]
  # metadata = Path(...path to ingest file...)

  # Make a dry run to check for errors and fail early, before having
  # committed anything to ICAT yet.  As a side effect, this will
  # update the datasets, setting the attribute values that are read
  # from the input file:
  try:
      reader = IngestReader(client, metadata, investigation)
      reader.ingest(datasets, dry_run=True, update_ds=True)
  except (icat.InvalidIngestFileError, icat.SearchResultError) as e:
      raise RuntimeError("invalid ingest file") from e

  # Create the datasets.  In a real production script, you'd copy the
  # content of the datafiles to IDS storage at the same time:
  for ds in datasets:
      ds.create()

  # Now read the metadata into ICAT for real:
  reader.ingest(datasets)

There is a somewhat more complete script in the example directory of
the python-icat source distribution.


.. _ingest-customize:

Customizing the input format
----------------------------

The ingest input file format may be customized by providing custom XSD
and XSLT files.  The easiest way to do that is to subclass
:class:`~icat.ingest.IngestReader`.  In most cases, you'd only need to
override some class attributes as follows::

  from pathlib import Path
  import icat.ingest

  class MyFacilityIngestReader(icat.ingest.IngestReader):

      # Override the directory to search for XSD and XSLT files:
      SchemaDir = Path("/usr/share/icat/my-facility")

      # Override the XSD files to use:
      XSD_Map = {
          ('legacyingest', '0.5'): "legacy-ingest-05.xsd",
          ('myingest', '4.3'): "my-ingest-40.xsd",
      }

      # Override the XSLT file to use:
      XSLT_Map = {
          'legacyingest': "legacy-ingest.xslt",
          'myingest': "my-ingest.xslt",
      }

:attr:`~icat.ingest.IngestReader.XSD_Map` and
:attr:`~icat.ingest.IngestReader.XSLT_Map` are mappings with
properties of the root element of the input data as keys and file
names as values.  The methods
:meth:`~icat.ingest.IngestReader.get_xsd` and
:meth:`~icat.ingest.IngestReader.get_xslt` respectively inspect the
input file and use these mappings to select the XSD and XSLT file
accordingly.  Note that :attr:`~icat.ingest.IngestReader.XSD_Map`
takes tuples of root element name and version attribute as keys, while
:attr:`~icat.ingest.IngestReader.XSLT_Map` uses the name of the root
element name alone.  It is is assumed that it is fairly easy to
formulate adaptations to the input version directly in XSLT, so one
single XSLT file would be sufficient to cover all versions.

In the above example, `MyFacilityIngestReader` would recognize input
files like

.. code-block:: xml

  <?xml version='1.0' encoding='UTF-8'?>
  <legacyingest version="0.5">
      <!-- ... -->
  </legacyingest>

and

.. code-block:: xml

  <?xml version='1.0' encoding='UTF-8'?>
  <myingest version="4.3">
      <!-- ... -->
  </myingest>

Input files having any other combination of root element name and
version number would be rejected.

In more involved scenarios of selecting the XSD or XSLT files based on
the input, one may also override the
:meth:`~icat.ingest.IngestReader.get_xsd` and
:meth:`~icat.ingest.IngestReader.get_xslt` methods.
