#! /usr/bin/python
#
# Delete all content from an ICAT.
#

import icat
import icat.config
import logging

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

conf = icat.config.Config().getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)

# Entity types needed for access permissions.  Must be deleted last,
# otherwise we would take delete permission from ourselves.
if client.apiversion < '4.3':
    authztables = [ "Group", "Rule", "User", "UserGroup", ]
else:
    authztables = [ "Grouping", "Rule", "User", "UserGroup", ]


# First step, delete the Facility.  By cascading, this already wipes
# almost everything.
client.deleteMany(client.search("Facility"))

# Second step, delete almost all remaining bits, keep only
# authztables.  This will hit stuff not directly linked to Facility,
# such as Study, Log, and PublicStep, but also Application and
# Datafile in ICAT 4.2.
for t in client.getEntityNames():
    if t not in authztables:
        client.deleteMany(client.search(t))

# Third step, delete the authztables.
for t in authztables:
    client.deleteMany(client.search(t))
