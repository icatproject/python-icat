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
from icat.exception import *

date = "$Date$"
lastupdate = re.search(r'\((.*)\)',date).group(1)

configfile = "/etc/cgi/icat.cfg"
configsection = "cgi"
config = configparser.ConfigParser()
config.read(configfile)

url = config.get(configsection, "url")
auth = config.get(configsection, "auth")
session = icat.cgi.Session(url)

# If a session cookie is already set, log out first.
if session.isActive():
    session.logout()


htmlfile = config.get(configsection, "htmlfile")
with open(htmlfile, 'r') as f:
    html = yaml.load(f)

form = cgi.FieldStorage()

if "username" in form and "password" in form:

    # Ignore login failed error here, it is handled in the else branch
    # of if session.isActive() below.
    try:
        session.login(auth, form["username"].value, form["password"].value)
    except ICATSessionError as error:
        pass

    if session.isActive():
        print("Content-Type: text/html")
        print(session.cookie)
        print()
        print(html["head"].encode("utf8"))
        print(html["status_in"].encode("utf8") % session.username)
        print("<p>\n  Login to %s was successful.\n</p>" % url)
        print(html["foot"].encode("utf8") % lastupdate)
    else:
        print("Content-Type: text/html")
        print(session.cookie)
        print()
        print(html["head"].encode("utf8"))
        print("<h1>Welcome to ICAT</h1>\n\n<h2>Login</h2>\n")
        print("<p class=\"error\">%s</p>" % error.message)
        print(html["login_form"].encode("utf8"))
        print(html["foot"].encode("utf8") % lastupdate)

else:

    print("Content-Type: text/html")
    print(session.cookie)
    print()
    print(html["head"].encode("utf8"))
    print("<h1>Welcome to ICAT</h1>\n\n<h2>Login</h2>\n")
    print(html["login_form"].encode("utf8"))
    print(html["foot"].encode("utf8") % lastupdate)
