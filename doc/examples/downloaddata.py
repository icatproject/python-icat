#! /usr/bin/python
#
# Download all Datafiles from a Dataset from IDS.
#
# The script takes an investigation identifier, a dataset name, and a
# method name files as arguments.  The investigation identifier may
# contain one colon, then it is taken as name:visitid, otherwise it is
# taken as the investigation name.  The investigation and the dataset
# (identified by the name within the investigation) must exist in the
# ICAT and must be unique.
#
# The method name selects one out of four different download methods
# offered by IDS:
# - getData:            directly downloads the files,
# - getDataUrl:         print a download URL to stdout.
# - getPreparedData:    first call prepareData for the files, then
#                       wait for the prepared data to be ready, and
#                       finally download the prepared data.
# - getPreparedDataUrl: call prepareData for the files, wait for the
#                       prepared data to be ready, and finally print a
#                       download URL for the prepared data to stdout.
# In all cases, the result will be a zip archive containing the files.
#
# For "getData" and "getPreparedData", the name of the output file can
# be set with the option "--outputfile".  If not set the output file
#

import logging
import sys
import time
import icat
import icat.config

logging.basicConfig(level=logging.INFO)

config = icat.config.Config(ids="mandatory")
config.add_variable('outputfile', ("--outputfile",),
                    dict(help="name of the output file"), optional=True)
config.add_variable('investigation', ("investigation",),
                    dict(help="name and optionally visit id "
                         "(separated by a colon) of the investigation"))
config.add_variable('dataset', ("dataset",),
                    dict(help="name of the dataset"))
config.add_variable('method', ("method",),
                    dict(choices=['getData', 'getDataUrl',
                                  'getPreparedData', 'getPreparedDataUrl'],
                         help="download method"))
client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)
client.ids.ping()


# ------------------------------------------------------------
# helper
# ------------------------------------------------------------

def copyfile(infile, outfile, chunksize=8192):
    """Read all data from infile and write them to outfile.
    """
    while True:
        chunk = infile.read(chunksize)
        if not chunk:
            break
        outfile.write(chunk)


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

investigation = getinvestigation(conf.investigation)
dataset = getdataset(conf.dataset, investigation)
datafiles = client.search("Datafile <-> Dataset [id=%d]" % dataset.id)
if not datafiles:
    # No files in the Dataset, nothing to download.
    sys.exit()


# ------------------------------------------------------------
# Dowload or get URL according to selected method.
# ------------------------------------------------------------

if conf.method == 'getData':

    response = client.getData(datafiles)
    if conf.outputfile:
        with open(conf.outputfile, 'wb') as f:
            copyfile(response, f)
    else:
        copyfile(response, sys.stdout)

elif conf.method == 'getDataUrl':

    print(client.getDataUrl(datafiles))
    # Must not logout to keep the sessionId in the download url valid.
    client.autoLogout = False

elif conf.method == 'getPreparedData':

    prepid = client.prepareData(datafiles)
    while not client.isDataPrepared(prepid):
        time.sleep(5)
    response = client.getData(prepid)
    if conf.outputfile:
        with open(conf.outputfile, 'wb') as f:
            copyfile(response, f)
    else:
        copyfile(response, sys.stdout)

elif conf.method == 'getPreparedDataUrl':

    prepid = client.prepareData(datafiles)
    while not client.isDataPrepared(prepid):
        time.sleep(5)
    print(client.getDataUrl(prepid))

else:
    raise RuntimeError("Invalid method %s." % conf.method)

