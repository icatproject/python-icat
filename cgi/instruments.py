#! /usr/bin/python

from __future__ import print_function
import cgi
import re
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

fields = cgi.FieldStorage()

if session.isActive():

    print("Content-Type: text/html")
    print()
    print(html["head"].encode("utf8"))
    print(html["status_in"].encode("utf8") % session.username)

    if "name" in fields:
        i = None
        name = fields["name"].value
        if re.match(r'^[a-zA-Z0-9]+$', name):
            l = session.client.search("Instrument[name='%s']" % name)
            if l: i = l[0]
        if i:
            print("<h1>%s</h1>" % i.name)
            print("<dl>")
            print("  <dt>Name:</dt>")
            print("  <dd>%s</dd>" % i.fullName)
            print("  <dt>Description:</dt>")
            print("  <dd>%s</dd>" % i.description.encode("utf8"))
            print("  <dt>Instrument Scientists:</dt>")
            print("  <dd><ul>")
            for u in session.client.search("User <-> InstrumentScientist <-> Instrument[name='%s']" % i.name):
                print("    <li>%s</li>" % u.fullName)
            print("  </ul></dd>")
            print("</dl>")
        else:
            print("<p>Instrument not found.</p>")
    else:
        print("<h1>Instruments</h1>")
        print("<ul>")
        for i in session.client.search("Instrument"):
            print("<li><a href=\"/cgi-bin/instruments.py?name=%s\">%s</a></li>" % (i.name, i.fullName))
        print("</ul>")

    print(html["foot"].encode("utf8"))

else:

    print("Content-Type: text/html")
    print()
    print(html["head"].encode("utf8"))
    print(html["status_out"].encode("utf8"))
    print("<p>\n  You need to login first.\n</p>")
    print(html["foot"].encode("utf8"))
