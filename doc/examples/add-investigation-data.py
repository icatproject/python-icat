#! /usr/bin/python
#
# Populate some sample investigations with data.
#
# It is assumed that the investigation in question already exists and
# that the permissions are set up accordingly.  This script should be
# run by an ICAT user having write permissions on the investigation,
# e.g. a user that is in the writer group of the given investigation.
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
config.add_variable('skipfiles', ("--skipdatafiles",), 
                    dict(help="skip adding Datafiles", action='store_true'))
config.add_variable('datafile', ("datafile",), 
                    dict(metavar="inputdata.yaml", 
                         help="name of the input datafile"))
config.add_variable('investigationname', ("investigationname",), 
                    dict(help="name of the investigation to add"))
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def initobj(obj, attrs):
    """Initialize an entity object from a dict of attributes."""
    for a in obj.InstAttr:
        if a != 'id' and a in attrs:
            setattr(obj, a, attrs[a])

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
    investigationdata = data['investigations'][conf.investigationname]
except KeyError:
    raise RuntimeError("unknown investigation '%s'" % conf.investigationname)


# ------------------------------------------------------------
# Get some objects that we assume to be already present in ICAT
# and that we need later on
# ------------------------------------------------------------

facilityname = data['facilities'][investigationdata['facility']]['name']
facility = client.assertedSearch("Facility[name='%s']" % facilityname)[0]
facility_const = "AND facility.id=%d" % facility.id

invsearch = "Investigation[name='%s']" % investigationdata['name']
investigation = client.assertedSearch(invsearch)[0]

need_dataset_types = set()
need_datafile_formats = set()
for ds in investigationdata['datasets']:
    need_dataset_types.add(ds['type'])
    if not conf.skipfiles:
        for df in ds['datafiles']:
            need_datafile_formats.add(df['format'])

dataset_types = {}
for t in need_dataset_types:
    dstsearch = ("DatasetType[name='%s' %s]" 
                 % (data['dataset_types'][t]['name'], facility_const))
    dataset_types[t] = client.assertedSearch(dstsearch)[0]

datafile_formats = {}
for t in need_datafile_formats:
    dffsearch = ("DatafileFormat[name='%s' AND version='%s' %s]" 
                 % (data['datafile_formats'][t]['name'], 
                    data['datafile_formats'][t]['version'], 
                    facility_const))
    datafile_formats[t] = client.assertedSearch(dffsearch)[0]


# ------------------------------------------------------------
# Create the investigation data
# ------------------------------------------------------------

sampledata = investigationdata['sample']

stsearch = ("SampleType[name='%s']" 
            % data['sample_types'][sampledata['type']]['name'])
sample_type = client.assertedSearch(stsearch)[0]

print("Sample: creating '%s' ..." % sampledata['name'])
sample = client.new("sample", name=sampledata['name'], 
                    type=sample_type, investigation=investigation)
sample.create()


for datasetdata in investigationdata['datasets']:
    print("Dataset: creating '%s' ..." % datasetdata['name'])
    dataset = client.new("dataset")
    initobj(dataset, datasetdata)
    # Need to override the complete flag from the example data as we
    # do not have create permissions on complete datasets.
    dataset.complete = False
    dataset.sample = sample
    dataset.investigation = investigation
    dataset.type = dataset_types[datasetdata['type']]

    if not conf.skipfiles:
        for datafiledata in datasetdata['datafiles']:
            print("Datafile: creating '%s' ..." % datafiledata['name'])
            datafile = client.new("datafile")
            initobj(datafile, datafiledata)
            datafile.datafileFormat = datafile_formats[datafiledata['format']]
            dataset.datafiles.append(datafile)

    dataset.create()

