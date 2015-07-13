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


with open_dumpfile(client, conf.file, conf.format, 'r') as dumpfile:
    for obj in dumpfile.getobjs():
        obj.create()
