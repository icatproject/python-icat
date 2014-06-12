#! /usr/bin/python
#
# Restore the content of the ICAT from a YAML file as created by
# icatdump.py.
#
# The script reads the YAML input from stdin.  It should by run by the
# ICAT root user against an otherwise empty ICAT server.  There is no
# collision check with data already present at the ICAT.
#
# Known issues and limitations:
#  + It is assumed that the dump file contains appropriate rules that
#    gives the ICAT root user CRUD permission on all entity types.
#    These rules and corresponding user and group objects must be in
#    the first chunk (see below) of the file.
#  + This script requires ICAT 4.3.0 or newer.
#  + A dump and restore of an ICAT will not preserve the attributes
#    id, createId, createTime, modId, and modTime of any objects.
#    This is by design and cannot be fixed.  As a consequence, access
#    rules that are based on object ids will not work after a restore.
#    The Log will also not be restored.
#  + Restoring of several entity types has not yet been
#    tested.  See icatdump.py for a list.
#

import icat
import icat.config
import sys
import logging
from icat.dumpfile_yaml import YAMLDumpFileReader as DumpFileReader

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)
log = logging.getLogger(__name__)

config = icat.config.Config()
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
if client.apiversion < '4.3':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.3.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


# We read the data in chunks (or documents in YAML terminology).  This
# way we can avoid having the whole file, e.g. the complete inventory
# of the ICAT, at once in memory.  The problem is that some objects
# contain references to other objects (e.g. Datafiles refer to
# Datasets, the latter refer to Investigations, and so forth).  We
# need to resolve these references before we can create the objects.
# To this end, we keep an index of the objects.  But there is a memory
# versus time tradeoff: we cannot keep all the objects in the index,
# that would again mean the complete inventory of the ICAT.  And we
# can't know beforehand which object is going to be referenced later
# on, so we don't know which to keep and which to discard from the
# index.  Fortunately we can query objects we discarded back from the
# ICAT server with client.searchUniqueKey().  But this is expensive.
# So the strategy is as follows: keep all objects from the current
# chunk in the index and discard the complete index each time a chunk
# has been processed.  This will work fine if objects are mostly
# referencing other objects from the same chunk.  It is in the
# responsibility of the creator of the dumpfile to create the chunks
# in this manner.

dumpfile = DumpFileReader(client, sys.stdin)
for data in dumpfile.getdata():
    objindex = {}
    for key, obj in dumpfile.getobjs(data, objindex):
        obj.create()
        obj.truncateRelations()
        objindex[key] = obj

