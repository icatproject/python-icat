#! /usr/bin/python

import logging
import icat
import icat.config

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

icat.config.defaultsection = "hzb"
conf = icat.config.Config().getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
sessionId = client.login(conf.auth, conf.credentials)

print "Login to", conf.url, "was successful."
username = client.getUserName()
print "User:", username
