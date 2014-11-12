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
initobj(investigation, investigationdata)
investigation.facility = facility
investigation.type = investigation_type
investigation.create()
investigation.addInstrument(instrument)
investigation.addKeywords(investigationdata['keywords'])


# ------------------------------------------------------------
# Add users and setup access groups
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
# Setup InvestigationGroups or permissions
# ------------------------------------------------------------

# InvestigationGroup have been introduced with ICAT 4.4.  If
# available, just create them.  Then we don't need to setup
# permissions, as the static rules created in init-icat.py apply.  For
# older versions of ICAT, we need to setup per investigation rules.

if client.apiversion > '4.3.99':

    investigation.addInvestigationGroup(owngroup, role="owner")
    investigation.addInvestigationGroup(writegroup, role="writer")
    investigation.addInvestigationGroup(readgroup, role="reader")

else:

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
                 "Publication <-> %s", ] 

    invcond = "Investigation[name='%s']" % investigation.name

    # set permissions for the writer group
    client.createRules("R", [ invcond ], writegroup)
    client.createRules("CRUD", [ s % invcond for s in invitems ], writegroup)

    # set permissions for the reader group
    client.createRules("R", [ invcond ], readgroup)
    client.createRules("R", [ s % invcond for s in invitems ], readgroup)

    # set owners permissions
    if client.apiversion < '4.2.99':
        groupclass = "Group"
    else:
        groupclass = "Grouping"
    items = [ "UserGroup <-> %s[name='%s']" % (groupclass, s) 
              for s in [ writegroupname, readgroupname ] ]
    client.createRules("CRUD", items, owngroup)
    items = [ "%s[name='%s']" % (groupclass, s) 
              for s in [ writegroupname, readgroupname ] ]
    client.createRules("R", items, owngroup)

