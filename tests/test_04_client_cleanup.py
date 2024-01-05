"""Test whether Client.cleanup() is properly called in all cases.
"""

import gc
import logging
import weakref
import pytest
import icat
import icat.config
from conftest import getConfig

logger = logging.getLogger(__name__)

class SessionRegisterClient(icat.Client):
    """An ICAT Client class that separately keeps track of open sessions.
    """

    Sessions = set()

    def login(self, auth, credentials):
        super().login(auth, credentials)
        self.Sessions.add(self.sessionId)
        return self.sessionId

    def logout(self):
        if self.sessionId:
            self.Sessions.discard(self.sessionId)
        super().logout()

# The ICAT client is instantiated in icat.config.Config.  Note that we
# must monkeypatch the icat.config module rather than icat.client, as
# the former already imported the Client class at this point.

@pytest.fixture(scope="function")
def registerClient(monkeypatch):
    SessionRegisterClient.Sessions.clear()
    monkeypatch.setattr(icat.config, "Client", SessionRegisterClient)
    yield
    logger.debug("%d sessions still active during tear down",
                 len(SessionRegisterClient.Sessions))

def test_explicit_logout(registerClient):
    """client logs in and client logs out, as simple as that.
    """
    client, conf = getConfig(confSection="acord")
    client.login(conf.auth, conf.credentials)
    assert len(SessionRegisterClient.Sessions) == 1
    client.logout()
    assert len(SessionRegisterClient.Sessions) == 0

def test_cleanup_call(registerClient):
    """client logs in, client does not log out, but cleanup() is called
    instead which automatically logs the client out.
    """
    client, conf = getConfig(confSection="acord")
    client.login(conf.auth, conf.credentials)
    assert len(SessionRegisterClient.Sessions) == 1
    client.cleanup()
    assert len(SessionRegisterClient.Sessions) == 0

def test_no_autologout_cleanup_call(registerClient):
    """client logs in, client does not log out, but cleanup() is called
    instead.  But the client is marked not to auto logout.  The
    session remains active.
    """
    client, conf = getConfig(confSection="acord")
    client.autoLogout = False
    client.login(conf.auth, conf.credentials)
    assert len(SessionRegisterClient.Sessions) == 1
    client.cleanup()
    assert len(SessionRegisterClient.Sessions) == 1

def test_client_delete(registerClient):
    """client logs in, client does not log out, but is explicitely
    deleted, which invokes cleanup(), which automatically logs the
    client out.
    """
    client, conf = getConfig(confSection="acord")
    client.login(conf.auth, conf.credentials)
    assert len(SessionRegisterClient.Sessions) == 1
    # Keep a weak reference to the client to be able to observe when it
    # has been garbage collected.
    r = weakref.ref(client)
    assert r() is client
    del client
    gc.collect()
    assert r() is None
    assert len(SessionRegisterClient.Sessions) == 0

def test_client_garbage_collect(registerClient):
    """client logs in, client does not log out, but the last reference to
    it vanisches.  The client is eventually garbage collected (forced
    in this test), which invokes cleanup(), which automatically logs
    the client out.
    """
    client, conf = getConfig(confSection="acord")
    client.login(conf.auth, conf.credentials)
    assert len(SessionRegisterClient.Sessions) == 1
    # Keep a weak reference to the client to be able to observe when it
    # has been garbage collected.
    r = weakref.ref(client)
    assert r() is client
    client = None
    gc.collect()
    assert r() is None
    assert len(SessionRegisterClient.Sessions) == 0

def test_cleanupall(registerClient):
    """Three clients, all logged in.  The first logs out, the other two
    remain logged in.  The second is marked not to auto logout.  The
    classmethod cleanupall() is called, which invokes cleanup() for
    all three.  This logs the third out, the session for the second
    remains active.
    """
    client1, conf1 = getConfig(confSection="acord")
    sessionId1 = client1.login(conf1.auth, conf1.credentials)
    client2, conf2 = getConfig(confSection="ahau")
    client2.autoLogout = False
    sessionId2 = client2.login(conf2.auth, conf2.credentials)
    client3, conf3 = getConfig(confSection="jbotu")
    sessionId3 = client3.login(conf3.auth, conf3.credentials)
    assert len(SessionRegisterClient.Sessions) == 3
    client1.logout()
    assert len(SessionRegisterClient.Sessions) == 2
    icat.Client.cleanupall()
    assert len(SessionRegisterClient.Sessions) == 1
    assert sessionId2 in SessionRegisterClient.Sessions
