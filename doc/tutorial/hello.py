#! /usr/bin/python

from __future__ import print_function
import icat.client

url = "https://icat.example.com:8181"
client = icat.client.Client(url)
print("Connect to %s\nICAT version %s" % (url, client.apiversion))
