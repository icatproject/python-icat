"""Provide the IdsClient class.

This module is derived from the Python IDS client from the original
`IDS distribution`_.  Permission to include it in python-icat and to
publish it under its license has generously been granted by its
author.

.. _IDS distribution: http://code.google.com/p/icat-data-service/
"""

from urllib2 import Request, ProxyHandler, build_opener
from urllib import urlencode
from icat.chunkedhttp import ChunkedHTTPHandler, ChunkedHTTPSHandler
import json
import zlib
from icat.exception import IDSServerError, IDSResponseError

__all__ = ['IdsClient']


class IDSRequest(Request):

    def __init__(self, url, parameters, data=None, headers={}, method=None):

        if parameters:
            parameters = urlencode(parameters)
            if method == "POST":
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                data = parameters
            else:
                url += "?" + parameters
        Request.__init__(self, url, data, headers)
        if method:
            self.method = method

        self.add_header("Cache-Control", "no-cache")
        self.add_header("Pragma", "no-cache")
        self.add_header("Accept", 
                        "text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2")
        self.add_header("Connection", "keep-alive") 

    def get_method(self):
        """Return a string indicating the HTTP request method."""
        default_method = "POST" if self.data is not None else "GET"
        return getattr(self, 'method', default_method)


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


class IdsClient(object):
    
    """A client accessing an ICAT Data Service.

    The attribute sessionId must be set to a valid ICAT session id
    from the ICAT client.
    """

    def __init__(self, url, sessionId=None, proxy=None):
        """Create an IdsClient.
        """
        self.url = url
        if not self.url.endswith("/"): self.url += "/"
        self.sessionId = sessionId
        if proxy:
            proxyhandler = ProxyHandler(proxy)
            self.default = build_opener(proxyhandler)
            self.chunked = build_opener(proxyhandler, 
                                        ChunkedHTTPHandler, ChunkedHTTPSHandler)
        else:
            self.default = build_opener()
            self.chunked = build_opener(ChunkedHTTPHandler, ChunkedHTTPSHandler)

    def ping(self):
        """Check that the server is alive and is an IDS server.
        """
        req = IDSRequest(self.url + "ping", {})
        result = self._checkresponse(self.default.open(req)).read()
        if result != "IdsOK": 
            raise IDSResponseError("unexpected response to ping: %s" % result)

    def getServiceStatus(self):
        """Return information about what the IDS is doing.

        If all lists are empty it is quiet.  To use this call, the
        user represented by the sessionId must be in the set of
        rootUserNames defined in the IDS configuration.
        """
        parameters = {"sessionId": self.sessionId}
        req = IDSRequest(self.url + "getServiceStatus", parameters)
        result = self._checkresponse(self.default.open(req)).read()
        return json.loads(result)
    
    def getStatus(self, datafileIds=[], datasetIds=[], investigationIds=[]):
        """Return the status of data.

        The data is specified by the datafileIds datasetIds and
        investigationIds.
        """
        parameters = {"sessionId": self.sessionId}
        parameters = {}
        parameters["sessionId"] = self.sessionId   
        self._fillParms(parameters, datafileIds, datasetIds, investigationIds)
        req = IDSRequest(self.url + "getStatus", parameters)
        return self._checkresponse(self.default.open(req)).read()
    
    def restore(self, datafileIds=[], datasetIds=[], investigationIds=[]):
        """Restore data.

        The data is specified by the datafileIds datasetIds and
        investigationIds.
        """
        parameters = {"sessionId": self.sessionId}
        self._fillParms(parameters, datafileIds, datasetIds, investigationIds)
        req = IDSRequest(self.url + "restore", parameters, method="POST")
        return self._checkresponse(self.default.open(req)).read()

    def archive(self, datafileIds=[], datasetIds=[], investigationIds=[]):
        """Archive data.

        The data is specified by the datafileIds datasetIds and
        investigationIds.
        """
        parameters = {"sessionId": self.sessionId}
        self._fillParms(parameters, datafileIds, datasetIds, investigationIds)
        req = IDSRequest(self.url + "archive", parameters, method="POST")
        return self._checkresponse(self.default.open(req)).read()

    def isPrepared(self, preparedId):
        """Check if data is ready.

        Returns true if the data identified by the preparedId returned
        by a call to prepareData is ready.
        """
        parameters = {"preparedId": preparedId}
        req = IDSRequest(self.url + "isPrepared", parameters)
        response = self._checkresponse(self.default.open(req)).read()
        return response.lower() == "true"

    def prepareData(self, datafileIds=[], datasetIds=[], investigationIds=[], 
                    compressFlag=False, zipFlag=False):
        """Prepare data for a subsequent getPreparedData call.
        """
        parameters = {"sessionId": self.sessionId}
        self._fillParms(parameters, datafileIds, datasetIds, investigationIds)
        if zipFlag:  parameters["zip"] = "true"
        if compressFlag: parameters["compress"] = "true"
        req = IDSRequest(self.url + "prepareData", parameters, method="POST")
        return self._checkresponse(self.default.open(req)).read()
    
    def getData(self, datafileIds=[], datasetIds=[], investigationIds=[], 
                compressFlag=False, zipFlag=False, outname=None, offset=0):
        """Stream the requested data.
        """
        parameters = {"sessionId": self.sessionId}
        self._fillParms(parameters, datafileIds, datasetIds, investigationIds)
        if zipFlag:  parameters["zip"] = "true"
        if compressFlag: parameters["compress"] = "true"
        if outname: parameters["outname"] = outname
        req = IDSRequest(self.url + "getData", parameters)
        if offset:
            req.add_header("Range", "bytes=" + str(offset) + "-") 
        return self._checkresponse(self.default.open(req))
    
    def getDataUrl(self, datafileIds=[], datasetIds=[], investigationIds=[], 
                   compressFlag=False, zipFlag=False, outname=None):
        """Get the URL to retrieve the requested data.
        """
        parameters = {"sessionId": self.sessionId}
        self._fillParms(parameters, datafileIds, datasetIds, investigationIds)
        if zipFlag:  parameters["zip"] = "true"
        if compressFlag: parameters["compress"] = "true"
        if outname: parameters["outname"] = outname
        return self._getDataUrl(parameters)
    
    def delete(self, datafileIds=[], datasetIds=[], investigationIds=[]):
        """Delete data.

        The data is identified by the datafileIds, datasetIds and
        investigationIds.
        """
        parameters = {"sessionId": self.sessionId}
        self._fillParms(parameters, datafileIds, datasetIds, investigationIds)
        req = IDSRequest(self.url + "delete", parameters, method="DELETE")
        self._checkresponse(self.default.open(req))

    def getPreparedData(self, preparedId, outname=None, offset=0):
        """Get prepared data.

        Get the data using the preparedId returned by a call to
        prepareData.
        """
        parameters = {"preparedId": preparedId}
        if outname: parameters["outname"] = outname
        req = IDSRequest(self.url + "getData", parameters)
        if offset:
            req.add_header("Range", "bytes=" + str(offset) + "-") 
        return self._checkresponse(self.default.open(req))
    
    def getPreparedDataUrl(self, preparedId, outname=None):
        """Get the URL to retrieve prepared data.

        Get the URL to retrieve data using the preparedId returned by
        a call to prepareData.
        """
        parameters = {"preparedId": preparedId}
        if outname: parameters["outname"] = outname
        return self._getDataUrl(parameters)
      
    def put(self, inputStream, name, datasetId, datafileFormatId, 
            description=None, doi=None, datafileCreateTime=None, 
            datafileModTime=None):
        """Put data into IDS.

        Put the data in the inputStream into a data file and catalogue
        it.  The client generates a checksum which is compared to that
        produced by the server to detect any transmission errors.
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

        req = IDSRequest(self.url + "put", parameters, method="PUT")
        req.add_header('Content-Type', 'application/octet-stream')
        inputreader = ChunkedFileReader(inputStream)
        req.add_data(inputreader)
        result = self._checkresponse(self.chunked.open(req)).read()
        crc = inputreader.crc32 & 0xffffffff
        om = json.loads(result)
        if om["checksum"] != crc:
            raise IDSResponseError("checksum error")
        return long(om["id"])

    def _fillParms(self, parameters, dfIds, dsIds, invIds):
        if invIds:
            parameters["investigationIds"] = ",".join(str(x) for x in invIds)
        if dsIds:
            parameters["datasetIds"] = ",".join(str(x) for x in dsIds)
        if dfIds:
            parameters["datafileIds"] = ",".join(str(x) for x in dfIds)

    def _getDataUrl(self, parameters):
        return (self.url + "getData" + "?" + urlencode(parameters))

    def _checkresponse(self, response):
        """Check the response from the IDS, raise an error if appropriate."""

        rc = response.getcode()
        if (rc / 100 != 2):
            responseContent = response.read()
            try:
                om = json.loads(responseContent)
                code = om["code"]
                message = om["message"]
            except Exception:
                raise IDSResponseError(responseContent)
            raise IDSServerError(rc, code, message)

        return response
