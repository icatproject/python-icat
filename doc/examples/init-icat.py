#! /usr/bin/python
#
# Basic initialization of a test ICAT.  Setup all the stuff that must
# be there before useroffice may add investigations.
# - setup basic permissions
# - create a facility
# - create an instrument
# - create InvestigationType, DatasetType, DatafileFormat
#
# This script must be run by the ICAT root user as configured in the
# rootUserNames property.
#

import datetime
import logging
import sys
import yaml
import icat
import icat.config
from icat.query import Query

logging.basicConfig(level=logging.INFO)

config = icat.config.Config()
config.add_variable('datafile', ("datafile",),
                    dict(metavar="inputdata.yaml",
                         help="name of the input datafile"))
client, conf = config.getconfig()

if client.apiversion < '4.4.0':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.4.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def initobj(obj, attrs):
    """Initialize an entity object from a dict of attributes."""
    for a in obj.InstAttr:
        if a != 'id' and a in attrs:
            setattr(obj, a, attrs[a])

def getUser(client, attrs):
    """Get the user, create it as needed.
    """
    try:
        return client.assertedSearch("User [name='%s']" % attrs['name'])[0]
    except icat.SearchResultError:
        user = client.new("User")
        initobj(user, attrs)
        user.create()
        return user

# ------------------------------------------------------------
# Read input data
# ------------------------------------------------------------

if conf.datafile == "-":
    f = sys.stdin
else:
    f = open(conf.datafile, 'r')
data = yaml.safe_load(f)
f.close()


# ------------------------------------------------------------
# Setup some basic permissions
# ------------------------------------------------------------

# List of all tables in the schema
alltables = set(client.getEntityNames())

# Public tables that may be read by anybody.  Basically anything thats
# static and not related to any particular investigation.
pubtables = { "Application", "DatafileFormat", "DatasetType",
              "Facility", "FacilityCycle", "Instrument",
              "InvestigationType", "ParameterType",
              "PermissibleStringValue", "SampleType", "User", }
if "dataPublicationType" in client.typemap:
    pubtables |= { "DataPublicationType" }
if "technique" in client.typemap:
    pubtables |= { "Technique" }

# Objects that useroffice might need to create.  Basically anything
# related to a particular investigation as a whole, but not to
# individual items created during the investigation (Datafiles and
# Datasets).  Plus FacilityCycle and InstrumentScientist.
uotables = { "FacilityCycle", "Grouping", "InstrumentScientist",
             "Investigation", "InvestigationGroup",
             "InvestigationInstrument", "InvestigationParameter",
             "InvestigationUser", "Keyword", "Publication", "Shift",
             "Study", "StudyInvestigation", "User", "UserGroup", }
if "fundingReference" in client.typemap:
    uotables |= { "InvestigationFunding", "FundingReference" }

# Create a root user for the sake of completeness.  No need to grant
# any access rights, because with ICAT 4.4 and newer, the root user
# already has CRUD permission on everything built in.
client.createUser("simple/root", fullName="Root")

# Grant public read permission to some basic tables.  Note that the
# created rules do not refer to any group.  That means they will apply
# to anybody.  SampleType is a special case, dealt with below.
client.createRules("R", pubtables - {"SampleType"})

# Special rules: each user gets the permission to see the groups he
# is in and the studies he is leading.
client.createRules("R", ["Grouping <-> UserGroup <-> User [name=:user]"])
client.createRules("R", ["Study <-> User [name=:user]"])

# Add a special user to be configured as reader in ids.server.  This
# user needs at least permission to read all datasets, datafiles,
# investigations and facilities.  But well, then we can make live
# simple by giving him read all permissions.
idsreader = client.createUser("simple/idsreader", fullName="IDS reader")
rallgroup = client.createGroup("rall", [ idsreader ])
client.createRules("R", alltables - pubtables - {"Log"}, rallgroup)

