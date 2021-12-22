#! /usr/bin/python
#
# Dump the content of the ICAT to a file or to stdout.

import logging
from pathlib import Path
import icat
import icat.config
from icat.dump_queries import *
from icat.dumpfile import open_dumpfile
try:
    import icat.dumpfile_xml
except ImportError:
    pass
try:
    import icat.dumpfile_yaml
except ImportError:
    pass
from icat.query import Query


logging.basicConfig(level=logging.INFO)

formats = icat.dumpfile.Backends.keys()
if len(formats) == 0:
    raise RuntimeError("No datafile backends available.")

def getPath(f):
    if f == '-':
        return f
    else:
        return Path(f).expanduser()

config = icat.config.Config(ids=False)
config.add_variable('file', ("-o", "--outputfile"), 
                    dict(help="output file name or '-' for stdout"),
                    type=getPath, default='-')
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
    dumpfile.writedata(getFundingQueries(client))
    # Dump the investigations each in their own chunk
    investsearch = Query(client, "Investigation", attributes="id",
                         order=["facility.name", "name", "visitId"])
    for i in client.searchChunked(investsearch):
        # We fetch Dataset including DatasetParameter.  This may lead
        # to a large total number of objects even for a small number
        # of Datasets fetched at once.  Set a very small chunksize to
        # avoid hitting the limit.
        dumpfile.writedata(getInvestigationQueries(client, i), chunksize=5)
    dumpfile.writedata(getDataCollectionQueries(client))
    if 'dataPublication' in client.typemap:
        pubsearch = Query(client, "DataPublication", attributes="id",
                          order=["facility.name", "pid"])
        for i in client.searchChunked(pubsearch):
            dumpfile.writedata(getDataPublicationQueries(client, i))
    dumpfile.writedata(getOtherQueries(client))
