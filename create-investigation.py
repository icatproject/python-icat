#! /usr/bin/python
#
# Create some sample investigations.
#
# This script should be run by the ICAT user useroffice.
#

from icat.client import Client
import logging
import sys
import icat.config
import yaml

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

icat.config.defaultsection = "hzb"
conf = icat.config.Config()
conf.add_field('datafile', ("datafile",), 
               dict(metavar="inputdata.yaml", 
                    help="name of the input datafile"))
conf.add_field('investigationname', ("investigationname",), 
               dict(help="name of the investigation to add"))
conf.getconfig()

client = Client(conf.url)
client.login(conf.auth, conf.credentials)


# ------------------------------------------------------------
# Read input data
# ------------------------------------------------------------

try:
    if conf.datafile == "-":
        f = sys.stdin
    else:
        f = open(conf.datafile, 'r')
    try:
        data = yaml.load(f)
    finally:
        f.close()
except IOError as e:
    print >> sys.stderr, e
    sys.exit(2)
except yaml.YAMLError:
    print >> sys.stderr, "Parsing error in input datafile"
    sys.exit(2)


try:
    investigationdata = data['investigations'][conf.investigationname]
except KeyError:
    print >> sys.stderr, "unknown investigation", investigationname
    sys.exit(2)


# ------------------------------------------------------------
# Get some objects from ICAT we need later on
# ------------------------------------------------------------

facilityname = data['facilities'][investigationdata['facility']]['name']
facilities = client.search("Facility[name='%s']" % facilityname)
if len(facilities): 
    facility = facilities[0]
else:
    print "Facility '%s' not found." % facilityname
    sys.exit(3)
facility_const = "AND facility.id=%d" % facility.id

instrumentname = data['instruments'][investigationdata['instrument']]['name']
instruments = client.search("Instrument[name='%s' %s]" 
                            % (instrumentname, facility_const))
if len(instruments): 
    instrument = instruments[0]
else:
    print "Instrument '%s' not found." % instrumentname
    sys.exit(3)

typename = data['investigation_types'][investigationdata['type']]['name']
investigation_types = client.search("InvestigationType[name='%s' %s]" 
                                    % (typename, facility_const))
if len(investigation_types): 
    investigation_type = investigation_types[0]
else:
    print "InvestigationType '%s' not found." % typename
    sys.exit(3)


# ------------------------------------------------------------
# Create the investigation
# ------------------------------------------------------------

investigations = client.search("Investigation[name='%s']" 
                               % investigationdata['name'])
if len(investigations): 
    print "Investigation: '%s' already exists ..." % investigationdata['name']
    sys.exit(3)

print "Investigation: creating '%s' ..." % investigationdata['name']
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
userpi = investigation.addInvestigationUser(user['name'], 
                                            fullName=user['fullName'], 
                                            search=True, 
                                            role="Principal Investigator")
investigationowner.append(userpi)
investigationwriter.append(userpi)

# Additional Investigators
for u in investigationdata['invcol']:
    user = data['users'][u]
    usercol = investigation.addInvestigationUser(user['name'], 
                                                 fullName=user['fullName'], 
                                                 search=True)
    investigationwriter.append(usercol)

# More users that will get read permissions
for u in investigationdata['invguest']:
    user = data['users'][u]
    userguest = client.createUser(user['name'], fullName=user['fullName'], 
                                  search=True)
    investigationreader.append(userguest)

# Add InstrumentScientists to the writers
if investigationdata['addinstuser']:
    instrumentscientists = client.search("User <-> InstrumentScientist "
                                         "<-> Instrument[id=%d]" 
                                         % instrument.id)
    investigationwriter.extend(instrumentscientists)

owngroupname = "investigation_%d_owner" % investigation.id
writegroupname = "investigation_%d_writer" % investigation.id
readgroupname = "investigation_%d_reader" % investigation.id
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


investigationstr = "Investigation[id=%d]" % investigation.id
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


# ------------------------------------------------------------

client.logout()
