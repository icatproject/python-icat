#! /usr/bin/python
#
# Create some sample sample types.
#
# This script should be run by a member of the samplewriter group
#

import sys
import logging
import yaml
import icat
import icat.config

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

icat.config.defaultsection = "hzb"
config = icat.config.Config()
config.add_field('datafile', ("datafile",), 
                 dict(metavar="inputdata.yaml", 
                      help="name of the input datafile"))
config.add_field('sampletypename', ("sampletypename",), 
                 dict(help="name of the sample type to add"))
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
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
    sampletypedata = data['sample_types'][conf.sampletypename]
except KeyError:
    print >> sys.stderr, "unknown sample type", sampletypename
    sys.exit(2)


# ------------------------------------------------------------
# Get some objects from ICAT we need later on
# ------------------------------------------------------------

facilityname = data['facilities'][sampletypedata['facility']]['name']
facilities = client.search("Facility[name='%s']" % facilityname)
if len(facilities): 
    facility = facilities[0]
else:
    print "Facility '%s' not found." % facilityname
    sys.exit(3)

# ------------------------------------------------------------
# Create the sample type
# ------------------------------------------------------------

sampletypes = client.search("SampleType[name='%s']" % sampletypedata['name'])
if len(sampletypes): 
    print "SampleType: '%s' already exists ..." % sampletypedata['name']
    sys.exit(3)

print "SampleType: creating '%s' ..." % sampletypedata['name']
sampletype = client.new("sampleType")
sampletype.name = sampletypedata['name']
sampletype.molecularFormula = sampletypedata['molecularFormula']
sampletype.facility = facility
sampletype.create()


# ------------------------------------------------------------

client.logout()
