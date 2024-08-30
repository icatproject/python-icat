"""Verfify that deprecated features raise a deprecation warning.
"""

import pytest
import icat

# Deprecations not tested in this module:
# - Module variable icat.config.defaultsection.
#   It's easier to test this in the setting of the test_01_config.py
#   module.
# - Passing a mapping in the conditions argument to icat.query.Query
#   and icat.query.Query.addConditions(): tested in test_06_query.py
#
# No other deprecations for the moment.
