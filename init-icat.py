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
# This script requires the new JPQL style query syntax introduced with
# ICAT 4.3.0 to setup access rules for investigations.
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
if client.apiversion < '4.3':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.3.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


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

# List of all tables in the schema
alltables = client.getEntityNames()

# Public tables that may be read by anybody.  Basically anything thats
# static and not related to any particular investigation.
pubtables = [ "Application", "DatafileFormat", "DatasetType", "Facility", "FacilityCycle", "Instrument", "InstrumentScientist", "InvestigationType", "ParameterType", "PermissibleStringValue", "SampleType", "Grouping", "User", ]

# Tables needed to setup access permissions
authztables = [ "Grouping", "Rule", "User", "UserGroup", ]

# Objects that useroffice might need to create.  Basically anything
# related to a particular investigation as a whole, but not to
# individual items created during the investigation (Datafiles and
# Datasets).  Plus FacilityCycle and InstrumentScientist.
uotables = [ "FacilityCycle", "InstrumentScientist", "Investigation", "InvestigationInstrument", "InvestigationParameter", "InvestigationUser", "Keyword", "Publication", "Shift", "Study", "StudyInvestigation", ] + authztables


# Permit root to read and write everything.  This gives ourselves the
# permissions to continue this script further on.
root = client.createUser("root", fullName="Root")
rootgroup = client.createGroup("root", [ root ])
client.createRules(rootgroup, "CRUD", alltables)

# Grant public read permission to some basic tables.  Note that the
# created rules do not refer to any group.  That means they will apply
# to anybody.
client.createRules(None, "R", pubtables)

# Special rule: each user gets the permission to see which groups he
# is in.
client.createRules(None, "R", [ "UserGroup <-> User[name=:user]" ])

# Add a sepcial user to be configured as reader in ids.server.  This
# user needs at least permission to read all datasets, datafiles,
# investigations and facilities.  But well, then we can make live
# simple by giving him read all permissions.
idsreader = client.createUser("idsreader", fullName="IDS reader")
rallgroup = client.createGroup("rall", [ idsreader ])
client.createRules(rallgroup, "R", alltables)

# Setup permissions for useroffice.  They need to create
# Investigations and to setup access permissions for them.  Note that
# this requires the useroffice to have write permission to authz
# tables which basically gives useroffice root power.
useroffice = client.createUser("useroffice", fullName="User Office")
uogroup = client.createGroup("useroffice", [ useroffice ])
client.createRules(uogroup, "CRUD", uotables)

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
client.createRules(st_writers, "CRUD", [ "SampleType" ])


# ------------------------------------------------------------
# Setup access rules for investigations
# ------------------------------------------------------------

# For each investigation, three groups of users will be created:
#   investigation_<name>_reader
#   investigation_<name>_writer
#   investigation_<name>_owner
# where <name> is the name of the corresponding investigation.  The
# reader and writer group gets read and write permission on the
# investigation respectively.  The owner group gets permission to add
# and remove users to and from the other two group and thus to grant
# and revoke read or write permissions on the investigation.  Here, we
# setup only the rules, the groups will be created in
# create-investigation.py.  The rules are based on the magic names of
# these groups.

# Condition that the current user is in one of the groups
# corresponding to investigation i
inv_cond = ("JOIN Grouping g JOIN g.userGroups ug JOIN ug.user u "
            "WHERE g.name = CONCAT('investigation_',i.name,'_%s') "
            "AND u.name = :user")
inv_writer_cond = inv_cond % "writer"
inv_reader_cond = inv_cond % "reader"
inv_owner_cond = inv_cond % "owner"

