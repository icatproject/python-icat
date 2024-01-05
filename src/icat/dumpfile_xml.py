"""XML data file backend for icatdump.py and icatingest.py.
"""

import datetime
import os
import sys
from lxml import etree

from . import __version__
from .dumpfile import DumpFileReader, DumpFileWriter, register_backend
from .entity import Entity
from .exception import SearchResultError
from .query import Query

utc = datetime.timezone.utc


# ------------------------------------------------------------
# XMLDumpFileReader
# ------------------------------------------------------------

class XMLDumpFileReader(DumpFileReader):
    """Backend for reading ICAT data from a XML file.

    :param client: a client object configured to connect to the ICAT
        server that the objects in the data file belong to.
    :type client: :class:`icat.client.Client`
    :param infile: the data source to read the objects from.  This
        backend accepts a file object, a file name, or a XML tree
        object (:class:`lxml.etree._ElementTree`) as input.  Note that
        the latter case requires by definition the complete input to
        be at once in memory.  This is only useful if the input is
        small enough.
    """

    mode = "rb"
    """File mode suitable for this backend.
    """

    def __init__(self, client, infile):
        super().__init__(client, infile)
        self.insttypemap = { c.BeanName:t 
                             for t,c in self.client.typemap.items() }
        if isinstance(self.infile, etree._ElementTree):
            self.getdata = self.getdata_etree
        else:
            self.getdata = self.getdata_file

    def _file_open(self, infile):
        if infile == "-":
            # lxml requires binary mode
            f = os.fdopen(os.dup(sys.stdin.fileno()), self.mode)
            sys.stdin.close()
            return f
        else:
            return super()._file_open(infile)

    def _searchByReference(self, element, objtype, objindex):
        """Search for a referenced object.
        """
        ref = element.get('ref')
        if ref:
            # object is referenced by key.
            try:
                return self.client.searchUniqueKey(ref, objindex)
            except ValueError:
                raise SearchResultError("invalid reference %s" % ref)
        else:
            # object is referenced by attributes.
            attrs = set(element.keys()) - {'id'}
            conditions = dict()
            for attr in attrs:
                if attr.endswith(".ref"):
                    ref = element.get(attr)
                    robj = self.client.searchUniqueKey(ref, objindex)
                    attr = "%s.id" % attr[:-4]
                    conditions[attr] = "= %d" % robj.id
                else:
                    conditions[attr] = "= '%s'" % element.get(attr)
            query = Query(self.client, objtype, conditions=conditions)
            return self.client.assertedSearch(query)[0]

    def _elem2entity(self, element, objtype, objindex):
        """Create an entity object from XML element data."""
        obj = self.client.new(self.insttypemap[objtype])
        for subelem in element:
            attr = subelem.tag
            if attr in obj.AttrAlias:
                attr = obj.AttrAlias[attr]
            if attr in obj.InstAttr:
                setattr(obj, attr, subelem.text)
            elif attr in obj.InstRel:
                rtype = obj.getAttrType(attr)
                robj = self._searchByReference(subelem, rtype, objindex)
                setattr(obj, attr, robj)
            elif attr in obj.InstMRel:
                rtype = obj.getAttrType(attr)
                robj = self._elem2entity(subelem, rtype, objindex)
                getattr(obj, attr).append(robj)
            else:
                raise ValueError("invalid subelement '%s' in '%s'" 
                                 % (subelem.tag, element.tag))
        return obj

    def getdata_file(self):
        """Iterate over the chunks in the data file.
        """
        for event, data in etree.iterparse(self.infile, tag='data'):
            yield data
            data.clear()

    def getdata_etree(self):
        """Iterate over the chunks from a XML tree object.
        """
        for elem in self.infile.getroot():
            if elem.tag == 'data':
                yield elem

    def getobjs_from_data(self, data, objindex):
        """Iterate over the objects in a data chunk.

        Yield a new entity object in each iteration.  The object is
        initialized from the data, but not yet created at the client.
        """
        for elem in data:
            key = elem.get('id')
            tag = elem.tag
            if tag.endswith("Ref"):
                # elem is a reference to an already existing object.
                # Do not yield it as it should not be created, but add
                # it to the objindex so it can be referenced later on
                # from other objects.
                if key:
                    objtype = self.client.typemap[tag[0:-3]].BeanName
                    obj = self._searchByReference(elem, objtype, objindex)
                    objindex[key] = obj
            else:
                objtype = self.client.typemap[tag].BeanName
                obj = self._elem2entity(elem, objtype, objindex)
                yield key, obj


