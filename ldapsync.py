#! /usr/bin/python
#
# Sync the user base from a LDAP server.  Poll all user entries from
# the LDAP server and add those to the ICAT that are not already
# present.
#
# This script should be run by the ICAT user useroffice.
#

import ldap
from icat.client import Client
import logging
import icat.config
import re

logging.basicConfig(level=logging.INFO)

# the LDAP search filter is hard wired by now
ldapfilter = '(uid=*)'

icat.config.defaultsection = "hzb"
conf = icat.config.Config()
conf.add_field('ldapuri', ("-l", "--ldapuri"), 
               dict(help="URL of the LDAP server"))
conf.add_field('ldapbase', ("-b", "--ldapbase"), 
               dict(help="base DN for searching the LDAP server"))
conf.getconfig()


client = Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)

icatuser = { u.name:u for u in client.search("User") }


ldapclient = ldap.initialize(conf.ldapuri)
msgid = ldapclient.search(conf.ldapbase, ldap.SCOPE_SUBTREE, ldapfilter,
                          ('uid', 'displayName', 'givenName', 'sn', 'cn'))

while True:
    (t, data) = ldapclient.result(msgid, 0)
    if data:

        for dn, attrs in data:
            uid = attrs['uid'][0]
            # We have a mess of real accounts, system accounts, test
            # accounts, inactive records, and plain garbage in the
            # LDAP.  In order to filter out at least the system
            # accounts, we say that if it got a givenName, then it
            # belongs to a real person.  This seems to be the only
            # working criterion.
            if 'givenName' in attrs and uid not in icatuser:
                fullName = None
                if 'displayName' in attrs:
                    displayName = attrs['displayName'][0]
                    m = re.match(r'^([^,]*),\s*([^,]*)$', displayName)
                    if m:
                        fullName = "%s %s" % m.group(2, 1)
                    else:
                        fullName = displayName
                elif 'sn' in attrs:
                    fullName = "%s %s" % (attrs['givenName'][0], attrs['sn'][0])
                elif 'cn' in attrs:
                    fullName = attrs['cn'][0]

                client.createUser(uid, fullName=fullName)

    else:
        break

