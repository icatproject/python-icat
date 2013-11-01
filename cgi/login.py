#! /usr/bin/python

import cgi
import yaml
import re
import icat.cgi
import icat.exception
import ConfigParser

date = "$Date$"
lastupdate = re.search(r'\((.*)\)',date).group(1)

configfile = "/etc/cgi/icat.cfg"
configsection = "cgi"
config = ConfigParser.ConfigParser()
config.read(configfile)

url = config.get(configsection, "url")
auth = config.get(configsection, "auth")
session = icat.cgi.Session(url)

# If a session cookie is already set, log out first.
if session.isActive():
    session.logout()


htmlfile = config.get(configsection, "htmlfile")
f = open(htmlfile, 'r')
html = yaml.load(f)
f.close()

form = cgi.FieldStorage()

if "username" in form and "password" in form:

    # Ignore login failed error here, it is handled in the else branch
    # of if session.isActive() below.
    try:
        session.login(auth, form["username"].value, form["password"].value)
    except icat.exception.ICATSessionError as error:
        pass

    if session.isActive():
        print "Content-Type: text/html"
        print session.cookie
        print
        print html["head"].encode("utf8")
        print html["status_in"].encode("utf8") % session.username
        print "<p>\n  Login to %s was successful.\n</p>" % url
        print html["foot"].encode("utf8") % lastupdate
    else:
        print "Content-Type: text/html"
        print session.cookie
        print
        print html["head"].encode("utf8")
        print "<h1>Welcome to ICAT</h1>\n\n<h2>Login</h2>\n"
        print "<p class=\"error\">%s</p>" % error.message
        print html["login_form"].encode("utf8")
        print html["foot"].encode("utf8") % lastupdate

else:

    print "Content-Type: text/html"
    print session.cookie
    print
    print html["head"].encode("utf8")
    print "<h1>Welcome to ICAT</h1>\n\n<h2>Login</h2>\n"
    print html["login_form"].encode("utf8")
    print html["foot"].encode("utf8") % lastupdate
