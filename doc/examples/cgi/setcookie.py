#! /usr/bin/python
#
# Set a cookie with a given sessionId.  Only useful for testing.

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

htmlfile = config.get(configsection, "htmlfile")
with open(htmlfile, 'r') as f:
    html = yaml.load(f)

fields = cgi.FieldStorage()

if "sessionId" in fields:
    sessionId = fields["sessionId"].value
    statusline = "<p>SessionId set to '%s'.</p>" % sessionId
else:
    sessionId = None
    statusline = "<p>SessionId cleared.</p>"

cookie = icat.cgi.SessionCookie()
cookie.sessionId = sessionId

print("Content-Type: text/html")
print(cookie)
print()
print(html["head"].encode("utf8"))
print(statusline)
print(html["foot"].encode("utf8"))
