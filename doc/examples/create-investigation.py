#! /usr/bin/python
#
# Create some sample investigations.
#
# This script should be run by the ICAT user useroffice.
#

import logging
import sys
import yaml
import icat
import icat.config
from icat.helper import parse_attr_string
from icat.query import Query

logging.basicConfig(level=logging.INFO)

config = icat.config.Config()
config.add_variable('datafile', ("datafile",),
                    dict(metavar="inputdata.yaml",
                         help="name of the input datafile"))
config.add_variable('investigationname', ("investigationname",),
                    dict(help="name of the investigation to add"))
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
investigation = client.new("Investigation")
initobj(investigation, investigationdata)
investigation.facility = facility
investigation.type = investigation_type
if 'parameters' in investigationdata:
    for pdata in investigationdata['parameters']:
        ip = client.new("InvestigationParameter")
        initobj(ip, pdata)
        ptdata = data['parameter_types'][pdata['type']]
        query = ("ParameterType [name='%s' AND units='%s']"
                 % (ptdata['name'], ptdata['units']))
        ip.type = client.assertedSearch(query)[0]
        investigation.parameters.append(ip)
if 'shifts' in investigationdata:
    for sdata in investigationdata['shifts']:
        s = client.new("Shift")
        initobj(s, sdata)
        if 'instrument' in s.InstRel:
            s.instrument = instrument
        investigation.shifts.append(s)
if 'investigationFacilityCycles' in investigation.InstMRel:
    # ICAT 5.0 or newer
    sd = investigation.startDate or investigation.endDate
    ed = investigation.endDate or investigation.startDate
    if sd and ed:
        query = Query(client, "FacilityCycle", conditions={
            "startDate": "<= '%s'" % parse_attr_string(ed, "Date"),
            "endDate": "> '%s'" % parse_attr_string(sd, "Date"),
        })
        for fc in client.search(query):
            ifc = client.new("InvestigationFacilityCycle", facilityCycle=fc)
            investigation.investigationFacilityCycles.append(ifc)
if 'fundingReferences' in investigation.InstMRel:
    for fr in investigationdata['fundingReferences']:
        funding_ref = client.new("FundingReference")
        initobj(funding_ref, data['fundings'][fr])
        try:
            funding_ref.create()
        except icat.ICATObjectExistsError:
            funding_ref = client.searchMatching(funding_ref)
        inv_fund = client.new("InvestigationFunding", funding=funding_ref)
        investigation.fundingReferences.append(inv_fund)
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
userpi = getUser(client, user)
investigation.addInvestigationUsers([userpi], role="Principal Investigator")
investigationowner.append(userpi)
investigationwriter.append(userpi)

# Additional Investigators
usercols = []
for u in investigationdata['invcol']:
    user = data['users'][u]
    usercols.append(getUser(client, user))
investigation.addInvestigationUsers(usercols)
investigationwriter.extend(usercols)

# More users that will get read permissions
for u in investigationdata['invguest']:
    user = data['users'][u]
    userguest = getUser(client, user)
    investigationreader.append(userguest)

owngroupname = "investigation_%s_owner" % investigation.name
writegroupname = "investigation_%s_writer" % investigation.name
readgroupname = "investigation_%s_reader" % investigation.name
owngroup = client.createGroup(owngroupname, investigationowner)
writegroup = client.createGroup(writegroupname, investigationwriter)
readgroup = client.createGroup(readgroupname, investigationreader)

investigation.addInvestigationGroup(owngroup, role="owner")
investigation.addInvestigationGroup(writegroup, role="writer")
investigation.addInvestigationGroup(readgroup, role="reader")
