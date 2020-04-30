#! /usr/bin/python

import icat
import icat.config
import logging

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

config = icat.config.Config(ids="optional")
client, conf = config.getconfig()
sessionId = client.login(conf.auth, conf.credentials)

print("Login to", conf.url, "was successful.")
username = client.getUserName()
print("User:", username)
