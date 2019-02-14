"""Provide the IDSClient class.

This module is derived from the Python IDS client from the original
`IDS distribution`_.  Permission to include it in python-icat and to
publish it under its license has generously been granted by its
author.

.. _IDS distribution: http://code.google.com/p/icat-data-service/
"""

import sys
try:
    # Python 3.3 and newer
    from collections.abc import Mapping, Iterable
except ImportError:
    # Python 2
    from collections import Mapping, Iterable
import ssl
from urllib2 import Request, HTTPError
from urllib2 import HTTPDefaultErrorHandler, ProxyHandler
from urllib2 import build_opener
from urllib import urlencode
import json
import zlib
import re
from distutils.version import StrictVersion as Version
import getpass

from icat.entity import Entity
from icat.exception import *

# For Python versions older then 3.6.0b1, the standard library does
# not support sending the body using chunked transfer encoding.  Need
# to replace the HTTPHandler with our modified versions from
# icat.chunkedhttp in this case.
if sys.version_info < (3, 6, 0, 'beta'):
    from icat.chunkedhttp import HTTPHandler, HTTPSHandler
else:
    from urllib2 import HTTPHandler, HTTPSHandler

__all__ = ['DataSelection', 'IDSClient']


class IDSRequest(Request):

    def __init__(self, url, parameters={}, data=None, headers={}, method=None):

        if parameters:
            parameters = urlencode(parameters)
            if method == "POST":
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                data = parameters.encode('ascii')
            else:
                url += "?" + parameters
        Request.__init__(self, url, data, headers)
        self.method = method

        self.add_header("Cache-Control", "no-cache")
        self.add_header("Pragma", "no-cache")
        self.add_header("Accept", 
                        "text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2")
        self.add_header("Connection", "keep-alive") 

    def get_method(self):
        """Return a string indicating the HTTP request method."""
        if self.method:
            return self.method
        elif self.data is not None:
            return "POST"
        else:
            return "GET"


class IDSHTTPErrorHandler(HTTPDefaultErrorHandler):
    def http_error_default(self, req, fp, code, msg, hdrs):
        """Handle HTTP errors, in particular errors raised by the IDS server."""
        content = fp.read().decode('ascii')
        try:
            err = translateError(json.loads(content), code, "IDS")
        except Exception:
            err = HTTPError(req.get_full_url(), code, msg, hdrs, fp)
        raise err


class ChunkedFileReader(object):
    """An iterator that yields chunks of data read from a file.
    As a side effect, a checksum of the read data is calulated.
    """
    def __init__(self, inputfile, chunksize=8192):
        self.inputfile = inputfile
        self.chunksize = chunksize
        self.crc32 = 0

    def __iter__(self):
        return self

    def next(self):
        chunk = self.inputfile.read(self.chunksize)
        if chunk:
            self.crc32 = zlib.crc32(chunk, self.crc32)
            return chunk
        else:
            raise StopIteration


class DataSelection(object):
    """A set of data to be processed by the ICAT Data Service.

    This can be passed as the `selection` argument to
    :class:`icat.ids.IDSClient` method calls.
    """

    def __init__(self, objs=None):
        super(DataSelection, self).__init__()
        self.invIds = set()
        self.dsIds = set()
        self.dfIds = set()
        if objs:
            self.extend(objs)

    def __len__(self):
        return len(self.invIds) + len(self.dsIds) + len(self.dfIds)

    def __str__(self):
        return ("{invIds:%s, dsIds:%s, dfIds:%s}" 
                % (self.invIds, self.dsIds, self.dfIds))

    def extend(self, objs):
        """Add `objs` to the DataSelection.

        :param objs: either a dict having some of the keys
            `investigationIds`, `datasetIds`, and `datafileIds`
            with a list of object ids as value respectively, or a list
            of entity objects, or another data selection.
        :type objs: :class:`dict`, :class:`list` of
            :class:`icat.entity.Entity`, or
            :class:`icat.ids.DataSelection`
        """
        if isinstance(objs, DataSelection):
            self.invIds.update(objs.invIds)
            self.dsIds.update(objs.dsIds)
            self.dfIds.update(objs.dfIds)
        elif isinstance(objs, Mapping):
            self.invIds.update(objs.get('investigationIds', []))
            self.dsIds.update(objs.get('datasetIds', []))
            self.dfIds.update(objs.get('datafileIds', []))
        elif isinstance(objs, Iterable):
            for o in objs:
                if isinstance(o, Entity):
                    if o.BeanName == 'Investigation':
                        self.invIds.add(o.id)
                    elif o.BeanName == 'Dataset':
                        self.dsIds.add(o.id)
                    elif o.BeanName == 'Datafile':
                        self.dfIds.add(o.id)
                    else:
                        raise ValueError("invalid object '%s'." % o.BeanName)
                else:
                    raise TypeError("invalid object type '%s'." % type(o))
        else:
            raise TypeError("objs must either be a list of objects or "
                            "a dict of ids.")

    def fillParams(self, params):
        if self.invIds:
            params["investigationIds"] = ",".join(str(i) for i in self.invIds)
        if self.dsIds:
            params["datasetIds"] = ",".join(str(i) for i in self.dsIds)
        if self.dfIds:
            params["datafileIds"] = ",".join(str(i) for i in self.dfIds)


