#! /usr/bin/python

from __future__ import print_function
import icat
import icat.config

conf = icat.config.Config(ids="optional").getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)

print("Login to %s was successful." % (conf.url))
print("User: %s" % (client.getUserName()))
