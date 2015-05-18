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

import sys
import logging
import yaml
import icat
import icat.config
from icat.query import Query

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

config = icat.config.Config()
config.add_variable('datafile', ("datafile",), 
                    dict(metavar="inputdata.yaml", 
                         help="name of the input datafile"))
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def initobj(obj, attrs):
    """Initialize an entity object from a dict of attributes."""
    for a in obj.InstAttr:
        if a != 'id' and a in attrs:
            setattr(obj, a, attrs[a])

# ------------------------------------------------------------
# Read input data
# ------------------------------------------------------------

if conf.datafile == "-":
    f = sys.stdin
else:
    f = open(conf.datafile, 'r')
data = yaml.load(f)
f.close()


# ------------------------------------------------------------
# Setup some basic permissions
# ------------------------------------------------------------

# The name of the Group entity type has been changed to Grouping in
# ICAT 4.3.
if client.apiversion < '4.2.99':
    groupname = "Group"
else:
    groupname = "Grouping"

# List of all tables in the schema
alltables = set(client.getEntityNames())

# Public tables that may be read by anybody.  Basically anything thats
# static and not related to any particular investigation.
pubtables = { "Application", "DatafileFormat", "DatasetType", 
              "Facility", "FacilityCycle", "Instrument", 
              "InvestigationType", "ParameterType", 
              "PermissibleStringValue", "SampleType", "User", }

# Objects that useroffice might need to create.  Basically anything
# related to a particular investigation as a whole, but not to
# individual items created during the investigation (Datafiles and
# Datasets).  Plus FacilityCycle and InstrumentScientist.
#
# With ICAT 4.4 and newer, access permisions on investigations are
# based InvestigationGroup.  In this case, we have a fixed set of
# static rules.  With older ICAT versions, we need per investigation
# rules and thus useroffice need permission to create them.
uotables = { "FacilityCycle", groupname, "InstrumentScientist", 
             "Investigation", "InvestigationParameter", 
             "InvestigationUser", "Keyword", "Publication", "Shift", 
             "Study", "StudyInvestigation", "User", "UserGroup", }
if client.apiversion > '4.2.99':
    uotables.add("InvestigationInstrument")
if client.apiversion > '4.3.99':
    uotables.add("InvestigationGroup")
else:
    uotables.add("Rule")


# Permit root to read and write everything.  This gives ourselves the
# permissions to continue this script further on.  With ICAT 4.4 and
# newer this is not needed, as the root user already has CRUD
# permission on everything built in.
root = client.createUser("root", fullName="Root")
if client.apiversion < '4.3.99':
    rootgroup = client.createGroup("root", [ root ])
    client.createRules("CRUD", alltables, rootgroup)

# Grant public read permission to some basic tables.  Note that the
# created rules do not refer to any group.  That means they will apply
# to anybody.  SampleType is a special case, dealt with below.
client.createRules("R", pubtables - {"SampleType"})

# Special rule: each user gets the permission to see the groups he
# is in.
client.createRules("R", [ "%s <-> UserGroup <-> User[name=:user]" % groupname ])

# Add a sepcial user to be configured as reader in ids.server.  This
# user needs at least permission to read all datasets, datafiles,
# investigations and facilities.  But well, then we can make live
# simple by giving him read all permissions.
idsreader = client.createUser("idsreader", fullName="IDS reader")
rallgroup = client.createGroup("rall", [ idsreader ])
client.createRules("R", alltables - pubtables - {"Log"}, rallgroup)

# Setup permissions for useroffice.  They need to create
# Investigations and to setup access permissions for them.  Note that
# this requires the useroffice to have write permission to authz
# tables which basically gives useroffice root power.
useroffice = client.createUser("useroffice", fullName="User Office")
uogroup = client.createGroup("useroffice", [ useroffice ])
client.createRules("CRUD", uotables, uogroup)


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
# DataCollections they created themselves.  Similar thing for Job.
owndccond = "DataCollection [createId=:user]"
owndc = [ s % owndccond for s in 
          [ "%s", 
            "DataCollectionDatafile <-> %s", 
            "DataCollectionDataset <-> %s" ] ]
client.createRules("CRUD", owndc)
client.createRules("CRUD", ["Job [createId=:user]"])


# ------------------------------------------------------------
# Access rules for investigations (ICAT 4.4 and newer)
# ------------------------------------------------------------

# ICAT 4.4 introduced InvestigationGroup.  This allows us to setup one
# static set of permissions to access individual investigations rather
# then creating individual rules for each investigation.

