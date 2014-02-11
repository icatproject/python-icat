#! /usr/bin/python

import icat
import icat.config
import logging

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

conf = icat.config.Config(needlogin=False).getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
print "Connect to %s\nICAT version %s\n" % (conf.url, client.apiversion)
