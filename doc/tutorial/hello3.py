#! /usr/bin/python

from __future__ import print_function
import icat
import icat.config

conf = icat.config.Config(needlogin=False).getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
print("Connect to %s\nICAT version %s" % (conf.url, client.apiversion))
