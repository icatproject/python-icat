#! /usr/bin/python
#
# Restore the content of the ICAT from a YAML file as created by
# icatdump.py.
#
# The script reads the YAML input from stdin.  It should by run by the
# ICAT root user against an otherwise empty ICAT server.  There is no
# collision check with data already present at the ICAT.
#
# Known issues and limitations:
#  + This script is NOT suitable for a real production size ICAT.
#  + A dump and restore of an ICAT will not preserve the attributes
#    id, createId, createTime, modId, and modTime of any objects.
#    This is by design and cannot be fixed.  As a consequence, access
#    rules that are based on object ids will not work after a restore.
#    The Log will also not be restored.
#  + Version dependency.  This script currently works for ICAT 4.3.*
#    only.
#  + Restoring of several entity types has not yet been
#    tested.  See icatdump.py for a list.
#

import icat
import icat.config
import sys
import logging
import yaml

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)
log = logging.getLogger(__name__)

icat.config.defaultsection = "hzb"
config = icat.config.Config()
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)

# ------------------------------------------------------------
# Read input data
# ------------------------------------------------------------

data = yaml.load(sys.stdin)


# ------------------------------------------------------------
# Create data at the ICAT server
# ------------------------------------------------------------

keyindex = {}

def substkeys(d, keys):
    for k in keys:
        if d[k] is not None:
            d[k] = keyindex[d[k]]

# Users
for id, d in data['User'].iteritems():
    log.info("create User %s ...", d['name'])
    obj = client.new('user', **d)
    obj.create()
    keyindex[id] = obj

# Groups
for id, d in data['Group'].iteritems():
    log.info("create Group %s ...", d['name'])
    obj = client.createGroup(d['name'], [ keyindex[u] for u in d['users'] ])
    keyindex[id] = obj

# Rules
objs = []
for d in data['Rule'].itervalues():
    substkeys(d, ['grouping'])
    objs.append(client.new('rule', **d))
log.info("create %d Rules ...", len(objs))
client.createMany(objs)

# PublicSteps
objs = []
for d in data['PublicStep'].itervalues():
    objs.append(client.new('publicStep', **d))
log.info("create %d PublicSteps ...", len(objs))
client.createMany(objs)

# Facilities
for id, d in data['Facility'].iteritems():
    log.info("create Facility %s ...", d['name'])
    obj = client.new('facility', **d)
    obj.create()
    keyindex[id] = obj

# Instruments
for id, d in data['Instrument'].iteritems():
    log.info("create Instrument %s ...", d['name'])
    instrsci = [keyindex[u] for u in d['instrumentScientists']]
    del d['instrumentScientists']
    substkeys(d, ['facility'])
    obj = client.new('instrument', **d)
    obj.create()
    obj.addInstrumentScientists(instrsci)
    keyindex[id] = obj

# ParameterTypes
for id, d in data['ParameterType'].iteritems():
    log.info("create ParameterType %s ...", d['name'])
    permissibleStringValues = d['permissibleStringValues']
    del d['permissibleStringValues']
    substkeys(d, ['facility'])
    obj = client.new('parameterType', **d)
    for v in permissibleStringValues:
        o = client.new('permissibleStringValue', **v)
        obj.permissibleStringValues.append(o)
    obj.create()
    keyindex[id] = obj

# InvestigationTypes, SampleTypes, DatasetTypes, DatafileFormats,
# FacilityCycles, Applications
for t in ['investigationType', 'sampleType', 'datasetType', 'datafileFormat', 
          'facilityCycle', 'application']:
    bean = client.typemap[t].BeanName
    for id, d in data[bean].iteritems():
        log.info("create %s %s ...", bean, d['name'])
        substkeys(d, ['facility'])
        obj = client.new(t, **d)
        obj.create()
        keyindex[id] = obj

