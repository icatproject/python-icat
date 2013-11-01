#! /usr/bin/python
#
# Create some sample sample types.
#
# This script should be run by a member of the samplewriter group
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
conf.argparser.add_argument("datafile", metavar="inputdata.yaml", 
                            help="name of the input datafile")
conf.argparser.add_argument("sampletypename", 
                            help="name of the sample type to add")
conf.getconfig()
datafile = conf.args.datafile
sampletypename = conf.args.sampletypename

client = Client(conf.url)
client.login(conf.auth, conf.credentials)


# ------------------------------------------------------------
# Read input data
# ------------------------------------------------------------

try:
    if datafile == "-":
        f = sys.stdin
    else:
        f = open(datafile, 'r')
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
    sampletypedata = data['sample_types'][sampletypename]
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
