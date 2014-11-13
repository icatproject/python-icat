"""XML dump file backend for icatdump.py and icatrestore.py.
"""

import os
import datetime
from lxml import etree
import icat
from icat.dumpfile import *

__all__ = ['XMLDumpFileReader', 'XMLDumpFileWriter']


# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------

def entity2elem(obj, tag, keyindex):
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
        elif isinstance(v, (int, long)):
            v = str(v)
        elif isinstance(v, datetime.datetime):
            if v.tzinfo is not None and v.tzinfo.utcoffset(v) is not None:
                # v has timezone info, assume v.isoformat() to have a
                # valid timezone suffix.
                v = v.isoformat()
            else:
                # v has no timezone info, assume it to be UTC, append
                # the corresponding timezone suffix.
                v = v.isoformat() + 'Z'
        else:
            try:
                v = str(v)
            except UnicodeError:
                v = unicode(v)
        etree.SubElement(d, attr).text = v

    for attr in sorted(obj.InstRel):
        o = getattr(obj, attr, None)
        if o is not None:
            k = o.getUniqueKey(autoget=False, keyindex=keyindex)
            etree.SubElement(d, attr, ref=k)

    for attr in sorted(obj.InstMRel):
        for o in sorted(getattr(obj, attr), 
                        key=icat.entity.Entity.__sortkey__):
            d.append(entity2elem(o, tag=attr, keyindex=keyindex))

    return d

def elem2entity(client, insttypemap, element, objtype, objindex):
    """Create an entity object from XML element data."""
    if objtype is None:
        objtype = element.tag
    obj = client.new(objtype)
    for subelem in element:
        attr = subelem.tag
        if attr in obj.AttrAlias:
            attr = obj.AttrAlias[attr]
        if attr in obj.InstAttr:
            setattr(obj, attr, subelem.text)
        elif attr in obj.InstRel:
            ref = subelem.get('ref')
            robj = client.searchUniqueKey(ref, objindex)
            setattr(obj, attr, robj)
        elif attr in obj.InstMRel:
            rtype = insttypemap[obj.getAttrType(attr)]
            robj = elem2entity(client, insttypemap, subelem, rtype, objindex)
            getattr(obj, attr).append(robj)
        else:
            raise ValueError("invalid subelement '%s' in '%s'" 
                             % (subelem.tag, element.tag))
    return obj


# ------------------------------------------------------------
# XMLDumpFileReader
# ------------------------------------------------------------

class XMLDumpFileReader(DumpFileReader):
    """Backend for icatrestore.py to read a XML dump file."""

    def __init__(self, client, infile):
        super(XMLDumpFileReader, self).__init__(client)
        # need binary mode for infile
        self.infile = os.fdopen(os.dup(infile.fileno()), 'rb')
        self.insttypemap = { c.BeanName:t 
                             for t,c in self.client.typemap.iteritems() }

    def getdata(self):
        """Iterate over the data chunks in the dump file.
        """
        for event, data in etree.iterparse(self.infile, tag='data'):
            yield data
            data.clear()

    def getobjs(self, data, objindex):
        """Iterate over the objects in a data chunk.

        Yield a new entity object in each iteration.  The object is
        initialized from the data, but not yet created at the client.
        """
        for elem in data:
            key = elem.get('id')
            obj = elem2entity(self.client, self.insttypemap, 
                              elem, None, objindex)
            yield key, obj


# ------------------------------------------------------------
# XMLDumpFileWriter
# ------------------------------------------------------------

class XMLDumpFileWriter(DumpFileWriter):
    """Backend for icatdump.py to write a XML dump file."""

    def __init__(self, client, outfile):
        super(XMLDumpFileWriter, self).__init__(client)
        # need binary mode for outfile
        self.outfile = os.fdopen(os.dup(outfile.fileno()), 'wb')
        self.data = etree.Element("data")

    def head(self, service, apiversion):
        """Write a header with some meta information to the dump file."""
        date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        head = etree.Element("head")
        etree.SubElement(head, "date").text = date
        etree.SubElement(head, "service").text = service
        etree.SubElement(head, "apiversion").text = apiversion
        etree.SubElement(head, "generator").text = ("icatdump (python-icat %s)" 
                                                    % icat.__version__)
        self.outfile.write(b"""<?xml version="1.0" encoding="utf-8"?>
<icatdump>
""")
        self.outfile.write(etree.tostring(head, pretty_print=True))

    def startdata(self):
        """Start a new data chunk.

        If the current chunk contains any data, write it to the dump
        file.
        """
        if len(self.data) > 0:
            self.outfile.write(etree.tostring(self.data, pretty_print=True))
        self.data = etree.Element("data")

    def writeobj(self, key, obj, keyindex):
        """Add an entity object to the current data chunk."""
        elem = entity2elem(obj, None, keyindex)
        elem.set('id', key)
        self.data.append(elem)

    def finalize(self):
        """Finalize the dump file."""
        self.startdata()
        self.outfile.write(b"</icatdump>\n")
        self.outfile.close()
