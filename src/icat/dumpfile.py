"""Backend for icatdump and icatingest.

This module provides the base classes DumpFileReader and
DumpFileWriter that define the API and the logic for reading and
writing ICAT data files.  The actual work is done in file format
specific modules that should provide subclasses that must implement
the abstract methods.
"""

from collections import ChainMap
import os
import sys

from .entity import Entity
from .query import Query


def _get_retain_entities(client):
    """Get a list of object types to retain in the index.

    Some objects can't be queried based on their attributes.  They
    should thus not be discarded from the index.  A particular
    relevant example is DataCollection.  The list of object types to
    retain depends on the ICAT schema version and thus on the server
    we talk to.  That is why we compile that list at runtime.

    The criterion is: we need to retain all object types having any
    one-to-many relationship and not having a uniqueness constraint.
    """
    retain_set = set()
    for cls in client.typemap.values():
        if not cls.BeanName:
            continue
        if cls.InstMRel and 'id' in cls.Constraint:
            retain_set.add(cls.BeanName)
    return frozenset(retain_set)


# ------------------------------------------------------------
# DumpFileReader
# ------------------------------------------------------------

class DumpFileReader():
    """Base class for backends that read a data file.

    :param client: a client object configured to connect to the ICAT
        server that the objects in the data file belong to.  This
        client will be used among others to instantiate the objects
        read from the file and to search for related objects.
    :type client: :class:`icat.client.Client`
    :param infile: the data source to read the objects from.  It
        depends on the backend which kind of data source they accept.
        Most backends will at least accept a file object opened for
        reading or a :class:`~pathlib.Path` or a :class:`str` with a
        file name.

    .. versionchanged:: 1.0.0
        the `infile` parameter also accepts a :class:`~pathlib.Path`
        object.
    """

    mode = "r"
    """File mode suitable for the backend.

    Subclasses should override this with either "rt" or "rb",
    according to the mode required for the backend.
    """

    def __init__(self, client, infile):
        self.client = client
        self._closefile = False
        if hasattr(infile, 'open') or isinstance(infile, str):
            self.infile = self._file_open(infile)
            self._closefile = True
        else:
            self.infile = infile
        self._retain_entities = _get_retain_entities(client)
        self.objindex = {}

    def _file_open(self, infile):
        if hasattr(infile, 'open'):
            return infile.open(mode=self.mode)
        elif infile == "-":
            return sys.stdin
        else:
            return open(infile, self.mode)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self._closefile:
            self.infile.close()

    def getdata(self):
        """Iterate over the chunks in the data file.

        Yield some data object in each iteration.  This data object is
        specific to the implementing backend and should be passed as
        the `data` argument to
        :meth:`~icat.dumpfile.DumpFileReader.getobjs_from_data`.

        This abstract method must be implemented in the file format
        specific backend.
        """
        raise NotImplementedError

    def getobjs_from_data(self, data, objindex):
        """Iterate over the objects in a data chunk.

        Yield a new entity object in each iteration.  The object is
        initialized from the data, but not yet created at the client.

        This abstract method must be implemented in the file format
        specific backend.
        """
        raise NotImplementedError

    def getobjs(self, objindex=None):
        """Iterate over the objects in the data file.

        Yield a new entity object in each iteration.  The object is
        initialized from the data, but not yet created at the client.

        :param objindex: a mapping from keys to entity objects, see
            :meth:`icat.client.Client.searchUniqueKey` for details.
            This serves as a cache of previously retrieved objects,
            used to resolve object relations.  If this is
            :const:`None`, an internal cache will be used that is
            purged at the start of every new data chunk.
        :type objindex: :class:`dict`
        """
        resetindex = (objindex is None)
        for data in self.getdata():
            self.client.autoRefresh()
            if resetindex:
                objindex = ChainMap(dict(), self.objindex)
            for key, obj in self.getobjs_from_data(data, objindex):
                yield obj
                obj.truncateRelations(keepInstRel=True)
                if key:
                    if obj.BeanName in self._retain_entities:
                        self.objindex[key] = obj
                    else:
                        objindex[key] = obj


# ------------------------------------------------------------
# DumpFileWriter
# ------------------------------------------------------------

