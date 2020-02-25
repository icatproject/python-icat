#! /usr/bin/python

from __future__ import print_function
import icat
import icat.config

config = icat.config.Config(needlogin=False, ids=False)
client, conf = config.getconfig()
print("Connect to %s\nICAT version %s" % (conf.url, client.apiversion))
