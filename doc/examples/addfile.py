#! /usr/bin/python
#
# Add one or more Datafiles to a Dataset.
#
# The script takes an investigation identifier, a dataset name, a
# datafile format identifier, and the names of one or more files as
# arguments.  The investigation identifier may contain one colon, then
# it is taken as name:visitid, otherwise it is taken as the
# investigation name.  Similarly, if datafile format identifier
# contains a colon, it is taken as name:version, otherwise as name of
# the datafile format.  The investigation, the dataset (identified by
# the name within the investigation), and the datafile format must
# exist in the ICAT and must be unique.
#
# The datafiles are uploaded to the IDS.  Its attributes, e.g. the
# file name and the modification time, are taken from the respective
# file on disk.
#
# The user running the script need to have write permission for
# datafiles in this dataset, e.g. the user must be in the writer group
# of the investigation.
#

import logging
from pathlib import Path
import icat
import icat.config

logging.basicConfig(level=logging.INFO)

config = icat.config.Config(ids="mandatory")
config.add_variable('investigation', ("investigation",),
                    dict(help="name and optionally visit id "
                         "(separated by a colon) of the investigation"))
config.add_variable('dataset', ("dataset",),
                    dict(help="name of the dataset"))
config.add_variable('datafileformat', ("datafileformat",),
                    dict(help="name and optionally version "
                         "(separated by a colon) of the datafile format"))
config.add_variable('files', ("files",),
                    dict(help="name of the files to upload", nargs="+"),
                    type=lambda l: [Path(f) for f in l])
client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)


# ------------------------------------------------------------
# Get the objects that we assume to be already present in ICAT.
# ------------------------------------------------------------

def getinvestigation(invid):
    l = invid.split(':')
    if len(l) == 1:
        # No colon, invid == name
        searchexp = "Investigation [name='%s']" % tuple(l)
    elif len(l) == 2:
        # one colon, invid == name:visitId
        searchexp = "Investigation [name='%s' AND visitId='%s']" % tuple(l)
    else:
        # too many colons
        raise RuntimeError("Invalid investigation identifier '%s'" % invid)
    return (client.assertedSearch(searchexp)[0])

def getdataset(dsname, investigation):
    searchexp = ("Dataset [name='%s' AND investigation.id=%d]"
                 % (dsname, investigation.id))
    return (client.assertedSearch(searchexp)[0])

def getdatafileformat(dffid):
    l = dffid.split(':')
    if len(l) == 1:
        # No colon, dffid == name
        searchexp = "DatafileFormat [name='%s']" % tuple(l)
    elif len(l) == 2:
        # one colon, dffid == name:version
        searchexp = "DatafileFormat [name='%s' AND version='%s']" % tuple(l)
    else:
        # too many colons
        raise RuntimeError("Invalid datafile format identifier '%s'" % dffid)
    return (client.assertedSearch(searchexp)[0])

investigation = getinvestigation(conf.investigation)
dataset = getdataset(conf.dataset, investigation)
datafileformat = getdatafileformat(conf.datafileformat)

# ------------------------------------------------------------
# Upload the files
# ------------------------------------------------------------

for fname in conf.files:
    datafile = client.new("Datafile", name=fname.name,
                          dataset=dataset, datafileFormat=datafileformat)
    client.putData(fname, datafile)


