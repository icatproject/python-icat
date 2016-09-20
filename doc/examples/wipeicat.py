#! /usr/bin/python
#
# Delete all content from an ICAT.
#
# This is surprisingly involved to do it reliably.  See the comments
# below for the issues that need to be taken into account.
#
# This script uses the JPQL syntax for searching in the ICAT.  It thus
# requires ICAT version 4.3.0 or greater.
#

import time
import logging
import icat
from icat.ids import DataSelection
import icat.config
from icat.query import Query

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
    query = Query(client, t, limit=(0, searchlimit))
    while True:
        objs = client.search(query)
        if not objs:
            break
        # Deleting Study on ICAT 4.4.0 throws ICATInternalError.  The
        # deletion succeeds though, at least, the Study object is gone
        # afterwards.  This seem to be fixed in recent ICAT versions.
        # As a work around, just ignore ICATInternalError here.
        try:
            client.deleteMany(objs)
        except icat.ICATInternalError:
            pass

def waitOpsQueue():
    """Wait for the opsQueue in the service status to drain.
    """
    while True:
        status = client.ids.getServiceStatus()
        if len(status['opsQueue']) == 0:
            break
        time.sleep(30)


# First step, delete all Datafiles from IDS.
# 
# This is somewhat tricky: if the Datafile has been created with IDS
# by a file upload then we MUST delete it with IDS, otherwise it would
# leave an orphan file in the storage.  If the Datafile has been
# created in the ICAT client without IDS, we cannot delete it with
# IDS, because IDS will not find the actual file and will throw a
# server error.  But there is no reliable way to tell the one from the
# other.  As a rule, we will assume that the file has been created
# with IDS if the location attribute is set.  Furthermore, we must
# restore the datasets first, because IDS can only delete datafiles
# that are online.  But restoring one dataset may cause another one to
# get archived if free main storage is low.  So we might need several
# sweeps to get everything deleted.  In each sweep, we delete
# everything that is currently online in a first step and file a
# restore request for all the rest in a second step.
def getDfSelections(status=None):
    """Yield selections of Datafiles.
    """
    skip = 0
    while True:
        query = Query(client, "Datafile", 
                      conditions={"location": "IS NOT NULL"}, 
                      limit=(skip, searchlimit))
        datafiles = client.search(query)
        skip += searchlimit
        if not datafiles:
            break
        selection = DataSelection()
        # It is certainly not very efficient to query the status of
        # every single Datafile individually rather then that of
        # entire Datasets.  But querying the status of a Dataset may
        # fail if it has many Datafiles, see
        # https://github.com/icatproject/ids.server/issues/42
        for df in datafiles:
            if (status and 
                client.ids.getStatus(DataSelection([df])) != status):
                continue
            selection.extend([df])
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
        query = Query(client, "Datafile", 
                      conditions={"location": "IS NOT NULL"}, limit=(0, 1))
        if client.search(query):
            time.sleep(30)
        else:
            break


# Second step, delete most content from ICAT.
#
# In theory, this could be done by just deleting the Facilities.  By
# cascading, this would already wipe almost everything.  Practical
# experience show that the object tree related to a single facility
# may be too large to be deleted in one single run, resulting in
# strange errors from the database backend.  Thus, we start little by
# little, deleting all Investigations individually first.  This
# already removes a major part of all content.  Then we delete the
# Facilities which removes most of the rest by cascading.  Finally we
# got for all the remaining bits, not related to a facility, such as
# DataCollection and Study.
#
# But we must take care not to delete the authz tables now, because
# with old ICAT versions before 4.4.0, the root user has only
# unconditional write access to the authz tables.  For the other
# stuff, he needs a rule in place that allows him access.  If we
# remove the authz tables too early, we may take away delete
# permission from ourselves.

authztables = [ "Grouping", "Rule", "User", "UserGroup", ]
alltables = client.getEntityNames()
tables = ["Investigation", "Facility"] + list(set(alltables) - set(authztables))
for t in tables:
    deletetype(t)


# Last step, delete the authztables.
for t in authztables:
    deletetype(t)
