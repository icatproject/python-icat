"""Python interface to ICAT and IDS

This package provides a collection of modules for writing Python
programs that access an `ICAT`_ service using the SOAP interface.  It
is based on Suds and extends it with ICAT specific features.

.. _ICAT: https://icatproject.org/
"""

from ._meta import version as __version__
from .client import *
from .exception import *

