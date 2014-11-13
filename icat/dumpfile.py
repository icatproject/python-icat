"""Define the interface that dump file backends for icatdump.py and
icatrestore.py must implement.
"""

import icat

__all__ = ['DumpFileReader', 'DumpFileWriter']


# ------------------------------------------------------------
# DumpFileReader
# ------------------------------------------------------------

class DumpFileReader(object):
    """Base class for backends that read a dump file."""

    def __init__(self, client):
        self.client = client

    def getdata(self):
        """Iterate over the data chunks in the dump file.
        """
        raise NotImplementedError

    def getobjs_from_data(self, data, objindex):
        """Iterate over the objects in a data chunk.

        Yield a new entity object in each iteration.  The object is
        initialized from the data, but not yet created at the client.
        """
        raise NotImplementedError


# ------------------------------------------------------------
# DumpFileWriter
# ------------------------------------------------------------

class DumpFileWriter(object):
    """Base class for backends that write a dump file."""

    def __init__(self, client):
        self.client = client

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

    def writeobjs(self, searchexp, keyindex):
        """Write some entity objects to the current data chunk.

        The objects are searched from the ICAT server.  The key index
        is used to serialize object relations in the dump file.  For
        object types that do not have an appropriate uniqueness
        constraint in the ICAT schema, a generic key is generated.
        These objects may only be referenced from the same data chunk
        in the dump file.

        :param searchexp: expression to use for searching the objects.
            It must contain appropriate INCLUDE statements to include
            all related objects from many to one relations.  These
            related objects must also include all informations needed
            to generate their unique key, unless they are registered
            in the key index already.

            Furthermore, related objects from one to many relations
            may be included.  These objects will then be embedded with
            the relating object in the dump file.  The same
            requirements for including their respective related
            objects apply.
        :type searchexp: ``str``
        :param keyindex: cache of generated keys.  It maps object ids
            to unique keys.  See the getUniqueKey() method of `Entity`
            for details.
        :type keyindex: ``dict``
        """
        i = 0
        objs = self.client.search(searchexp)
        objs.sort(key=icat.entity.Entity.__sortkey__)
        for obj in objs:
            # Entities without a constraint will use their id to form
            # the unique key as a last resort.  But we want the keys
            # not to depend on volatile attributes such as the id.
            # Use a generic numbered key for the concerned entity
            # types instead.
            if 'id' in obj.Constraint:
                i += 1
                k = "%s_%08d" % (obj.BeanName, i)
                keyindex[obj.id] = k
            else:
                k = obj.getUniqueKey(autoget=False, keyindex=keyindex)
            self.writeobj(k, obj, keyindex)

    def writedata(self, searchexps):
        """Write a data chunk.

        :param searchexps: a list of expressions to search for the
            objects to write.  See `writeobjs` for details.
        :type searchexps: ``list`` of ``str``
        """
        keyindex = {}
        self.startdata()
        for searchexp in searchexps:
            self.writeobjs(searchexp, keyindex)
