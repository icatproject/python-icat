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
import logging
from icat.dumpfile_xml import XMLDumpFileWriter as DumpFileWriter

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

config = icat.config.Config()
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
if client.apiversion < '4.3':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.3.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


def dumpobjs(dumpfile, tag, searchexp, keyindex):
    i = 0
    objs = client.search(searchexp)
    for obj in sorted(objs, key=icat.entity.Entity.__sortkey__):
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
        dumpfile.add(tag, k, obj, keyindex)


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


authtypes = [('user', "User"), 
             ('grouping', "Grouping INCLUDE UserGroup, User"),
             ('rule', "Rule INCLUDE Grouping"),
             ('publicStep', "PublicStep")]
statictypes = [('facility', "Facility"),
               ('instrument', 
                "Instrument INCLUDE Facility, InstrumentScientist, User"),
               ('parameterType', 
                "ParameterType INCLUDE Facility, PermissibleStringValue"),
               ('investigationType', "InvestigationType INCLUDE Facility"),
               ('sampleType', "SampleType INCLUDE Facility"),
               ('datasetType', "DatasetType INCLUDE Facility"),
               ('datafileFormat', "DatafileFormat INCLUDE Facility"),
               ('facilityCycle', "FacilityCycle INCLUDE Facility"),
               ('application', "Application INCLUDE Facility")]
investtypes = [('investigation', 
                "SELECT i FROM Investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE i.facility, i.type AS it, it.facility, "
                "i.investigationInstruments AS ii, "
                "ii.instrument AS iii, iii.facility, "
                "i.shifts, i.keywords, i.publications, "
                "i.investigationUsers AS iu, iu.user, "
                "i.parameters AS ip, ip.type AS ipt, ipt.facility"),
               ('study', 
                "SELECT o FROM Study o "
                "JOIN o.studyInvestigations si JOIN si.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.user, "
                "o.studyInvestigations AS si, si.investigation"),
               ('sample', 
                "SELECT o FROM Sample o JOIN o.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.investigation, o.type AS ot, ot.facility, "
                "o.parameters AS op, op.type AS opt, opt.facility"),
               ('dataset', 
                "SELECT o FROM Dataset o JOIN o.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.investigation, o.type AS ot, ot.facility, o.sample, "
                "o.parameters AS op, op.type AS opt, opt.facility"),
               ('datafile', 
                "SELECT o FROM Datafile o "
                "JOIN o.dataset ds JOIN ds.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.dataset, o.datafileFormat AS dff, dff.facility, "
                "o.parameters AS op, op.type AS opt, opt.facility")]
othertypes = [('relatedDatafile', 
               "SELECT o FROM RelatedDatafile o "
               "INCLUDE o.sourceDatafile AS sdf, sdf.dataset AS sds, "
               "sds.investigation AS si, si.facility, "
               "o.destDatafile AS ddf, ddf.dataset AS dds, "
               "dds.investigation AS di, di.facility"),
              ('dataCollection', 
               "SELECT o FROM DataCollection o "
               "INCLUDE o.dataCollectionDatasets AS ds, ds.dataset AS dsds, "
               "dsds.investigation AS dsi, dsi.facility, "
               "o.dataCollectionDatafiles AS df, "
               "df.datafile AS dfdf, dfdf.dataset AS dfds, "
               "dfds.investigation AS dfi, dfi.facility, "
               "o.%s AS op, op.type" % datacolparamname),
              ('job', 
               "SELECT o FROM Job o "
               "INCLUDE o.application AS app, app.facility, "
               "o.inputDataCollection, o.outputDataCollection")]

dumpfile = DumpFileWriter(sys.stdout)
dumpfile.head(conf.url, str(client.apiversion))

keyindex = {}
dumpfile.startdata()
for name, searchexp in authtypes:
    dumpobjs(dumpfile, name, searchexp, keyindex)

keyindex = {}
dumpfile.startdata()
for name, searchexp in statictypes:
    dumpobjs(dumpfile, name, searchexp, keyindex)

# Dump the investigations each in their own document
investsearch = "SELECT i FROM Investigation i INCLUDE i.facility"
investigations = [(i.facility.id, i.name, i.visitId) 
                  for i in client.search(investsearch)]
investigations.sort()
for inv in investigations:
    keyindex = {}
    dumpfile.startdata()
    for name, searchexp in investtypes:
        dumpobjs(dumpfile, name, searchexp % inv, keyindex)

keyindex = {}
dumpfile.startdata()
for name, searchexp in othertypes:
    dumpobjs(dumpfile, name, searchexp, keyindex)

dumpfile.finalize()
