#! /usr/bin/python
#
# Dump the content of the ICAT to a file or to stdout.
#
# The following items are deliberately not included in the output:
#  + Log objects,
#  + the attributes id, createId, createTime, modId, and modTime.
#
# Known issues and limitations:
#  + This script requires ICAT 4.3.0 or newer.
#  + IDS is not supported: the script only dumps the meta data stored
#    in the ICAT, not the content of the files stored in the IDS.
#  + It is assumed that for each Dataset ds in the ICAT where
#    ds.sample is not NULL, the condition
#    ds.investigation == ds.sample.investigation holds.  If this
#    is not met, this script will fail with a DataConsistencyError.
#  + The partition of the data into chunks ist static.  It should
#    rather be dynamic, e.g. chunks should be splitted if the number
#    of objects in them grows too large.
#  + The data in the ICAT server must not be modified while this
#    script is retrieving it.  Otherwise the script may fail or the
#    dumpfile be inconsistent.  There is not too much that can be done
#    about this.  A database dump is a snapshot after all.  The
#    picture will be blurred if the subject is moving while we take
#    it.
#  + icatdump fails for Study if ICAT is older then 4.6.0.  This is a
#    bug in icat.server, see Issue icatproject/icat.server#155.
#

import logging
import icat
import icat.config
from icat.query import Query
from icat.dumpfile import open_dumpfile
try:
    import icat.dumpfile_xml
except ImportError:
    pass
try:
    import icat.dumpfile_yaml
except ImportError:
    pass
from icat.dump_queries import *


logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

formats = icat.dumpfile.Backends.keys()
if len(formats) == 0:
    raise RuntimeError("No datafile backends available.")

config = icat.config.Config(ids=False)
config.add_variable('file', ("-o", "--outputfile"), 
                    dict(help="output file name or '-' for stdout"),
                    default='-')
config.add_variable('format', ("-f", "--format"), 
                    dict(help="output file format", choices=formats),
                    default='YAML')
client, conf = config.getconfig()

if client.apiversion < '4.3':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.3.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


with open_dumpfile(client, conf.file, conf.format, 'w') as dumpfile:
    dumpfile.writedata(getAuthQueries(client))
    dumpfile.writedata(getStaticQueries(client))
    # Dump the investigations each in their own chunk
    investsearch = Query(client, "Investigation", attribute="id", 
                         order=["facility.name", "name", "visitId"])
    for i in client.searchChunked(investsearch):
        # We fetch Dataset including DatasetParameter.  This may lead
        # to a large total number of objects even for a small number
        # of Datasets fetched at once.  Set a very small chunksize to
        # avoid hitting the limit.
        dumpfile.writedata(getInvestigationQueries(client, i), chunksize=5)
    dumpfile.writedata(getOtherQueries(client))
