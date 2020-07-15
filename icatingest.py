#! /usr/bin/python
#
# Restore the content of the ICAT from a dump file as created by
# icatdump.py.

import logging
from pathlib import Path
import icat
import icat.config
from icat.dumpfile import open_dumpfile
try:
    import icat.dumpfile_xml
except ImportError:
    pass
try:
    import icat.dumpfile_yaml
except ImportError:
    pass
from icat.helper import parse_attr_string

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.CRITICAL)
log = logging.getLogger(__name__)

formats = icat.dumpfile.Backends.keys()
if len(formats) == 0:
    raise RuntimeError("No datafile backends available.")

def getPath(f):
    if f == '-':
        return f
    else:
        return Path(f).expanduser()

config = icat.config.Config(ids="optional")
config.add_variable('file', ("-i", "--inputfile"), 
                    dict(help="input file name or '-' for stdin"),
                    type=getPath, default='-')
config.add_variable('format', ("-f", "--format"), 
                    dict(help="input file format", choices=formats),
                    default='YAML')
config.add_variable('uploadDatafiles', ("--upload-datafiles",), 
                    dict(help="upload datafiles to IDS"), 
                    type=icat.config.flag, default=False)
config.add_variable('dataDir', ("--datafile-dir",), 
                    dict(help="datafile directory"),
                    type=lambda f: Path(f).expanduser(), default='.')
config.add_variable('duplicate', ("--duplicate",), 
                    dict(help="behavior in case of duplicate objects",
                         choices=["THROW", "IGNORE", "CHECK", "OVERWRITE"]), 
                    default='THROW')
client, conf = config.getconfig()

if conf.uploadDatafiles:
    if conf.idsurl is None:
        raise icat.ConfigError("Config option 'idsurl' not given, "
                               "but required for uploadDatafiles.")
    conf.dataDir = conf.dataDir.resolve()

if client.apiversion < '4.3.0':
    raise RuntimeError("Sorry, ICAT version %s is too old, need 4.3.0 or newer."
                       % client.apiversion)
client.login(conf.auth, conf.credentials)


def check_duplicate(obj):
    """Deal with duplicate objects according conf.duplicate.
    """
    if conf.duplicate == "THROW":
        raise
    # Allow IGNORE, CHECK, and OVERWRITE only on single objects
    for r in obj.InstMRel:
        if getattr(obj, r):
            raise ValueError("Cannot %s duplicate on %s if %s is not empty."
                             % (conf.duplicate, obj.BeanName, r))
    dobj = client.searchMatching(obj, includes="1")
    if conf.duplicate == "IGNORE":
        pass
    elif conf.duplicate == "CHECK":
        for a in obj.InstAttr:
            v = parse_attr_string(getattr(obj, a), obj.getAttrType(a))
            if v is not None and getattr(dobj, a) != v:
                raise
    elif conf.duplicate == "OVERWRITE":
        for a in obj.InstAttr:
            v = getattr(obj, a)
            if v is not None:
                setattr(dobj, a, v)
        dobj.update()
    obj.id = dobj.id

with open_dumpfile(client, conf.file, conf.format, 'r') as dumpfile:
    for obj in dumpfile.getobjs():
        if conf.uploadDatafiles and obj.BeanName == "Datafile":
            fname = conf.dataDir / obj.name
            client.putData(fname, obj)
        else:
            try:
                obj.create()
            except icat.ICATObjectExistsError:
                check_duplicate(obj)
