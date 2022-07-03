#! /usr/bin/python

import icat
import icat.config

config = icat.config.Config(ids="optional",
                            preset={"configSection": "myicat_root"})
client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)

print("Login to %s was successful." % (conf.url))
print("User: %s" % (client.getUserName()))
