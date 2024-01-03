.. _ICAT-data-files:

ICAT data files
===============

ICAT data files provide a way to serialize ICAT content to a flat
file.  These files are read by the :ref:`icatingest` and written by
the :ref:`icatdump` command line scripts respectively.  The program
logic for reading and writing the files is provided by the
:mod:`icat.dumpfile` module.

The actual file format depends on the version of the ICAT schema and
on the backend: python-icat provides backends using XML and YAML.

Logical structure of ICAT data files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is a one-to-one correspondence of the objects in the data
file and the corresponding object in ICAT according to the ICAT
schema, including all attributes and relations to other objects.
Special unique keys are used to encode the relations.
:meth:`icat.entity.Entity.getUniqueKey` may be used to get such a
unique key for an entity object and
:meth:`icat.client.Client.searchUniqueKey` may be used to search an
object by its key.  Otherwise these keys should be considered as
opaque ids.

Data files are partitioned in chunks.  This is done to avoid having
the whole file, e.g. the complete inventory of the ICAT, at once in
memory.  The problem is that objects contain references to other
objects (e.g. Datafiles refer to Datasets, the latter refer to
Investigations, and so forth).  We keep an index of the objects as
cache in order to resolve these references.  But there is a memory
versus time tradeoff: we cannot keep all the objects in the index,
that would again mean the complete inventory of the ICAT.  And we
can't know beforehand which object is going to be referenced later on,
so we don't know which one to keep and which one to discard from the
index.  Fortunately we can query objects that we discarded once back
from the ICAT server.  But this is expensive.  So the strategy is as
follows: keep all objects from the current chunk in the index and
discard the complete index each time a chunk has been
processed. [#dc]_ This will work fine if objects are mostly
referencing other objects from the same chunk and only a few
references go across chunk boundaries.

Therefore, we want these chunks to be small enough to fit into memory,
but at the same time large enough to keep as many relations between
objects as possible local in a chunk.  It is in the responsibility of
the writer of the data file to create the chunks in this manner.

The objects that get written to the data file and how this file is
organized is controlled by lists of ICAT search expressions or entity
objects, see :meth:`icat.dumpfile.DumpFileWriter.writeobjs`.  There is
some degree of flexibility: an object may include related objects in
an one-to-many relation.  In this case, these related objects should
not be added on their own again.  For instance, you may write User,
Grouping, and UserGroup as separate objects into the file.  In this
case, the UserGroup entries must properly reference related User and
Grouping.  Alternatively you may include the UserGroups in the
corresponding Grouping objects.  In this case, you must not add the
UserGroups again on their own.

Objects related in a many-to-one relation must always be included in
the search expression.  This is also true if the object is
indirectly related to one of the included objects.  In this case,
only a reference to the related object will be included in the data
file.  The related object must have its own entry.

ICAT data XML files
~~~~~~~~~~~~~~~~~~~

In this section we describe the ICAT data file format using the XML
backend.  Consider the following example:

.. literalinclude:: ../examples/icatdump-simple-1.xml
   :language: xml

The root element of ICAT data XML files is ``icatdata``.  It may
optionally have one ``head`` subelement and one or more ``data``
subelements.

The ``head`` element will be ignored by :ref:`icatingest`.  It serves
to provide some information on the context of the creation of the data
file, which may be useful for debugging in case of issues.

The content of each ``data`` element is one chunk according to the
logical structure explained above.  The present example contains two
chunks.  Each element within the ``data`` element corresponds to an
ICAT object according to the ICAT schema.  In the present example, the
first chunk contains five User objects and three Grouping objects.
The second chunk only contains one Investigation.

These object elements should have an ``id`` attribute that may be used
to reference the object in relations later on.  The ``id`` value has
no meaning other than this file internal referencing between objects.
The subelements of the object elements correspond to the object's
attributes and relations in the ICAT schema.  All many-to-one
relations must be provided and reference already existing objects,
e.g. they must either already have existed before starting the
ingestion or appear earlier in the ICAT data file than the referencing
object, so that they will be created earlier.  The related object may
either be referenced by id using the special attribute ``ref`` or by
the related object's attribute values, using XML attributes of the
same name.  In the latter case, the attribute values must uniquely
define the related object.

The object elements may include one-to-many relations.  In this case,
the related objects will be created along with the parent in one
single cascading call.  Alternatively, these related objects may be
added separately as subelements of the ``data`` element later in the
file.  In the present example, the Grouping object include their
related UserGroup objects.  Note that these UserGroups include their
relation to the User.  The User object is referenced by their
respective id in the ``ref`` attribute.  But the UserGroups do not
include their relation with Grouping.  That relationship is implied by
the parent relation of the object in the file.

In a similar way, the Investigation in the second chunk includes
related InvestigationGroups that will be created along with the
Investigation.  The InvestigationGroup objects include a reference to
the corresponding Grouping.  Note that these references go across
chunk boundaries.  The index that caches the object ids to resolve
object relations from the first chunk that did contain the ids of the
Groupings will already have been discarded from memeory when the
second chunk is read.  But the references use the key that can be
passed to :meth:`icat.client.Client.searchUniqueKey` to search these
Groupings from ICAT.

Finally note the the file format also depends on the ICAT schema
version: the present example can only be ingested into ICAT server 5.0
or newer, because the attributes fileCount and fileSize have been
added to Investigation in this version.  With older ICAT versions, it
will fail because the attributes are not defined.

Consider a second example, it defines a subset of the same content
as the previous example:

.. literalinclude:: ../examples/icatdump-simple-2.xml
   :language: xml
   :lines: 1-9,28-52,56-58,70-82,108

The difference is that we now add the Usergroup objects separately in
direct subelements of ``data`` instead of including them in the
related Grouping objects.

You will find more extensive examples in the source distribution of
python-icat.  The distribution also provides XML Schema Definition
files for the ICAT data XML file format corresponding to various ICAT
schema versions.

ICAT data YAML files
~~~~~~~~~~~~~~~~~~~~

In this section we describe the ICAT data file format using the YAML
backend.

.. literalinclude:: ../examples/icatdump-simple-1.yaml
   :language: yaml

.. literalinclude:: ../examples/icatdump-simple-2.yaml
   :language: yaml
   :lines: 1-7,10-11,14,23-45,52-60


.. [#dc] There is one exception: DataCollections don't have a
         uniqueness constraint and can't reliably be searched by
         attributes.  They are always kept in the index.
