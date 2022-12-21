#! /usr/bin/python
#
# Create some sample sample types.
#
# This script should be run by a member of the samplewriter group
#

import logging
import sys
import yaml
import icat
import icat.config

logging.basicConfig(level=logging.INFO)

config = icat.config.Config()
config.add_variable('datafile', ("datafile",),
                    dict(metavar="inputdata.yaml",
                         help="name of the input datafile"))
config.add_variable('sampletypename', ("sampletypename",),
                    dict(help="name of the sample type to add"))
client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)


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

print("SampleType: creating '%s' ..." % sampletypedata['name'])
sampletype = client.new("SampleType")
sampletype.name = sampletypedata['name']
sampletype.molecularFormula = sampletypedata['molecularFormula']
sampletype.facility = facility
sampletype.create()


