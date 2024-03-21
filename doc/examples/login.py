#! /usr/bin/python

import logging
import icat
import icat.config

logging.basicConfig(level=logging.INFO)

config = icat.config.Config(ids="optional")
client, conf = config.getconfig()
sessionId = client.login(conf.auth, conf.credentials)

print("Login to", conf.url, "was successful.")
username = client.getUserName()
print("User:", username)
