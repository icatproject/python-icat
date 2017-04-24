"""Test setting Suds Options in the client.
"""

from __future__ import print_function
import pytest
import icat
import icat.config
from icat.sslcontext import create_ssl_context, HTTPSTransport
from conftest import getConfig


def test_client_sslContext_kwarg(setupicat):
    """Set the `sslContext` keyword argument to the Client constructor.
    Issue #34.
    """
    conf = getConfig()
    kwargs = dict(conf.client_kwargs)
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
        super(MyHTTPSTransport, self).__init__(context, **kwargs)
        self.sendCounter = 0
    def send(self, request):
        result = super(MyHTTPSTransport, self).send(request)
        self.sendCounter += 1
        return result

def test_client_set_transport(setupicat):
    """Try setting a custom transport in the client using set_options().
    See Issue #33 why this is relevant.
    """
    conf = getConfig()
    client = icat.Client(conf.url, **conf.client_kwargs)
    proxy = {}
    if conf.http_proxy:
        proxy['http'] = config.http_proxy
    if conf.https_proxy:
        proxy['https'] = config.https_proxy
    transport = MyHTTPSTransport(client.sslContext, proxy=proxy)
    client.set_options(transport=transport)
    client.login(conf.auth, conf.credentials)
    assert transport.sendCounter == 1
