#! /usr/bin/python
#
# Sync the user base from a LDAP server.  Poll all user entries from
# the LDAP server and add those to the ICAT that are not already
# present.
#
# This script should be run by the ICAT user useroffice.
#

import icat
import icat.config
import ldap
import logging
import re

logging.basicConfig(level=logging.INFO)

config = icat.config.Config()
config.add_variable('ldap_uri', ("-l", "--ldap-uri"), 
                    dict(help="URL of the LDAP server"),
                    envvar='LDAP_URI')
config.add_variable('ldap_base', ("-b", "--ldap-base"), 
                    dict(help="base DN for searching the LDAP server"),
                    envvar='LDAP_BASE')
config.add_variable('ldap_filter', ("-f", "--ldap-filter"), 
                    dict(help="search filter to select the user entries"),
                    default='(uid=*)')
conf = config.getconfig()


client = icat.Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)

icatuser = { u.name:u for u in client.search("User") }


ldapclient = ldap.initialize(conf.ldap_uri)
msgid = ldapclient.search(conf.ldap_base, ldap.SCOPE_SUBTREE, conf.ldap_filter,
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

