#! /usr/bin/python
#
# Dump the objects related to a single investigation to a file or to
# stdout.
#
# This is intended to demonstrate the dumpfile API.  The result
# should be a subset of the dumpfile created by icatdump.
#

import logging
import icat
import icat.config
from icat.dumpfile import open_dumpfile
import icat.dumpfile_xml
import icat.dumpfile_yaml

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

formats = icat.dumpfile.Backends.keys()
config = icat.config.Config()
config.add_variable('file', ("-o", "--outputfile"), 
                    dict(help="output file name or '-' for stdout"),
                    default='-')
config.add_variable('format', ("-f", "--format"), 
                    dict(help="output file format", choices=formats),
                    default='YAML')
config.add_variable('investigation', ("investigation",), 
                    dict(help="name and optionally visit id "
                         "(separated by a colon) of the investigation"))
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
if client.apiversion < '4.3.99':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.4.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


# ------------------------------------------------------------
# helper
# ------------------------------------------------------------

def getinvestigation(invid):
    """Search the investigation id from name and optionally visitid."""
    l = invid.split(':')
    if len(l) == 1:
        # No colon, invid == name
        searchexp = "Investigation.id [name='%s']" % tuple(l)
    elif len(l) == 2:
        # one colon, invid == name:visitId
        searchexp = "Investigation.id [name='%s' AND visitId='%s']" % tuple(l)
    else:
        # too many colons
        raise RuntimeError("Invalid investigation identifier '%s'" % invid)
    return (client.assertedSearch(searchexp)[0])

def mergesearch(sexps):
    """Do many searches and merge the results in one list excluding dups."""
    objs = set()
    for se in sexps:
        objs.update(client.search(se))
    return list(objs)


# ------------------------------------------------------------
# Do it
# ------------------------------------------------------------

invid = getinvestigation(conf.investigation)


# We need the users related to our investigation via
# InvestigationUser, the users member of one of the groups related via
# InvestigationGroup, and the instrument scientists from the
# instruments related to the investigations.  These are independent
# searches, but the results are likely to overlap.  So we need to
# search and merge results first.  Similar situation for ParameterType.
usersearch = [("User <-> InvestigationUser <-> Investigation [id=%d]"),
              ("User <-> UserGroup <-> Grouping <-> InvestigationGroup "
               "<-> Investigation [id=%d]"),
              ("User <-> InstrumentScientist <-> Instrument "
               "<-> InvestigationInstrument <-> Investigation [id=%d]")]
ptsearch = [("ParameterType INCLUDE Facility, PermissibleStringValue "
             "<-> InvestigationParameter <-> Investigation [id=%d]"), 
            ("ParameterType INCLUDE Facility, PermissibleStringValue "
             "<-> SampleParameter <-> Sample <-> Investigation [id=%d]"), 
            ("ParameterType INCLUDE Facility, PermissibleStringValue "
             "<-> DatasetParameter <-> Dataset <-> Investigation [id=%d]"), 
            ("ParameterType INCLUDE Facility, PermissibleStringValue "
             "<-> DatafileParameter <-> Datafile <-> Dataset "
             "<-> Investigation [id=%d]"), ]

# We may either provide a search expression or a list of objects.
authtypes = [mergesearch([s % invid for s in usersearch]),
             ("Grouping INCLUDE UserGroup, User <-> InvestigationGroup "
              "<-> Investigation [id=%d]" % invid)]
statictypes = [("Facility"),
               ("Instrument INCLUDE Facility, InstrumentScientist, User "
                "<-> InvestigationInstrument <-> Investigation [id=%d]" 
                % invid),
               (mergesearch([s % invid for s in ptsearch])),
               ("InvestigationType INCLUDE Facility "
                "<-> Investigation [id=%d]" % invid),
               ("SampleType INCLUDE Facility "
                "<-> Sample <-> Investigation [id=%d]" % invid),
               ("DatasetType INCLUDE Facility "
                "<-> Dataset <-> Investigation [id=%d]" % invid),
               ("DatafileFormat INCLUDE Facility "
                "<-> Datafile <-> Dataset <-> Investigation [id=%d]" % invid)]
investtypes = [("SELECT i FROM Investigation i WHERE i.id = %d "
                "INCLUDE i.facility, i.type AS it, it.facility, "
                "i.investigationInstruments AS ii, "
                "ii.instrument AS iii, iii.facility, "
                "i.shifts, i.keywords, i.publications, "
                "i.investigationUsers AS iu, iu.user, "
                "i.investigationGroups AS ig, ig.grouping, "
                "i.parameters AS ip, ip.type AS ipt, ipt.facility"
                % invid), 
               ("SELECT o FROM Sample o JOIN o.investigation i "
                "WHERE i.id = %d "
                "INCLUDE o.investigation, o.type AS ot, ot.facility, "
                "o.parameters AS op, op.type AS opt, opt.facility" % invid),
               ("SELECT o FROM Dataset o JOIN o.investigation i "
                "WHERE i.id = %d "
                "INCLUDE o.investigation, o.type AS ot, ot.facility, o.sample, "
                "o.parameters AS op, op.type AS opt, opt.facility" % invid),
               ("SELECT o FROM Datafile o "
                "JOIN o.dataset ds JOIN ds.investigation i "
                "WHERE i.id = %d "
                "INCLUDE o.dataset, o.datafileFormat AS dff, dff.facility, "
                "o.parameters AS op, op.type AS opt, opt.facility" % invid)]

with open_dumpfile(client, conf.file, conf.format, 'w') as dumpfile:
    dumpfile.writedata(authtypes)
    dumpfile.writedata(statictypes)
    dumpfile.writedata(investtypes)
