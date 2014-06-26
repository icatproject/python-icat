#! /usr/bin/python
#
# Create a job along with the input and output datacollection.
#
# The Datasets and Datafiles in the input datacollection are assumed
# to already exists.  The output Datasets and Datafiles will be
# created by this script.  This script must be run by an ICAT user
# having appropriate permissions.
#

from __future__ import print_function
import icat
import icat.config
import sys
import logging
import yaml

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

config = icat.config.Config()
config.add_variable('datafile', ("datafile",), 
                    dict(metavar="inputdata.yaml", 
                         help="name of the input datafile"))
config.add_variable('jobname', ("jobname",), 
                    dict(help="name of the job to add"))
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
if client.apiversion < '4.3':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.3.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


# ------------------------------------------------------------
# Read input data
# ------------------------------------------------------------

if conf.datafile == "-":
    f = sys.stdin
else:
    f = open(conf.datafile, 'r')
data = yaml.load(f)
f.close()

try:
    jobdata = data['jobs'][conf.jobname]
except KeyError:
    raise RuntimeError("unknown job '%s'" % conf.jobname)


# Note: to simplify things, we assume that the is only one facility.
# E.g. we assume that Investigationa and DatasetTypes are unique by
# its name and that DatafileFormats and Applications are unique by
# name and version.


# ------------------------------------------------------------
# Create the input data collection
# ------------------------------------------------------------

inputcollection = client.new("dataCollection")

for ds in jobdata['input']['datasets']:
    searchexp = ("SELECT ds FROM Dataset ds "
                 "JOIN ds.investigation i "
                 "WHERE ds.name = '%s' AND i.name = '%s'"
                 % (ds['name'], ds['investigation']))
    dataset = client.assertedSearch(searchexp)[0]
    dcs = client.new("dataCollectionDataset", dataset=dataset)
    inputcollection.dataCollectionDatasets.append(dcs)

for df in jobdata['input']['datafiles']:
    searchexp = ("SELECT df FROM Datafile df "
                 "JOIN df.dataset ds JOIN ds.investigation i "
                 "WHERE df.name = '%s' AND ds.name = '%s' AND i.name = '%s'"
                 % (df['name'], df['dataset'], df['investigation']))
    datafile = client.assertedSearch(searchexp)[0]
    dcf = client.new("dataCollectionDatafile", datafile=datafile)
    inputcollection.dataCollectionDatafiles.append(dcf)

inputcollection.create()


# ------------------------------------------------------------
# Create the output data collection
# ------------------------------------------------------------

outputcollection = client.new("dataCollection")

for ds in jobdata['output']['datasets']:
    searchexp = ("SELECT i FROM Investigation i WHERE i.name='%s'" 
                 % ds['investigation'])
    investigation = client.assertedSearch(searchexp)[0]
    searchexp = ("SELECT dst FROM DatasetType dst WHERE dst.name='%s'" 
                 % data['dataset_types'][ds['type']]['name'])
    dataset_type = client.assertedSearch(searchexp)[0]
    print("Dataset: creating '%s' ..." % datasetdata['name'])
    dataset = client.new("dataset")
    dataset.name = ds['name']
    dataset.startDate = ds['startDate']
    dataset.endDate = ds['endDate']
    dataset.complete = ds['complete']
    dataset.investigation = investigation
    dataset.type = dataset_type

    for df in ds['datafiles']:
        searchexp = ("SELECT dff FROM DatafileFormat dff "
                     "WHERE dff.name='%s' AND dff.version='%s'" 
                     % (data['datafile_formats'][df['format']]['name'], 
                        data['datafile_formats'][df['format']]['version']))
        datafile_format = client.assertedSearch(dstsearch)[0]
        print("Datafile: creating '%s' ..." % df['name'])
        datafile = client.new("datafile")
        datafile.name = df['name']
        datafile.fileSize = df['fileSize']
        datafile.datafileCreateTime = df['createTime']
        datafile.datafileModTime = df['modTime']
        datafile.datafileFormat = datafile_format
        dataset.datafiles.append(datafile)

    dataset.create()
    dcs = client.new("dataCollectionDataset", dataset=dataset)
    outputcollection.dataCollectionDatasets.append(dcs)

for df in jobdata['output']['datafiles']:
    searchexp = ("SELECT ds FROM Dataset ds "
                 "JOIN ds.investigation i "
                 "WHERE ds.name = '%s' AND i.name = '%s'"
                 % (df['dataset'], df['investigation']))
    dataset = client.assertedSearch(searchexp)[0]
    searchexp = ("SELECT dff FROM DatafileFormat dff "
                 "WHERE dff.name='%s' AND dff.version='%s'" 
                 % (data['datafile_formats'][df['format']]['name'], 
                    data['datafile_formats'][df['format']]['version']))
    datafile_format = client.assertedSearch(searchexp)[0]
    print("Datafile: creating '%s' ..." % df['name'])
    datafile = client.new("datafile")
    datafile.name = df['name']
    datafile.fileSize = df['fileSize']
    datafile.datafileCreateTime = df['createTime']
    datafile.datafileModTime = df['modTime']
    datafile.dataset = dataset
    datafile.datafileFormat = datafile_format
    datafile.create()
    dcf = client.new("dataCollectionDatafile", datafile=datafile)
    outputcollection.dataCollectionDatafiles.append(dcf)

outputcollection.create()


# ------------------------------------------------------------
# Create the job
# ------------------------------------------------------------

appdata = data['applications'][jobdata['application']]
appsearch = ("Application [name='%s' AND version='%s']" 
             % ( appdata['name'], appdata['version'] ))
application = client.assertedSearch(appsearch)[0]

job = client.new("job", 
                 application=application, 
                 inputDataCollection=inputcollection, 
                 outputDataCollection=outputcollection)
job.create()

