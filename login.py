#! /usr/bin/python

from __future__ import print_function
import icat
import icat.config
import logging

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

conf = icat.config.Config(ids="optional").getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
sessionId = client.login(conf.auth, conf.credentials)

print("Login to", conf.url, "was successful.")
username = client.getUserName()
print("User:", username)
