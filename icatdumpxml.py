#! /usr/bin/python
#
# Dump the content of the ICAT to a XML document to stdout.  This is
# experimental and should be merged back with icatdump.py later on.
#
# The following items are deliberately not included in the output:
#  + Log objects,
#  + the attributes id, createId, createTime, modId, and modTime.
#
# Known issues and limitations:
#  + This script requires ICAT 4.3.0 or newer.
#  + The serialization of the following entity types has not yet been
#    tested: Application, DataCollection, DataCollectionDatafile,
#    DataCollectionDataset, DataCollectionParameter,
#    DatafileParameter, DatasetParameter, FacilityCycle,
#    InvestigationParameter, Job, ParameterType,
#    PermissibleStringValue, PublicStep, Publication, RelatedDatafile,
#    SampleParameter, Shift, Study, StudyInvestigation.
#  + The data in the ICAT server must not be modified while this
#    script is retrieving it.  Otherwise the script may fail or the
#    dumpfile be inconsistent.  There is not too much that can be done
#    about this.  A database dump is a snapshot after all.  The
#    picture will be blurred if the subject is moving while we take
#    it.
#

import sys
import icat
import icat.config
import datetime
import logging
import collections
from lxml import etree

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

config = icat.config.Config()
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
if client.apiversion < '4.3':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.3.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


keyindex = {}

class ElementList(collections.MutableSequence):
    def __init__(self):
        super(ElementList, self).__init__()
        self.elemlist = []

    def __len__(self):
        return len(self.elemlist)

    def __getitem__(self, index):
        item = self.elemlist.__getitem__(index)
        if isinstance(index, slice):
            return [ i['elem'] for i in item ]
        else:
            return item['elem']

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            value = [{'elem':v, 'sortkey':v} for v in value]
        else:
            value = {'elem':value, 'sortkey':value}
        self.elemlist.__setitem__(index, value)

    def __delitem__(self, index):
        self.elemlist.__delitem__(index)

    def insert(self, index, value, sortkey=None):
        if sortkey is None:
            sortkey = value
        self.elemlist.insert(index, {'elem':value, 'sortkey':sortkey})

    def append(self, value, sortkey=None):
        if sortkey is None:
            sortkey = value
        self.elemlist.append({'elem':value, 'sortkey':sortkey})

    def reverse(self):
        self.elemlist.reverse()

    def sort(self):
        self.elemlist.sort(key = lambda e:e['sortkey'])

    def add_strvals(self, tag, values):
        for v in values:
            elem = etree.Element(tag)
            elem.text = v
            self.append(elem, v)

    def add_entityrefs(self, tag, entities):
        for e in entities:
            key = e.getUniqueKey(keyindex=keyindex)
            elem = etree.Element(tag, ref=key)
            self.append(elem, key)

    def as_element(self, tag):
        elem = etree.Element(tag)
        self.sort()
        for e in self:
            elem.append(e)
        return elem

def entityattrelem(e):
    """Convert an entity to an etree.Element, not considering the relations."""
    if e.BeanName is None:
        raise TypeError("Cannot convert an entity of abstract type '%s'." 
                        % e.instancetype)
    d = etree.Element(e.BeanName)
    for attr in e.InstAttr:
        if attr == 'id':
            continue
        v = getattr(e, attr, None)
        if v is None:
            pass
        elif isinstance(v, long) or isinstance(v, int):
            v = str(v)
        elif isinstance(v, datetime.datetime):
            if v.tzinfo is not None and v.tzinfo.utcoffset(v) is not None:
                # v has timezone info, assume v.isoformat() to have a
                # valid timezone suffix.
                v = v.isoformat()
            else:
                # v has no timezone info, assume it to be UTC, append
                # the corresponding timezone suffix.
                v = v.isoformat() + 'Z'
        else:
            try:
                v = str(v)
            except UnicodeError:
                v = unicode(v)
        etree.SubElement(d, attr).text = v
    return d

def entityelem(e):
    """Convert an entity to an etree.Element."""
    d = entityattrelem(e)
    for attr in e.InstRel:
        o = getattr(e, attr, None)
        if o is not None:
            k = o.getUniqueKey(keyindex=keyindex)
            etree.SubElement(d, attr, ref=k)
        else:
            etree.SubElement(d, attr)
    return d

def entityparamelem(e):
    """Convert an entity including its parameters to an etree.Element."""
    d = entityelem(e)
    params = ElementList()
    for i in e.parameters:
        p = entityattrelem(i)
        t = i.type.getUniqueKey(keyindex=keyindex)
        etree.SubElement(p, 'type', ref=t)
        params.append(p, t)
    d.append(params.as_element('parameters'))
    return d

def groupelem(e):
    """Convert a group including its users to an etree.Element."""
    d = entityelem(e)
    users = ElementList()
    users.add_entityrefs('user', [ug.user for ug in e.userGroups])
    d.append(users.as_element('users'))
    return d