# Investigations
for id, d in data['Investigation'].iteritems():
    log.info("create Investigation %s ...", d['name'])
    r = {}
    for t in ['instruments', 'investigationUsers', 'parameters', 
              'shifts', 'keywords', 'publications']:
        r[t] = d[t]
        del d[t]
    substkeys(d, ['facility', 'type'])
    obj = client.new('investigation', **d)
    for s in r['instruments']:
        o = client.new('investigationInstrument', instrument=keyindex[s])
        obj.investigationInstruments.append(o)
    for s in r['investigationUsers']:
        substkeys(s, ['user'])
        o = client.new('investigationUser', **s)
        obj.investigationUsers.append(o)
    for s in r['parameters']:
        substkeys(d, ['type'])
        obj.parameters.append(client.new('investigationParameter', **s))
    for s in r['shifts']:
        obj.shifts.append(client.new('shift', **s))
    for s in r['keywords']:
        obj.keywords.append(client.new('keyword', **s))
    for s in r['publications']:
        obj.publications.append(client.new('publication', **s))
    obj.create()
    keyindex[id] = obj

# Studies
for id, d in data['Study'].iteritems():
    log.info("create Study %s ...", d['name'])
    studyInvestigations = d['studyInvestigations']
    del d['studyInvestigations']
    substkeys(d, ['user'])
    obj = client.new('study', **d)
    for s in studyInvestigations:
        substkeys(s, ['investigation'])
        obj.parameters.append(client.new('studyInvestigation', **s))
    obj.create()
    keyindex[id] = obj

# Samples
for id, d in data['Sample'].iteritems():
    log.info("create Sample %s ...", d['name'])
    parameters = d['parameters']
    del d['parameters']
    substkeys(d, ['type', 'investigation'])
    obj = client.new('sample', **d)
    for p in parameters:
        substkeys(p, ['type'])
        obj.parameters.append(client.new('sampleParameter', **p))
    obj.create()
    keyindex[id] = obj

# Datasets
for id, d in data['Dataset'].iteritems():
    log.info("create Dataset %s ...", d['name'])
    parameters = d['parameters']
    del d['parameters']
    substkeys(d, ['type', 'investigation', 'sample'])
    obj = client.new('dataset', **d)
    for p in parameters:
        substkeys(p, ['type'])
        obj.parameters.append(client.new('datasetParameter', **p))
    obj.create()
    keyindex[id] = obj

# Datafiles
for id, d in data['Datafile'].iteritems():
    log.info("create Datafile %s ...", d['name'])
    parameters = d['parameters']
    del d['parameters']
    substkeys(d, ['datafileFormat', 'dataset'])
    obj = client.new('datafile', **d)
    for p in parameters:
        substkeys(p, ['type'])
        obj.parameters.append(client.new('datafileParameter', **p))
    obj.create()
    keyindex[id] = obj

# RelatedDatafiles
objs = []
for d in data['RelatedDatafile'].itervalues():
    substkeys(d, ['sourceDatafile', 'destDatafile'])
    objs.append(client.new('relatedDatafile', **d))
log.info("create %d RelatedDatafiles ...", len(objs))
client.createMany(objs)

# DataCollections
for id, d in data['DataCollection'].iteritems():
    log.info("create DataCollection %s ...", d['name'])
    obj = client.new('dataCollection')
    for r in d['dataCollectionDatafiles']:
        o = client.new('dataCollectionDatafile', datafile=keyindex[r])
        obj.dataCollectionDatafiles.append(o)
    for r in d['dataCollectionDatasets']:
        o = client.new('dataCollectionDataset', dataset=keyindex[r])
        obj.dataCollectionDatasets.append(o)
    for r in d['parameters']:
        substkeys(r, ['type'])
        o = client.new('dataCollectionParameter', **r)
        obj.parameters.append(o)
    obj.create()
    keyindex[id] = obj

# Jobs
objs = []
for d in data['Job'].itervalues():
    substkeys(d, ['application', 'inputDataCollection', 'outputDataCollection'])
    objs.append(client.new('job', **d))
log.info("create %d Jobs ...", len(objs))
client.createMany(objs)
