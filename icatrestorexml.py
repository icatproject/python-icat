#! /usr/bin/python
#
# Restore the content of the ICAT from a XML file as created by
# icatdumpxml.py.  This is experimental and should be merged back with
# icatrestore.py later on.
#
# The script reads the XML input from stdin.  It should by run by the
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
from lxml import etree

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)
log = logging.getLogger(__name__)

config = icat.config.Config()
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
if client.apiversion < '4.3':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.3.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def elem2dict(elem, objindex):
    """Transform a XML element to a dict.
    """
    d = {}
    for child in elem:
        k = child.tag
        ref = child.get('ref')
        if ref is not None:
            d[k] = client.searchUniqueKey(ref, objindex)
        elif len(child):
            d[k] = child
        elif child.text is not None:
            d[k] = child.text
            # FIXME: must have some sort of type checking here
            if d[k] == 'True':
                d[k] = True
            elif d[k] == 'False':
                d[k] = False
    return d

def getstrlist(data, attr, tag):
    """Get a list of strings from an attribute in the data.
    """
    if attr in data:
        strs = [ s.text for s in data[attr].iter(tag) ]
        del data[attr]
    else:
        strs = []
    return strs

def getobjdatalist(data, attr, objindex):
    """Get a list of dicts with object attributes an attribute in the
    data.
    """
    if attr in data:
        objs = [ elem2dict(e, objindex) for e in data[attr] ]
        del data[attr]
    else:
        objs = []
    return objs

def getreflist(data, attr, tag, objindex):
    """Get a list of references to existing objects from an attribute
    in the data.
    """
    if attr in data:
        objs = [ client.searchUniqueKey(o.get('ref'), objindex) 
                 for o in data[attr].iter(tag) ]
        del data[attr]
    else:
        objs = []
    return objs

# ------------------------------------------------------------
# Creator functions
# ------------------------------------------------------------

def createObjs(data, insttype, objindex):
    """Create objects, generic method."""
    bean = client.typemap[insttype].BeanName
    for o in data:
        key = o.get('id')
        d = elem2dict(o, objindex)
        log.info("create %s %s ...", bean, d['name'])
        obj = client.new(insttype, **d)
        obj.create()
        obj.truncateRelations()
        objindex[key] = obj

def createBulkObjs(data, insttype, objindex):
    """Create objects, bulk method: use createMany, do not add them to
    the objindex."""
    bean = client.typemap[insttype].BeanName
    objs = []
    for o in data:
        d = elem2dict(o, objindex)
        objs.append(client.new(insttype, **d))
    log.info("create %d %ss ...", len(objs), bean)
    client.createMany(objs)

def createGroups(data, insttype, objindex):
    for o in data:
        key = o.get('id')
        d = elem2dict(o, objindex)
        users = getreflist(d, 'users', 'user', objindex)
        log.info("create Group %s ...", d['name'])
        obj = client.createGroup(d['name'], users)
        obj.truncateRelations()
        objindex[key] = obj

def createInstruments(data, insttype, objindex):
    bean = client.typemap[insttype].BeanName
    for o in data:
        key = o.get('id')
        d = elem2dict(o, objindex)
        instrsci = getreflist(d, 'instrumentScientists', 'user', objindex)
        log.info("create %s %s ...", bean, d['name'])
        obj = client.new(insttype, **d)
        obj.create()
        obj.addInstrumentScientists(instrsci)
        obj.truncateRelations()
        objindex[key] = obj

def createParameterTypes(data, insttype, objindex):
    bean = client.typemap[insttype].BeanName
    for o in data:
        key = o.get('id')
        d = elem2dict(o, objindex)
        strvals = getstrlist(d, 'permissibleStringValues', 'value')
        log.info("create %s %s ...", bean, d['name'])
        obj = client.new(insttype, **d)
        for v in strvals:
            o = client.new('permissibleStringValue', value=v)
            obj.permissibleStringValues.append(o)
        obj.create()
        obj.truncateRelations()
        objindex[key] = obj

def createInvestigations(data, insttype, objindex):
    bean = client.typemap[insttype].BeanName
    for o in data:
        key = o.get('id')
        d = elem2dict(o, objindex)
        params = getobjdatalist(d, 'parameters', objindex)
        instruments = getreflist(d, 'instruments', 'instrument', objindex)
        shifts = getobjdatalist(d, 'shifts', objindex)
        keywords = getstrlist(d, 'keywords', 'name')
        publications = getobjdatalist(d, 'publications', objindex)
        users = getobjdatalist(d, 'investigationUsers', objindex)
        log.info("create %s %s ...", bean, d['name'])
        obj = client.new(insttype, **d)
        for i in instruments:
            ii = client.new('investigationInstrument', instrument=i)
            obj.investigationInstruments.append(ii)
        for s in shifts:
            obj.shifts.append(client.new('shift', **s))
        for n in keywords:
            obj.keywords.append(client.new('keyword', name=n))
        for s in publications:
            obj.publications.append(client.new('publication', **s))
        for s in params:
            obj.parameters.append(client.new('investigationParameter', **s))
        for s in users:
            obj.investigationUsers.append(client.new('investigationUser', **s))
        obj.create()
        obj.truncateRelations()
        objindex[key] = obj