def instrumentelem(e):
    """Convert an instrument including its instrument scientists to an
    etree.Element."""
    d = entityelem(e)
    users = ElementList()
    users.add_entityrefs('user', [uis.user for uis in e.instrumentScientists])
    d.append(users.as_element('instrumentScientists'))
    return d

def parametertypeelem(e):
    """Convert an parameter type including its permissible string
    values to an etree.Element."""
    d = entityelem(e)
    strvals = ElementList()
    strvals.add_strvals('value', [sv.value for sv in e.permissibleStringValues])
    d.append(strvals.as_element('permissibleStringValues'))
    return d

def investigationelem(e):
    """Convert an investigation including its instruments, shifts,
    keywords, publications, investigation users, and parameters to an
    etree.Element."""
    d = entityparamelem(e)

    instruments = ElementList()
    l = [ii.instrument for ii in e.investigationInstruments]
    instruments.add_entityrefs('instrument', l)
    d.append(instruments.as_element('instruments'))

    shifts = ElementList()
    for s in e.shifts:
        shifts.append(entityattrelem(s), (s.startDate,s.endDate))
    d.append(shifts.as_element('shifts'))

    keywords = ElementList()
    keywords.add_strvals('name', [i.name for i in e.keywords])
    d.append(keywords.as_element('keywords'))

    publications = ElementList()
    for p in e.publications:
        publications.append(entityattrelem(p), p.fullReference)
    d.append(publications.as_element('publications'))

    invusers = ElementList()
    for i in e.investigationUsers:
        iu = entityattrelem(i)
        u = i.user.getUniqueKey(keyindex=keyindex)
        etree.SubElement(iu, 'user', ref=u)
        invusers.append(iu, u)
    d.append(invusers.as_element('investigationUsers'))

    return d

def studyelem(e):
    """Convert a study to an etree.Element."""
    d = entityelem(e)
    studyInvest = ElementList()
    l = [si.investigation for si in e.studyInvestigations]
    studyInvest.add_entityrefs('investigation', l)
    d.append(studyInvest.as_element('studyInvestigations'))
    return d

def datacollectionelem(e):
    """Convert a data collection to an etree.Element."""
    d = entityparamelem(e)

    datasets = ElementList()
    l = [i.dataset for i in e.dataCollectionDatasets]
    datasets.add_entityrefs('dataset', l)
    d.append(datasets.as_element('dataCollectionDatasets'))

    datafiles = ElementList()
    l = [i.datafile for i in e.dataCollectionDatafiles]
    datafiles.add_entityrefs('datafile', l)
    d.append(datafiles.as_element('dataCollectionDatafiles'))

    return d

def getobjs(data, name, convert, searchexp, reindex):
    objs = []

    for e in client.search(searchexp):
        k = e.getUniqueKey(autoget=False, keyindex=keyindex)
        elem = convert(e)
        # Entities without a constraint will use their id to form the
        # unique key as a last resort.  But we want the keys to have a
        # well defined order, independent from the id.  For the
        # concerned entities, reindex is set to the list of attributes
        # that shall determine the sort order.
        if reindex:
            sortkey = []
            for a in reindex:
                v = getattr(e, a, None)
                if v is None:
                    v = '\x00'
                elif isinstance(v, icat.entity.Entity):
                    v = v.getUniqueKey(autoget=False, keyindex=keyindex)
                sortkey.append(v)
            sortkey.append(k)
        else:
            sortkey = k
        objs.append({ 'elem':elem, 'key':k, 'sortkey':sortkey })

    objs.sort(key = lambda o:o['sortkey'])

    # If reindex is set, we also want to get rid of the id in the key.
    if reindex:
        idindex = { k:i for i,k in keyindex.iteritems() }
        i = 0
        for o in objs:
            i += 1
            n = "%s_%08d" % (name, i)
            keyindex[idindex[o['key']]] = n
            o['key'] = n

    # Prepare the result
    for o in objs:
        elem = o['elem']
        elem.set('id', o['key'])
        data.append(elem)


# We write the data in chunks (or documents in YAML terminology).
# This way we can avoid having the whole file, e.g. the complete
# inventory of the ICAT, at once in memory.  We want to keep these
# chunks small enough, but at the same time keep as many relations
# between objects as possible local in a chunk.  See the comment in
# icatrestore for an explanation why this is needed.  The partition
# used here is the following:
#  1. One chunk with all objects that define authorization (User,
#     Group, Rule, PublicStep).
#  2. All static content in one chunk, e.g. all objects not related to
#     individual investigations and that need to be present, before we
#     can add investigations.
#  3. The investigation data.  All content related to individual
#     investigations.  Each investigation with all its data in one
#     single chunk on its own.
#  4. One last chunk with all remaining stuff (RelatedDatafile,
#     DataCollection, Job).