# Items that the writers group get CRUD permissions on:
inv_w_crud_items = [
    "SELECT sa FROM Sample sa JOIN sa.investigation i ",
    "SELECT ds FROM Dataset ds JOIN ds.investigation i ",
    "SELECT df FROM Datafile df JOIN df.dataset ds JOIN ds.investigation i ",
    "SELECT ip FROM InvestigationParameter ip JOIN ip.investigation i ",
    "SELECT sp FROM SampleParameter sp JOIN sp.sample sa JOIN sa.investigation i ",
    "SELECT dsp FROM DatasetParameter dsp JOIN dsp.dataset ds JOIN ds.investigation i ",
    "SELECT dfp FROM DatafileParameter dfp JOIN dfp.datafile df JOIN df.dataset ds JOIN ds.investigation i ",
    "SELECT sh FROM Shift sh JOIN sh.investigation i ",
    "SELECT kw FROM Keyword kw JOIN kw.investigation i ",
    "SELECT pb FROM Publication pb JOIN pb.investigation i ",
    "SELECT ii FROM InvestigationInstrument ii JOIN ii.investigation i ",
]

# Items that the writers group get RU permissions on:
inv_w_ru_items = [
    "SELECT i FROM Investigation i ",
]

# Items that the writers group get R permissions on:
inv_w_r_items = [
    "SELECT iu FROM InvestigationUser iu JOIN iu.investigation i ",
]

# writers permissions
client.createRules(None, "CRUD", 
                   [ i + inv_writer_cond for i in inv_w_crud_items ])
client.createRules(None, "RU", 
                   [ i + inv_writer_cond for i in inv_w_ru_items ])
client.createRules(None, "R", 
                   [ i + inv_writer_cond for i in inv_w_r_items ])
# readers just get read access on the whole bunch
inv_r_items = inv_w_crud_items + inv_w_ru_items + inv_w_r_items
client.createRules(None, "R", 
                   [ i + inv_reader_cond for i in inv_r_items ])

# Owner rules.  Could be done in one single expression, but it's
# already complicated enough, so lets make two rules for readers and
# writers respectively.
inv_own_items = [ ("SELECT aug FROM UserGroup aug "
                   "JOIN aug.grouping ag "
                   "JOIN Investigation i "
                   "JOIN Grouping g JOIN g.userGroups ug "
                   "JOIN ug.user u "
                   "WHERE ag.name = CONCAT('investigation_',i.name,'_%s') "
                   "AND g.name = CONCAT('investigation_',i.name,'_owner') "
                   "AND u.name = :user") % g for g in ["reader", "writer"] ]
client.createRules(None, "CRUD", inv_own_items)


# ------------------------------------------------------------
# Create facilities
# ------------------------------------------------------------

facilities = {}
for k in data['facilities'].keys():
    fac = client.new("facility")
    fac.name = data['facilities'][k]['name']
    fac.fullName = data['facilities'][k]['fullName']
    fac.description = data['facilities'][k]['description']
    fac.url = data['facilities'][k]['url']
    fac.create()
    facilities[k] = fac


# ------------------------------------------------------------
# Create instruments
# ------------------------------------------------------------

instusers = []
for k in data['instruments'].keys():
    inst = client.new("instrument")
    inst.name = data['instruments'][k]['name']
    inst.description = data['instruments'][k]['description']
    inst.fullName = data['instruments'][k]['fullName']
    inst.type = data['instruments'][k]['type']
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
    it.name = data['investigation_types'][k]['name']
    it.description = data['investigation_types'][k]['description']
    it.facility = facilities[data['investigation_types'][k]['facility']]
    investigation_types.append(it)
client.createMany(investigation_types)

# datasetTypes
dataset_types = []
for k in data['dataset_types'].keys():
    dt = client.new("datasetType")
    dt.name = data['dataset_types'][k]['name']
    dt.description = data['dataset_types'][k]['description']
    dt.facility = facilities[data['dataset_types'][k]['facility']]
    dataset_types.append(dt)
client.createMany(dataset_types)

# datafileFormats
fileformats = []
for k in data['datafile_formats'].keys():
    ff = client.new("datafileFormat")
    ff.name = data['datafile_formats'][k]['name']
    ff.description = data['datafile_formats'][k]['description']
    ff.facility = facilities[data['datafile_formats'][k]['facility']]
    ff.version = data['datafile_formats'][k]['version']
    fileformats.append(ff)
client.createMany(fileformats)

