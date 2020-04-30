#! /usr/bin/python

import icat.client

url = "https://icat.example.com:8181"
client = icat.client.Client(url, checkCert=False)
print("Connect to %s\nICAT version %s" % (url, client.apiversion))
