"""Helper functions and classes related to SSL contexts.

.. note::
   This module is mostly intended for the internal use in python-icat.
   Most users will not need to use it directly or even care about it.
"""

import ssl
from urllib.request import HTTPSHandler
import suds.transport.http


def create_ssl_context(verify=True, cafile=None, capath=None):
    """Set up the SSL context.
    """
    context = ssl.create_default_context(cafile=cafile, capath=capath)
    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    return context


class HTTPSTransport(suds.transport.http.HttpTransport):
    """A modified HttpTransport using an explicit SSL context.
    """

    def __init__(self, context, **kwargs):
        """Initialize the HTTPSTransport instance.

        :param context: The SSL context to use.
        :type context: :class:`ssl.SSLContext`
        :param kwargs: keyword arguments.
        :see: :class:`suds.transport.http.HttpTransport` for the
            keyword arguments.
        """
        suds.transport.http.HttpTransport.__init__(self, **kwargs)
        self.ssl_context = context

    def u2handlers(self):
        """Get a collection of urllib handlers.
        """
        handlers = suds.transport.http.HttpTransport.u2handlers(self)
        if self.ssl_context:
            handlers.append(HTTPSHandler(context=self.ssl_context))
        return handlers