class DumpFileWriter():
    """Base class for backends that write a data file.

    :param client: a client object configured to connect to the ICAT
        server to search the data objects from.
    :type client: :class:`icat.client.Client`
    :param outfile: the data file to write the objects to.  It depends
        on the backend what they accept here.  Most backends will at
        least accept a file object opened for writing or a
        :class:`~pathlib.Path` or a :class:`str` with a file name.

    .. versionchanged:: 1.0.0
        the `outfile` parameter also accepts a :class:`~pathlib.Path`
        object.
    """

    mode = "w"
    """File mode suitable for the backend.

    Subclasses should override this with either "wt" or "wb",
    according to the mode required for the backend.
    """

    def __init__(self, client, outfile):
        self.client = client
        self._closefile = False
        if hasattr(outfile, 'open') or isinstance(outfile, str):
            self.outfile = self._file_open(outfile)
            self._closefile = True
        else:
            self.outfile = outfile
        self.idcounter = {}
        self._retain_entities = _get_retain_entities(client)
        self.keyindex = {}

    def _file_open(self, outfile):
        if hasattr(outfile, 'open'):
            return outfile.open(mode=self.mode)
        elif outfile == "-":
            return sys.stdout
        else:
            return open(outfile, self.mode)

    def __enter__(self):
        self.head()
        return self

    def __exit__(self, type, value, traceback):
        if type is None:
            self.finalize()
        if self._closefile:
            self.outfile.close()

    def head(self):
        """Write a header with some meta information to the data file.

        This abstract method must be implemented in the file format
        specific backend.
        """
        raise NotImplementedError

    def startdata(self):
        """Start a new data chunk.

        If the current chunk contains any data, write it to the data
        file.

        This abstract method must be implemented in the file format
        specific backend.
        """
        raise NotImplementedError

    def writeobj(self, key, obj, keyindex):
        """Add an entity object to the current data chunk.

        This abstract method must be implemented in the file format
        specific backend.
        """
        raise NotImplementedError

    def finalize(self):
        """Finalize the data file.

        This abstract method must be implemented in the file format
        specific backend.
        """
        raise NotImplementedError

    def writeobjs(self, objs, keyindex, chunksize=100):
        """Write some entity objects to the current data chunk.

        The objects are searched from the ICAT server.  The key index
        is used to serialize object relations in the data file.  For
        object types that do not have an appropriate uniqueness
        constraint in the ICAT schema, a generic key is generated.
        These objects may only be referenced from the same chunk in
        the data file.

        :param objs: query to search the objects, either a Query
            object or a string.  It must contain an appropriate
            include clause to include all related objects from
            many-to-one relations.  These related objects must also
            include all informations needed to generate their unique
            key, unless they are registered in the key index already.

            Furthermore, related objects from one-to-many relations
            may be included.  These objects will then be embedded with
            the relating object in the data file.  The same
            requirements for including their respective related
            objects apply.

            As an alternative to a query, objs may also be a list of
            entity objects.  The same conditions on the inclusion of
            related objects apply.
        :type objs: :class:`icat.query.Query` or :class:`str` or
            :class:`list`
        :param keyindex: cache of generated keys.  It maps object ids
            to unique keys.  See the
            :meth:`icat.entity.Entity.getUniqueKey` for details.
        :type keyindex: :class:`dict`
        :param chunksize: tuning parameter, see
            :meth:`icat.client.Client.searchChunked` for details.
        :type chunksize: :class:`int`
        """
        if isinstance(objs, Query) or isinstance(objs, str):
            objs = self.client.searchChunked(objs, chunksize=chunksize)
        for obj in sorted(objs, key=Entity.__sortkey__):
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
                if obj.BeanName in self._retain_entities:
                    self.keyindex[(obj.BeanName, obj.id)] = k
                else:
                    keyindex[(obj.BeanName, obj.id)] = k
            else:
                k = obj.getUniqueKey(keyindex=keyindex)
            self.writeobj(k, obj, keyindex)

    def writedata(self, objs, keyindex=None, chunksize=100):
        """Write a data chunk.

        :param objs: an iterable that yields either queries to search
            for the objects or object lists.  See
            :meth:`icat.dumpfile.DumpFileWriter.writeobjs` for
            details.
        :param keyindex: cache of generated keys, see
            :meth:`icat.dumpfile.DumpFileWriter.writeobjs` for
            details.  If this is :const:`None`, an internal index will
            be used.
        :type keyindex: :class:`dict`
        :param chunksize: tuning parameter, see
            :meth:`icat.client.Client.searchChunked` for details.
        :type chunksize: :class:`int`
        """
        self.client.autoRefresh()
        if keyindex is None:
            keyindex = ChainMap(dict(), self.keyindex)
        self.startdata()
        for o in objs:
            self.writeobjs(o, keyindex, chunksize=chunksize)


# ------------------------------------------------------------
# Register of backends and open_dumpfile()
# ------------------------------------------------------------

Backends = {}
"""A register of all known backends."""

def register_backend(formatname, reader, writer):
    """Register a backend.

    This function should be called by file format specific backends at
    initialization.

    :param formatname: name of the file format that the backend
        implements.
    :type formatname: :class:`str`
    :param reader: class for reading data files.  Should be a subclass
        of :class:`icat.dumpfile.DumpFileReader`.
    :param writer: class for writing data files.  Should be a subclass
        of :class:`icat.dumpfile.DumpFileWriter`.
    """
    Backends[formatname] = (reader, writer)

def open_dumpfile(client, f, formatname, mode):
    """Open a data file, either for reading or for writing.

    Note that depending on the backend, the file must either be opened
    in binary or in text mode.  If f is a file object, it must have
    been opened in the appropriate mode according to the backend
    selected by formatname.  The backend classes define a
    corresponding class attribute `mode`.  If f is a file name, the
    file will be opened in the appropriate mode.

    The subclasses of :class:`icat.dumpfile.DumpFileReader` and
    :class:`icat.dumpfile.DumpFileWriter` may be used as context
    managers.  This function is suitable to be used in the :obj:`with`
    statement.

    >>> with open_dumpfile(client, f, "XML", 'r') as dumpfile:
    ...     for obj in dumpfile.getobjs():
    ...         obj.create()

    :param client: the ICAT client.
    :type client: :class:`icat.client.Client`
    :param f: the object to read the data from or write the data to,
        according to mode.  What object types are supported depends on
        the backend.  All backends support at least a file object or
        the name of file.  The special value of "-" may be used as an
        alias for :data:`sys.stdin` or :data:`sys.stdout`.
    :param formatname: name of the file format that has been registered by
        the backend.
    :type formatname: :class:`str`
    :param mode: either "r" or "w" to indicate that the file should be
        opened for reading or writing respectively.
    :type mode: :class:`str`
    :return: an instance of the appropriate class.  This is either the
        reader or the writer class, according to the mode, that has
        been registered by the backend.
    :raise ValueError: if the format is not known or if the mode is
        not "r" or "w".
    """
    if formatname not in Backends:
        raise ValueError("Unknown data file format '%s'" % formatname)
    if mode == 'r':
        cls = Backends[formatname][0]
        return cls(client, f)
    elif mode == 'w':
        cls = Backends[formatname][1]
        return cls(client, f)
    else:
        raise ValueError("Invalid file mode '%s'" % mode)

