"""Backend for icatdump and icatingest.

This module provides the base classes DumpFileReader and
DumpFileWriter that define the API and the logic for reading and
writing ICAT dump files.  The actual work is done in file format
specific modules that should provide subclasses that must implement
the abstract methods.

Dump files are partitioned in chunks.  This is done to avoid having
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
server with the ``searchUniqueKey()`` method of `Client`.  But this is
expensive.  So the strategy is as follows: keep all objects from the
current chunk in the index and discard the complete index each time a
chunk has been processed.  This will work fine if objects are mostly
referencing other objects from the same chunk and only a few
references go across chunk boundaries.

Therefore, we want these chunks to be small enough to fit into memory,
but at the same time large enough to keep as many relations between
objects as possible local in a chunk.  It is in the responsibility of
the writer of the dump file to create the chunks in this manner.

The objects that get written to the dump file and how this file is
organized is controlled by lists of ICAT search expressions, see the
``writeobjs()`` method of `DumpFileWriter`.  There is some degree of
flexibility: an object may include related objects in an one-to-many
relation, just by including them in the search expression.  In this
case, these related objects should not have a search expression on
their own again.  For instance, the search expression for Grouping may
include UserGroup.  The UserGroups will then be embedded in their
respective grouping in the dump file.  There should not be a search
expression for UserGroup then.

Objects related in a many-to-one relation must always be included in
the search expression.  This is also true if the object is
indirectly related to one of the included objects.  In this case,
only a reference to the related object will be included in the dump
file.  The related object must have its own list entry.
"""

import sys
import icat
from icat.query import Query


# ------------------------------------------------------------
# DumpFileReader
# ------------------------------------------------------------

class DumpFileReader(object):
    """Base class for backends that read a dump file."""

    def __init__(self, client, infile):
        self.client = client
        self.infile = infile

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.infile.close()

    def getdata(self):
        """Iterate over the data chunks in the dump file.

        Yield some data object in each iteration.  This data object is
        specific to the implementing backend and should be passed as
        the data argument to `getobjs_from_data`.
        """
        raise NotImplementedError

    def getobjs_from_data(self, data, objindex):
        """Iterate over the objects in a data chunk.

        Yield a new entity object in each iteration.  The object is
        initialized from the data, but not yet created at the client.
        """
        raise NotImplementedError

    def getobjs(self):
        """Iterate over the objects in the dump file.

        Yield a new entity object in each iteration.  The object is
        initialized from the data, but not yet created at the client.
        """
        for data in self.getdata():
            objindex = {}
            for key, obj in self.getobjs_from_data(data, objindex):
                yield obj
                obj.truncateRelations()
                if key:
                    objindex[key] = obj


# ------------------------------------------------------------
# DumpFileWriter
# ------------------------------------------------------------