def createStudies(data, insttype, objindex):
    bean = client.typemap[insttype].BeanName
    for o in data:
        key = o.get('id')
        d = elem2dict(o, objindex)
        investigations = getreflist(d, 'studyInvestigations', 'investigation', 
                                    objindex)
        log.info("create %s %s ...", bean, d['name'])
        obj = client.new(insttype, **d)
        for s in investigations:
            o = client.new('studyInvestigation', investigation=s)
            obj.studyInvestigations.append(o)
        obj.create()
        obj.truncateRelations()
        objindex[key] = obj

def createSamples(data, insttype, objindex):
    bean = client.typemap[insttype].BeanName
    for o in data:
        key = o.get('id')
        d = elem2dict(o, objindex)
        params = getobjdatalist(d, 'parameters', objindex)
        log.info("create %s %s ...", bean, d['name'])
        obj = client.new(insttype, **d)
        for s in params:
            obj.parameters.append(client.new('sampleParameter', **s))
        obj.create()
        obj.truncateRelations()
        objindex[key] = obj

def createDatasets(data, insttype, objindex):
    bean = client.typemap[insttype].BeanName
    for o in data:
        key = o.get('id')
        d = elem2dict(o, objindex)
        params = getobjdatalist(d, 'parameters', objindex)
        log.info("create %s %s ...", bean, d['name'])
        obj = client.new(insttype, **d)
        for s in params:
            obj.parameters.append(client.new('datasetParameter', **s))
        obj.create()
        obj.truncateRelations()
        objindex[key] = obj

def createDatafiles(data, insttype, objindex):
    bean = client.typemap[insttype].BeanName
    for o in data:
        key = o.get('id')
        d = elem2dict(o, objindex)
        params = getobjdatalist(d, 'parameters', objindex)
        log.info("create %s %s ...", bean, d['name'])
        obj = client.new(insttype, **d)
        for s in params:
            obj.parameters.append(client.new('datafileParameter', **s))
        obj.create()
        obj.truncateRelations()
        objindex[key] = obj

def createDataCollections(data, insttype, objindex):
    bean = client.typemap[insttype].BeanName
    for o in data:
        key = o.get('id')
        d = elem2dict(o, objindex)
        params = getobjdatalist(d, 'parameters', objindex)
        datasets = getreflist(d, 'dataCollectionDatasets', 'dataset', objindex)
        datafiles = getreflist(d, 'dataCollectionDatafiles', 'datafile', 
                               objindex)
        log.info("create %s %s ...", bean, d['name'])
        obj = client.new(insttype, **d)
        for s in params:
            obj.parameters.append(client.new('dataCollectionParameter', **s))
        for ds in datasets:
            o = client.new('dataCollectionDataset', dataset=ds)
            obj.dataCollectionDatasets.append(o)
        for df in datafiles:
            o = client.new('dataCollectionDatafile', datafile=df)
            obj.dataCollectionDatafiles.append(o)
        obj.create()
        obj.truncateRelations()
        objindex[key] = obj

# ------------------------------------------------------------
# Create data at the ICAT server
# ------------------------------------------------------------

entitytypes = {
    'User': ('user', createObjs),
    'Grouping': ('grouping', createGroups),
    'Rule': ('rule', createBulkObjs),
    'PublicStep': ('publicStep', createBulkObjs),
    'Facility': ('facility', createObjs),
    'Instrument': ('instrument', createInstruments),
    'ParameterType': ('parameterType', createParameterTypes),
    'InvestigationType': ('investigationType', createObjs),
    'SampleType': ('sampleType', createObjs),
    'DatasetType': ('datasetType', createObjs),
    'DatafileFormat': ('datafileFormat', createObjs),
    'FacilityCycle': ('facilityCycle', createObjs),
    'Application': ('application', createObjs),
    'Investigation': ('investigation', createInvestigations),
    'Study': ('study', createStudies),
    'Sample': ('sample', createSamples),
    'Dataset': ('dataset', createDatasets),
    'Datafile': ('datafile', createDatafiles),
    'RelatedDatafile': ('relatedDatafile', createBulkObjs),
    'DataCollection': ('dataCollection', createDataCollections),
    'Job': ('job', createBulkObjs),
}

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

for event, element in etree.iterparse(sys.stdin, tag='data'):
    # Discard the old objindex when we start to process a new chunk.
    objindex = {}
    # We need to create the objects in file order so that objects are
    # processed before they get referenced by other objects coming
    # later in the file.  Process them in bunches of the same class.
    lasttag = None
    objs = []
    for obj in element:
        if lasttag != obj.tag:
            if lasttag is not None:
                try:
                    insttype, creator = entitytypes[lasttag]
                except KeyError:
                    raise RuntimeError("Unknown entity class '%s'" % lasttag)
                creator(objs, insttype, objindex)
            lasttag = obj.tag
            objs = []
        objs.append(obj)
    if lasttag is not None:
        try:
            insttype, creator = entitytypes[lasttag]
        except KeyError:
            raise RuntimeError("Unknown entity class '%s'" % lasttag)
        creator(objs, insttype, objindex)
    element.clear()
