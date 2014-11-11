#! /usr/bin/python
#
# Basic initialization of a test ICAT.  Setup all the stuff that must
# be there before useroffice may add investigations.
# - setup basic permissions
# - create a facility
# - create an instrument
# - create InvestigationType, DatasetType, DatafileParameter
#
# This script must be run by the ICAT root user as configured in the
# rootUserNames property.
#

import icat
import icat.config
import sys
import logging
import yaml

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
alltables = client.getEntityNames()

# Public tables that may be read by anybody.  Basically anything thats
# static and not related to any particular investigation.
pubtables = [ "Application", "DatafileFormat", "DatasetType", 
              "Facility", "FacilityCycle", "Instrument", 
              "InstrumentScientist", "InvestigationType", 
              "ParameterType", "PermissibleStringValue", "SampleType", 
              "User", ]

# Objects that useroffice might need to create.  Basically anything
# related to a particular investigation as a whole, but not to
# individual items created during the investigation (Datafiles and
# Datasets).  Plus FacilityCycle and InstrumentScientist.
uotables = [ "FacilityCycle", groupname, "InstrumentScientist", 
             "Investigation", "InvestigationParameter", 
             "InvestigationUser", "Keyword", "Publication", "Shift", 
             "Study", "StudyInvestigation", "User", "UserGroup", ]
if client.apiversion > '4.2.99':
    uotables += [ "InvestigationInstrument", ]
if client.apiversion > '4.3.99':
    uotables += [ "InvestigationGroup", ]
if client.apiversion < '4.3.99':
    uotables += [ "Rule", ]


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
# to anybody.
client.createRules("R", pubtables)

# Special rule: each user gets the permission to see the groups he
# is in.
client.createRules("R", [ "%s <-> UserGroup <-> User[name=:user]" % groupname ])

# Add a sepcial user to be configured as reader in ids.server.  This
# user needs at least permission to read all datasets, datafiles,
# investigations and facilities.  But well, then we can make live
# simple by giving him read all permissions.
idsreader = client.createUser("idsreader", fullName="IDS reader")
rallgroup = client.createGroup("rall", [ idsreader ])
client.createRules("R", alltables, rallgroup)

# Setup permissions for useroffice.  They need to create
# Investigations and to setup access permissions for them.  Note that
# this requires the useroffice to have write permission to authz
# tables which basically gives useroffice root power.
useroffice = client.createUser("useroffice", fullName="User Office")
uogroup = client.createGroup("useroffice", [ useroffice ])
client.createRules("CRUD", uotables, uogroup)

# Special case SampleType: most tables in the data base are either
# specific to the site as a whole (most public tables) or specific to
# a particular investigation.  The former contain public data that is
# mostly static, created once at initialization and does not change
# too much later on.  The latter is private and created during each
# investigation.  SampleType is something inbetween: it is considered
# public data and shared among unrelated investigations.  But still
# each investigation might come up with a new SampleType and might
# need to create them.
#
# This requires special permissions.  Create a group of SampleType
# writers that have write permissions in SampleType.  We will populate
# this group later.
st_writers = client.createGroup("samplewriter")
client.createRules("CRUD", [ "SampleType" ], st_writers)


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
# As a default rule, instrument scientists are SampleType writers
st_writers.addUsers(instusers)


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


# ------------------------------------------------------------
# Access rules for investigations (ICAT 4.4 and newer)
# ------------------------------------------------------------

# ICAT 4.4 introduced InvestigationGroup.  This allows us to setup one
# static set of permissions to access individual investigations rather
# then creating individual rules for each investigation.

if client.apiversion > '4.3.99':

    # Items that are considered to belong to the content of an
    # investigation, where %s represents the investigation itself.
    # The writer group will get CRUD permissions and the reader group
    # R permissions on these items.
    invitems = [ "Sample <-> %s",
                 "Dataset <-> %s",
                 "Datafile <-> Dataset <-> %s",
                 "InvestigationParameter <-> %s",
                 "SampleParameter <-> Sample <-> %s",
                 "DatasetParameter <-> Dataset <-> %s",
                 "DatafileParameter <-> Datafile <-> Dataset <-> %s",
                 "Shift <-> %s",
                 "Keyword <-> %s",
                 "Publication <-> %s",
                 "InvestigationInstrument <-> %s", ] 

    # set permissions for the writer group
    invcond = ("Investigation <-> InvestigationGroup [role='writer'] "
               "<-> Grouping <-> UserGroup <-> User [name=:user]")
    client.createRules("CRUD", [ s % invcond for s in invitems ])

    # set permissions for the reader group.  Actually, we give read
    # permissions to all groups related to the investigation.
    invcond = ("Investigation <-> InvestigationGroup "
               "<-> Grouping <-> UserGroup <-> User [name=:user]")
    client.createRules("R", [ invcond ])
    client.createRules("R", [ s % invcond for s in invitems ])

    # set permission to grant and to revoke permissions for the owner
    # Would like to add a condition 
    # ,
    # but this is too long (have 255 chars max).
    item = ("SELECT tug FROM UserGroup tug "
            "JOIN tug.grouping tg "
            "JOIN tg.investigationGroups tig "
            "JOIN tig.investigation i "
            "JOIN i.investigationGroups uig "
            "JOIN uig.grouping ug "
            "JOIN ug.userGroups uug JOIN uug.user u "
            "WHERE (tig.role = 'writer' OR tig.role = 'reader') "
            "AND uig.role = 'owner' AND u.name = :user")
    client.createRules("CRUD", [ item ])
    item = ("SELECT tg FROM Grouping tg "
            "JOIN tg.investigationGroups tig "
            "JOIN tig.investigation i "
            "JOIN i.investigationGroups uig "
            "JOIN uig.grouping ug "
            "JOIN ug.userGroups uug JOIN uug.user u "
            "WHERE uig.role = 'owner' AND u.name = :user")
    client.createRules("R", [ item ])


# ------------------------------------------------------------
# Public steps
# ------------------------------------------------------------

if client.apiversion > '4.2.99':
    pubsteps = [ ("DataCollection", "parameters"), 
                 ("Datafile", "dataset"), 
                 ("Datafile", "parameters"), 
                 ("Dataset", "datafiles"), 
                 ("Dataset", "investigation"), 
                 ("Dataset", "parameters"), 
                 ("Dataset", "sample"), 
                 ("Grouping", "userGroups"), 
                 ("Investigation", "datasets"), 
                 ("Investigation", "investigationInstruments"), 
                 ("Investigation", "investigationUsers"), 
                 ("Investigation", "keywords"), 
                 ("Investigation", "parameters"), 
                 ("Investigation", "publications"), 
                 ("Investigation", "samples"), 
                 ("Investigation", "shifts"), 
                 ("Sample", "investigation"), 
                 ("Sample", "parameters"), ]
    objs = [ client.new("publicStep", origin=origin, field=field)
             for (origin, field) in pubsteps ]
    client.createMany(objs)

