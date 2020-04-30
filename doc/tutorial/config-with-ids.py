#! /usr/bin/python

import icat
import icat.config

config = icat.config.Config(needlogin=False, ids="optional")
client, conf = config.getconfig()
print("Connect to %s\nICAT version %s" % (conf.url, client.apiversion))
if conf.idsurl:
    print("Connect to %s\nIDS version %s"
          % (conf.idsurl, client.ids.apiversion))
else:
    print("No IDS configured")
