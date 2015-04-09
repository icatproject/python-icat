#! /usr/bin/python
#
# Export the content of the ICAT to a file or to stdout.
#
# Use the export feature from ICAT server: make the appropriate call
# to the ICAT RESTful interface to get the ICAT content and store the
# result to a file.  Try to keep the command line interface as close
# as possible to the one from icatdump.py.
#

import sys
from urllib2 import Request, ProxyHandler, build_opener
from urllib import urlencode
import json
import re
import logging
import icat
import icat.config

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

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
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
if client.apiversion < '4.3.99':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.4.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)

if conf.resturl is True:
    # As a default, derive the RESTful URL from the URL to the SOAP service.
    conf.resturl = re.sub(r'(?<=/)ICATService/.*', 'icat', conf.url)
if not conf.resturl.endswith("/"):
    conf.resturl += "/"

if client.options.proxy:
    opener = build_opener(ProxyHandler(client.options.proxy))
else:
    opener = build_opener()


class RESTRequest(Request):

    def __init__(self, url, parameters, data=None, headers={}, method=None):

        if parameters:
            parameters = urlencode(parameters)
            if method == "POST":
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                data = parameters.encode('ascii')
            else:
                url += "?" + parameters
        Request.__init__(self, url, data, headers)
        self.method = method

        self.add_header("Cache-Control", "no-cache")
        self.add_header("Pragma", "no-cache")
        self.add_header("Accept", 
                        "text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2")
        self.add_header("Connection", "keep-alive") 

    def get_method(self):
        """Return a string indicating the HTTP request method."""
        if self.method:
            return self.method
        elif self.data is not None:
            return "POST"
        else:
            return "GET"

def copyfile(infile, outfile, chunksize=8192):
    """Read all data from infile and write them to outfile.
    """
    while True:
        chunk = infile.read(chunksize)
        if not chunk:
            break
        outfile.write(chunk)


# Leave query out which means the whole ICAT.
args = {"sessionId": client.sessionId, "attributes":conf.attributes}
if conf.query:
    args['query'] = conf.query
parameters = {"json":json.dumps(args)}
req = RESTRequest(conf.resturl + "port", parameters)
response = opener.open(req)
if conf.file == "-":
    copyfile(response, sys.stdout)
else:
    with open(conf.file, 'wb') as f:
        copyfile(response, f)

