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


.. [#dc] There is one exception: DataCollections don't have a
         uniqueness constraint and can't reliably be searched by
         attributes.  They are always kept in the index.
