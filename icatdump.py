#! /usr/bin/python
#
# Dump the content of the ICAT to a file or to stdout.

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

if client.apiversion < '4.3.0':
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
