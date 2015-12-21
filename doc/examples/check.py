#! /usr/bin/python

from __future__ import print_function
import icat
import icat.config
import sys
import logging
from icat.icatcheck import *

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)
#logging.getLogger('icat.icatcheck').setLevel(logging.DEBUG)

config = icat.config.Config(needlogin=False)
config.add_variable('test', ("-t", "--test"), 
                    dict(help="test consistency of the ICAT client with the server", 
                         action='store_true'))
config.add_variable('python', ("-p", "--python"), 
                    dict(help="Generate Python source code that match the server", 
                         action='store_true'))
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
checker = ICATChecker(client)

retcode = 0

if conf.test:
    nwarn = checker.check()
    nwarn += checker.checkExceptions()
    if nwarn:
        logging.warning("%d warnings", nwarn)
        retcode = 1

if conf.python:
    genealogyrules=[(r'.*Parameter$', 'parameter'), (r'','entityBaseBean')]
    print(checker.pythonsrc(genealogyrules))

sys.exit(retcode)
