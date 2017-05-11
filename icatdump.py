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
#  + The data in the ICAT server must not be modified while this
#    script is retrieving it.  Otherwise the script may fail or the
#    dumpfile be inconsistent.  There is not too much that can be done
#    about this.  A database dump is a snapshot after all.  The
#    picture will be blurred if the subject is moving while we take
#    it.
#  + icatdump fails for Study if ICAT is older then 4.6.0.  This is a
#    bug in icat.server, see Issue icatproject/icat.server#155.
#

import logging
import icat
import icat.config
from icat.query import Query
from icat.dumpfile import open_dumpfile
try:
    import icat.dumpfile_xml
except ImportError:
    pass
try:
    import icat.dumpfile_yaml
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

formats = icat.dumpfile.Backends.keys()
if len(formats) == 0:
    raise RuntimeError("No datafile backends available.")

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
inv_includes = { "facility", "type.facility", "investigationInstruments", 
                 "investigationInstruments.instrument.facility", "shifts", 
                 "keywords", "publications", "investigationUsers", 
                 "investigationUsers.user", "parameters", 
                 "parameters.type.facility" }
if client.apiversion > '4.3.99':
    inv_includes |= { "investigationGroups", "investigationGroups.grouping" }


authtypes =   [Query(client, "User", order=True), 
               Query(client, "Grouping", order=True, 
                     includes={"userGroups", "userGroups.user"}),
               Query(client, "Rule", order=["what", "id"], 
                     conditions={"grouping":"IS NULL"}), 
               Query(client, "Rule", order=["grouping.name", "what", "id"], 
                     conditions={"grouping":"IS NOT NULL"}, 
                     includes={"grouping"}), 
               Query(client, "PublicStep", order=True) ]
statictypes = [Query(client, "Facility", order=True), 
               Query(client, "Instrument", order=True, 
                     includes={"facility", "instrumentScientists.user"}), 
               Query(client, "ParameterType", order=True, 
                     includes={"facility", "permissibleStringValues"}), 
               Query(client, "InvestigationType", order=True, 
                     includes={"facility"}), 
               Query(client, "SampleType", order=True, 
                     includes={"facility"}), 
               Query(client, "DatasetType", order=True, 
                     includes={"facility"}), 
               Query(client, "DatafileFormat", order=True, 
                     includes={"facility"}), 
               Query(client, "FacilityCycle", order=True, 
                     includes={"facility"}), 
               Query(client, "Application", order=True, 
                     includes={"facility"}) ]
investtypes = [Query(client, "Investigation", 
                     conditions={"id":"in (%d)"}, 
                     includes=inv_includes), 
               Query(client, "Sample", order=["name"], 
                     conditions={"investigation.id":"= %d"}, 
                     includes={"investigation", "type.facility", 
                               "parameters", "parameters.type.facility"}), 
               Query(client, "Dataset", order=["name"], 
                     conditions={"investigation.id":"= %d"}, 
                     includes={"investigation", "type.facility", 
                               "sample", "parameters.type.facility"}), 
               Query(client, "Datafile", order=["dataset.name", "name"], 
                     conditions={"dataset.investigation.id":"= %d"}, 
                     includes={"dataset", "datafileFormat.facility", 
                               "parameters.type.facility"}) ]
othertypes =  [Query(client, "Study", order=True, 
                     includes={"user", "studyInvestigations", 
                               "studyInvestigations.investigation.facility"}), 
               Query(client, "RelatedDatafile", order=True, 
                     includes={"sourceDatafile.dataset.investigation.facility", 
                               "destDatafile.dataset.investigation.facility"}), 
               Query(client, "DataCollection", order=True, 
                     includes={("dataCollectionDatasets.dataset."
                                "investigation.facility"), 
                               ("dataCollectionDatafiles.datafile.dataset."
                                "investigation.facility"), 
                               "%s.type.facility" % datacolparamname}), 
               Query(client, "Job", order=True, 
                     includes={"application.facility", 
                               "inputDataCollection", "outputDataCollection"})]

with open_dumpfile(client, conf.file, conf.format, 'w') as dumpfile:
    dumpfile.writedata(authtypes)
    dumpfile.writedata(statictypes)
    # Dump the investigations each in their own chunk
    investsearch = Query(client, "Investigation", attribute="id", 
                         order=["facility.name", "name", "visitId"])
    for i in client.searchChunked(investsearch):
        # We fetch Dataset including DatasetParameter.  This may lead
        # to a large total number of objects even for a small number
        # of Datasets fetched at once.  Set a very small chunksize to
        # avoid hitting the limit.
        dumpfile.writedata([ str(q) % (i) for q in investtypes ], chunksize=5)
    dumpfile.writedata(othertypes)
