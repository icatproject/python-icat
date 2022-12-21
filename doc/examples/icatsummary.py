#! /usr/bin/python
#
# Search the ICAT for all entity types and report the number of
# objects found for each type.
#

import logging
import icat
import icat.config

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
    res = client.assertedSearch("SELECT COUNT(e) FROM %s e" % entityname)[0]
    print("%-*s : %d" % (entitycolwidth, entityname, res))
print()
