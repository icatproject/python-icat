:mod:`icat.dumpfile` --- Backend for icatdump and icatingest
============================================================

.. py:module:: icat.dumpfile

This module provides the base classes
:class:`icat.dumpfile.DumpFileReader` and
:class:`icat.dumpfile.DumpFileWriter` that define the API and the
logic for reading and writing ICAT data files.  The actual work is
done in file format specific modules that should provide subclasses
that must implement the abstract methods.

.. autoclass:: icat.dumpfile.DumpFileReader
    :members:
    :show-inheritance:

.. autoclass:: icat.dumpfile.DumpFileWriter
    :members:
    :show-inheritance:

.. autodata:: icat.dumpfile.Backends

.. autofunction:: icat.dumpfile.register_backend

.. autofunction:: icat.dumpfile.open_dumpfile


.. _ICAT-data-files:

ICAT data files
---------------

Data files are partitioned in chunks.  This is done to avoid having
the whole file, e.g. the complete inventory of the ICAT, at once in
memory.  The problem is that objects contain references to other
objects (e.g. Datafiles refer to Datasets, the latter refer to
Investigations, and so forth).  We keep an index of the objects in
order to resolve these references.  But there is a memory versus time
tradeoff: we cannot keep all the objects in the index, that would
again mean the complete inventory of the ICAT.  And we can't know
beforehand which object is going to be referenced later on, so we
don't know which one to keep and which one to discard from the index.
Fortunately we can query objects we discarded once back from the ICAT
server with :meth:`icat.client.Client.searchUniqueKey`.  But this is
expensive.  So the strategy is as follows: keep all objects from the
current chunk in the index and discard the complete index each time a
chunk has been processed.  This will work fine if objects are mostly
referencing other objects from the same chunk and only a few
references go across chunk boundaries.

Therefore, we want these chunks to be small enough to fit into memory,
but at the same time large enough to keep as many relations between
objects as possible local in a chunk.  It is in the responsibility of
the writer of the data file to create the chunks in this manner.

The objects that get written to the data file and how this file is
organized is controlled by lists of ICAT search expressions, see
:meth:`icat.dumpfile.DumpFileWriter.writeobjs`.  There is some degree
of flexibility: an object may include related objects in an
one-to-many relation, just by including them in the search expression.
In this case, these related objects should not have a search
expression on their own again.  For instance, the search expression
for Grouping may include UserGroup.  The UserGroups will then be
embedded in their respective grouping in the data file.  There should
not be a search expression for UserGroup then.

Objects related in a many-to-one relation must always be included in
the search expression.  This is also true if the object is
indirectly related to one of the included objects.  In this case,
only a reference to the related object will be included in the data
file.  The related object must have its own list entry.
