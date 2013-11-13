#! /usr/bin/python

from icat.client import Client
import logging
import icat.config

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

icat.config.defaultsection = "hzb"
conf = icat.config.Config().getconfig()

client = Client(conf.url, **conf.client_kwargs)
sessionId = client.login(conf.auth, conf.credentials)

print "Login to", conf.url, "was successful."
username = client.getUserName()
print "User:", username
