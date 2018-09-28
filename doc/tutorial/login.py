#! /usr/bin/python

from __future__ import print_function
import icat
import icat.config

config = icat.config.Config(ids="optional")
client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)

print("Login to %s was successful." % (conf.url))
print("User: %s" % (client.getUserName()))
