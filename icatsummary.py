#! /usr/bin/python
#
# Search the ICAT for all entity types and report the number of
# objects found for each type.
#

import icat
import icat.config
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.CRITICAL)

conf = icat.config.Config().getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)


print "Connect to %s" % conf.url
print "User: %s" % client.getUserName()
print

entitycolwidth = 24
print "%-*s   %s" % (entitycolwidth, "Entity", "count")
print "-" * (entitycolwidth + 3 + 5)
for entityname in client.getEntityNames():
    try:
        res = client.search(entityname)
    except icat.exception.ICATPrivilegesError:
        # ICAT 4.2.* raises a PrivilegesError if there are entities
        # matching the search but the user has no read permission to
        # any of them.  ICAT 4.3.* returns an empty list.  See ICAT
        # Issue 120.
        res = []
    print "%-*s : %d" % (entitycolwidth, entityname, len(res))
print