# Compatibility ICAT 4.3.0 vs. ICAT 4.3.1 and later: name of the
# parameters relation in DataCollection.
if client.apiversion < '4.3.1':
    datacolparamname = 'dataCollectionParameters'
else:
    datacolparamname = 'parameters'

authtypes = [('User', entityelem, "User", False), 
             ('Group', groupelem, "Grouping INCLUDE UserGroup, User", False),
             ('Rule', entityelem, "Rule INCLUDE Grouping", 
              ['grouping', 'what']),
             ('PublicStep', entityelem, "PublicStep", False)]
statictypes = [('Facility', entityelem, "Facility", False),
               ('Instrument', instrumentelem, 
                "Instrument INCLUDE Facility, InstrumentScientist, User", 
                False),
               ('ParameterType', parametertypeelem, 
                "ParameterType INCLUDE Facility, PermissibleStringValue", 
                False),
               ('InvestigationType', entityelem, 
                "InvestigationType INCLUDE Facility", False),
               ('SampleType', entityelem, "SampleType INCLUDE Facility", 
                False),
               ('DatasetType', entityelem, "DatasetType INCLUDE Facility", 
                False),
               ('DatafileFormat', entityelem, 
                "DatafileFormat INCLUDE Facility", False),
               ('FacilityCycle', entityelem, "FacilityCycle INCLUDE Facility", 
                False),
               ('Application', entityelem, "Application INCLUDE Facility", 
                False)]
investtypes = [('Investigation', investigationelem, 
                "SELECT i FROM Investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE i.facility, i.type, "
                "i.investigationInstruments AS ii, ii.instrument, "
                "i.shifts, i.keywords, i.publications, "
                "i.investigationUsers AS iu, iu.user, "
                "i.parameters AS ip, ip.type", 
                False),
               ('Study', studyelem, 
                "SELECT o FROM Study o "
                "JOIN o.studyInvestigations si JOIN si.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.user, "
                "o.studyInvestigations AS si, si.investigation", 
                ['name']),
               ('Sample', entityparamelem, 
                "SELECT o FROM Sample o "
                "JOIN o.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.investigation, o.type, "
                "o.parameters AS op, op.type", 
                False),
               ('Dataset', entityparamelem, 
                "SELECT o FROM Dataset o "
                "JOIN o.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.investigation, o.type, o.sample, "
                "o.parameters AS op, op.type", 
                False),
               ('Datafile', entityparamelem, 
                "SELECT o FROM Datafile o "
                "JOIN o.dataset ds JOIN ds.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.dataset, o.datafileFormat, "
                "o.parameters AS op, op.type", 
                False)]
othertypes = [('RelatedDatafile', entityelem, 
               "SELECT o FROM RelatedDatafile o "
               "INCLUDE o.sourceDatafile, o.destDatafile", 
               False),
              ('DataCollection', datacollectionelem, 
               "SELECT o FROM DataCollection o "
               "INCLUDE o.dataCollectionDatasets AS ds, ds.dataset, "
               "o.dataCollectionDatafiles AS df, df.datafile, "
               "o.%s AS op, op.type" % datacolparamname, 
               ['dataCollectionDatasets', 'dataCollectionDatafiles']),
              ('Job', entityelem, 
               "SELECT o FROM Job o INCLUDE o.application, "
               "o.inputDataCollection, o.outputDataCollection", 
               ['application', 'arguments'])]

date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
head = etree.Element("head")
etree.SubElement(head, "date").text = date
etree.SubElement(head, "service").text = conf.url
etree.SubElement(head, "apiversion").text = str(client.apiversion)
etree.SubElement(head, "generator").text = ("icatdump (python-icat %s)" 
                                            % icat.__version__)

print "<icatdump>"
print etree.tostring(head, pretty_print=True),

data = etree.Element("data")
for name, convert, searchexp, reindex in authtypes:
    getobjs(data, name, convert, searchexp, reindex)
if len(data) > 0:
    print etree.tostring(data, pretty_print=True),

data = etree.Element("data")
for name, convert, searchexp, reindex in statictypes:
    getobjs(data, name, convert, searchexp, reindex)
if len(data) > 0:
    print etree.tostring(data, pretty_print=True),

# Dump the investigations each in their own document
investsearch = "SELECT i FROM Investigation i INCLUDE i.facility"
investigations = [(i.facility.id, i.name, i.visitId) 
                  for i in client.search(investsearch)]
investigations.sort()
for inv in investigations:
    data = etree.Element("data")
    for name, convert, searchexp, reindex in investtypes:
        getobjs(data, name, convert, searchexp % inv, reindex)
    if len(data) > 0:
        print etree.tostring(data, pretty_print=True),

data = etree.Element("data")
for name, convert, searchexp, reindex in othertypes:
    getobjs(data, name, convert, searchexp, reindex)
if len(data) > 0:
    print etree.tostring(data, pretty_print=True),

print "</icatdump>"
