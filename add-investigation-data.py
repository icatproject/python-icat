#! /usr/bin/python
#
# Populate some sample investigations with data.
#
# It is assumed that the investigation in question already exists and
# that the permissions are set up accordingly.  This script should be
# run by an ICAT user having write permissions on the investigation,
# e.g. a user that is in the writer group of the given investigation.
#

from icat.client import Client
import logging
import sys
import icat.config
import yaml

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

icat.config.defaultsection = "hzb"
conf = icat.config.Config()
conf.add_field('datafile', ("datafile",), 
               dict(metavar="inputdata.yaml", 
                    help="name of the input datafile"))
conf.add_field('investigationname', ("investigationname",), 
               dict(help="name of the investigation to add"))
conf.getconfig()
investigationname = conf.investigationname

client = Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)


# ------------------------------------------------------------
# Read input data
# ------------------------------------------------------------

try:
    if conf.datafile == "-":
        f = sys.stdin
    else:
        f = open(conf.datafile, 'r')
    try:
        data = yaml.load(f)
    finally:
        f.close()
except IOError as e:
    print >> sys.stderr, e
    sys.exit(2)
except yaml.YAMLError:
    print >> sys.stderr, "Parsing error in input datafile"
    sys.exit(2)


try:
    investigationdata = data['investigations'][investigationname]
except KeyError:
    print >> sys.stderr, "unknown investigation", investigationname
    sys.exit(2)


# ------------------------------------------------------------
# Get some objects that we assume to be already present in ICAT
# and that we need later on
# ------------------------------------------------------------

facilityname = data['facilities'][investigationdata['facility']]['name']
facilities = client.search("Facility[name='%s']" % facilityname)
if len(facilities): 
    facility = facilities[0]
else:
    print "Facility '%s' not found." % facilityname
    sys.exit(3)
facility_const = "AND facility.id=%d" % facility.id

invname = investigationdata['name']
investigations = client.search("Investigation[name='%s']" % investigationname)
if len(investigations): 
    investigation = investigations[0]
else:
    print "Investigation '%s' not found." % investigationname
    sys.exit(3)

need_dataset_types = set()
need_datafile_formats = set()
for ds in investigationdata['datasets']:
    need_dataset_types.add(ds['type'])
    for df in ds['datafiles']:
        need_datafile_formats.add(df['format'])

dataset_types = {}
for t in need_dataset_types:
    dstname = data['dataset_types'][t]['name']
    types = client.search("DatasetType[name='%s' %s]" 
                          % (dstname, facility_const))
    if len(types): 
        dataset_types[t] = types[0]
    else:
        print "DatasetType '%s' not found." % dstname
        sys.exit(3)

datafile_formats = {}
for t in need_datafile_formats:
    dffname = data['datafile_formats'][t]['name']
    formats = client.search("DatafileFormat[name='%s' %s]" 
                            % (dffname, facility_const))
    if len(formats): 
        datafile_formats[t] = formats[0]
    else:
        print "DatafileFormat '%s' not found." % dffname
        sys.exit(3)


# ------------------------------------------------------------
# Create the investigation data
# ------------------------------------------------------------

sampledata = investigationdata['sample']

sampletypename = data['sample_types'][sampledata['type']]['name']
sample_types = client.search("SampleType[name='%s']" % sampletypename)
if len(sample_types): 
    sample_type = sample_types[0]
else:
    print "SampleType '%s' not found." % sampletypename
    sys.exit(3)

print "Sample: creating '%s' ..." % sampledata['name']
sample = client.new("sample", name=sampledata['name'], 
                    type=sample_type, investigation=investigation)
sample.create()


for datasetdata in investigationdata['datasets']:
    print "Dataset: creating '%s' ..." % datasetdata['name']
    dataset = client.new("dataset")
    dataset.name = datasetdata['name']
    dataset.startDate = datasetdata['startDate']
    dataset.endDate = datasetdata['endDate']
    dataset.complete = datasetdata['complete']
    dataset.sample = sample
    dataset.investigation = investigation
    dataset.type = dataset_types[datasetdata['type']]

    for datafiledata in datasetdata['datafiles']:
        print "Datafile: creating '%s' ..." % datafiledata['name']
        datafile = client.new("datafile")
        datafile.name = datafiledata['name']
        datafile.location = datafiledata['location']
        datafile.fileSize = datafiledata['fileSize']
        datafile.datafileCreateTime = datafiledata['createTime']
        datafile.datafileModTime = datafiledata['modTime']
        datafile.datafileFormat = datafile_formats[datafiledata['format']]
        dataset.datafiles.append(datafile)

    dataset.create()


# ------------------------------------------------------------

client.logout()
