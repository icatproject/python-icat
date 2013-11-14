#! /usr/bin/python
#
# Set a cookie with a given sessionId.  Only useful for testing.

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

htmlfile = config.get(configsection, "htmlfile")
f = open(htmlfile, 'r')
html = yaml.load(f)
f.close()

fields = cgi.FieldStorage()

if "sessionId" in fields:
    sessionId = fields["sessionId"].value
    statusline = "<p>SessionId set to '%s'.</p>" % sessionId
else:
    sessionId = None
    statusline = "<p>SessionId cleared.</p>"

cookie = icat.cgi.SessionCookie()
cookie.sessionId = sessionId

print "Content-Type: text/html"
print cookie
print
print html["head"].encode("utf8")
print statusline
print html["foot"].encode("utf8") % lastupdate
