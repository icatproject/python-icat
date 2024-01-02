"""Evaluate a Python expression in the context of an ICAT session.

This module is intended to be run using the "-m" command line switch
to Python.  It adds an "-e" command line switch and evaluates the
Python expression given as argument to it after having started an ICAT
session.  This allows one to run simple programs as one liners
directly from the command line, as in::

  # get all Dataset ids
  $ python -m icat.eval -e 'client.search("Dataset.id")' -s root
  [102284, 102288, 102289, 102293]
"""

import logging
from .config import Config

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    config = Config(ids="optional")
    config.add_variable('expression', ("-e", "--eval"), 
                        dict(help="Python expression to evaluate"))
    client, conf = config.getconfig()

    client.login(conf.auth, conf.credentials)

    result = eval(conf.expression)
    if result is not None:
        print(result)
