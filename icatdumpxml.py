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

import icat
import icat.config
import datetime
import logging
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


sortkey = icat.entity.Entity.__sortkey__

def entityelem(e, tag=None, keyindex=None):
    """Convert an entity object to an etree.Element."""
    if tag is None:
        tag = e.instancetype
    d = etree.Element(tag)

    for attr in sorted(e.InstAttr):
        if attr == 'id':
            continue
        v = getattr(e, attr, None)
        if v is None:
            continue
        elif isinstance(v, bool):
            v = str(v).lower()
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

    for attr in sorted(e.InstRel):
        o = getattr(e, attr, None)
        if o is not None:
            k = o.getUniqueKey(autoget=False, keyindex=keyindex)
            etree.SubElement(d, attr, ref=k)

    for attr in sorted(e.InstMRel):
        for o in sorted(getattr(e, attr), key=sortkey):
            d.append(entityelem(o, tag=attr, keyindex=keyindex))

    return d

def getobjs(data, searchexp, keyindex=None):
    i = 0
    for obj in sorted(client.search(searchexp), key=sortkey):
        # Entities without a constraint will use their id to form the
        # unique key as a last resort.  But we want the keys to have a
        # well defined order, independent from the id.  Use a simple
        # numbered key for the concerned entity types.
        if 'id' in obj.Constraint:
            i += 1
            k = "%s_%08d" % (obj.BeanName, i)
            keyindex[obj.id] = k
        else:
            k = obj.getUniqueKey(autoget=False, keyindex=keyindex)
        elem = entityelem(obj, keyindex=keyindex)
        elem.set('id', k)
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

authtypes = [("User"), 
             ("Grouping INCLUDE UserGroup, User"),
             ("Rule INCLUDE Grouping"),
             ("PublicStep")]
statictypes = [("Facility"),
               ("Instrument INCLUDE Facility, InstrumentScientist, User"),
               ("ParameterType INCLUDE Facility, PermissibleStringValue"),
               ("InvestigationType INCLUDE Facility"),
               ("SampleType INCLUDE Facility"),
               ("DatasetType INCLUDE Facility"),
               ("DatafileFormat INCLUDE Facility"),
               ("FacilityCycle INCLUDE Facility"),
               ("Application INCLUDE Facility")]
investtypes = [("SELECT i FROM Investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE i.facility, i.type AS it, it.facility, "
                "i.investigationInstruments AS ii, "
                "ii.instrument AS iii, iii.facility, "
                "i.shifts, i.keywords, i.publications, "
                "i.investigationUsers AS iu, iu.user, "
                "i.parameters AS ip, ip.type AS ipt, ipt.facility"),
               ("SELECT o FROM Study o "
                "JOIN o.studyInvestigations si JOIN si.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.user, "
                "o.studyInvestigations AS si, si.investigation"),
               ("SELECT o FROM Sample o "
                "JOIN o.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.investigation, o.type AS ot, ot.facility, "
                "o.parameters AS op, op.type AS opt, opt.facility"),
               ("SELECT o FROM Dataset o "
                "JOIN o.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.investigation, o.type AS ot, ot.facility, o.sample, "
                "o.parameters AS op, op.type AS opt, opt.facility"),
               ("SELECT o FROM Datafile o "
                "JOIN o.dataset ds JOIN ds.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.dataset, o.datafileFormat AS dff, dff.facility, "
                "o.parameters AS op, op.type AS opt, opt.facility")]
othertypes = [("SELECT o FROM RelatedDatafile o "
               "INCLUDE o.sourceDatafile, o.destDatafile"),
              ("SELECT o FROM DataCollection o "
               "INCLUDE o.dataCollectionDatasets AS ds, ds.dataset, "
               "o.dataCollectionDatafiles AS df, df.datafile, "
               "o.%s AS op, op.type" % datacolparamname),
              ("SELECT o FROM Job o INCLUDE o.application, "
               "o.inputDataCollection, o.outputDataCollection")]

date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
head = etree.Element("head")
etree.SubElement(head, "date").text = date
etree.SubElement(head, "service").text = conf.url
etree.SubElement(head, "apiversion").text = str(client.apiversion)
etree.SubElement(head, "generator").text = ("icatdump (python-icat %s)" 
                                            % icat.__version__)

print '<?xml version="1.0" encoding="utf-8"?>\n<icatdump>'
print etree.tostring(head, pretty_print=True),

keyindex = {}
data = etree.Element("data")
for searchexp in authtypes:
    getobjs(data, searchexp, keyindex=keyindex)
if len(data) > 0:
    print etree.tostring(data, pretty_print=True),

keyindex = {}
data = etree.Element("data")
for searchexp in statictypes:
    getobjs(data, searchexp, keyindex=keyindex)
if len(data) > 0:
    print etree.tostring(data, pretty_print=True),

# Dump the investigations each in their own document
investsearch = "SELECT i FROM Investigation i INCLUDE i.facility"
investigations = [(i.facility.id, i.name, i.visitId) 
                  for i in client.search(investsearch)]
investigations.sort()
for inv in investigations:
    keyindex = {}
    data = etree.Element("data")
    for searchexp in investtypes:
        getobjs(data, searchexp % inv, keyindex=keyindex)
    if len(data) > 0:
        print etree.tostring(data, pretty_print=True),

keyindex = {}
data = etree.Element("data")
for searchexp in othertypes:
    getobjs(data, searchexp, keyindex=keyindex)
if len(data) > 0:
    print etree.tostring(data, pretty_print=True),

print "</icatdump>"