# Setup permissions for useroffice.  They need to create
# Investigations and related objects, including Users.
useroffice = client.createUser("simple/useroffice", fullName="User Office")
uogroup = client.createGroup("useroffice", [ useroffice ])
client.createRules("CRUD", uotables, uogroup)

# Setup permissions for the data ingester.  They need read permission
# on Investigation and Shift and create permission on Dataset,
# Datafile, and the respective Parameter.
ingest = client.createUser("simple/dataingest", fullName="Data Ingester")
ingestgroup = client.createGroup("ingest", [ ingest ])
client.createRules("R", [ "Investigation", "Shift" ], ingestgroup)
ingest_cru_classes = [ "Sample", "Dataset", "Datafile",
                       "DatasetParameter", "DatafileParameter" ]
if "datasetInstrument" in client.typemap:
    ingest_cru_classes.append("DatasetInstrument")
if "datasetTechnique" in client.typemap:
    ingest_cru_classes.append("DatasetTechnique")
client.createRules("CRU", ingest_cru_classes, ingestgroup)


# ------------------------------------------------------------
# Permissions for DataPublications (if available)
# ------------------------------------------------------------

if "dataPublication" in client.typemap:
    # Create a dedicated user to generate data publication landing
    # pages.  Add two groups: publisher and pubreader.  The former
    # gets the required permissions to create a data publication, the
    # latter the permissions to read all objects related to a data
    # publications.
    pubreader = client.createUser("simple/pubreader", fullName="Pub reader")
    publisher_group = client.createGroup("publisher", [ useroffice ])
    pubreader_group = client.createGroup("pubreader", [ pubreader ])

    # publisher: CRUD permission on Datapublications and related classes
    publisher_tables = { "Affiliation", "DataPublication",
                         "DataPublicationDate", "DataPublicationFunding",
                         "DataPublicationUser", "FundingReference",
                         "FundingReference", "RelatedItem" }
    client.createRules("CRUD", publisher_tables, publisher_group)

    # read permissions: DataPublication should be publicly readable as
    # soon as they are published.  But pubreader also needs access to
    # not yet published ones.  Access permissions to some related
    # objects are covered by PublicStep below and don't need included
    # here.
    dpitems = [
        ("DataPublication", ""),
        ("Datafile", "dataCollectionDatafiles.dataCollection.dataPublications"),
        ("Datafile",
         "dataset.dataCollectionDatasets.dataCollection.dataPublications"),
        ("Datafile",
         "dataset.investigation.dataCollectionInvestigations.dataCollection."
         "dataPublications"),
        ("Dataset", "dataCollectionDatasets.dataCollection.dataPublications"),
        ("Dataset",
         "investigation.dataCollectionInvestigations.dataCollection."
         "dataPublications"),
        ("Investigation",
         "dataCollectionInvestigations.dataCollection.dataPublications"),
    ]
    all_items = []
    pr_items = []
    for name, a in dpitems:
        query = Query(client, name)
        if a:
            query.addConditions({("%s.id" % a): "IS NOT NULL"})
        pr_items.append(query)
        pd_attr = "%s.publicationDate" % a if a else "publicationDate"
        query = Query(client, name, conditions={pd_attr: "< CURRENT_TIMESTAMP"})
        all_items.append(query)
    client.createRules("R", all_items)
    client.createRules("R", pr_items, pubreader_group)


# ------------------------------------------------------------
# Permissions for some special cases
# ------------------------------------------------------------

# SampleType is a public table that may be read by anybody.
# Furthermore still, users may come up with their own special samples
# and might need to create their own type.  So allow also creation by
# anybody.  Since also these special sample types may be shared
# between users, we do not allow update or delete, not even for the
# sample type that the user created himself.  Only scientific staff is
# allowed to do housekeeping.  To do this, scientific staff must also
# be allowed to update all samples, in order to merge duplicate sample
# types.
staff = client.createGroup("scientific_staff")
client.createRules("CR", ["SampleType"])
client.createRules("UD", ["SampleType"], staff)
client.createRules("RU", ["Sample"], staff)

