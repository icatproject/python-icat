"""Test :meth:`icat.client.Client.clone`.
"""

import pytest
import icat
import icat.config
from conftest import getConfig


def test_clone_minimal(setupicat):
    """Clone a simple client.  Not logged in, no ids.
    """
    client, conf = getConfig(ids=False)
    clone = client.clone()
    assert isinstance(clone, icat.client.Client)
    assert clone.url == client.url
    assert clone.ids is None
    assert clone.kwargs == client.kwargs
    assert clone.apiversion == client.apiversion


def test_clone_ids(setupicat):
    """Same as above, but configure ids this time.
    """
    client, conf = getConfig(ids="mandatory")
    clone = client.clone()
    assert isinstance(clone, icat.client.Client)
    assert clone.url == client.url
    assert clone.ids.url == client.ids.url
    assert clone.kwargs == client.kwargs
    assert clone.apiversion == client.apiversion


def test_clone_login(setupicat):
    """Clone a client that is logged in.

    The clone should not share the session.  Original client and clone
    should be able to login and out without interfering the other.
    """
    client, conf = getConfig()
    client.login(conf.auth, conf.credentials)
    clone = client.clone()
    assert clone.url == client.url
    assert clone.kwargs == client.kwargs
    assert clone.apiversion == client.apiversion
    assert clone.sessionId is None, "the clone must not inherit the session"
    # The clone may start it's own session
    clone.login(conf.auth, conf.credentials)
    assert clone.sessionId
    assert clone.sessionId != client.sessionId
    # both are still logged in as the same user
    assert clone.getUserName() == client.getUserName()
    # Now logout the clone.  This must not affect the client's session.
    clone.logout()
    assert clone.sessionId is None
    assert client.sessionId

