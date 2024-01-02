#! /usr/bin/python3
#
# Create a datafile.
#
# This script takes a file as argument and creates the corresponding
# datafile.  The datafile must already be stored at the proper path in
# the main storage such that the IDS storage plugin can find it.
#
# This script is an example and intended to be as simple as possible.
# It does the bare minimum.  There are some build in assumptions to
# keep things simple that may not be suitable in a production
# environment.  For instance, the script creates the dataset along
# with the datafile and implicitly assumes that any dataset contains
# only one single datafile.  The dataset name is set to the file name
# without the suffix.

import datetime
from pathlib import Path
import icat
import icat.config
from icat.query import Query

# ------------------------- Config section ---------------------------
# You may want to adapt these default values

# Directory for main storage
maindir = Path.cwd()
# Name of the DatasetType
dst_name = None
# Name of the DatafileFormat
dff_name = None

# --------------------------------------------------------------------

config = icat.config.Config()
config.add_variable('maindir', ("--maindir",),
                    dict(help="directory for the main storage"),
                    type=Path, default=maindir)
config.add_variable('dst_name', ("--dst_name",),
                    dict(help="name of the dataset type"), default=dst_name)
config.add_variable('dff_name', ("--dff_name",),
                    dict(help="name of the datafile format"), default=dff_name)
config.add_variable('investigation', ("investigation",),
                    dict(help="investigation name"))
config.add_variable('datafile', ("datafile",),
                    dict(help="relative path of the datafile"), type=Path)
client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)

if not conf.maindir.is_dir():
    raise RuntimeError("main storage dir %s not found" % conf.maindir)
if conf.datafile.is_absolute():
    raise RuntimeError("datafile %s must be a relative path" % conf.datafile)
df_path = conf.maindir / conf.datafile
if not df_path.is_file():
    raise RuntimeError("datafile %s not found" % df_path)

query = Query(client, "DatasetType",
              conditions={ "name": "= '%s'" % conf.dst_name })
dst = client.assertedSearch(query)[0]
query = Query(client, "DatafileFormat",
              conditions={ "name": "= '%s'" % conf.dff_name })
dff = client.assertedSearch(query)[0]
query = Query(client, "Investigation",
              conditions={ "name": "= '%s'" % conf.investigation })
investigation = client.assertedSearch(query)[0]

fstats = df_path.stat()
utc = datetime.timezone.utc
modTime = datetime.datetime.fromtimestamp(fstats.st_mtime, tz=utc)
datafile = client.new("Datafile")
datafile.datafileFormat = dff
datafile.name = conf.datafile.name
datafile.location = str(conf.datafile)
datafile.datafileModTime = modTime
datafile.datafileCreateTime = modTime
datafile.fileSize = fstats.st_size

dataset = client.new("Dataset")
dataset.investigation=investigation
dataset.type=dst
dataset.complete=False
dataset.name=conf.datafile.with_suffix('').name
dataset.datafiles.append(datafile)
dataset.create()
