
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

from icat.client import *
from icat.exception import *

