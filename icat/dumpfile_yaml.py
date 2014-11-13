"""YAML dump file backend for icatdump.py and icatrestore.py.
"""

import datetime
import yaml
import icat
from icat.dumpfile import *

__all__ = ['YAMLDumpFileReader', 'YAMLDumpFileWriter']


# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------

# List of entity types.  This defines in particular the order in which
# the types must be restored.
entitytypes = [
    'user',
    'grouping',
    'userGroup',
    'rule',
    'publicStep',
    'facility',
    'instrument',
    'instrumentScientist',
    'parameterType',
    'permissibleStringValue',
    'investigationType',
    'sampleType',
    'datasetType',
    'datafileFormat',
    'facilityCycle',
    'application',
    'investigation',
    'investigationParameter',
    'keyword',
    'publication',
    'shift',
    'investigationGroup',
    'investigationInstrument',
    'investigationUser',
    'sample',
    'sampleParameter',
    'dataset',
    'datasetParameter',
    'datafile',
    'datafileParameter',
    'study',
    'studyInvestigation',
    'relatedDatafile',
    'dataCollection',
    'dataCollectionParameter',
    'dataCollectionDataset',
    'dataCollectionDatafile',
    'job',
]

def entity2dict(obj, keyindex):
    """Convert an entity object to a dict."""
    d = {}

    for attr in obj.InstAttr:
        if attr == 'id':
            continue
        v = getattr(obj, attr, None)
        if v is None:
            continue
        elif isinstance(v, bool):
            pass
        elif isinstance(v, (int, long)):
            v = int(v)
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
        d[attr] = v

    for attr in obj.InstRel:
        o = getattr(obj, attr, None)
        if o is not None:
            d[attr] = o.getUniqueKey(autoget=False, keyindex=keyindex)

    for attr in obj.InstMRel:
        if len(getattr(obj, attr)) > 0:
            d[attr] = []
            for o in sorted(getattr(obj, attr), 
                            key=icat.entity.Entity.__sortkey__):
                d[attr].append(entity2dict(o, keyindex=keyindex))

    return d


def dict2entity(client, insttypemap, d, objtype, objindex):
    """Create an entity object from a dict of attributes."""
    obj = client.new(objtype)
    for k in d:
        attr = k
        if attr in obj.AttrAlias:
            attr = obj.AttrAlias[attr]
        if attr in obj.InstAttr:
            setattr(obj, attr, d[k])
        elif attr in obj.InstRel:
            robj = client.searchUniqueKey(d[k], objindex)
            setattr(obj, attr, robj)
        elif attr in obj.InstMRel:
            rtype = insttypemap[obj.getAttrType(attr)]
            for rd in d[k]:
                robj = dict2entity(client, insttypemap, rd, rtype, objindex)
                getattr(obj, attr).append(robj)
        else:
            raise ValueError("invalid attribute '%s' in '%s'" 
                             % (k, objtype))
    return obj


# ------------------------------------------------------------
# YAMLDumpFileReader
# ------------------------------------------------------------

class YAMLDumpFileReader(DumpFileReader):
    """Backend for icatrestore.py to read a YAML dump file."""

    def __init__(self, client, infile):
        super(YAMLDumpFileReader, self).__init__(client)
        self.infile = infile
        self.insttypemap = { c.BeanName:t 
                             for t,c in self.client.typemap.iteritems() }

    def getdata(self):
        """Iterate over the data chunks in the dump file.
        """
        # yaml.load_all() returns a generator that yield one chunk
        # (YAML document) from the file in each iteration.
        return yaml.load_all(self.infile)

    def getobjs_from_data(self, data, objindex):
        """Iterate over the objects in a data chunk.

        Yield a new entity object in each iteration.  The object is
        initialized from the data, but not yet created at the client.
        """
        # check first that the chunk contains only known entries
        for name in data.keys():
            if name not in entitytypes:
                raise RuntimeError("Unknown entry %s in the data." % name)
        for name in entitytypes:
            if name in data:
                for key, d in data[name].iteritems():
                    obj = dict2entity(self.client, self.insttypemap, 
                                      d, name, objindex)
                    yield key, obj


# ------------------------------------------------------------
# YAMLDumpFileWriter
# ------------------------------------------------------------

class YAMLDumpFileWriter(DumpFileWriter):
    """Backend for icatdump.py to write a YAML dump file."""

    def __init__(self, client, outfile):
        super(YAMLDumpFileWriter, self).__init__(client)
        self.outfile = outfile
        self.data = {}

    def head(self):
        """Write a header with some meta information to the dump file."""
        dateformat = "%a, %d %b %Y %H:%M:%S +0000"
        date = datetime.datetime.utcnow().strftime(dateformat)
        head = """%%YAML 1.1
# Date: %s
# Service: %s
# ICAT-API: %s
# Generator: icatdump (python-icat %s)
""" % (date, self.client.url, self.client.apiversion, icat.__version__)
        self.outfile.write(head)

    def startdata(self):
        """Start a new data chunk.

        If the current chunk contains any data, write it to the dump
        file.
        """
        if self.data:
            yaml.dump(self.data, self.outfile, 
                      default_flow_style=False, explicit_start=True)
        self.data = {}

    def writeobj(self, key, obj, keyindex):
        """Add an entity object to the current data chunk."""
        tag = obj.instancetype
        if tag not in entitytypes:
            raise ValueError("Unknown entity type '%s'" % tag)
        if tag not in self.data:
            self.data[tag] = {}
        self.data[tag][key] = entity2dict(obj, keyindex)

    def finalize(self):
        """Finalize the dump file."""
        self.startdata()
