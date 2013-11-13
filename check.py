#! /usr/bin/python

from icat.client import Client
from icat.icatcheck import ICATChecker
import logging
import sys
import icat.config

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)
#logging.getLogger('icat.icatcheck').setLevel(logging.DEBUG)

icat.config.defaultsection = "hzb"
config = icat.config.Config(needlogin=False)
config.add_field('test', ("-t", "--test"), 
                 dict(help="test consistency of the ICAT client with the server", 
                      action='store_true'))
config.add_field('python', ("-p", "--python"), 
                 dict(help="Generate Python source code that match the server", 
                      action='store_true'))
conf = config.getconfig()

client = Client(conf.url, **conf.client_kwargs)
checker = ICATChecker(client)

retcode = 0

if conf.test:
    nwarn = checker.check()
    if nwarn:
        logging.warning("%d warnings", nwarn)
        retcode = 1

if conf.python:
    genealogyrules=[(r'.*Parameter$', 'parameter'), (r'','entityBaseBean')]
    print checker.pythonsrc(genealogyrules)

sys.exit(retcode)