# ------------------------------------------------------------
# XMLDumpFileWriter
# ------------------------------------------------------------

class XMLDumpFileWriter(DumpFileWriter):
    """Backend for writing ICAT data to a XML file.

    :param client: a client object configured to connect to the ICAT
        server to search the data objects from.
    :type client: :class:`icat.client.Client`
    :param outfile: the data file to write the objects to.  This
        backend accepts a file object or a file name.
    """

    mode = "wb"
    """File mode suitable for this backend.
    """

    def __init__(self, client, outfile):
        super().__init__(client, outfile)
        self.data = etree.Element("data")

    def _file_open(self, outfile):
        if outfile == "-":
            # lxml requires binary mode
            f = os.fdopen(os.dup(sys.stdout.fileno()), self.mode)
            sys.stdout.close()
            return f
        else:
            return super()._file_open(outfile)

    def _entity2elem(self, obj, tag, keyindex):
        """Convert an entity object to an etree.Element."""
        if tag is None:
            tag = obj.instancetype
        d = etree.Element(tag)
        for attr in sorted(obj.InstAttr):
            if attr == 'id':
                continue
            v = getattr(obj, attr, None)
            if v is None:
                continue
            elif isinstance(v, bool):
                v = str(v).lower()
            elif isinstance(v, int):
                v = str(v)
            elif isinstance(v, datetime.datetime):
                if v.tzinfo is not None and v.tzinfo.utcoffset(v) is not None:
                    # v has timezone info.  This will be the timezone set
                    # in the ICAT server.  Convert it to UTC to avoid
                    # dependency of server settings in the dumpfile.
                    # Assume v.isoformat() to have a valid timezone
                    # suffix.
                    v = v.astimezone(tz=utc).isoformat()
                else:
                    # v has no timezone info, assume it to be UTC.
                    v = v.replace(tzinfo=utc).isoformat()
            else:
                v = str(v)
            etree.SubElement(d, attr).text = v
        for attr in sorted(obj.InstRel):
            o = getattr(obj, attr, None)
            if o is not None:
                k = o.getUniqueKey(keyindex=keyindex)
                etree.SubElement(d, attr, ref=k)
        for attr in sorted(obj.InstMRel):
            for o in sorted(getattr(obj, attr), key=Entity.__sortkey__):
                d.append(self._entity2elem(o, tag=attr, keyindex=keyindex))
        return d

    def head(self):
        """Write a header with some meta information to the data file."""
        date = datetime.datetime.now(tz=utc).isoformat()
        head = etree.Element("head")
        etree.SubElement(head, "date").text = date
        etree.SubElement(head, "service").text = self.client.url
        etree.SubElement(head, "apiversion").text = str(self.client.apiversion)
        etree.SubElement(head, "generator").text = ("icatdump (python-icat %s)" 
                                                    % __version__)
        self.outfile.write(b"""<?xml version="1.0" encoding="utf-8"?>
<icatdata>
""")
        self.outfile.write(etree.tostring(head, pretty_print=True))

    def startdata(self):
        """Start a new data chunk.

        If the current chunk contains any data, write it to the data
        file.
        """
        if len(self.data) > 0:
            self.outfile.write(etree.tostring(self.data, pretty_print=True))
        self.data = etree.Element("data")

    def writeobj(self, key, obj, keyindex):
        """Add an entity object to the current data chunk."""
        elem = self._entity2elem(obj, None, keyindex)
        elem.set('id', key)
        self.data.append(elem)

    def finalize(self):
        """Finalize the data file."""
        self.startdata()
        self.outfile.write(b"</icatdata>\n")


register_backend("XML", XMLDumpFileReader, XMLDumpFileWriter)
