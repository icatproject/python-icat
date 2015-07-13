"""XML dump file backend for icatdump.py and icatrestore.py.
"""

import os
import datetime
from lxml import etree
import icat
import icat.dumpfile
from icat.query import Query


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

def searchByReference(client, element, objtype, objindex):
    """Search for a referenced object.

    If the element is a reference to an existing object, search and
    return the object.  Otherwise return None.
    """
    ref = element.get('ref')
    if ref:
        # element references the object by key.
        return client.searchUniqueKey(ref, objindex)
    attrs = set(element.keys()) - {'id'}
    if len(attrs):
        # element references the object by attributes.
        conditions = { a: "= '%s'" % element.get(a) for a in attrs }
        query = Query(client, objtype, conditions=conditions)
        return client.assertedSearch(query)[0]
    # element is not a reference.
    return None

def elem2entity(client, insttypemap, element, objtype, objindex):
    """Create an entity object from XML element data."""
    if objtype is None:
        objtype = client.typemap[element.tag].BeanName
    obj = searchByReference(client, element, objtype, objindex)
    if not obj:
        obj = client.new(insttypemap[objtype])
        for subelem in element:
            attr = subelem.tag
            if attr in obj.AttrAlias:
                attr = obj.AttrAlias[attr]
            if attr in obj.InstAttr:
                setattr(obj, attr, subelem.text)
            elif attr in obj.InstRel:
                rtype = obj.getAttrType(attr)
                robj = searchByReference(client, subelem, rtype, objindex)
                if robj:
                    setattr(obj, attr, robj)
                else:
                    raise ValueError("many to one relationships '%s' in '%s' "
                                     "must be a reference" 
                                     % (subelem.tag, element.tag))
            elif attr in obj.InstMRel:
                rtype = obj.getAttrType(attr)
                robj = elem2entity(client, insttypemap, subelem, rtype, 
                                   objindex)
                getattr(obj, attr).append(robj)
            else:
                raise ValueError("invalid subelement '%s' in '%s'" 
                                 % (subelem.tag, element.tag))
    return obj


# ------------------------------------------------------------
# XMLDumpFileReader
# ------------------------------------------------------------

class XMLDumpFileReader(icat.dumpfile.DumpFileReader):
    """Backend for icatrestore.py to read a XML dump file."""

    def __init__(self, client, infile):
        super(XMLDumpFileReader, self).__init__(client, infile)
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

    def getobjs_from_data(self, data, objindex):
        """Iterate over the objects in a data chunk.

        Yield a new entity object in each iteration.  The object is
        initialized from the data, but not yet created at the client.
        """
        for elem in data:
            key = elem.get('id')
            obj = elem2entity(self.client, self.insttypemap, 
                              elem, None, objindex)
            if obj.id is not None:
                # elem was a reference to an already existing object.
                # Do not yield it as it should not be created, but add
                # it to the objindex so it can be referenced later on
                # from other objects.
                objindex[key] = obj
            else:
                yield key, obj


# ------------------------------------------------------------
# XMLDumpFileWriter
# ------------------------------------------------------------

class XMLDumpFileWriter(icat.dumpfile.DumpFileWriter):
    """Backend for icatdump.py to write a XML dump file."""

    def __init__(self, client, outfile):
        super(XMLDumpFileWriter, self).__init__(client, outfile)
        # need binary mode for outfile
        self.outfile = os.fdopen(os.dup(outfile.fileno()), 'wb')
        self.data = etree.Element("data")

    def head(self):
        """Write a header with some meta information to the dump file."""
        date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        head = etree.Element("head")
        etree.SubElement(head, "date").text = date
        etree.SubElement(head, "service").text = self.client.url
        etree.SubElement(head, "apiversion").text = str(self.client.apiversion)
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


icat.dumpfile.register_backend("XML", XMLDumpFileReader, XMLDumpFileWriter)
