#! /usr/bin/python
#
# Dump the content of the ICAT to a file or to stdout.
#
# The following items are deliberately not included in the output:
#  + Log objects,
#  + the attributes id, createId, createTime, modId, and modTime.
#
# Known issues and limitations:
#  + This script requires ICAT 4.3.0 or newer.
#  + IDS is not supported: the script only dumps the meta data stored
#    in the ICAT, not the content of the files stored in the IDS.
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

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

config = icat.config.Config()
config.add_variable('file', ("-o", "--outputfile"), 
                    dict(help="output file name or '-' for stdout"),
                    default='-')
config.add_variable('format', ("-f", "--format"), 
                    dict(help="output file format", choices=['XML', 'YAML']),
                    default='YAML')
conf = config.getconfig()

if conf.format == 'YAML':
    from icat.dumpfile_yaml import YAMLDumpFileWriter as DumpFileWriter
elif conf.format == 'XML':
    from icat.dumpfile_xml import XMLDumpFileWriter as DumpFileWriter
else:
    raise icat.ConfigError("Unknown dump file format '%s'." % conf.format)

client = icat.Client(conf.url, **conf.client_kwargs)
if client.apiversion < '4.2.99':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.3.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


# We write the data in chunks (separate YAML documents in the case of
# a YAML dump file, content of separate data elements in the case of
# XML).  This way we can avoid having the whole file, e.g. the
# complete inventory of the ICAT, at once in memory.  We want to keep
# these chunks small enough to fit into memory, but at the same time
# large enough to keep as many relations between objects as possible
# local in a chunk.  See the comment in icatrestore for an explanation
# why this is needed.  The partition used here is the following:
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


# Lists of search expressions.
# 
# These lists control which objects get written to the dump file and
# how this file is organized.  Each list defines the objects that get
# written to one chunk in the output.
# 
# There is some degree of flexibility: an object may include related
# objects in an one to many relation, just by including it in the
# search expression.  In this case, these related objects should not
# be listed on their own again.  For instance, here we include
# UserGroup with Grouping.  UserGroups are included in their
# respective grouping in the dump file.  We do do not have an own
# entry for UserGroup in the lists.  We could also have included Rules
# in Grouping, but we chosed to list them separately.  If we would
# have included Rules with Grouping, we still would need a list entry
# for Rule, but then we would need to search only for rules where
# grouping is NULL.
# 
# Objects related in a many to one relation must always be included in
# the search expression.  This is also true if the object is
# indirectly related to one of the included objects.  In this case,
# only a reference to the related object will be included in the dump
# file.  The related object must have its own list entry.

# Compatibility ICAT 4.3.* vs. ICAT 4.4.0 and later: include
# InvestigationGroups.
if client.apiversion < '4.3.99':
    investigationsearch = ("SELECT i FROM Investigation i "
                           "WHERE i.facility.id = %d AND i.name = '%s' "
                           "AND i.visitId = '%s' "
                           "INCLUDE i.facility, i.type AS it, it.facility, "
                           "i.investigationInstruments AS ii, "
                           "ii.instrument AS iii, iii.facility, "
                           "i.shifts, i.keywords, i.publications, "
                           "i.investigationUsers AS iu, iu.user, "
                           "i.parameters AS ip, ip.type AS ipt, ipt.facility")
else:
    investigationsearch = ("SELECT i FROM Investigation i "
                           "WHERE i.facility.id = %d AND i.name = '%s' "
                           "AND i.visitId = '%s' "
                           "INCLUDE i.facility, i.type AS it, it.facility, "
                           "i.investigationInstruments AS ii, "
                           "ii.instrument AS iii, iii.facility, "
                           "i.shifts, i.keywords, i.publications, "
                           "i.investigationUsers AS iu, iu.user, "
                           "i.investigationGroups AS ig, ig.grouping, "
                           "i.parameters AS ip, ip.type AS ipt, ipt.facility")

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
investtypes = [(investigationsearch),
               ("SELECT o FROM Sample o JOIN o.investigation i "
                "WHERE i.facility.id = %d AND i.name = '%s' "
                "AND i.visitId = '%s' "
                "INCLUDE o.investigation, o.type AS ot, ot.facility, "
                "o.parameters AS op, op.type AS opt, opt.facility"),
               ("SELECT o FROM Dataset o JOIN o.investigation i "
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
othertypes = [("SELECT o FROM Study o "
               "INCLUDE o.user, "
               "o.studyInvestigations AS si, si.investigation"),
              ("SELECT o FROM RelatedDatafile o "
               "INCLUDE o.sourceDatafile AS sdf, sdf.dataset AS sds, "
               "sds.investigation AS si, si.facility, "
               "o.destDatafile AS ddf, ddf.dataset AS dds, "
               "dds.investigation AS di, di.facility"),
              ("SELECT o FROM DataCollection o "
               "INCLUDE o.dataCollectionDatasets AS ds, ds.dataset AS dsds, "
               "dsds.investigation AS dsi, dsi.facility, "
               "o.dataCollectionDatafiles AS df, "
               "df.datafile AS dfdf, dfdf.dataset AS dfds, "
               "dfds.investigation AS dfi, dfi.facility, "
               "o.%s AS op, op.type" % datacolparamname),
              ("SELECT o FROM Job o "
               "INCLUDE o.application AS app, app.facility, "
               "o.inputDataCollection, o.outputDataCollection")]

if conf.file == "-":
    f = sys.stdout
else:
    f = open(conf.file, 'w')
dumpfile = DumpFileWriter(client, f)
dumpfile.head(conf.url, str(client.apiversion))

dumpfile.writedata(authtypes)

dumpfile.writedata(statictypes)

# Dump the investigations each in their own chunk
investsearch = "SELECT i FROM Investigation i INCLUDE i.facility"
investigations = [(i.facility.id, i.name, i.visitId) 
                  for i in client.search(investsearch)]
investigations.sort()
for inv in investigations:
    dumpfile.writedata([ se % inv for se in investtypes])

dumpfile.writedata(othertypes)

dumpfile.finalize()
f.close()
