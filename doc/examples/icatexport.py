#! /usr/bin/python
#
# Export the content of the ICAT to a file or to stdout.
#
# Use the export feature from ICAT server: make the appropriate call
# to the ICAT RESTful interface to get the ICAT content and store the
# result to a file.  Try to keep the command line interface as close
# as possible to the one from icatdump.py.
#

import json
import logging
import os
import re
import sys
import requests
import icat
import icat.config
from icat.exception import translateError

logging.basicConfig(level=logging.INFO)
logging.getLogger('requests.packages.urllib3').setLevel(logging.WARNING)

config = icat.config.Config()
config.add_variable('resturl', ("--resturl",),
                    dict(help="URL to the ICAT RESTful interface"),
                    default=True)
config.add_variable('file', ("-o", "--outputfile"),
                    dict(help="output file name or '-' for stdout"),
                    default='-')
# The format argument makes in fact little sense, as there is no
# choice.  It's here for compatiblity with the command line interface
# of icatdump.py only.
config.add_variable('format', ("-f", "--format"),
                    dict(help="output file format", choices=["ICAT"]),
                    default='ICAT')
# Additional arguments that icatdump.py does not provide:
config.add_variable('query', ("--query",),
                    dict(help="query string to select the content"),
                    optional=True)
config.add_variable('attributes', ("--attributes",),
                    dict(help="attributes to include in the output",
                         choices=["ALL", "USER"]),
                    default='USER')
client, conf = config.getconfig()

if client.apiversion < '4.4.0':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.4.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)

if conf.resturl is True:
    # As a default, derive the RESTful URL from the URL of the SOAP service.
    conf.resturl = re.sub(r'(?<=/)ICATService/.*', 'icat', conf.url)
if not conf.resturl.endswith("/"):
    conf.resturl += "/"


args = {"sessionId": client.sessionId, "attributes":conf.attributes}
if conf.query:
    args['query'] = conf.query
parameters = {"json":json.dumps(args)}
request = requests.get(conf.resturl + "port", params=parameters,
                       stream=True, verify=conf.checkCert)
if request.status_code == requests.codes.ok:
    if conf.file == "-":
        # Need to reopen stdout in binary mode.
        with os.fdopen(os.dup(sys.stdout.fileno()), 'wb') as f:
            for chunk in request.iter_content(8192):
                f.write(chunk)
    else:
        with open(conf.file, 'wb') as f:
            for chunk in request.iter_content(8192):
                f.write(chunk)
else:
    try:
        raise translateError(request.json(), status=request.status_code)
    except (ValueError, TypeError):
        request.raise_for_status()
