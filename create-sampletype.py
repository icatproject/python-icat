#! /usr/bin/python
#
# Create some sample sample types.
#
# This script should be run by a member of the samplewriter group
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
config.add_variable('sampletypename', ("sampletypename",), 
                    dict(help="name of the sample type to add"))
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
    sampletypedata = data['sample_types'][conf.sampletypename]
except KeyError:
    raise RuntimeError("unknown sample type '%s'" % conf.sampletypename)


# ------------------------------------------------------------
# Get some objects from ICAT we need later on
# ------------------------------------------------------------

facilityname = data['facilities'][sampletypedata['facility']]['name']
facility = client.assertedSearch("Facility[name='%s']" % facilityname)[0]

# ------------------------------------------------------------
# Create the sample type
# ------------------------------------------------------------

try:
    searchexp = "SampleType[name='%s']" % sampletypedata['name']
    client.assertedSearch(searchexp, assertmax=None)
except icat.exception.SearchResultError:
    pass
else:
    raise RuntimeError("SampleType: '%s' already exists." 
                       % sampletypedata['name'])

print "SampleType: creating '%s' ..." % sampletypedata['name']
sampletype = client.new("sampleType")
sampletype.name = sampletypedata['name']
sampletype.molecularFormula = sampletypedata['molecularFormula']
sampletype.facility = facility
sampletype.create()


