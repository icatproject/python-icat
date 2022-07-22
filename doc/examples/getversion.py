#! /usr/bin/python

import logging
import sys
import icat
import icat.config

logging.basicConfig(level=logging.INFO)

config = icat.config.Config(needlogin=False, ids="optional")
client, conf = config.getconfig()

print("Python %s\n" % (sys.version))
print("python-icat version %s\n" % (icat.__version__))
print("Connect to %s\nICAT version %s\n" % (conf.url, client.apiversion))
if client.ids:
    print("Connect to %s\nIDS version %s\n"
          % (conf.idsurl, client.ids.apiversion))
