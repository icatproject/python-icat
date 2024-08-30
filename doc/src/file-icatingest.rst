.. _ICAT-ingest-files:

Metadata ingest files
=====================

Metadata ingest files are the input format for class
:class:`icat.ingest.IngestReader`.  This class is intended to be used
in scripts that read the metadata created by experiments into ICAT.
The file format is basically a restricted version of
:ref:`ICAT-data-xml-files`.

The underlying idea is that ICAT data files are in principle suitable
to encode the metadata to be ingested from the experiment.  The only
problem is that this file format is too powerful: it can encode any
ICAT content.  We want the ingest files from the experiment to create
new Datasets and DatasetParameters, we certainly don't want these
files to create new Instruments or Users in ICAT.  And we also want to
control to which Investigation newly created Datasets are going to be
added.  It would be rather difficult to control the power of the input
format if we would use plain ICAT data files for this purpose.

.. note::
   The metadata ingest file format is versioned.  This version number
   is independent from the python-icat version.  It is incremented
   only when the format changes.  The latest version of the metadata
   ingest file format is 1.1.

.. versionchanged:: 1.2.0
   add metadata ingest file format version 1.1, adding support for
   relating Datasets with Samples.

Differences compared to ICAT data XML files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Class :class:`icat.ingest.IngestReader` takes an ``investigation``
argument.  We will refer to the Investigation given in this argument
as the *prescribed Investigation* in the following.  The metadata
ingest file format restricts ICAT data XML files in the following
ways:

* ingest files must contain one and only one  ``data`` element,
  e.g. one chunk according to the :ref:`ICAT-data-files-structure`.

* the allowed object types are restricted to Dataset,
  DatasetInstrument, DatasetTechnique, and DatasetParameter.

* the attributes in the object definitions for Datasets are restricted
  to name, description, startDate, and endDate.

* object definitions for Datasets can not include references to the
  related Investigation or DatasetType.  These relation will be added
  by :class:`icat.ingest.IngestReader`.  The relation to the
  Investigation will be set to the prescribed Investigation.

* object definitions for Datasets can reference a related Sample only
  by name or by pid.  A relation of the related Sample with the
  prescribed Investigation will be implied.

* references to the related Dataset in DatasetInstrument,
  DatasetTechnique, and DatasetParameter definitions are restricted to
  :ref:`local keys <ICAT-data-files-references>`.  As a result, these
  objects can only relate to Datasets defined in the same ingest file.

* other object references are restricted to reference by attributes.

These restrictions are enforced by validating the input against an XML
Schema Definition (XSD).

Another change with respect to ICAT data XML files is that the name of
the root element is ``icatingest`` and that it must have a ``version``
attribute.

Example
~~~~~~~

Consider the following example:

.. literalinclude:: ../examples/metadata.xml
   :language: xml

This file defines four Datasets with related objects.  All datasets
have a ``name``, ``description``, ``startDate``, and ``endDate``
attribute and include a relation with an Instrument and a Technique,
respectively.

Note that the Datasets have no ``complete`` attribute and no relation
with Investigation or DatasetType respectively.  All of these are
added with prescribed values by class
:class:`icat.ingest.IngestReader`.

Some Datasets relate to Samples: the first two Datasets relate to the
same Sample, the third Dataset to another Sample, while the last
Dataset has no relation with any Sample.  All Samples are referenced
by their name.  Class :class:`icat.ingest.IngestReader` will add a
reference to the Investigation to this, so that only Samples that are
related to the prescribed Investigation can actually be referenced.

Some DatasetParameter are added as separate objects in the file.  They
respectively reference their related Datasets using local keys that
are defined in the ``id`` attribute of the corresponding Dataset
earlier in the file.  Alternatively, the DatasetParameter could have
been included into into the respective Datasets.
