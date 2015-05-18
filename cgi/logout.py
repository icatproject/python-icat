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
logoutsuccess = False

if session.isActive():
    session.logout()
    logoutsuccess = True


htmlfile = config.get(configsection, "htmlfile")
with open(htmlfile, 'r') as f:
    html = yaml.load(f)

print("Content-Type: text/html")
print(session.cookie)
print()
print(html["head"].encode("utf8"))
print(html["status_out"].encode("utf8"))
if logoutsuccess:
    print("<p>\n  Logout successful.\n</p>")
else:
    print("<p>\n  You have not been logged in.\n</p>")
print(html["foot"].encode("utf8"))