class IDSClient(object):
    
    """A client accessing an ICAT Data Service.

    The attribute sessionId must be set to a valid ICAT session id
    from the ICAT client.
    """

    def __init__(self, url, sessionId=None, sslContext=None, proxy=None):
        """Create an IDSClient.
        """
        self.url = url
        if not self.url.endswith("/"): self.url += "/"
        self.sessionId = sessionId
        if sslContext:
            verify = (sslContext.verify_mode != ssl.CERT_NONE)
            try:
                httpsHandler = HTTPSHandler(context=sslContext, 
                                            check_hostname=verify)
            except TypeError:
                # Python 2.7.9 HTTPSHandler does not accept the
                # check_hostname keyword argument.
                httpsHandler = HTTPSHandler(context=sslContext)
        else:
            httpsHandler = HTTPSHandler()
        if proxy:
            proxyhandler = ProxyHandler(proxy)
            self.opener = build_opener(proxyhandler, HTTPHandler, 
                                       httpsHandler, IDSHTTPErrorHandler)
        else:
            self.opener = build_opener(HTTPHandler, httpsHandler, 
                                       IDSHTTPErrorHandler)
        apiversion = self.version()["version"]
        # Translate a version having a trailing '-SNAPSHOT' into
        # something that StrictVersion would accept.
        apiversion = re.sub(r'-SNAPSHOT$', 'a1', apiversion)
        self.apiversion = Version(apiversion)

    def ping(self):
        """Check that the server is alive and is an IDS server.
        """
        req = IDSRequest(self.url + "ping")
        result = self.opener.open(req).read().decode('ascii')
        if result != "IdsOK": 
            raise IDSResponseError("unexpected response to ping: %s" % result)

    def getApiVersion(self):
        """Get the version of the IDS server.

        Note: the `getApiVersion` call has been added in IDS server
        version 1.3.0.  For older servers, try to guess the server
        version from features visible in the API.  Obviously this
        cannot always be accurate as we cannot distinguish server
        version with no visible API changes.  In particular, versions
        older then 1.2.0 will always reported as 1.0.0.  Nevertheless,
        the result of the guess should be fair enough for most use
        cases.
        """
        try:
            req = IDSRequest(self.url + "getApiVersion")
            return self.opener.open(req).read().decode('ascii')
        except (HTTPError, IDSError):
            pass

        # Verify that the server is reachable to avoid misinterpreting
        # connection errors as missing features.
        self.ping()

        # Older then 1.3.0.

        try:
            self.isReadOnly()
            return "1.2.0"
        except (HTTPError, IDSError):
            pass

        # Older then 1.2.0.
        # No way to distinguish 1.1.0, 1.0.1, and 1.0.0, report as 1.0.0.
        return "1.0.0"

    def version(self):
        """Get the version of the IDS server.

        Note: the `version` call has been added in IDS server version
        1.8.0, deprecating `getApiVersion` at the same time.  For
        older servers, we fall back to `getApiVersion` to emulate this
        call.  Note furthermore that `version` returns a dict, while
        `getApiVersion` returns the plain version number as a string.
        """
        try:
            req = IDSRequest(self.url + "version")
            result = self.opener.open(req).read().decode('ascii')
            return json.loads(result)
        except (HTTPError, IDSError) as err:
            try:
                return {"version": self.getApiVersion()}
            except:
                raise err

    def getIcatUrl(self):
        """Get the URL of the ICAT server connected to this IDS.
        """
        req = IDSRequest(self.url + "getIcatUrl")
        try:
            return self.opener.open(req).read().decode('ascii')
        except (HTTPError, IDSError) as e:
            raise self._versionMethodError("getIcatUrl", '1.4', e)

    def isReadOnly(self):
        """See if the server is configured to be readonly.
        """
        req = IDSRequest(self.url + "isReadOnly")
        response = self.opener.open(req).read().decode('ascii')
        return response.lower() == "true"

    def isTwoLevel(self):
        """See if the server is configured to use both main and archive storage.
        """
        req = IDSRequest(self.url + "isTwoLevel")
        response = self.opener.open(req).read().decode('ascii')
        return response.lower() == "true"

    def getServiceStatus(self):
        """Return information about what the IDS is doing.

        If all lists are empty it is quiet.  To use this call, the
        user represented by the sessionId must be in the set of
        rootUserNames defined in the IDS configuration.
        """
        parameters = {"sessionId": self.sessionId}
        req = IDSRequest(self.url + "getServiceStatus", parameters)
        result = self.opener.open(req).read().decode('ascii')
        return json.loads(result)
    
    def getSize(self, selection):
        """Return the total size of the datafiles.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        req = IDSRequest(self.url + "getSize", parameters)
        return long(self.opener.open(req).read().decode('ascii'))
    
    def getStatus(self, selection):
        """Return the status of data.
        """
        parameters = {}
        if self.sessionId:
            parameters["sessionId"] = self.sessionId
        selection.fillParams(parameters)
        req = IDSRequest(self.url + "getStatus", parameters)
        return self.opener.open(req).read().decode('ascii')
    
    def archive(self, selection):
        """Archive data.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        req = IDSRequest(self.url + "archive", parameters, method="POST")
        self.opener.open(req)

    def restore(self, selection):
        """Restore data.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        req = IDSRequest(self.url + "restore", parameters, method="POST")
        self.opener.open(req)

    def write(self, selection):
        """Write data.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        req = IDSRequest(self.url + "write", parameters, method="POST")
        try:
            self.opener.open(req)
        except (HTTPError, IDSError) as e:
            raise self._versionMethodError("write", '1.9', e)

    def reset(self, selection):
        """Reset data so that they can be queried again.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        req = IDSRequest(self.url + "reset", parameters, method="POST")
        try:
            self.opener.open(req)
        except (HTTPError, IDSError) as e:
            raise self._versionMethodError("reset", '1.6', e)

    def resetPrepared(self, preparedId):
        """Reset prepared data so that they can be queried again.
        """
        parameters = {"preparedId": preparedId}
        req = IDSRequest(self.url + "reset", parameters, method="POST")
        try:
            self.opener.open(req)
        except (HTTPError, IDSError) as e:
            raise self._versionMethodError("reset", '1.6', e)

    def prepareData(self, selection, compressFlag=False, zipFlag=False):
        """Prepare data for a subsequent
        :meth:`icat.ids.IDSClient.getPreparedData` call.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        if zipFlag:  parameters["zip"] = "true"
        if compressFlag: parameters["compress"] = "true"
        req = IDSRequest(self.url + "prepareData", parameters, method="POST")
        return self.opener.open(req).read().decode('ascii')
    
    def isPrepared(self, preparedId):
        """Check if data is ready.

        Returns true if the data identified by the `preparedId`
        returned by a call to :meth:`icat.ids.IDSClient.prepareData`
        is ready.
        """
        parameters = {"preparedId": preparedId}
        req = IDSRequest(self.url + "isPrepared", parameters)
        response = self.opener.open(req).read().decode('ascii')
        return response.lower() == "true"

    def getDatafileIds(self, selection):
        """Get the list of data file id corresponding to the selection.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        req = IDSRequest(self.url + "getDatafileIds", parameters)
        try:
            result = self.opener.open(req).read().decode('ascii')
            return json.loads(result)['ids']
        except (HTTPError, IDSError) as e:
            raise self._versionMethodError("getDatafileIds", '1.5', e)

    def getPreparedDatafileIds(self, preparedId):
        """Get the list of data file id corresponding to the prepared Id.
        """
        parameters = {"preparedId": preparedId}
        req = IDSRequest(self.url + "getDatafileIds", parameters)
        try:
            result = self.opener.open(req).read().decode('ascii')
            return json.loads(result)['ids']
        except (HTTPError, IDSError) as e:
            raise self._versionMethodError("getDatafileIds", '1.5', e)

    def getData(self, selection, 
                compressFlag=False, zipFlag=False, outname=None, offset=0):
        """Stream the requested data.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        if zipFlag:  parameters["zip"] = "true"
        if compressFlag: parameters["compress"] = "true"
        if outname: parameters["outname"] = outname
        req = IDSRequest(self.url + "getData", parameters)
        if offset > 0:
            req.add_header("Range", "bytes=" + str(offset) + "-") 
        return self.opener.open(req)

    def getDataUrl(self, selection, 
                   compressFlag=False, zipFlag=False, outname=None):
        """Get the URL to retrieve the requested data.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        if zipFlag:  parameters["zip"] = "true"
        if compressFlag: parameters["compress"] = "true"
        if outname: parameters["outname"] = outname
        return self._getDataUrl(parameters)
    
    def getPreparedData(self, preparedId, outname=None, offset=0):
        """Get prepared data.

        Get the data using the `preparedId` returned by a call to
        :meth:`icat.ids.IDSClient.prepareData`.
        """
        parameters = {"preparedId": preparedId}
        if outname: parameters["outname"] = outname
        req = IDSRequest(self.url + "getData", parameters)
        if offset > 0:
            req.add_header("Range", "bytes=" + str(offset) + "-") 
        return self.opener.open(req)
    
    def getPreparedDataUrl(self, preparedId, outname=None):
        """Get the URL to retrieve prepared data.

        Get the URL to retrieve data using the `preparedId` returned
        by a call to :meth:`icat.ids.IDSClient.prepareData`.
        """
        parameters = {"preparedId": preparedId}
        if outname: parameters["outname"] = outname
        return self._getDataUrl(parameters)
      
    def getLink(self, datafileId, username=None):
        """Return a hard link to a data file.

        This is only useful in those cases where the user has direct
        access to the file system where the IDS is storing data.  The
        caller is only granted read access to the file.
        """
        if username is None:
            username = getpass.getuser()
        parameters = {"sessionId": self.sessionId, 
                      "datafileId" : datafileId, "username": username }
        req = IDSRequest(self.url + "getLink", parameters, method="POST")
        return self.opener.open(req).read().decode('ascii')
    
    def put(self, inputStream, name, datasetId, datafileFormatId, 
            description=None, doi=None, datafileCreateTime=None, 
            datafileModTime=None):
        """Put data into IDS.

        Put the data in the `inputStream` into a data file and
        catalogue it.  The client generates a checksum which is
        compared to that produced by the server to detect any
        transmission errors.
        """
        parameters = {"sessionId":self.sessionId, "name":name, 
                      "datasetId":str(datasetId), 
                      "datafileFormatId":str(datafileFormatId)}
        if description:
            parameters["description"] = description
        if doi:
            parameters["doi"] = doi
        if datafileCreateTime:
            parameters["datafileCreateTime"] = str(datafileCreateTime)
        if datafileModTime:
            parameters["datafileModTime"] = str(datafileModTime)
        if not inputStream:
            raise ValueError("Input stream is null")

        inputreader = ChunkedFileReader(inputStream)
        req = IDSRequest(self.url + "put", parameters, 
                         data=inputreader, method="PUT")
        req.add_header('Content-Type', 'application/octet-stream')
        result = self.opener.open(req).read().decode('ascii')
        crc = inputreader.crc32 & 0xffffffff
        om = json.loads(result)
        if om["checksum"] != crc:
            raise IDSResponseError("checksum error")
        return long(om["id"])

    def delete(self, selection):
        """Delete data.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        req = IDSRequest(self.url + "delete", parameters, method="DELETE")
        self.opener.open(req)

    def _getDataUrl(self, parameters):
        return (self.url + "getData" + "?" + urlencode(parameters))

    def _versionMethodError(self, method, minversion, orgexc):
        """Prepare the proper exception if a method fails that is only
        available in newer IDS versions.
        """
        if self.apiversion < minversion:
            return VersionMethodError(method, version=self.apiversion, 
                                      service="IDS")
        else:
            return orgexc
