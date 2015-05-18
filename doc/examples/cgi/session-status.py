#! /usr/bin/python

from __future__ import print_function
import cgi
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import yaml
import icat.cgi

configfile = "/etc/cgi/icat.cfg"
configsection = "cgi"
config = configparser.ConfigParser()
config.read(configfile)

url = config.get(configsection, "url")
session = icat.cgi.Session(url)

htmlfile = config.get(configsection, "htmlfile")
with open(htmlfile, 'r') as f:
    html = yaml.load(f)

if session.isActive():
    statusline = html["status_in"].encode("utf8") % session.username
else:
    statusline = html["status_out"].encode("utf8")
    if session.sessionError:
        statusline += "\n<p class=\"error\">%s</p>" % session.sessionError

print("Content-Type: text/html")
print()
print(html["head"].encode("utf8"))
print(statusline)
print(html["foot"].encode("utf8"))