if client.apiversion > '4.3.99':

    # Items that are considered to belong to the content of an
    # investigation.  The writer group will get CRUD permissions and
    # the reader group R permissions on these items.  The list are
    # tuples with three items: the entity type, the attribute that
    # indicates the path to the investigation, and optionally, the
    # path to a dataset complete attribute.  If the latter is set, an
    # extra condition is added so that CRUD permission is only given
    # if complete is False.
    invitems = [ ( "Sample", "investigation.", "" ),
                 ( "Dataset", "investigation.", "complete" ),
                 ( "Datafile", "dataset.investigation.", "dataset.complete" ),
                 ( "InvestigationParameter", "investigation.", "" ),
                 ( "SampleParameter", "sample.investigation.", "" ),
                 ( "DatasetParameter", "dataset.investigation.", "" ),
                 ( "DatafileParameter", "datafile.dataset.investigation.", "" ),
                 ( "Shift", "investigation.", "" ),
                 ( "Keyword", "investigation.", "" ),
                 ( "Publication", "investigation.", "" ), ] 

    # set permissions for the writer group
    items = []
    for name, a, complete in invitems:
        conditions={
            a + "investigationGroups.role":"= 'writer'",
            a + "investigationGroups.grouping.userGroups.user.name":"= :user",
        }
        if complete:
            conditions[complete] = "= False"
        items.append(Query(client, name, conditions=conditions))
    client.createRules("CUD", items)

    # set permissions for the reader group.  Actually, we give read
    # permissions to all groups related to the investigation.
    # For reading, we add the investigation itself to the invitems.
    invitems.insert(0, ( "Investigation", "", "" ) )
    items = []
    for name, a, c in invitems:
        conditions={
            a + "investigationGroups.grouping.userGroups.user.name":"= :user",
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

if client.apiversion > '4.2.99':
    # Compatibility ICAT 4.3.0 vs. ICAT 4.3.1 and later: name of the
    # parameters relation in DataCollection.
    if client.apiversion < '4.3.1':
        datacolparamname = 'dataCollectionParameters'
    else:
        datacolparamname = 'parameters'
    pubsteps = [ ("DataCollection", "dataCollectionDatafiles"), 
                 ("DataCollection", "dataCollectionDatasets"), 
                 ("DataCollection", datacolparamname), 
                 ("Datafile", "dataset"), 
                 ("Datafile", "parameters"), 
                 ("Dataset", "datafiles"), 
                 ("Dataset", "investigation"), 
                 ("Dataset", "parameters"), 
                 ("Dataset", "sample"), 
                 ("Grouping", "userGroups"), 
                 ("Instrument", "instrumentScientists"), 
                 ("Investigation", "investigationInstruments"), 
                 ("Investigation", "investigationUsers"), 
                 ("Investigation", "keywords"), 
                 ("Investigation", "parameters"), 
                 ("Investigation", "publications"), 
                 ("Investigation", "samples"), 
                 ("Investigation", "shifts"), 
                 ("Job", "inputDataCollection"), 
                 ("Job", "outputDataCollection"), 
                 ("Sample", "parameters"), 
                 ("Study", "studyInvestigations"), ]
    if client.apiversion > '4.3.99':
        pubsteps += [ ("Investigation", "investigationGroups"), 
                      ("InvestigationGroup", "grouping"), ]
    objs = [ client.new("publicStep", origin=origin, field=field)
             for (origin, field) in pubsteps ]
    client.createMany(objs)


# ------------------------------------------------------------
# Create facilities
# ------------------------------------------------------------

facilities = {}
for k in data['facilities'].keys():
    fac = client.new("facility")
    initobj(fac, data['facilities'][k])
    fac.create()
    facilities[k] = fac


# ------------------------------------------------------------
# Create instruments
# ------------------------------------------------------------

instusers = []
for k in data['instruments'].keys():
    inst = client.new("instrument")
    initobj(inst, data['instruments'][k])
    inst.facility = facilities[data['instruments'][k]['facility']]
    inst.create()
    ud = data['users'][data['instruments'][k]['instrumentscientist']]
    instuser = client.createUser(ud['name'], fullName=ud['fullName'], 
                                 search=True)
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
    it = client.new("investigationType")
    initobj(it, data['investigation_types'][k])
    it.facility = facilities[data['investigation_types'][k]['facility']]
    investigation_types.append(it)
client.createMany(investigation_types)

# datasetTypes
dataset_types = []
for k in data['dataset_types'].keys():
    dt = client.new("datasetType")
    initobj(dt, data['dataset_types'][k])
    dt.facility = facilities[data['dataset_types'][k]['facility']]
    dataset_types.append(dt)
client.createMany(dataset_types)

# datafileFormats
fileformats = []
for k in data['datafile_formats'].keys():
    ff = client.new("datafileFormat")
    initobj(ff, data['datafile_formats'][k])
    ff.facility = facilities[data['datafile_formats'][k]['facility']]
    fileformats.append(ff)
client.createMany(fileformats)

# applications
applications = []
for k in data['applications'].keys():
    app = client.new("application")
    initobj(app, data['applications'][k])
    app.facility = facilities[data['applications'][k]['facility']]
    applications.append(app)
client.createMany(applications)

