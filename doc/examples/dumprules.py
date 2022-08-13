#! /usr/bin/python
#
# Dump the rules including the related groups and the public steps
# from the ICAT to a file or to stdout.
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

logging.basicConfig(level=logging.INFO)

formats = icat.dumpfile.Backends.keys()
if len(formats) == 0:
    raise RuntimeError("No datafile backends available.")

config = icat.config.Config()
config.add_variable('file', ("-o", "--outputfile"),
                    dict(help="output file name or '-' for stdout"),
                    default='-')
config.add_variable('format', ("-f", "--format"),
                    dict(help="output file format", choices=formats),
                    default='YAML')
client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)

groups = set()
query = Query(client, "Rule",
              conditions={"grouping": "IS NOT NULL"},
              includes={"grouping.userGroups.user"})
for r in client.search(query):
    groups.add(r.grouping)

items = [
    sorted(groups, key=icat.entity.Entity.__sortkey__),
    Query(client, "PublicStep"),
    Query(client, "Rule", order=["what", "id"],
          conditions={"grouping": "IS NULL"}),
    Query(client, "Rule", order=["grouping.name", "what", "id"],
          conditions={"grouping": "IS NOT NULL"},
          includes={"grouping"}),
]

with open_dumpfile(client, conf.file, conf.format, 'w') as dumpfile:
    dumpfile.writedata(items)
