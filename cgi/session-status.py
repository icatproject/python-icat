#! /usr/bin/python

import cgi
import re
import ConfigParser
import yaml
import icat.cgi

date = "$Date$"
lastupdate = re.search(r'\((.*)\)',date).group(1)

configfile = "/etc/cgi/icat.cfg"
configsection = "cgi"
config = ConfigParser.ConfigParser()
config.read(configfile)

url = config.get(configsection, "url")
session = icat.cgi.Session(url)

htmlfile = config.get(configsection, "htmlfile")
f = open(htmlfile, 'r')
html = yaml.load(f)
f.close()

if session.isActive():
    statusline = html["status_in"].encode("utf8") % session.username
else:
    statusline = html["status_out"].encode("utf8")
    if session.sessionError:
        statusline += "\n<p class=\"error\">%s</p>" % session.sessionError

print "Content-Type: text/html"
print
print html["head"].encode("utf8")
print statusline
print html["foot"].encode("utf8") % lastupdate
