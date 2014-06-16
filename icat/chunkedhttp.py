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

    def _set_content_length(self, body):
        # Must not set a Content-length header!
        pass

    def _send_output(self, message_body=None):
        """Send the currently buffered request and clear the buffer.

        Appends an extra \\r\\n to the buffer.
        A message_body may be specified, to be appended to the request.
        """
        self._buffer.extend((b"", b""))
        msg = b"\r\n".join(self._buffer)
        del self._buffer[:]
        self.send(msg)

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
        host = request.get_host()
        if not host:
            raise URLError('no host given')

        if not request.has_data():
            raise URLError('no data given')

        if not request.has_header('Content-type'):
            raise URLError('no Content-type header given')

        if request.has_header('Content-length'):
            raise URLError('must not set a Content-length header')

        if not request.has_header('Transfer-Encoding'):
            request.add_unredirected_header('Transfer-Encoding', 'chunked')

        sel_host = host
        if request.has_proxy():
            scheme, sel = splittype(request.get_selector())
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

