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
        user = client.new("user")
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

# Objects that useroffice might need to create.  Basically anything
# related to a particular investigation as a whole, but not to
# individual items created during the investigation (Datafiles and
# Datasets).  Plus FacilityCycle and InstrumentScientist.
uotables = { "FacilityCycle", "Grouping", "InstrumentScientist",
             "Investigation", "InvestigationGroup",
             "InvestigationInstrument", "InvestigationParameter",
             "InvestigationUser", "Keyword", "Publication", "Shift",
             "Study", "StudyInvestigation", "User", "UserGroup", }

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

# Add a sepcial user to be configured as reader in ids.server.  This
# user needs at least permission to read all datasets, datafiles,
# investigations and facilities.  But well, then we can make live
# simple by giving him read all permissions.
idsreader = client.createUser("simple/idsreader", fullName="IDS reader")
rallgroup = client.createGroup("rall", [ idsreader ])
client.createRules("R", alltables - pubtables - {"Log"}, rallgroup)

# Setup permissions for useroffice.  They need to create
# Investigations and to setup access permissions for them.  Note that
# this requires the useroffice to have write permission to authz
# tables which basically gives useroffice root power.
useroffice = client.createUser("simple/useroffice", fullName="User Office")
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
# DataCollections they created themselves.  Similar thing for Job and
# RelatedDatafile.
owndccond = "DataCollection [createId=:user]"
owndc = [ s % owndccond for s in
          [ "%s",
            "DataCollectionDatafile <-> %s",
            "DataCollectionDataset <-> %s",
            "DataCollectionParameter <-> %s" ] ]
client.createRules("CRUD", owndc)
client.createRules("CRUD", ["Job [createId=:user]"])
client.createRules("CRUD", ["RelatedDatafile [createId=:user]"])


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

# parameterTypes
param_types = []
for k in data['parameter_types'].keys():
    pt = client.new("parameterType")
    initobj(pt, data['parameter_types'][k])
    pt.facility = facilities[data['parameter_types'][k]['facility']]
    if 'values' in data['parameter_types'][k]:
        for v in data['parameter_types'][k]['values']:
            psv = client.new('permissibleStringValue', value=v)
            pt.permissibleStringValues.append(psv)
    param_types.append(pt)
client.createMany(param_types)

# applications
applications = []
for k in data['applications'].keys():
    app = client.new("application")
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
            cycle = client.new("facilityCycle")
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
