#! /usr/bin/python

import cgi
import yaml
import re
import icat.cgi
import ConfigParser

date = "$Date$"
lastupdate = re.search(r'\((.*)\)',date).group(1)

configfile = "/etc/cgi/icat.cfg"
configsection = "cgi"
config = ConfigParser.ConfigParser()
config.read(configfile)

url = config.get(configsection, "url")
session = icat.cgi.Session(url)
logoutsuccess = False

if session.isActive():
    session.logout()
    logoutsuccess = True


htmlfile = config.get(configsection, "htmlfile")
f = open(htmlfile, 'r')
html = yaml.load(f)
f.close()

print "Content-Type: text/html"
print session.cookie
print
print html["head"].encode("utf8")
print html["status_out"].encode("utf8")
if logoutsuccess:
    print "<p>\n  Logout successful.\n</p>"
else:
    print "<p>\n  You have not been logged in.\n</p>"
print html["foot"].encode("utf8") % lastupdate
