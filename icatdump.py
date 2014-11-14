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
#  + It is assumed that for each Dataset ds in the ICAT where
#    ds.sample is not NULL, the condition
#    ds.investigation == ds.sample.investigation holds.  If this
#    is not met, this script will fail with a DataConsistencyError.
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

import logging
import icat
import icat.config
from icat.dumpfile import open_dumpfile
import icat.dumpfile_xml
import icat.dumpfile_yaml

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

formats = icat.dumpfile.Backends.keys()
config = icat.config.Config()
config.add_variable('file', ("-o", "--outputfile"), 
                    dict(help="output file name or '-' for stdout"),
                    default='-')
config.add_variable('format', ("-f", "--format"), 
                    dict(help="output file format", choices=formats),
                    default='YAML')
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
if client.apiversion < '4.2.99':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.3.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


# The data is written in chunks, see the documentation of
# icat.dumpfile for details why this is needed.  The partition used
# here is the following:
#
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

with open_dumpfile(client, conf.file, conf.format, 'w') as dumpfile:
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
