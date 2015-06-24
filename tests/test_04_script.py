"""Calling simple scripts to connect to an ICAT server.

Same as test_03_getversion.py and test_03_login.py, but calling
external scripts.
"""

import pytest
import icat
import icat.config
from conftest import callscript

def test_getversion(icatconfigfile):
    """Get version info from the ICAT server.
    """

    args = ["-c", icatconfigfile, "-s", "root"]
    callscript("getversion.py", args)


@pytest.mark.parametrize("user", ["root", "useroffice", "acord"])
def test_login(icatconfigfile, user):
    """Login to the ICAT server.
    """

    args = ["-c", icatconfigfile, "-s", user]
    callscript("login.py", args)
