#! /usr/bin/python

import icat

url = "https://icat.example.com:8181"
client = icat.Client(url)
print("Connect to %s\nICAT version %s" % (url, client.apiversion))
