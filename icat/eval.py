"""Evaluate a Python expression in the context of an ICAT session.

This module is intended to be run using the "-m" command line switch
to Python.  It adds an "-e" command line switch and evaluates the
Python expression given as argument to it after having started an ICAT
session.  This allows one to run simple programs as one liners
directly from the command line, as in::

  # get all Dataset ids
  $ python -m icat.eval -e 'client.search("Dataset.id")' -s root
  [102284L, 102288L, 102289L, 102293L]
"""

from __future__ import print_function
import icat
import icat.config
import sys
import logging

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

config = icat.config.Config(ids="optional")
config.add_variable('expression', ("-e", "--eval"), 
                    dict(help="Python expression to evaluate"))
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)

result = eval(conf.expression)
if result is not None:
    print(result)
