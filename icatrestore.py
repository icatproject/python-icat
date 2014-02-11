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
#  + It is assumed that the dump file contains appropriate rules that
#    gives the ICAT root user CRUD permission on all entity types.
#    These rules and corresponding user and group objects must be in
#    the first chunk (see below) of the file.
#  + This script requires ICAT 4.3.0 or newer.
#  + A dump and restore of an ICAT will not preserve the attributes
#    id, createId, createTime, modId, and modTime of any objects.
#    This is by design and cannot be fixed.  As a consequence, access
#    rules that are based on object ids will not work after a restore.
#    The Log will also not be restored.
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

config = icat.config.Config()
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)

# ------------------------------------------------------------
# Helper function
# ------------------------------------------------------------

def substkeys(d, keys, objindex):
    """Substitude unique keys by the corresponding objects in the
    values of the dict d corresponding to keys.
    """
    for k in keys:
        if d[k] is not None:
            d[k] = client.searchUniqueKey(d[k], objindex)

# ------------------------------------------------------------
# Creator functions
# ------------------------------------------------------------

def createObjs(data, insttype, subst, objindex):
    """Create objects, generic method."""
    bean = client.typemap[insttype].BeanName
    for key, d in data.iteritems():
        log.info("create %s %s ...", bean, d['name'])
        substkeys(d, subst, objindex)
        obj = client.new(insttype, **d)
        obj.create()
        objindex[key] = obj

def createBulkObjs(data, insttype, subst, objindex):
    """Create objects, bulk method: use createMany, do not add them to
    the objindex."""
    bean = client.typemap[insttype].BeanName
    objs = []
    for d in data.itervalues():
        substkeys(d, subst, objindex)
        objs.append(client.new(insttype, **d))
    log.info("create %d %ss ...", len(objs), bean)
    client.createMany(objs)

def createGroups(data, insttype, subst, objindex):
    for key, d in data.iteritems():
        log.info("create Group %s ...", d['name'])
        users = [ client.searchUniqueKey(u, objindex) for u in d['users'] ]
        obj = client.createGroup(d['name'], users)
        objindex[key] = obj

def createInstruments(data, insttype, subst, objindex):
    bean = client.typemap[insttype].BeanName
    for key, d in data.iteritems():
        log.info("create %s %s ...", bean, d['name'])
        instrsci = [ client.searchUniqueKey(u, objindex) 
                     for u in d['instrumentScientists'] ]
        del d['instrumentScientists']
        substkeys(d, subst, objindex)
        obj = client.new(insttype, **d)
        obj.create()
        obj.addInstrumentScientists(instrsci)
        objindex[key] = obj

def createParameterTypes(data, insttype, subst, objindex):
    bean = client.typemap[insttype].BeanName
    for key, d in data.iteritems():
        log.info("create %s %s ...", bean, d['name'])
        permissibleStringValues = d['permissibleStringValues']
        del d['permissibleStringValues']
        substkeys(d, subst, objindex)
        obj = client.new(insttype, **d)
        for v in permissibleStringValues:
            o = client.new('permissibleStringValue', **v)
            obj.permissibleStringValues.append(o)
        obj.create()
        objindex[key] = obj

def createInvestigations(data, insttype, subst, objindex):
    bean = client.typemap[insttype].BeanName
    for key, d in data.iteritems():
        log.info("create %s %s ...", bean, d['name'])
        r = {}
        for t in ['instruments', 'investigationUsers', 'parameters', 
                  'shifts', 'keywords', 'publications']:
            r[t] = d[t]
            del d[t]
        substkeys(d, subst, objindex)
        obj = client.new(insttype, **d)
        for s in r['investigationUsers']:
            substkeys(s, ['user'], objindex)
            o = client.new('investigationUser', **s)
            obj.investigationUsers.append(o)
        for s in r['parameters']:
            substkeys(s, ['type'], objindex)
            o = client.new('investigationParameter', **s)
            obj.parameters.append(o)
        for s in r['shifts']:
            obj.shifts.append(client.new('shift', **s))
        for s in r['keywords']:
            obj.keywords.append(client.new('keyword', **s))
        for s in r['publications']:
            obj.publications.append(client.new('publication', **s))
        obj.create()
        for s in r['instruments']:
            instrument = client.searchUniqueKey(s, objindex)
            obj.addInstrument(instrument)
        objindex[key] = obj

def createStudies(data, insttype, subst, objindex):
    bean = client.typemap[insttype].BeanName
    for key, d in data.iteritems():
        log.info("create %s %s ...", bean, d['name'])
        studyInvestigations = d['studyInvestigations']
        del d['studyInvestigations']
        substkeys(d, subst, objindex)
        obj = client.new(insttype, **d)
        for s in studyInvestigations:
            substkeys(s, ['investigation'], objindex)
            o = client.new('studyInvestigation', **s)
            obj.studyInvestigations.append(o)
        obj.create()
        objindex[key] = obj

def createSamples(data, insttype, subst, objindex):
    bean = client.typemap[insttype].BeanName
    for key, d in data.iteritems():
        log.info("create %s %s ...", bean, d['name'])
        parameters = d['parameters']
        del d['parameters']
        substkeys(d, subst, objindex)
        obj = client.new(insttype, **d)
        for p in parameters:
            substkeys(p, ['type'])
            obj.parameters.append(client.new('sampleParameter', **p))
        obj.create()
        objindex[key] = obj

