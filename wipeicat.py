#! /usr/bin/python
#
# Delete all content from an ICAT.
#
# This is surprisingly involved to do it reliably.  See the comments
# below for the issues that need to be taken into account.
#
# This script uses the JPQL syntax for searching in the ICAT.  It thus
# requires icat.server version 4.3.0 or greater.
#
# The recommended version of ids.server is 1.6.0 or greater.  The
# script does not take any particular measure to work around issues
# in ids.server older than that.  In particular, the script mail fail
# or leave rubbish behind in to the following situations:
# - ids.server is older then 1.6.0 and there is any dataset with many
#   datafiles, Issue icatproject/ids.server#42.
# - ids.server is older then 1.3.0 and restoring of any dataset takes a
#   significant amount of time, Issue icatproject/ids.server#14.
#

import time
import logging
from warnings import warn
import icat
from icat.ids import DataSelection
import icat.config
from icat.query import Query

logging.basicConfig(level=logging.INFO)

config = icat.config.Config(ids="optional")
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
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
if client.ids:
    dfquery = Query(client, "Datafile", 
                    conditions={"location": "IS NOT NULL"}, limit=(0, 1))
    while True:
        deleteDatasets = []
        restoreDatasets = []
        errorDatasets = []
        for ds in client.searchChunked("Dataset", chunksize=objlimit):
            try:
                status = client.ids.getStatus(DataSelection([ds]))
            except icat.IDSInternalError:
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
        if len(errorDatasets) > 0:
            client.ids.reset(DataSelection(errorDatasets))
        # This whole loop may take a significant amount of time, make
        # sure our session does not time out.
        client.refresh()
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
