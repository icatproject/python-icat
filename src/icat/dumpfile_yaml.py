"""YAML data file backend for icatdump.py and icatingest.py.
"""

import datetime
import yaml

from . import __version__
from .dumpfile import DumpFileReader, DumpFileWriter, register_backend
from .entity import Entity
from .exception import SearchResultError

utc = datetime.timezone.utc


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
    'dataPublicationType',
    'investigationType',
    'sampleType',
    'datasetType',
    'datafileFormat',
    'technique',
    'facilityCycle',
    'application',
    'fundingReference',
    'investigation',
    'investigationParameter',
    'keyword',
    'publication',
    'shift',
    'investigationFunding',
    'investigationGroup',
    'investigationInstrument',
    'investigationUser',
    'sample',
    'sampleParameter',
    'dataset',
    'datasetParameter',
    'datasetInstrument',
    'datasetTechnique',
    'datafile',
    'datafileParameter',
    'dataCollection',
    'dataCollectionParameter',
    'dataCollectionDataset',
    'dataCollectionDatafile',
    'dataPublication',
    'dataPublicationDate',
    'dataPublicationFunding',
    'dataPublicationUser',
    'affiliation',
    'relatedItem',
    'study',
    'studyInvestigation',
    'relatedDatafile',
    'job',
]


# ------------------------------------------------------------
# YAMLDumpFileReader
# ------------------------------------------------------------

class YAMLDumpFileReader(DumpFileReader):
    """Backend for reading ICAT data from a YAML file.

    :param client: a client object configured to connect to the ICAT
        server that the objects in the data file belong to.
    :type client: :class:`icat.client.Client`
    :param infile: the data source to read the objects from.  This
        backend accepts a file object or a file name.
    """

    mode = "rt"
    """File mode suitable for this backend.
    """

    def __init__(self, client, infile):
        super().__init__(client, infile)
        self.insttypemap = { c.BeanName:t 
                             for t,c in self.client.typemap.items() }

    def _dict2entity(self, d, objtype, objindex):
        """Create an entity object from a dict of attributes."""
        obj = self.client.new(objtype)
        for k in d:
            attr = k
            if attr in obj.AttrAlias:
                attr = obj.AttrAlias[attr]
            if attr in obj.InstAttr:
                setattr(obj, attr, d[k])
            elif attr in obj.InstRel:
                try:
                    robj = self.client.searchUniqueKey(d[k], objindex)
                except ValueError:
                    raise SearchResultError("invalid reference %s" % d[k])
                setattr(obj, attr, robj)
            elif attr in obj.InstMRel:
                rtype = self.insttypemap[obj.getAttrType(attr)]
                for rd in d[k]:
                    robj = self._dict2entity(rd, rtype, objindex)
                    getattr(obj, attr).append(robj)
            else:
                raise ValueError("invalid attribute '%s' in '%s'" 
                                 % (k, objtype))
        return obj

    def getdata(self):
        """Iterate over the chunks in the data file.
        """
        # yaml.load_all() returns a generator that yield one chunk
        # (YAML document) from the file in each iteration.
        return yaml.safe_load_all(self.infile)

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
                for key in sorted(data[name].keys()):
                    obj = self._dict2entity(data[name][key], name, objindex)
                    yield key, obj


# ------------------------------------------------------------
# YAMLDumpFileWriter
# ------------------------------------------------------------

class YAMLDumpFileWriter(DumpFileWriter):
    """Backend for writing ICAT data to a YAML file.

    :param client: a client object configured to connect to the ICAT
        server to search the data objects from.
    :type client: :class:`icat.client.Client`
    :param outfile: the data file to write the objects to.  This
        backend accepts a file object or a file name.
    """

    mode = "wt"
    """File mode suitable for this backend.
    """

    def __init__(self, client, outfile):
        super().__init__(client, outfile)
        self.data = {}

    def _entity2dict(self, obj, keyindex):
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
            elif isinstance(v, int):
                v = int(v)
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
            d[attr] = v
        for attr in obj.InstRel:
            o = getattr(obj, attr, None)
            if o is not None:
                d[attr] = o.getUniqueKey(keyindex=keyindex)
        for attr in obj.InstMRel:
            if len(getattr(obj, attr)) > 0:
                d[attr] = []
                for o in sorted(getattr(obj, attr), key=Entity.__sortkey__):
                    d[attr].append(self._entity2dict(o, keyindex=keyindex))
        return d

    def head(self):
        """Write a header with some meta information to the data file."""
        dateformat = "%a, %d %b %Y %H:%M:%S %z"
        date = datetime.datetime.now(tz=utc).strftime(dateformat)
        head = """%%YAML 1.1
# Date: %s
# Service: %s
# ICAT-API: %s
# Generator: icatdump (python-icat %s)
""" % (date, self.client.url, self.client.apiversion, __version__)
        self.outfile.write(head)

    def startdata(self):
        """Start a new data chunk.

        If the current chunk contains any data, write it to the data
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
        self.data[tag][key] = self._entity2dict(obj, keyindex)

    def finalize(self):
        """Finalize the data file."""
        self.startdata()


register_backend("YAML", YAMLDumpFileReader, YAMLDumpFileWriter)