def createDatasets(data, insttype, subst, objindex):
    bean = client.typemap[insttype].BeanName
    for key, d in data.iteritems():
        log.info("create %s %s ...", bean, d['name'])
        parameters = d['parameters']
        del d['parameters']
        substkeys(d, subst, objindex)
        obj = client.new(insttype, **d)
        for p in parameters:
            substkeys(p, ['type'])
            obj.parameters.append(client.new('datasetParameter', **p))
        obj.create()
        objindex[key] = obj

def createDatafiles(data, insttype, subst, objindex):
    bean = client.typemap[insttype].BeanName
    for key, d in data.iteritems():
        log.info("create %s %s ...", bean, d['name'])
        parameters = d['parameters']
        del d['parameters']
        substkeys(d, subst, objindex)
        obj = client.new(insttype, **d)
        for p in parameters:
            substkeys(p, ['type'])
            obj.parameters.append(client.new('datafileParameter', **p))
        obj.create()
        objindex[key] = obj

def createDataCollections(data, insttype, subst, objindex):
    bean = client.typemap[insttype].BeanName
    for key, d in data.iteritems():
        log.info("create %s %s ...", bean, d['name'])
        obj = client.new(insttype)
        for r in d['dataCollectionDatafiles']:
            datafile = client.searchUniqueKey(r, objindex) 
            o = client.new('dataCollectionDatafile', datafile=datafile)
            obj.dataCollectionDatafiles.append(o)
        for r in d['dataCollectionDatasets']:
            dataset = client.searchUniqueKey(r, objindex) 
            o = client.new('dataCollectionDataset', dataset=dataset)
            obj.dataCollectionDatasets.append(o)
        for r in d['parameters']:
            substkeys(r, ['type'], objindex)
            o = client.new('dataCollectionParameter', **r)
            obj.parameters.append(o)
        obj.create()
        objindex[key] = obj

# ------------------------------------------------------------
# Create data at the ICAT server
# ------------------------------------------------------------

entitytypes = [
    ('User', 'user', createObjs, []),
    ('Group', 'grouping', createGroups, []),
    ('Rule', 'rule', createBulkObjs, ['grouping']),
    ('PublicStep', 'publicStep', createBulkObjs, []),
    ('Facility', 'facility', createObjs, []),
    ('Instrument', 'instrument', createInstruments, ['facility']),
    ('ParameterType', 'parameterType', createParameterTypes, ['facility']),
    ('InvestigationType', 'investigationType', createObjs, ['facility']),
    ('SampleType', 'sampleType', createObjs, ['facility']),
    ('DatasetType', 'datasetType', createObjs, ['facility']),
    ('DatafileFormat', 'datafileFormat', createObjs, ['facility']),
    ('FacilityCycle', 'facilityCycle', createObjs, ['facility']),
    ('Application', 'application', createObjs, ['facility']),
    ('Investigation', 'investigation', createInvestigations, 
     ['facility', 'type']),
    ('Study', 'study', createStudies, ['user']),
    ('Sample', 'sample', createSamples, ['type', 'investigation']),
    ('Dataset', 'dataset', createDatasets, ['type', 'investigation', 'sample']),
    ('Datafile', 'datafile', createDatafiles, ['datafileFormat', 'dataset']),
    ('RelatedDatafile', 'relatedDatafile', createBulkObjs, 
     ['sourceDatafile', 'destDatafile']),
    ('DataCollection', 'dataCollection', createDataCollections, []),
    ('Job', 'job', createBulkObjs, 
     ['application', 'inputDataCollection', 'outputDataCollection']),
]

# We read the data in chunks (or documents in YAML terminology).  This
# way we can avoid having the whole file, e.g. the complete inventory
# of the ICAT, at once in memory.  The problem is that some objects
# contain references to other objects (e.g. Datafiles refer to
# Datasets, the latter refer to Investigations, and so forth).  We
# need to resolve these references before we can create the objects.
# To this end, we keep an index of the objects.  But there is a memory
# versus time tradeoff: we cannot keep all the objects in the index,
# that would again mean the complete inventory of the ICAT.  And we
# can't know beforehand which object is going to be referenced later
# on, so we don't know which to keep and which to discard from the
# index.  Fortunately we can query objects we discarded back from the
# ICAT server with client.searchUniqueKey().  But this is expensive.
# So the strategy is as follows: keep all objects from the current
# chunk in the index and discard the complete index each time a chunk
# has been processed.  This will work fine if objects are mostly
# referencing other objects from the same chunk.  It is in the
# responsibility of the creator of the dumpfile to create the chunks
# in this manner.

# yaml.load_all() returns a generator that yield one chunk (YAML
# document) from the file in each iteration.
for data in yaml.load_all(sys.stdin):
    objindex = {}
    # We need to create the objects in order so that objects are
    # processed before those referencing the former.
    for name, insttype, creator, subst in entitytypes:
        if name in data:
            creator(data[name], insttype, subst, objindex)
