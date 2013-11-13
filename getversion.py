#! /usr/bin/python

from icat.client import Client
import logging
import icat.config

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

icat.config.defaultsection = "hzb"
conf = icat.config.Config(needlogin=False)
conf.getconfig()

client = Client(conf.url, **conf.client_kwargs)
print "Connect to %s\nICAT version %s\n" % (conf.url, client.apiversion)