# Everybody is allowed to create DataCollections.  But they are
# private, so users are only allowed to read, update or delete
# DataCollections they created themselves.  Similar thing for Job and
# RelatedDatafile.
#
# *Note*: allowing everybody to create their own DataCollections was a
# nice idea to try out and it even works.  But it has some security
# implications that are quite difficult to handle.  I leave it in
# here, because some other example scripts need it.  But I'd rather
# not recommended to do this on a production server.
dcitems = [
    ( "DataCollection", "" ),
    ( "DataCollectionDatafile", "dataCollection." ),
    ( "DataCollectionDataset", "dataCollection." ),
    ( "DataCollectionParameter", "dataCollection." ),
    ( "Job", "" ),
    ( "RelatedDatafile", "" ),
]
if "dataCollectionInvestigation" in client.typemap:
    dcitems.insert(3, ( "DataCollectionInvestigation", "dataCollection." ))
items = [ Query(client, name, conditions={ (a + "createId"): "= :user" })
          for name, a in dcitems ]
client.createRules("CRUD", items)


# ------------------------------------------------------------
# Access rules for investigations (ICAT 4.4 and newer)
# ------------------------------------------------------------

# We set access permissions on investigation related objects based on
# user groups.  We create three groups for each investigation:
# "reader", "writer", and "owner", where the first two have the
# obvious semantic.  User in "owner" may grant access to other users,
# e.g. add or remove users to or from the other two groups.
# Additionally, instrument scientist get the the same permissions as
# "writer" on the investigations related to their instrument.

# Items that are considered to belong to the content of an
# investigation.  The writer group will get CRUD permissions and
# the reader group R permissions on these items.  The list are
# tuples with three items: the entity type, the attribute that
# indicates the path to the investigation, and optionally, the
# path to a dataset complete attribute.  If the latter is set, an
# extra condition is added so that CRUD permission is only given
# if complete is False.
invitems = [
    ( "Sample", "investigation.", "" ),
    ( "Dataset", "investigation.", "complete" ),
    ( "Datafile", "dataset.investigation.", "dataset.complete" ),
    ( "InvestigationParameter", "investigation.", "" ),
    ( "SampleParameter", "sample.investigation.", "" ),
    ( "DatasetParameter", "dataset.investigation.", "" ),
    ( "DatafileParameter", "datafile.dataset.investigation.", "" ),
]
if "datasetInstrument" in client.typemap:
    invitems.append(( "DatasetInstrument", "dataset.investigation.", "" ))
if "datasetTechnique" in client.typemap:
    invitems.append(( "DatasetTechnique", "dataset.investigation.", "" ))

# Set write permissions
items = []
for name, a, complete in invitems:
    # ... for writer group.
    conditions={
        a + "investigationGroups.role":"= 'writer'",
        a + "investigationGroups.grouping.userGroups.user.name":"= :user",
    }
    if complete:
        conditions[complete] = "= False"
    items.append(Query(client, name, conditions=conditions))
    # ... for instrument scientists.
    conditions={
        a + "investigationInstruments.instrument.instrumentScientists"
        ".user.name":"= :user",
    }
    if complete:
        conditions[complete] = "= False"
    items.append(Query(client, name, conditions=conditions))
client.createRules("CUD", items)

# Set permissions for the reader group.  Actually, we give read
# permissions to all groups related to the investigation.  For
# read access, we add some more related items, in particular the
# investigation itself.
invitems.extend([ ( "Investigation", "", "" ),
                  ( "Shift", "investigation.", "" ),
                  ( "Keyword", "investigation.", "" ),
                  ( "Publication", "investigation.", "" ) ])
items = []
for name, a, c in invitems:
    conditions={
        a + "investigationGroups.grouping.userGroups.user.name":"= :user",
    }
    items.append(Query(client, name, conditions=conditions))
    conditions={
        a + "investigationInstruments.instrument.instrumentScientists"
        ".user.name":"= :user",
    }
    items.append(Query(client, name, conditions=conditions))
