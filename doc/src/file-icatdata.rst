.. _ICAT-data-files:

ICAT data files
===============

ICAT data files provide a way to serialize ICAT content to a flat
file.  These files are read by the :ref:`icatingest` and written by
the :ref:`icatdump` command line scripts respectively.  The program
logic for reading and writing the files is provided in the
:mod:`icat.dumpfile` module.

The actual file format depends on the version of the ICAT schema and
on the backend: python-icat provides backends using XML and YAML.

.. _ICAT-data-files-structure:

Logical structure of ICAT data files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Data files are partitioned in chunks.  This is done to avoid having
the whole file, e.g. the complete inventory of the ICAT, at once in
memory.  The problem is that objects contain references to other
objects, e.g. Datafiles refer to Datasets, the latter refer to
Investigations, and so forth.  We keep an index of the objects as
a cache in order to resolve these references.  But there is a memory
versus time tradeoff: in order to avoid the index to grow beyond
bounds, objects need to be discarded from the index from time to time.
References to objects that can not be resolved from the index need to
be searched from the ICAT server, which is of course expensive.  So
the strategy is as follows: keep all objects from the current chunk in
the index and discard the complete index each time a chunk has been
processed. [#dc]_ This will work fine if objects are mostly
referencing other objects from the same chunk and only a few
references go across chunk boundaries.

Therefore, we want these chunks to be small enough to fit into memory,
but at the same time large enough to keep as many relations between
objects as possible local in a chunk.  It is in the responsibility of
the writer of the data file to create the chunks in this manner.

The data chunks contain ICAT object definitions, e.g. serializations
of individual ICAT objects, including all attribute values and
many-to-one relations.  The many-to-one relations are provided as
references to other objects that must exist in the ICAT server at the
moment that this object definition is read.

There is some degree of flexibility with respect to related objects in
one-to-many relations: object definitions for these related objects
may be included in the object definitions of the parent object.  When
the parent is read, these related objects will be created along with
the parent in one single cascading call.  Thus, the related objects
must not be included again as a separate object in the ICAT data file.
For instance, an ICAT data file may include User, Grouping, and
UserGroup as separate objects.  In this case, the UserGroup entries
must properly reference User and Grouping as their related objects.
Alternatively the file may only contain User and Grouping objects,
with the UserGroups being included into the object definition of the
corresponding Grouping objects.

.. _ICAT-data-files-references:

References to ICAT objects and unique keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

References to ICAT objects may be encoded using reference keys.  There
are two kinds of those keys, local keys and unique keys:

When an ICAT object is defined in the file, it generally defines a
local key at the same time.  Local keys are stored in the object index
and may be used to reference this object from other objects in the
same data chunk.

Unique keys can be obtained from an object by calling
:meth:`icat.entity.Entity.getUniqueKey`.  An object can be searched by
its unique key from the ICAT server by calling
:meth:`icat.client.Client.searchUniqueKey`.  As a result, it is
possible to reference an object by its unique key even if the
reference is not in the object index.  All references that go across
chunk boundaries must use unique keys. [#dc]_

Reference keys should be considered as opaque ids.

.. _ICAT-data-xml-files:

ICAT data XML files
~~~~~~~~~~~~~~~~~~~

The root element of ICAT data XML files is ``icatdata``.  It may
optionally have one ``head`` subelement and one or more ``data``
subelements.

The ``head`` element will be ignored by :ref:`icatingest`.  It serves
to provide some information on the context of the creation of the data
file, which may be useful for debugging in case of issues.

The actual payload of an ICAT data XML file is in the ``data``
elements.  There can be any number of them and each is one chunk
according to the logical structure explained above.  The subelements
of ``data`` may either be ICAT object references or ICAT object
definitions, both explained in detail below.  Either of them may have
an ``id`` attribute that defines a local key that allows to reference
the corresponding object later on.

:numref:`snip-file-icatdata-xml-1` shows a simple example for an ICAT
data XML file having one single ``data`` element that defines four
Datasets.

.. code-block:: XML
    :name: snip-file-icatdata-xml-1
    :caption: A simple example for an ICAT data XML file
    :dedent: 2

      <?xml version="1.0" encoding="utf-8"?>
      <icatdata>
        <head>
          <date>2023-10-17T07:33:36Z</date>
          <generator>manual edit</generator>
        </head>
        <data>
          <investigationRef id="inv_1" name="10100601-ST" visitId="1.1-N"/>
          <dataset id="dataset_1">
            <complete>false</complete>
            <endDate>2012-07-30T01:10:08+00:00</endDate>
            <name>e209001</name>
            <startDate>2012-07-26T15:44:24+00:00</startDate>
            <investigation ref="inv_1"/>
            <sample name="ab3465" investigation.ref="inv_1"/>
            <type name="raw"/>
          </dataset>
          <dataset id="dataset_2">
            <complete>false</complete>
            <endDate>2012-08-06T01:10:08+00:00</endDate>
            <name>e209002</name>
            <startDate>2012-08-02T05:30:00+00:00</startDate>
            <investigation ref="inv_1"/>
            <sample name="ab3465" investigation.ref="inv_1"/>
            <type name="raw"/>
          </dataset>
          <dataset id="dataset_3">
            <complete>false</complete>
            <endDate>2012-07-16T14:30:17+00:00</endDate>
            <name>e209003</name>
            <startDate>2012-07-16T11:42:05+00:00</startDate>
            <investigation ref="inv_1"/>
            <sample name="ab3466" investigation.ref="inv_1"/>
            <type name="raw"/>
          </dataset>
          <dataset id="dataset_4">
            <complete>false</complete>
            <endDate>2012-07-31T22:52:23+00:00</endDate>
            <name>e209004</name>
            <startDate>2012-07-31T20:20:37+00:00</startDate>
            <investigation ref="inv_1"/>
            <type name="raw"/>
          </dataset>
        </data>
      </icatdata>

ICAT object references
......................

ICAT object references do not define an ICAT object to be created when
reading the ICAT data file but reference an already existing one.  It
is either assumed to exist in ICAT before ingesting the file or it
must appear earlier in the ICAT data file, so that it will be created
before the referencing object is read.

ICAT objects may either be referenced by reference key or by
attributes.  A reference key should be included as a ``ref``
attribute.

When referencing the object by attributes, these attributes should be
included using the same name in the reference element.  This may also
include attributes of related objects using the same dot notation as
for ICAT JPQL search expressions.  Referencing by attributes may be
combined with referencing related objects by reference key, using
``ref`` in place of the related object's attribute names.  In any
case, referenced objects must be uniquely defined by the attribute
values.

ICAT object references may be used in two locations in ICAT data XML
files: as direct subelements of ``data`` or to reference related
objects in many-to-one relations in ICAT object definitions, see
below.  In the former case, the name of the object reference element
is the name of the corresponding ICAT entity type (the first letter in
lowercase) with a ``Ref`` suffix appended.  In that case, the element
should have an ``id`` attribute that will define a local key that can
be used to reference that object in subsequent object references.
This is convenient to define a shortcut when the same object needs to
be referenced often, to avoid having to repeat the same set of
attributes each time.

In any case, object reference elements only have attributes, but no
content or subelements.

See :numref:`snip-file-icatdata-xml-1` for a few examples: the first
subelement of the ``data`` element in this case is
``investigationRef``.  It references a (supposed to be existing)
Investigation by its attributes ``name`` and ``visitId``.  It defines
a local key for that Investigation object in the ``id`` attribute.
The Dataset object definitions in that example each use that local key
to set their relation with the Investigation respectively.  The
Dataset object definitions each also include a relation with their
``type``, referencing the related DatasetType by the ``name``
attribute.  Some of the Dataset object definitions also include a
relation with a Sample.  The respective Sample object is referenced by
``name`` and the related Investigation.  The latter is referenced by
the local key defined earlier in the ``investigation.ref`` attribute.

ICAT object definitions
.......................

ICAT object definitions define objects that will be created in ICAT
when ingesting the ICAT data file.  As direct subelements of ``data``,
the name of the element must be the name of the corresponding entity
type in the ICAT schema (the first letter in lowercase).

The subelements of ICAT object definitions are the attributes and
object relations as defined in the ICAT schema using the same names.
Attributes must include the corresponding value as text content of the
element.  All many-to-one relations must be provided as ICAT object
references, see above.

The ICAT object definitions may include one-to-many relations as
subelements.  In this case, these subelements must in turn be ICAT
object definitions for the related objects.  These related objects
will be created along with the parent in one single cascading call.
The object definition for the related object must not include its
relation with the parent object as this is already implied by the
parent and child relationship.

When appearing as direct subelements of ``data``, ICAT object
definitions may have an ``id`` attribute that will define a local key
that can be used to reference the defined object later on.

.. literalinclude:: ../examples/icatdump-simple.xml
   :language: xml
   :name: snip-file-icatdata-xml-2
   :caption: An example for an ICAT data XML file

Consider the example in :numref:`snip-file-icatdata-xml-2`.  It
contains two chunks: the first chunk contains four User objects and
three Grouping objects.  The Groupings include related UserGroups.
Note that these UserGroups include their relation to the User, but not
their relation with Grouping.  The latter is implied by the parent
relation of the object in the file.  The second chunk only contains
one Investigation, including related InvestigationGroups.

Finally note that the file format also depends on the ICAT schema
version: the present example can only be ingested into ICAT server 5.0
or newer, because the attributes fileCount and fileSize have been
added to Investigation in this version.  With older ICAT versions, it
will fail because these attributes are not defined.

You will find more extensive examples in the source distribution of
python-icat.  The distribution also provides XML Schema Definition
files for the ICAT data XML file format corresponding to various ICAT
schema versions.  Note the these  XML Schema Definition
files are provided for reference only.  The :ref:`icatingest` script
does not validate its input.

.. _ICAT-data-yaml-files:

ICAT data YAML files
~~~~~~~~~~~~~~~~~~~~

In this section we describe the ICAT data file format using the YAML
backend.  Consider the example in :numref:`snip-file-icatdata-yaml`,
it corresponds to the same ICAT content as the XML in
:numref:`snip-file-icatdata-xml-2`:

.. literalinclude:: ../examples/icatdump-simple.yaml
   :language: yaml
   :name: snip-file-icatdata-yaml
   :caption: An example for an ICAT data YAML file

ICAT data YAML files start with a head consisting of a few comment
lines, followed by one or more YAML documents.  YAML documents are
separated by a line containing only ``---``.  The comments in the head
provide some information on the context of the creation of the data
file, which may be useful for debugging in case of issues.

Each YAML document defines one chunk of data according to the logical
structure explained above.  It consists of a mapping having the name
of entity types in the ICAT schema (the first letter in lowercase) as
keys.  The values are in turn mappings that map object ids as key to
ICAT object definitions as value.  These object ids define local keys
that may be used to reference the respective object later on.  In the
present example, the first chunk contains four User objects and three
Grouping objects.  The Groupings include related UserGroups.  The
second chunk only contains one Investigation, including related
investigationGroups.

Each of the ICAT object definitions corresponds to an object in the
ICAT schema.  It is again a mapping with the object's attribute and
relation names as keys and corresponding values.  All many-to-one
relations must be provided and reference existing objects, e.g. they
must either already have existed before starting the ingestion or
appear in the same or an earlier YAML document in the ICAT data file.
The values of many-to-one relations are reference keys, either local
keys defined in the same YAML document or unique keys.  Unlike the XML
backend, the YAML backend does not support referencing objects by
attributes.

The object definitions may include one-to-many relations.  In this
case, the value for the relation name is a list of object definitions
for the related objects.  These related objects will be created along
with the parent in one single cascading call.  In the present example,
the Grouping objects include their related UserGroup objects.  Note
that these UserGroups include their relation to the User, but not with
Grouping.  The latter relationship is implied by the parent relation
of the object in the file.

Note that the entries in the mappings in YAML have no inherent order.
The :ref:`icatingest` script uses a predefined order to read the ICAT
entity types in order to make sure that referenced objects are created
before any object that may reference them.


.. [#dc] There is one exception: DataCollections doesn't have a
         uniqueness constraint and can't reliably be searched by
         attributes.  Therefore local keys for DataCollections are
         always kept in the object index and may be used to reference
         them across chunk boundaries.
