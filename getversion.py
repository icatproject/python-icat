#! /usr/bin/python

import logging
import icat
import icat.config

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

icat.config.defaultsection = "hzb"
conf = icat.config.Config(needlogin=False).getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
print "Connect to %s\nICAT version %s\n" % (conf.url, client.apiversion)
