"""Test connect to an ICAT and an IDS server and query the version.
"""

import pytest
import icat
import icat.config
import conftest
from conftest import getConfig


def test_get_icat_version():
    """Query the version from the test ICAT server.

    This implicitly tests that the test ICAT server is properly
    configured and that we can connect to it.
    """

    client, conf = getConfig(needlogin=False, ids=False)
    # python-icat supports ICAT server 4.3 or newer.  But actually, we
    # just want to check that client.apiversion is set and supports
    # comparison with version strings.
    assert client.apiversion > '1.0.0'
    print("\nConnect to %s\nICAT version %s\n" % (conf.url, client.apiversion))


def test_ids_version_calls():
    """Test that client.ids.getApiVersion() and client.ids.version() yield
    coherent results.  Ref. #131.
    """

    client, conf = getConfig(needlogin=False, ids="mandatory")
    ids_apiversion = client.ids.getApiVersion()
    ids_verion = client.ids.version()
    assert ids_apiversion == ids_verion["version"]


def test_get_ids_version():
    """Query the version from the test IDS server.

    This implicitly tests that the test ICAT and IDS servers are
    properly configured and that we can connect to them.
    """

    client, conf = getConfig(needlogin=False, ids="mandatory")
    # python-icat supports all publicly released IDS server version,
    # e.g. 1.0.0 or newer.  But actually, we just want to check that
    # client.apiversion is set and supports comparison with version
    # strings.
    assert client.ids.apiversion >= '1.0.0'
    print("\nConnect to %s\nIDS version %s\n" 
          % (conf.idsurl, client.ids.apiversion))
