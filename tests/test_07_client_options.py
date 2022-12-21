"""Test setting Suds Options in the client.
"""

import pytest
import icat
import icat.config
from icat.sslcontext import create_ssl_context, HTTPSTransport
from conftest import getConfig


def getClientKWargs(conf):
    kwargs = { 'idsurl': conf.idsurl, 'checkCert': conf.checkCert }
    if conf.http_proxy or conf.https_proxy:
        proxy={}
        if conf.http_proxy:
            proxy['http'] = conf.http_proxy
        if conf.https_proxy:
            proxy['https'] = conf.https_proxy
        kwargs['proxy'] = proxy
    return kwargs


def test_client_sslContext_kwarg(setupicat):
    """Set the `sslContext` keyword argument to the Client constructor.
    Issue #34.
    """
    _, conf = getConfig()
    kwargs = getClientKWargs(conf)
    sslverify = kwargs.pop('checkCert', True)
    cafile = kwargs.pop('caFile', None)
    capath = kwargs.pop('caPath', None)
    kwargs['sslContext'] = create_ssl_context(sslverify, cafile, capath)
    client = icat.Client(conf.url, **kwargs)
    client.login(conf.auth, conf.credentials)


# Define an HTTPSTransport that counts the messages sent to the server,
# just to have any behavior that we can observe from outside in order
# to verify that we were able to set a custom HttpTransport.
class MyHTTPSTransport(HTTPSTransport):
    def __init__(self, context, **kwargs):
        HTTPSTransport.__init__(self, context, **kwargs)
        self.sendCounter = 0
    def send(self, request):
        result = HTTPSTransport.send(self, request)
        self.sendCounter += 1
        return result

def test_client_set_transport(setupicat):
    """Try setting a custom transport in the client using set_options().
    See Issue #33 why this is relevant.
    """
    _, conf = getConfig()
    kwargs = getClientKWargs(conf)
    client = icat.Client(conf.url, **kwargs)
    proxy = {}
    if conf.http_proxy:
        proxy['http'] = conf.http_proxy
    if conf.https_proxy:
        proxy['https'] = conf.https_proxy
    transport = MyHTTPSTransport(client.sslContext, proxy=proxy)
    client.set_options(transport=transport)
    client.login(conf.auth, conf.credentials)
    assert transport.sendCounter >= 1