client.createRules("R", items)

# set permission to grant and to revoke permissions for the owner.
tig = "grouping.investigationGroups"
uig = "grouping.investigationGroups.investigation.investigationGroups"
item = Query(client, "UserGroup", conditions={
    uig + ".grouping.userGroups.user.name":"= :user",
    uig + ".role":"= 'owner'",
    tig + ".role":"in ('reader', 'writer')"
})
client.createRules("CRUD", [ item ])
uig = "investigationGroups.investigation.investigationGroups"
item = Query(client, "Grouping", conditions={
    uig + ".grouping.userGroups.user.name":"= :user",
    uig + ".role":"= 'owner'"
})
client.createRules("R", [ item ])


# ------------------------------------------------------------
# Public access
# ------------------------------------------------------------

# Allow public read access to investigations, datasets, and datafiles
# once the investigation's releaseDate has been passed.

invitems = [ ( "Investigation", "", "" ),
             ( "Dataset", "investigation.", "type.name" ),
             ( "Datafile", "dataset.investigation.", "dataset.type.name" ), ]

items = []
for name, a, dstype_name in invitems:
    conditions={
        a + "releaseDate":"< CURRENT_TIMESTAMP",
    }
    if dstype_name:
        conditions[dstype_name] = "= 'raw'"
    items.append(Query(client, name, conditions=conditions))
client.createRules("R", items)


# ------------------------------------------------------------
# Public steps
# ------------------------------------------------------------

pubsteps = [
    ("DataCollection", "dataCollectionDatafiles"),
    ("DataCollection", "dataCollectionDatasets"),
    ("DataCollection", "parameters"),
    ("Datafile", "dataset"),
    ("Datafile", "parameters"),
    ("Dataset", "datafiles"),
    ("Dataset", "investigation"),
    ("Dataset", "parameters"),
    ("Dataset", "sample"),
    ("Grouping", "userGroups"),
    ("Instrument", "instrumentScientists"),
    ("Investigation", "investigationGroups"),
    ("Investigation", "investigationInstruments"),
    ("Investigation", "investigationUsers"),
    ("Investigation", "keywords"),
    ("Investigation", "parameters"),
    ("Investigation", "publications"),
    ("Investigation", "samples"),
    ("Investigation", "shifts"),
    ("InvestigationGroup", "grouping"),
    ("Job", "inputDataCollection"),
    ("Job", "outputDataCollection"),
    ("Sample", "parameters"),
    ("Study", "studyInvestigations"),
]
# Note: to simplify things, we take DataPublication as pars pro toto
# for all the schema extensions in ICAT 5.0 here.
if "dataPublication" in client.typemap:
    pubsteps.extend([
        ( "DataCollection", "dataCollectionInvestigations" ),
        ( "DataPublication", "content"),
        ( "DataPublication", "dates"),
        ( "DataPublication", "fundingReferences"),
        ( "DataPublication", "relatedItems"),
        ( "DataPublication", "users"),
        ( "DataPublicationFunding", "funding"),
        ( "DataPublicationUser", "affiliations"),
        ( "DataPublicationUser", "user"),
        ( "Dataset", "datasetInstruments"),
        ( "Dataset", "datasetTechniques"),
        ( "Investigation", "fundingReferences"),
        ( "InvestigationFunding", "funding"),
    ])
    pubsteps.sort()
objs = [ client.new("PublicStep", origin=origin, field=field)
         for (origin, field) in pubsteps ]
client.createMany(objs)


# ------------------------------------------------------------
# Create facilities
# ------------------------------------------------------------

facilities = {}
for k in data['facilities'].keys():
    fac = client.new("Facility")
    initobj(fac, data['facilities'][k])
    fac.create()
    facilities[k] = fac


# ------------------------------------------------------------
# Create techniques (if available)
# ------------------------------------------------------------

if "technique" in client.typemap:
    techniques = []
    for k in data['techniques'].keys():
        t = client.new("Technique")
        initobj(t, data['techniques'][k])
        techniques.append(t)
    client.createMany(techniques)


