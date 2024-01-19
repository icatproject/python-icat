.. _ICAT-ingest-files:

Metadata ingest files
=====================

Metadata ingest files are the input format for class
:class:`icat.ingest.IngestReader`.  This class is intended to be uesd
in scripts that read the metadata created by experimments into ICAT.
The file format is basically a restricted version of
:ref:`ICAT-data-xml-files`.

The underlying idea is that ICAT data files are in principle suitable
to encode the metadata to be ingested from the experiment.  The only
problem is that this file format is too powerful: it can encode any
ICAT content.  We want the ingest files from the experiment to create
new Datasets and DatasetParameters, we certainly don't want these
files to create new Instruments or Users in ICAT.  And we also want to
control the Investigation that newly created Datasets will be added
to.  It would be rather difficult to control the power of the input
format if we would use plain ICAT data files for this purpose.

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

* object definitions for Datasets can not include a reference to the
  related Investigation.  The relation with the prescribed
  Investigation will be implied.

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
attrbute.
