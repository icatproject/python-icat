#! /usr/bin/python
#
# Search the ICAT for all entity types and report the number of
# objects found for each type.
#

from __future__ import print_function
import icat
import icat.config
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.CRITICAL)

client, conf = icat.config.Config().getconfig()
client.login(conf.auth, conf.credentials)


print("User: %s" % client.getUserName())
print()

entitycolwidth = 24
print("%-*s   %s" % (entitycolwidth, "Entity", "count"))
print("-" * (entitycolwidth + 3 + 5))
for entityname in client.getEntityNames():
    if entityname == "Log":
        continue
    try:
        res = client.search("SELECT COUNT(e) FROM %s e" % entityname)[0]
    except icat.exception.ICATPrivilegesError:
        # ICAT 4.2.* raises a PrivilegesError if there are entities
        # matching the search but the user has no read permission to
        # any of them.  ICAT 4.3.* returns an empty list.  See ICAT
        # Issue 120.
        res = 0
    except IndexError:
        # ref. ICAT issue 131
        res = 0
    print("%-*s : %d" % (entitycolwidth, entityname, res))
print()