# ------------------------------------------------------------
# Create instruments
# ------------------------------------------------------------

instusers = []
for k in data['instruments'].keys():
    inst = client.new("Instrument")
    initobj(inst, data['instruments'][k])
    inst.facility = facilities[data['instruments'][k]['facility']]
    inst.create()
    ud = data['users'][data['instruments'][k]['instrumentscientist']]
    instuser = getUser(client, ud)
    inst.addInstrumentScientists([instuser])
    instusers.append(instuser)
# As a default rule, instrument scientists are scientific staff
staff.addUsers(instusers)


# ------------------------------------------------------------
# Create InvestigationType, DatasetType, DatafileFormat
# ------------------------------------------------------------

# investigationTypes
investigation_types = []
for k in data['investigation_types'].keys():
    it = client.new("InvestigationType")
    initobj(it, data['investigation_types'][k])
    it.facility = facilities[data['investigation_types'][k]['facility']]
    investigation_types.append(it)
client.createMany(investigation_types)

# datasetTypes
dataset_types = []
for k in data['dataset_types'].keys():
    dt = client.new("DatasetType")
    initobj(dt, data['dataset_types'][k])
    dt.facility = facilities[data['dataset_types'][k]['facility']]
    dataset_types.append(dt)
client.createMany(dataset_types)

# datafileFormats
fileformats = []
for k in data['datafile_formats'].keys():
    ff = client.new("DatafileFormat")
    initobj(ff, data['datafile_formats'][k])
    ff.facility = facilities[data['datafile_formats'][k]['facility']]
    fileformats.append(ff)
client.createMany(fileformats)

# dataPublicationTypes
if "dataPublicationType" in client.typemap:
    data_publication_types = []
    for k in data['data_publication_types'].keys():
        dpt = client.new("DataPublicationType")
        initobj(dpt, data['data_publication_types'][k])
        dpt.facility = facilities[data['data_publication_types'][k]['facility']]
        data_publication_types.append(dpt)
    client.createMany(data_publication_types)

# parameterTypes
param_types = []
for k in data['parameter_types'].keys():
    pt = client.new("ParameterType")
    initobj(pt, data['parameter_types'][k])
    pt.facility = facilities[data['parameter_types'][k]['facility']]
    if 'values' in data['parameter_types'][k]:
        for v in data['parameter_types'][k]['values']:
            psv = client.new("PermissibleStringValue", value=v)
            pt.permissibleStringValues.append(psv)
    param_types.append(pt)
client.createMany(param_types)

# applications
applications = []
for k in data['applications'].keys():
    app = client.new("Application")
    initobj(app, data['applications'][k])
    app.facility = facilities[data['applications'][k]['facility']]
    applications.append(app)
client.createMany(applications)

# facilityCycles
cet = datetime.timezone(datetime.timedelta(hours=1))
cest = datetime.timezone(datetime.timedelta(hours=2))

def gettz(month):
    """Very simplified switch between DST on and off.
    """
    if 3 < month <= 10:
        return cest
    else:
        return cet

facility_cycles = []
for fcdata in data['facility_cycles']:
    for y in range(fcdata['startYear'],fcdata['endYear']):
        year = 2000 + int(y)
        c = 0
        for p in fcdata['cycles']:
            c += 1
            cycle = client.new("FacilityCycle")
            cycle.name = "%02d%d" % (y, c)
            cycle.startDate = datetime.datetime(year, p[0], p[1],
                                                tzinfo=gettz(p[0]))
            if p[2] > p[0]:
                cycle.endDate = datetime.datetime(year, p[2], p[3],
                                                  tzinfo=gettz(p[2]))
            else:
                cycle.endDate = datetime.datetime(year+1, p[2], p[3],
                                                  tzinfo=gettz(p[2]))
            cycle.facility = facilities[fcdata['facility']]
            facility_cycles.append(cycle)
client.createMany(facility_cycles)
