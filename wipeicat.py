#! /usr/bin/python
#
# Delete all content from an ICAT.
#

import icat
import icat.config
import logging

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

config = icat.config.Config(needids=True)
config.add_variable('keepids', ("--keepids",), 
                    dict(help="do not delete data from IDS, only wipe ICAT", 
                         action='store_true'))
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)


# Entity types needed for access permissions.  Must be deleted last,
# otherwise we would take delete permission from ourselves.
if client.apiversion < '4.3':
    authztables = [ "Group", "Rule", "User", "UserGroup", ]
else:
    authztables = [ "Grouping", "Rule", "User", "UserGroup", ]


# First step, delete all Datafiles.  Do it with the IDS, not directly
# in the ICAT, because otherwise it would leave orphan files in the
# IDS.
if not conf.keepids:
    datafileIds = client.search("Datafile.id")
    if datafileIds:
        client.deleteData(dict(datafileIds=datafileIds))

# Second step, delete the Facility.  By cascading, this already wipes
# almost everything.
client.deleteMany(client.search("Facility"))

# Third step, delete almost all remaining bits, keep only
# authztables.  This will hit stuff not directly linked to Facility,
# such as Study, Log, and PublicStep, but also Application and
# Datafile in ICAT 4.2.
for t in client.getEntityNames():
    if t not in authztables:
        client.deleteMany(client.search(t))

# Last step, delete the authztables.
for t in authztables:
    client.deleteMany(client.search(t))
