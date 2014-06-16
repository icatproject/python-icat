#! /usr/bin/python
#
# Delete all content from an ICAT.
#

import icat
import icat.config
import logging

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

config = icat.config.Config(ids="optional")
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)


def deletetype(t):
    """Delete all objects of some type t.
    """
    # The search may fail if there are too many objects to return.
    # Limit the result to 100 at a time.  This requires the JPQL
    # syntax introduced with ICAT 4.3.  Try and hope for the best with
    # older ICATs.
    if client.apiversion < '4.3':
        client.deleteMany(client.search(t))
    else:
        while True:
            objs = client.search("SELECT o FROM %s o LIMIT 0, 100" % t)
            if not objs:
                break
            client.deleteMany(objs)

# Entity types needed for access permissions.  Must be deleted last,
# otherwise we would take delete permission from ourselves.
if client.apiversion < '4.3':
    authztables = [ "Group", "Rule", "User", "UserGroup", ]
else:
    authztables = [ "Grouping", "Rule", "User", "UserGroup", ]


# First step, delete all Datafiles from IDS.
# 
# There is a problem: if the Datafile has been created with IDS by a
# file upload then we MUST delete it with IDS, otherwise it would
# leave an orphan file in the IDS.  If the Datafile has been created
# in the ICAT client without IDS, we MUST NOT delete it with IDS,
# because IDS will not find the actual file and will throw an internal
# server error.  But there is no reliable way to tell the one from the
# other.  As a rule, we will assume that the file has been created
# with IDS if the location attribute is set.  But of course, there is
# no way to prevent you from creating the file in the ICAT client and
# set a location ...
if client.ids:
    datafileIds = client.search("SELECT d.id from Datafile d "
                                "WHERE d.location IS NOT NULL")
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
        deletetype(t)

# Last step, delete the authztables.
for t in authztables:
    deletetype(t)
