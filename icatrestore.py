#! /usr/bin/python
#
# Restore the content of the ICAT from a dump file as created by
# icatdump.py.
#
# Known issues and limitations:
#  + The user running this script need to have create permission for
#    all objects in the dump file.  Appropriate rules must either
#    already been set up at the ICAT server or must be contained in
#    the dump file.  In the latter case, the rules and corresponding
#    user and group objects must be in the first chunk (see below) of
#    the file.  In the generic case of restoring the entire content on
#    an empty ICAT server, the script must be run by the ICAT root
#    user.
#  + It is assumed that the data in the dump file may be created right
#    away in the ICAT server.  There is no collision check with data
#    already present at the server.
#  + IDS is not supported: the script only restores the meta data
#    stored in the ICAT, not the content of the files stored in the
#    IDS.
#  + This script requires ICAT 4.3.0 or newer.
#  + A dump and restore of an ICAT will not preserve the attributes
#    id, createId, createTime, modId, and modTime of any objects.
#    This is by design and cannot be fixed.  As a consequence, access
#    rules that are based on object ids will not work after a restore.
#  + Restoring of several entity types has not yet been
#    tested.  See icatdump.py for a list.

import logging
import icat
import icat.config
from icat.dumpfile import open_dumpfile
import icat.dumpfile_xml
import icat.dumpfile_yaml

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)
log = logging.getLogger(__name__)

formats = icat.dumpfile.Backends.keys()
config = icat.config.Config()
config.add_variable('file', ("-i", "--inputfile"), 
                    dict(help="input file name or '-' for stdin"),
                    default='-')
config.add_variable('format', ("-f", "--format"), 
                    dict(help="input file format", choices=formats),
                    default='YAML')
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
if client.apiversion < '4.3':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.3.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


# We read the data in chunks (separate YAML documents in the case of a
# YAML dump file, content of separate data elements in the case of
# XML).  This way we can avoid having the whole file, e.g. the
# complete inventory of the ICAT, at once in memory.  The problem is
# that objects contain references to other objects (e.g. Datafiles
# refer to Datasets, the latter refer to Investigations, and so
# forth).  We keep an index of the objects in order to resolve these
# references.  But there is a memory versus time tradeoff: we cannot
# keep all the objects in the index, that would again mean the
# complete inventory of the ICAT.  And we can't know beforehand which
# object is going to be referenced later on, so we don't know which
# one to keep and which one to discard from the index.  Fortunately we
# can query objects we discarded once back from the ICAT server with
# client.searchUniqueKey().  But this is expensive.  So the strategy
# is as follows: keep all objects from the current chunk in the index
# and discard the complete index each time a chunk has been processed.
# This will work fine if objects are mostly referencing other objects
# from the same chunk and only a few references go across chunk
# boundaries.  It is in the responsibility of the creator of the dump
# file to create the chunks in this manner.

with open_dumpfile(client, conf.file, conf.format, 'r') as dumpfile:
    for obj in dumpfile.getobjs():
        obj.create()
