#! /usr/bin/python
#
# Import the content of the ICAT from a file or from stdin.
#
# Use the import feature from ICAT server: make the appropriate call
# to the ICAT RESTful interface to upload content to the ICAT server.
# Try to keep the command line interface as close as possible to the
# one from icatingest.py.
#

import json
import logging
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
config.add_variable('file', ("-i", "--inputfile"),
                    dict(help="input file name or '-' for stdin"),
                    default='-')
# The format argument makes in fact little sense, as there is no
# choice.  It's here for compatiblity with the command line interface
# of icatingest.py only.
config.add_variable('format', ("-f", "--format"),
                    dict(help="input file format", choices=["ICAT"]),
                    default='ICAT')
config.add_variable('duplicate', ("--duplicate",),
                    dict(help="behavior in case of duplicate objects",
                         choices=["THROW", "IGNORE", "CHECK", "OVERWRITE"]),
                    default='THROW')
# Additional arguments that icatdump.py does not provide:
config.add_variable('attributes', ("--attributes",),
                    dict(help="attributes to consider in the input",
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


args = {"sessionId": client.sessionId,
        "duplicate": conf.duplicate,
        "attributes": conf.attributes}
if conf.file == "-":
    f = sys.stdin
else:
    f = open(conf.file, 'rb')
url = conf.resturl + "port"
request = requests.post(url, data={"json":json.dumps(args)},
                        files={'file': f}, stream=True, verify=conf.checkCert)
if request.status_code != requests.codes.ok:
    try:
        raise translateError(request.json(), status=request.status_code)
    except (ValueError, TypeError):
        request.raise_for_status()