class DumpFileWriter(object):
    """Base class for backends that write a dump file."""

    def __init__(self, client, outfile):
        self.client = client
        self.outfile = outfile
        self.idcounter = {}

    def __enter__(self):
        self.head()
        return self

    def __exit__(self, type, value, traceback):
        if type is None:
            self.finalize()
        self.outfile.close()

    def head(self):
        """Write a header with some meta information to the dump file."""
        raise NotImplementedError

    def startdata(self):
        """Start a new data chunk.

        If the current chunk contains any data, write it to the dump
        file.
        """
        raise NotImplementedError

    def writeobj(self, key, obj, keyindex):
        """Add an entity object to the current data chunk."""
        raise NotImplementedError

    def finalize(self):
        """Finalize the dump file."""
        raise NotImplementedError

    def writeobjs(self, objs, keyindex):
        """Write some entity objects to the current data chunk.

        The objects are searched from the ICAT server.  The key index
        is used to serialize object relations in the dump file.  For
        object types that do not have an appropriate uniqueness
        constraint in the ICAT schema, a generic key is generated.
        These objects may only be referenced from the same data chunk
        in the dump file.

        :param objs: query to search the objects, either a Query
            object or a string.  It must contain appropriate INCLUDE
            statements to include all related objects from many-to-one
            relations.  These related objects must also include all
            informations needed to generate their unique key, unless
            they are registered in the key index already.

            Furthermore, related objects from one-to-many relations
            may be included.  These objects will then be embedded with
            the relating object in the dump file.  The same
            requirements for including their respective related
            objects apply.

            As an alternative to a query, objs may also be a list of
            entity objects.  The same conditions on the inclusion of
            related objects apply.
        :type objs: `Query` or ``str`` or ``list``
        :param keyindex: cache of generated keys.  It maps object ids
            to unique keys.  See the ``getUniqueKey()`` method of
            `Entity` for details.
        :type keyindex: ``dict``
        """
        if isinstance(objs, Query) or isinstance(objs, basestring):
            objs = self.client.searchChunked(objs)
        else:
            objs.sort(key=icat.entity.Entity.__sortkey__)
        for obj in objs:
            # Entities without a constraint will use their id to form
            # the unique key as a last resort.  But we want the keys
            # not to depend on volatile attributes such as the id.
            # Use a generic numbered key for the concerned entity
            # types instead.
            if 'id' in obj.Constraint:
                t = obj.BeanName
                if t not in self.idcounter:
                    self.idcounter[t] = 0
                self.idcounter[t] += 1
                k = "%s_%08d" % (t, self.idcounter[t])
                keyindex[obj.id] = k
            else:
                k = obj.getUniqueKey(autoget=False, keyindex=keyindex)
            self.writeobj(k, obj, keyindex)

    def writedata(self, objs):
        """Write a data chunk.

        :param objs: an iterable that yields either queries to search
            for the objects or object lists.  See `writeobjs` for
            details.
        """
        keyindex = {}
        self.startdata()
        for o in objs:
            self.writeobjs(o, keyindex)


# ------------------------------------------------------------
# Register of backends and open_dumpfile()
# ------------------------------------------------------------

Backends = {}
"""A register of all known backends."""

def register_backend(format, reader, writer):
    """Register a backend.

    :param format: name of the file format that the backend
        implements.
    :type format: ``str``
    :param reader: class for reading dump files.  Should be a subclass
        of `DumpFileReader`.
    :param writer: class for writing dump files.  Should be a subclass
        of `DumpFileWriter`.
    """
    Backends[format] = (reader, writer)

def open_dumpfile(client, f, format, mode):
    """Open a dumpfile, either for reading or for writing.

    Note that (subclasses of) `DumpFileReader` and `DumpFileWriter`
    may be used as context managers.  This function is suitable to be
    used in the ``with`` statement.

    :param client: the ICAT client.
    :type client: `Client`
    :param f: a file object or the name of file.  In the former case,
        the file must be opened in the appropriate mode, in the latter
        case a file by that name is opened using mode.  The special
        value of "-" may be used as an alias for ``sys.stdin`` or
        ``sys.stdout``.
    :param format: name of the file format that has been registered by
        the backend.
    :type format: ``str``
    :param mode: a string indicating how the file is to be opened.
        The first character must be either "r" or "w" for reading or
        writing respectively.
    :type mode: ``str``
    :return: an instance of the appropriate class.  This is either the
        reader or the writer class, according to the mode, that has
        been registered by the backend.
    :raise ValueError: if the format is not known or if the mode does
        not start with "r" or "w".
    """
    if format not in Backends:
        raise ValueError("Unknown dump file format '%s'" % format)
    if mode[0] == 'r':
        if isinstance(f, basestring):
            if f == "-":
                f = sys.stdin
            else:
                f = open(f, mode)
        cls = Backends[format][0]
        return cls(client, f)
    elif mode[0] == 'w':
        if isinstance(f, basestring):
            if f == "-":
                f = sys.stdout
            else:
                f = open(f, mode)
        cls = Backends[format][1]
        return cls(client, f)
    else:
        raise ValueError("Invalid file mode '%s'" % mode)

