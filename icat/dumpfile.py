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

    def getobjs(self, data, objindex):
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

    def head(self, service, apiversion):
        """Write a header with some meta information to the dump file."""
        raise NotImplementedError

    def startdata(self):
        """Start a new data chunk.

        If the current chunk contains any data, write it to the dump
        file.
        """
        raise NotImplementedError

    def add(self, key, obj, keyindex):
        """Add an entity object to the current data chunk."""
        raise NotImplementedError

    def finalize(self):
        """Finalize the dump file."""
        raise NotImplementedError
