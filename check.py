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
conf = icat.config.Config(needlogin=False)
conf.argparser.add_argument("-t", "--test", 
                            help="test consistency of the ICAT client "
                            "with the server", action='store_true')
conf.argparser.add_argument("-p", "--python", 
                            help="Generate Python source code that "
                            "match the server", action='store_true')
conf.getconfig()

client = Client(conf.url)
checker = ICATChecker(client)

retcode = 0

if conf.args.test:
    nwarn = checker.check()
    if nwarn:
        logging.warning("%d warnings", nwarn)
        retcode = 1

if conf.args.python:
    genealogyrules=[(r'.*Parameter$', 'parameter'), (r'','entityBaseBean')]
    print checker.pythonsrc(genealogyrules)

sys.exit(retcode)
