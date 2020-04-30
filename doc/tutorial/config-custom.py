#! /usr/bin/python

import sys
import icat
import icat.config

config = icat.config.Config(ids="optional")
config.add_variable("outfile", ("-o", "--outputfile"),
                    dict(help="output file name or '-' for stdout"),
                    default="-")
client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)

if conf.outfile == "-":
    out = sys.stdout
else:
    out = open(conf.outfile, "wt")

print("Login to %s was successful." % (conf.url), file=out)
print("User: %s" % (client.getUserName()), file=out)

out.close()
