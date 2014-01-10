"""A library for writing ICAT clients in Python.

This package provides a collection of modules for writing Python
programs that access an ICAT service using the SOAP interface.  It is
based on Suds and extends it with ICAT specific features.
"""

#
# Project properties
#

__author__    = "Rolf Krahl <rolf.krahl@helmholtz-berlin.de>"
__copyright__ = """Copyright 2013, 2014
Helmholtz-Zentrum Berlin fuer Materialien und Energie GmbH
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

 1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

 2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
__version__   = "0.3.0"

#
# Work around a bug in SUDS.
#
# The way SUDS deals with datetime values is completely broken: SUDS
# converts all incoming datetime values from the server into what it
# believes to be local time and then throws all time zone information
# away.  The problem is that SUDS' conception of the local time is
# flawed such that the result from this conversion is wrong.  Work
# around this by setting the local time zone to UTC.  As a result, all
# datetime values retrieved from the server will be in UTC, which at
# least is well defined.  The environment variable TZ must be set
# before importing suds to be effective.
#
import os
os.environ['TZ'] = 'UTC'

#
# Default import
#

from client import *
from exception import *

