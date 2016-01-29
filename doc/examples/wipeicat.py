#! /usr/bin/python
#
# Delete all content from an ICAT.
#
# This script uses the JPQL syntax for searching in the ICAT.  It thus
# requires ICAT version 4.3.0 or greater.
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

# Limit of the number of objects to be searched at a time.
searchlimit = 200

def deletetype(t):
    """Delete all objects of some type t.
    """
    searchexp = "SELECT o FROM %s o LIMIT 0, %d" % (t, searchlimit)
    while True:
        objs = client.search(searchexp)
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
# otherwise we might take delete permission from ourselves.
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
def getDfSelections(status=None):
    """Yield selections of Datafiles.
    """
    skip = 0
    while True:
        searchexp = ("SELECT o FROM Dataset o INCLUDE o.datafiles "
                     "LIMIT %d, %d" % (skip, searchlimit))
        skip += searchlimit
        datasets = client.search(searchexp)
        if not datasets:
            break
        selection = DataSelection()
        for ds in datasets:
            dfs = [df for df in ds.datafiles if df.location is not None]
            if dfs and (not status or 
                        client.ids.getStatus(DataSelection([ds])) == status):
                selection.extend(dfs)
        if selection:
            yield selection

if client.ids:
    while True:
        # Wait for the server to process all pending requests.  This
        # may be needed to avoid race conditions, see
        # https://github.com/icatproject/ids.server/issues/14
        # The problem has been fixed in IDS 1.3.0.
        if client.ids.apiversion < '1.3.0':
            waitOpsQueue()
        # First step: delete everything that is currently online.
        for selection in getDfSelections("ONLINE"):
            client.deleteData(selection)
        # Second step: request a restore of all remaining datasets.
        for selection in getDfSelections("ARCHIVED"):
            client.ids.restore(selection)
        # If any Datafile is left we need to continue the loop.
        query = ("SELECT df FROM Datafile df "
                 "WHERE df.location IS NOT NULL LIMIT 0,1")
        if client.search(query):
            time.sleep(30)
        else:
            break


# Second step, delete all Facilities.  By cascading, this already
# wipes almost everything.
client.deleteMany(client.search("Facility"))

# Third step, delete almost all remaining bits, keep only
# authztables.  This will hit stuff not directly linked to Facility,
# such as Study, Log, and PublicStep.
for t in client.getEntityNames():
    if t not in authztables:
        deletetype(t)

# Last step, delete the authztables.
for t in authztables:
    deletetype(t)
