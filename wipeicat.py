#! /usr/bin/python
#
# Delete all content from an ICAT.
#

import time
import logging
import icat
from icat.ids import DataSelection
import icat.config

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

def waitOpsQueue():
    """Wait for the opsQueue in the service status to drain.
    """
    while True:
        status = client.ids.getServiceStatus()
        if len(status['opsQueue']) == 0:
            break
        time.sleep(30)


# Entity types needed for access permissions.  Must be deleted last,
# otherwise we would take delete permission from ourselves.
if client.apiversion < '4.3':
    authztables = [ "Group", "Rule", "User", "UserGroup", ]
else:
    authztables = [ "Grouping", "Rule", "User", "UserGroup", ]


# First step, delete all Datafiles from IDS.
# 
# This is somewhat tricky: if the Datafile has been created with IDS
# by a file upload then we MUST delete it with IDS, otherwise it would
# leave an orphan file in the IDS.  If the Datafile has been created
# in the ICAT client without IDS, we cannot delete it with IDS,
# because IDS will not find the actual file and will throw a server
# error.  But there is no reliable way to tell the one from the other.
# As a rule, we will assume that the file has been created with IDS if
# the location attribute is set.  Furthermore, we must restore the
# datasets first, because IDS can only delete datafiles that are
# online.  But restoring one dataset may cause another one to get
# archived if free main storage is low.  So we might need several
# sweeps to get everything deleted.  In each sweep, we delete
# everything that is currently online in a first step and file a
# restore request for all the rest in a second step.
if client.ids:
    if client.apiversion < '4.3':
        searchexp = "Dataset INCLUDE Datafile"
    else:
        searchexp = "SELECT o FROM Dataset o INCLUDE o.datafiles LIMIT 0, 100"
    while True:
        restsel = DataSelection()
        deleted = False
        # Wait for the server to process all pending requests.  This
        # may be needed to avoid race conditions, see
        # https://code.google.com/p/icat-data-service/issues/detail?id=14
        waitOpsQueue()
        for ds in client.search(searchexp):
            selection = DataSelection([df for df in ds.datafiles 
                                       if df.location is not None])
            if selection:
                if client.ids.getStatus(selection) == "ONLINE":
                    client.deleteData(selection)
                    deleted = True
                else:
                    restsel.extend(selection)
            else:
                client.delete(ds)
                deleted = True
        if not deleted and not restsel:
            break
        if restsel:
            client.ids.restore(restsel)


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
