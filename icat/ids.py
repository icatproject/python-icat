"""Provide the IDSClient class.

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

__all__ = ['DataSelection', 'IDSClient']


class IDSRequest(Request):

    def __init__(self, url, parameters, data=None, headers={}, method=None):

        if parameters:
            parameters = urlencode(parameters)
            if method == "POST":
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                data = parameters.encode('ascii')
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


class DataSelection(object):
    """A set of data to be processed by the ICAT Data Service."""

    def __init__(self, objs=None):
        super(DataSelection, self).__init__()
        self.invIds = []
        self.dsIds = []
        self.dfIds = []
        if objs:
            self.extend(objs)

    def __len__(self):
        return len(self.invIds) + len(self.dsIds) + len(self.dfIds)

    def __str__(self):
        return ("{invIds:%s, dsIds:%s, dfIds:%s}" 
                % (self.invIds, self.dsIds, self.dfIds))

    def extend(self, objs):
        if isinstance(objs, DataSelection):
            self.invIds.extend(objs.invIds)
            self.dsIds.extend(objs.dsIds)
            self.dfIds.extend(objs.dfIds)
        elif isinstance(objs, list):
            for o in objs:
                if o.BeanName == 'Investigation':
                   self.invIds.append(o.id) 
                elif o.BeanName == 'Dataset':
                   self.dsIds.append(o.id) 
                elif o.BeanName == 'Datafile':
                   self.dfIds.append(o.id) 
                else:
                    raise ValueError("invalid object '%s'." % o.BeanName)
        elif isinstance(objs, dict):
            self.invIds.extend(objs.get('investigationIds', []))
            self.dsIds.extend(objs.get('datasetIds', []))
            self.dfIds.extend(objs.get('datafileIds', []))
        else:
            raise TypeError("objs must either be a list of objects or "
                            "a dict of ids.")

    def fillParams(self, params):
        if self.invIds:
            params["investigationIds"] = ",".join(str(x) for x in self.invIds)
        if self.dsIds:
            params["datasetIds"] = ",".join(str(x) for x in self.dsIds)
        if self.dfIds:
            params["datafileIds"] = ",".join(str(x) for x in self.dfIds)


class IDSClient(object):
    
    """A client accessing an ICAT Data Service.

    The attribute sessionId must be set to a valid ICAT session id
    from the ICAT client.
    """

    def __init__(self, url, sessionId=None, proxy=None):
        """Create an IDSClient.
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
        result = self._checkResponseContent(self.default.open(req))
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
        result = self._checkResponseContent(self.default.open(req))
        return json.loads(result)
    
    def getStatus(self, selection):
        """Return the status of data.

        The data is specified by the datafileIds datasetIds and
        investigationIds.
        """
        parameters = {"sessionId": self.sessionId}
        parameters = {}
        parameters["sessionId"] = self.sessionId   
        selection.fillParams(parameters)
        req = IDSRequest(self.url + "getStatus", parameters)
        return self._checkResponseContent(self.default.open(req))
    
    def restore(self, selection):
        """Restore data.

        The data is specified by the datafileIds datasetIds and
        investigationIds.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        req = IDSRequest(self.url + "restore", parameters, method="POST")
        return self._checkResponseContent(self.default.open(req))

    def archive(self, selection):
        """Archive data.

        The data is specified by the datafileIds datasetIds and
        investigationIds.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        req = IDSRequest(self.url + "archive", parameters, method="POST")
        return self._checkResponseContent(self.default.open(req))

    def isPrepared(self, preparedId):
        """Check if data is ready.

        Returns true if the data identified by the preparedId returned
        by a call to prepareData is ready.
        """
        parameters = {"preparedId": preparedId}
        req = IDSRequest(self.url + "isPrepared", parameters)
        response = self._checkResponseContent(self.default.open(req))
        return response.lower() == "true"

    def prepareData(self, selection, compressFlag=False, zipFlag=False):
        """Prepare data for a subsequent getPreparedData call.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        if zipFlag:  parameters["zip"] = "true"
        if compressFlag: parameters["compress"] = "true"
        req = IDSRequest(self.url + "prepareData", parameters, method="POST")
        return self._checkResponseContent(self.default.open(req))
    
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
        return self._checkResponse(self.default.open(req))
    
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
    
    def delete(self, selection):
        """Delete data.

        The data is identified by the datafileIds, datasetIds and
        investigationIds.
        """
        parameters = {"sessionId": self.sessionId}
        selection.fillParams(parameters)
        req = IDSRequest(self.url + "delete", parameters, method="DELETE")
        self._checkResponse(self.default.open(req))

    def getPreparedData(self, preparedId, outname=None, offset=0):
        """Get prepared data.

        Get the data using the preparedId returned by a call to
        prepareData.
        """
        parameters = {"preparedId": preparedId}
        if outname: parameters["outname"] = outname
        req = IDSRequest(self.url + "getData", parameters)
        if offset > 0:
            req.add_header("Range", "bytes=" + str(offset) + "-") 
        return self._checkResponse(self.default.open(req))
    
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
        result = self._checkResponseContent(self.chunked.open(req))
        crc = inputreader.crc32 & 0xffffffff
        om = json.loads(result)
        if om["checksum"] != crc:
            raise IDSResponseError("checksum error")
        return long(om["id"])

    def _getDataUrl(self, parameters):
        return (self.url + "getData" + "?" + urlencode(parameters))

    def _checkResponse(self, response):
        """Check the response from the IDS, raise an error if appropriate."""

        rc = response.getcode()
        if (int(rc / 100) != 2):
            responseContent = response.read().decode('ascii')
            try:
                om = json.loads(responseContent)
                code = om["code"]
                message = om["message"]
            except Exception:
                raise IDSResponseError(responseContent)
            raise IDSServerError(rc, code, message)

        return response

    def _checkResponseContent(self, response):
        """Check the response from the IDS and return the content."""
        return self._checkResponse(response).read().decode('ascii')
