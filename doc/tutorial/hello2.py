#! /usr/bin/python

from __future__ import print_function
import icat

url = "https://icat.example.com:8181/ICATService/ICAT?wsdl"
client = icat.Client(url)
print("Connect to %s\nICAT version %s" % (url, client.apiversion))
