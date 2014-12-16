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
#  + The partition of the data into chunks ist static.  It should
#    rather be dynamic, e.g. chunks should be splitted if the number
#    of objects in them grows too large.
#  + The serialization of the following entity types has not yet been
#    tested: DataCollectionParameter, DatafileParameter,
#    DatasetParameter, FacilityCycle, InvestigationParameter,
#    ParameterType, PermissibleStringValue, Publication,
#    RelatedDatafile, SampleParameter, Shift, Study,
#    StudyInvestigation.
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
                           "WHERE i.id in (%d) "
                           "INCLUDE i.facility, i.type.facility, "
                           "i.investigationInstruments AS ii, "
                           "ii.instrument.facility, "
                           "i.shifts, i.keywords, i.publications, "
                           "i.investigationUsers AS iu, iu.user, "
                           "i.parameters AS ip, ip.type.facility")
else:
    investigationsearch = ("SELECT i FROM Investigation i "
                           "WHERE i.id in (%d) "
                           "INCLUDE i.facility, i.type.facility, "
                           "i.investigationInstruments AS ii, "
                           "ii.instrument.facility, "
                           "i.shifts, i.keywords, i.publications, "
                           "i.investigationUsers AS iu, iu.user, "
                           "i.investigationGroups AS ig, ig.grouping, "
                           "i.parameters AS ip, ip.type.facility")

authtypes = [("User ORDER BY name"), 
             ("Grouping ORDER BY name INCLUDE UserGroup, User"),
             ("SELECT r FROM Rule r WHERE r.grouping IS NULL ORDER BY r.what"),
             ("SELECT r FROM Rule r JOIN r.grouping g "
              "ORDER BY g.name, r.what INCLUDE r.grouping"),
             ("PublicStep ORDER BY origin, field")]
statictypes = [("Facility ORDER BY name"),
               ("SELECT o FROM Instrument o JOIN o.facility f "
                "ORDER BY f.name, o.name "
                "INCLUDE o.facility, o.instrumentScientists.user"),
               ("SELECT o FROM ParameterType o JOIN o.facility f "
                "ORDER BY f.name, o.name, o.units "
                "INCLUDE o.facility, o.permissibleStringValues"),
               ("SELECT o FROM InvestigationType o JOIN o.facility f "
                "ORDER BY f.name, o.name INCLUDE o.facility"),
               ("SELECT o FROM SampleType o JOIN o.facility f "
                "ORDER BY f.name, o.name, o.molecularFormula "
                "INCLUDE o.facility"),
               ("SELECT o FROM DatasetType o JOIN o.facility f "
                "ORDER BY f.name, o.name INCLUDE o.facility"),
               ("SELECT o FROM DatafileFormat o JOIN o.facility f "
                "ORDER BY f.name, o.name, o.version INCLUDE o.facility"),
               ("SELECT o FROM FacilityCycle o JOIN o.facility f "
                "ORDER BY f.name, o.name INCLUDE o.facility"),
               ("SELECT o FROM Application o JOIN o.facility f "
                "ORDER BY f.name, o.name, o.version INCLUDE o.facility")]
investtypes = [(investigationsearch),
               ("SELECT o FROM Sample o JOIN o.investigation i "
                "WHERE i.id = %d ORDER BY o.name "
                "INCLUDE o.investigation, o.type.facility, "
                "o.parameters AS op, op.type.facility"),
               ("SELECT o FROM Dataset o JOIN o.investigation i "
                "WHERE i.id = %d ORDER BY o.name "
                "INCLUDE o.investigation, o.type.facility, o.sample, "
                "o.parameters AS op, op.type.facility"),
               ("SELECT o FROM Datafile o "
                "JOIN o.dataset ds JOIN ds.investigation i "
                "WHERE i.id = %d ORDER BY ds.name, o.name "
                "INCLUDE o.dataset, o.datafileFormat.facility, "
                "o.parameters AS op, op.type.facility")]
# It is in principle not possible to get a consistent ordering of
# DataCollection using an ORDER BY clause in the search expression.
# In the case of RelatedDatafile, it is possible in theory, but the
# ORDER BY clause would be rather complicated.  Fall back on sorting
# by id in these cases.
othertypes = [("SELECT o FROM Study o ORDER BY o.name, o.id "
               "INCLUDE o.user, "
               "o.studyInvestigations AS si, si.investigation"),
              ("SELECT o FROM RelatedDatafile o ORDER BY o.id "
               "INCLUDE o.sourceDatafile AS sdf, "
               "sdf.dataset.investigation.facility, "
               "o.destDatafile AS ddf, "
               "ddf.dataset.investigation.facility"),
              ("SELECT o FROM DataCollection o ORDER BY o.id "
               "INCLUDE o.dataCollectionDatasets AS ds, "
               "ds.dataset.investigation.facility, "
               "o.dataCollectionDatafiles AS df, "
               "df.datafile.dataset.investigation.facility, "
               "o.%s AS op, op.type" % datacolparamname),
              ("SELECT o FROM Job o JOIN o.application a JOIN a.facility f "
               "ORDER BY f.name, a.name, o.arguments, o.id "
               "INCLUDE o.application.facility, "
               "o.inputDataCollection, o.outputDataCollection")]

with open_dumpfile(client, conf.file, conf.format, 'w') as dumpfile:
    dumpfile.writedata(authtypes)
    dumpfile.writedata(statictypes)
    # Dump the investigations each in their own chunk
    investsearch = ("SELECT i.id FROM Investigation i JOIN i.facility f "
                    "ORDER BY f.name, i.name, i.visitId")
    for i in client.searchChunked(investsearch):
        dumpfile.writedata([ se % (i) for se in investtypes ])
    dumpfile.writedata(othertypes)
