#! /usr/bin/python
#
# Populate some sample investigations with data.
#
# It is assumed that the investigation in question already exists and
# that the permissions are set up accordingly.  This script should be
# run by an ICAT user having write permissions on the investigation,
# e.g. a user that is in the writer group of the given investigation.
#

import logging
import sys
import yaml
import icat
import icat.config

logging.basicConfig(level=logging.INFO)

config = icat.config.Config()
config.add_variable('skipfiles', ("--skipdatafiles",),
                    dict(help="skip adding Datafiles", action='store_true'))
config.add_variable('datafile', ("datafile",),
                    dict(metavar="inputdata.yaml",
                         help="name of the input datafile"))
config.add_variable('investigationname', ("investigationname",),
                    dict(help="name of the investigation to add"))
client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def initobj(obj, attrs):
    """Initialize an entity object from a dict of attributes."""
    for a in obj.InstAttr:
        if a != 'id' and a in attrs:
            setattr(obj, a, attrs[a])

def makeparam(t, pdata):
    param = client.new(t)
    initobj(param, pdata)
    ptdata = data['parameter_types'][pdata['type']]
    query = ("ParameterType [name='%s' AND units='%s']"
             % (ptdata['name'], ptdata['units']))
    param.type = client.assertedSearch(query)[0]
    return param

# ------------------------------------------------------------
# Read input data
# ------------------------------------------------------------

if conf.datafile == "-":
    f = sys.stdin
else:
    f = open(conf.datafile, 'r')
data = yaml.safe_load(f)
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

instrumentname = data['instruments'][investigationdata['instrument']]['name']
instrsearch = "Instrument[name='%s' %s]" % (instrumentname, facility_const)
instrument = client.assertedSearch(instrsearch)[0]

technique = None
if "technique" in client.typemap:
    t = data['instruments'][investigationdata['instrument']]['technique']
    if t:
        tn = data['techniques'][t]['name']
        techsearch = "Technique [name='%s']" % tn
        technique = client.assertedSearch(techsearch)[0]

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
sample = client.new("Sample")
initobj(sample, sampledata)
sample.type = sample_type
sample.investigation = investigation
if 'parameters' in sampledata:
    for pdata in sampledata['parameters']:
        sample.parameters.append(makeparam('sampleParameter', pdata))
sample.create()


for datasetdata in investigationdata['datasets']:
    print("Dataset: creating '%s' ..." % datasetdata['name'])
    dataset = client.new("Dataset")
    initobj(dataset, datasetdata)
    # Need to override the complete flag from the example data as we
    # do not have create permissions on complete datasets.
    dataset.complete = False
    dataset.sample = sample
    dataset.investigation = investigation
    dataset.type = dataset_types[datasetdata['type']]
    if 'parameters' in datasetdata:
        for pdata in datasetdata['parameters']:
            dataset.parameters.append(makeparam('datasetParameter', pdata))

    if not conf.skipfiles:
        for datafiledata in datasetdata['datafiles']:
            print("Datafile: creating '%s' ..." % datafiledata['name'])
            datafile = client.new("Datafile")
            initobj(datafile, datafiledata)
            datafile.datafileFormat = datafile_formats[datafiledata['format']]
            if 'parameters' in datafiledata:
                for pdata in datafiledata['parameters']:
                    datafile.parameters.append(makeparam('datafileParameter',
                                                         pdata))
            dataset.datafiles.append(datafile)

    if 'datasetInstruments' in dataset.InstMRel:
        di = client.new("DatasetInstrument", instrument=instrument)
        dataset.datasetInstruments.append(di)
    if 'datasetTechniques' in dataset.InstMRel and technique:
        dt = client.new("DatasetTechnique", technique=technique)
        dataset.datasetTechniques.append(dt)

    dataset.create()
