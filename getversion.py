#! /usr/bin/python

from __future__ import print_function
import sys
import logging
import icat
import icat.config

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

conf = icat.config.Config(needlogin=False).getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
print("Python %s\n" % (sys.version))
print("python-icat version %s (%s)\n" % (icat.__version__, icat.__revision__))
print("Connect to %s\nICAT version %s\n" % (conf.url, client.apiversion))
