#! /usr/bin/python
#
# Create some sample investigations.
#
# This script should be run by the ICAT user useroffice.
#

from __future__ import print_function
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
config.add_variable('investigationname', ("investigationname",), 
                    dict(help="name of the investigation to add"))
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
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

try:
    investigationdata = data['investigations'][conf.investigationname]
except KeyError:
    raise RuntimeError("unknown investigation '%s'" % conf.investigationname)


# ------------------------------------------------------------
# Get some objects from ICAT we need later on
# ------------------------------------------------------------

facilityname = data['facilities'][investigationdata['facility']]['name']
facility = client.assertedSearch("Facility[name='%s']" % facilityname)[0]
facility_const = "AND facility.id=%d" % facility.id

instrumentname = data['instruments'][investigationdata['instrument']]['name']
instrsearch = "Instrument[name='%s' %s]" % (instrumentname, facility_const)
instrument = client.assertedSearch(instrsearch)[0]

typename = data['investigation_types'][investigationdata['type']]['name']
typesearch = "InvestigationType[name='%s' %s]" % (typename, facility_const)
investigation_type = client.assertedSearch(typesearch)[0]


# ------------------------------------------------------------
# Create the investigation
# ------------------------------------------------------------

try:
    invsearch = "Investigation[name='%s']" % investigationdata['name']
    client.assertedSearch(invsearch, assertmax=None)
except icat.exception.SearchResultError:
    pass
else:
    raise RuntimeError("Investigation: '%s' already exists ..." 
                       % investigationdata['name'])

print("Investigation: creating '%s' ..." % investigationdata['name'])
investigation = client.new("investigation")
investigation.name = investigationdata['name']
investigation.title = investigationdata['title']
investigation.startDate = investigationdata['startDate']
investigation.endDate = investigationdata['endDate']
investigation.visitId = investigationdata['visitId']
investigation.facility = facility
investigation.type = investigation_type
investigation.create()
investigation.addInstrument(instrument)
investigation.addKeywords(investigationdata['keywords'])


# ------------------------------------------------------------
# Add some users
# ------------------------------------------------------------

investigationowner = []
investigationreader = []
investigationwriter = []

# Principal Investigator
user = data['users'][investigationdata['invpi']]
userpi = client.createUser(user['name'], fullName=user['fullName'], 
                           search=True)
investigation.addInvestigationUsers([userpi], role="Principal Investigator")
investigationowner.append(userpi)
investigationwriter.append(userpi)

# Additional Investigators
usercols = []
for u in investigationdata['invcol']:
    user = data['users'][u]
    usercols.append(client.createUser(user['name'], fullName=user['fullName'], 
                                      search=True))
investigation.addInvestigationUsers(usercols)
investigationwriter.extend(usercols)

# More users that will get read permissions
for u in investigationdata['invguest']:
    user = data['users'][u]
    userguest = client.createUser(user['name'], fullName=user['fullName'], 
                                  search=True)
    investigationreader.append(userguest)

# Add InstrumentScientists to the writers
if investigationdata['addinstuser']:
    investigationwriter.extend(instrument.getInstrumentScientists())

owngroupname = "investigation_%s_owner" % investigation.name
writegroupname = "investigation_%s_writer" % investigation.name
readgroupname = "investigation_%s_reader" % investigation.name
owngroup = client.createGroup(owngroupname, investigationowner)
writegroup = client.createGroup(writegroupname, investigationwriter)
readgroup = client.createGroup(readgroupname, investigationreader)


# ------------------------------------------------------------
# Setup permissions
# ------------------------------------------------------------

# perm_own_crud: items, that the owners should get CRUD perms on.
# perm_own_r: items, that the owners should get R perms on.
if client.apiversion < '4.3':
    perm_own_crud = [ "UserGroup <-> Group[name='%s']" % s for s in 
                      [ writegroupname, readgroupname ] ]
else:
    perm_own_crud = [ "UserGroup <-> Grouping[name='%s']" % s for s in 
                      [ writegroupname, readgroupname ] ]


investigationstr = "Investigation[name='%s']" % investigation.name
# Items, that people in the writers group should get CRUD perms on.
perm_crud = [ s % investigationstr for s in 
              [ "Sample <-> %s",
                "Dataset <-> %s",
                "Datafile <-> Dataset <-> %s",
                "InvestigationParameter <-> %s",
                "SampleParameter <-> Sample <-> %s",
                "DatasetParameter <-> Dataset <-> %s",
                "DatafileParameter <-> Datafile <-> Dataset <-> %s",
                "Shift <-> %s",
                "Keyword <-> %s",
                "Publication <-> %s", ] ]
if client.apiversion >= '4.3':
    perm_crud.append("InvestigationInstrument <-> %s" % investigationstr)

# Items, that people in the writers group should get RU perms on.
perm_ru = [ investigationstr, ]

# Items, that people in the writers group should get R perms on.
perm_r = [ "InvestigationUser <-> %s" % investigationstr, ]

# owners permissions
client.createRules(owngroup, "CRUD", perm_own_crud)
# writers permissions
client.createRules(writegroup, "RU", perm_ru)
client.createRules(writegroup, "CRUD", perm_crud)
client.createRules(writegroup, "R", perm_r)
# people in the readers group just get read access on the whole bunch
client.createRules(readgroup, "R", perm_ru + perm_crud + perm_r)

