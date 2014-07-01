"""HTTP with chunked transfer encoding for urllib.

This module provides the handlers ChunkedHTTPHandler and
ChunkedHTTPSHandler that are suitable to be used as openers for
urllib2.  These handlers differs from the standard counterparts in
that they send the data using chunked transfer encoding to the HTTP
server.

**Note**: This module might be useful independently of python-icat.
It is included here because python-icat uses it internally, but it is
not considered to be part of the API.  Changes in this module are not
considered API changes of python-icat.  It may even be removed from
future versions of the python-icat distribution without further
notice.
"""

from httplib import HTTPConnection, HTTPSConnection
from urllib2 import URLError, HTTPHandler, HTTPSHandler


def stringiterator(buffer, chunksize):
    while len(buffer) > chunksize:
        yield buffer[:chunksize]
        buffer = buffer[chunksize:]
    if len(buffer) > 0:
        yield buffer

def fileiterator(f, chunksize):
    while True:
        chunk = f.read(chunksize)
        if not chunk:
            break
        yield chunk

class ChunkedHTTPConnectionMixin:
    """Implement chunked transfer encoding in HTTP.

    This is designed as a mixin class to modify either HTTPConnection
    or HTTPSConnection accordingly.
    """

    default_chunk_size = 8192

    def _send_request(self, method, url, body, headers):
        # This method is taken and modified from the Python 2.7
        # httplib.py to prevent it from trying to set a Content-length
        # header and to hook in our send_body_chunked() method.
        # Admitted, it's an evil hack.
        header_names = dict.fromkeys([k.lower() for k in headers])
        skips = {}
        if 'host' in header_names:
            skips['skip_host'] = 1
        if 'accept-encoding' in header_names:
            skips['skip_accept_encoding'] = 1

        self.putrequest(method, url, **skips)

        for hdr, value in headers.iteritems():
            self.putheader(hdr, value)
        self.endheaders()
        self.send_body_chunked(body)

    def send_body_chunked(self, message_body=None):
        """Send the message_body with chunked transfer encoding.

        The empty line separating the headers from the body must have
        been send before calling this method.
        """
        if message_body is not None:
            chunksize = getattr(self, 'chunksize', self.default_chunk_size)
            if isinstance(message_body, type(b'')):
                bodyiter = stringiterator(message_body, chunksize)
            elif isinstance(message_body, type(u'')):
                bodyiter = stringiterator(message_body.encode('ascii'), 
                                          chunksize)
            elif hasattr(message_body, 'read'):
                bodyiter = fileiterator(message_body, chunksize)
            elif hasattr(message_body, '__iter__'):
                bodyiter = message_body
            else:
                raise TypeError("expect either a string, a file, "
                                "or an iterable")
            for chunk in bodyiter:
                self.send(hex(len(chunk))[2:].encode('ascii') 
                          + b"\r\n" + chunk + b"\r\n")
            self.send(b"0\r\n\r\n")

class ChunkedHTTPConnection(ChunkedHTTPConnectionMixin, HTTPConnection):
    pass

class ChunkedHTTPSConnection(ChunkedHTTPConnectionMixin, HTTPSConnection):
    pass


class ChunkedHTTPHandlerMixin:
    """Internal helper class.

    This is designed as a mixin class to modify either HTTPHandler or
    HTTPSHandler accordingly.  It overrides do_request_() inherited
    from AbstractHTTPHandler.
    """

    def do_request_(self, request):
        # The original method from AbstractHTTPHandler sets some
        # defaults that are unsuitable for our use case.  In
        # particular it tries to enforce Content-length to be set (and
        # fails doing so if data is not a string), while for chunked
        # transfer encoding Content-length must not be set.

        # Compatibility: in Python 2, we must call get_host() which
        # extracts the host part from the URL.  In Python 3, the
        # splitting is already done in the constructor, so we may just
        # access the attribute host instead.  In Python 3.4,
        # get_host() has been removed.
        try:
            host = request.get_host()
        except AttributeError:
            host = request.host
        if not host:
            raise URLError('no host given')

        if request.data is None:
            raise URLError('no data given')

        if not request.has_header('Content-type'):
            raise URLError('no Content-type header given')

        if request.has_header('Content-length'):
            raise URLError('must not set a Content-length header')

        if not request.has_header('Transfer-Encoding'):
            request.add_unredirected_header('Transfer-Encoding', 'chunked')

        sel_host = host
        if request.has_proxy():
            # Similar compatibility issue for selector as for host.
            try:
                selector = request.get_selector()
            except AttributeError:
                selector = request.selector
            scheme, sel = splittype(selector)
            sel_host, sel_path = splithost(sel)
        if not request.has_header('Host'):
            request.add_unredirected_header('Host', sel_host)
        for name, value in self.parent.addheaders:
            name = name.capitalize()
            if not request.has_header(name):
                request.add_unredirected_header(name, value)

        return request

class ChunkedHTTPHandler(ChunkedHTTPHandlerMixin, HTTPHandler):

    def http_open(self, req):
        return self.do_open(ChunkedHTTPConnection, req)

    http_request = ChunkedHTTPHandlerMixin.do_request_

class ChunkedHTTPSHandler(ChunkedHTTPHandlerMixin, HTTPSHandler):

    def https_open(self, req):
        return self.do_open(ChunkedHTTPSConnection, req)

    https_request = ChunkedHTTPHandlerMixin.do_request_

