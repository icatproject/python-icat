#! /usr/bin/python
#
# Delete all content from an ICAT.
#
# This is surprisingly involved to do it reliably.  See the comments
# below for the issues that need to be taken into account.

import logging
import time
from warnings import warn
import icat
import icat.config
from icat.ids import DataSelection
from icat.query import Query

logging.basicConfig(level=logging.INFO)

config = icat.config.Config(ids="optional")
client, conf = config.getconfig()

if client.apiversion < '4.3.0':
    raise RuntimeError("Sorry, icat.server version %s is too old, "
                       "need 4.3.0 or newer." % client.apiversion)
if client.ids and client.ids.apiversion < '1.6.0':
    warn("ids.server %s is older then the recommended minimal version 1.6.0."
         % client.ids.apiversion)
client.login(conf.auth, conf.credentials)

# Limit of the number of objects to be dealt with at a time.
objlimit = 200


def deleteobjs(query):
    """Delete all objects of matching the query.
    """
    query.setLimit( (0, objlimit) )
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


# First step, delete all Datafiles.
# 
# This is somewhat tricky: if the Datafile has been created with IDS
# by a file upload then we MUST delete it with IDS, otherwise it would
# leave an orphan file in the storage.  If the Datafile has been
# created directly in the ICAT without IDS, we cannot delete it with
# IDS, because IDS will not find the actual file and will throw a
# server error.  But there is no reliable way to tell the one from the
# other.  As a rule, we will assume that the file has been created
# with IDS if the location attribute is set.

# Delete all datafiles having location not set directly from ICAT
# first, because they would cause trouble when we try to delete the
# remaining datafiles from IDS, see Issue icatproject/ids.server#63.
deleteobjs(Query(client, "Datafile", conditions={"location": "IS NULL"}))

# To delete datafiles from IDS, we must restore the datasets first,
# because IDS can only delete datafiles that are online.  But
# restoring one dataset may cause another one to get archived if free
# main storage is low.  So we might need several sweeps to get
# everything deleted.  In each sweep, we delete everything that is
# currently online in a first step and file a restore request for some
# remaining datasets in a second step.
#
# Restoring a dataset may fail, in particular, if the files are not
# present in IDS storage, see above.  If that happens, we reset the
# error to retry.  But we do that only once per dataset.  If the
# restore fails again, we give up und delete the dataset from ICAT,
# without considering IDS.
if client.ids:
    dfquery = Query(client, "Datafile", 
                    conditions={"location": "IS NOT NULL"}, limit=(0, 1))
    retriedDatasets = set()
    while True:
        deleteDatasets = []
        restoreDatasets = []
        errorDatasets = []
        failedDatasets = []
        for ds in client.searchChunked("Dataset", chunksize=objlimit):
            try:
                status = client.ids.getStatus(DataSelection([ds]))
            except icat.IDSInternalError:
                if ds in retriedDatasets:
                    failedDatasets.append(ds)
                else:
                    errorDatasets.append(ds)
                continue
            if status == "ONLINE":
                deleteDatasets.append(ds)
                if len(deleteDatasets) >= objlimit:
                    client.deleteData(deleteDatasets)
                    client.deleteMany(deleteDatasets)
                    deleteDatasets = []
            elif status == "ARCHIVED":
                if len(restoreDatasets) < objlimit:
                    restoreDatasets.append(ds)
        if len(deleteDatasets) > 0:
            client.deleteData(deleteDatasets)
            client.deleteMany(deleteDatasets)
        if len(restoreDatasets) > 0:
            client.ids.restore(DataSelection(restoreDatasets))
        if len(failedDatasets) > 0:
            client.deleteMany(failedDatasets)
            retriedDatasets.difference_update(failedDatasets)
        if len(errorDatasets) > 0:
            client.ids.reset(DataSelection(errorDatasets))
            retriedDatasets.update(errorDatasets)
        # This whole loop may take a significant amount of time, make
        # sure our session does not time out.
        client.autoRefresh()
        # If any Datafile is left we need to continue the loop.
        if client.search(dfquery):
            time.sleep(60)
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
# go for all the remaining bits, not related to a facility, such as
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
    deleteobjs(Query(client, t))


# Last step, delete the authztables.
for t in authztables:
    deleteobjs(Query(client, t))
