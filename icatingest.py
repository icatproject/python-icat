#! /usr/bin/python
#
# Restore the content of the ICAT from a dump file as created by
# icatdump.py.
#
# Known issues and limitations:
#  + The user running this script need to have create permission for
#    all objects in the dump file.  Appropriate rules must either
#    already been set up at the ICAT server or must be contained in
#    the dump file.  In the latter case, the rules and corresponding
#    user and group objects must be in the first chunk (see below) of
#    the file.  In the generic case of restoring the entire content on
#    an empty ICAT server, the script must be run by the ICAT root
#    user.
#  + This script requires ICAT 4.3.0 or newer.
#  + A dump and restore of an ICAT will not preserve the attributes
#    id, createId, createTime, modId, and modTime of any objects.
#    This is by design and cannot be fixed.  As a consequence, access
#    rules that are based on object ids will not work after a restore.
#  + Restoring of several entity types has not yet been
#    tested.  See icatdump.py for a list.
#  + Dealing with duplicates (option --duplicate) is only supported
#    for single objects.  If the object contains related objects in
#    one to many relationships that are to be created at once, the
#    only allowed option to deal with duplicates is THROW.
#  + When using --duplicate=CHECK to raise an error (only) if the new
#    data does not match the old, spurious errors may be raised may be
#    raised for attributes that are not strings.
#

import os.path
import logging
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

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.CRITICAL)
log = logging.getLogger(__name__)

formats = icat.dumpfile.Backends.keys()
if len(formats) == 0:
    raise RuntimeError("No datafile backends available.")

config = icat.config.Config(ids="optional")
config.add_variable('file', ("-i", "--inputfile"), 
                    dict(help="input file name or '-' for stdin"),
                    default='-')
config.add_variable('format', ("-f", "--format"), 
                    dict(help="input file format", choices=formats),
                    default='YAML')
config.add_variable('uploadDatafiles', ("--upload-datafiles",), 
                    dict(help="upload datafiles to IDS"), 
                    type=icat.config.flag, default=False)
config.add_variable('dataDir', ("--datafile-dir",), 
                    dict(help="datafile directory"),
                    default='.')
config.add_variable('duplicate', ("--duplicate",), 
                    dict(help="behavior in case of duplicate objects",
                         choices=["THROW", "IGNORE", "CHECK", "OVERWRITE"]), 
                    default='THROW')
conf = config.getconfig()

if conf.uploadDatafiles:
    if conf.idsurl is None:
        raise icat.ConfigError("Config option 'idsurl' not given, "
                               "but required for uploadDatafiles.")
    conf.dataDir = os.path.abspath(conf.dataDir)

client = icat.Client(conf.url, **conf.client_kwargs)
if client.apiversion < '4.3':
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
            raise RuntimeError("Cannot %s duplicate on %s if %s is not empty."
                               % (conf.duplicate, obj.BeanName, r))
    dobj = client.searchMatching(obj)
    if conf.duplicate == "IGNORE":
        pass
    elif conf.duplicate == "CHECK":
        for a in obj.InstAttr:
            v = getattr(obj, a)
            # FIXME: must take the attribute type into account for the
            # comparision of the value.
            if v is not None and str(getattr(dobj, a)) != v:
                raise
    elif conf.duplicate == "OVERWRITE":
        dobj.get()
        for a in obj.InstAttr:
            v = getattr(obj, a)
            if v is not None:
                setattr(dobj, a, v)
        dobj.update()
    obj.id = dobj.id

with open_dumpfile(client, conf.file, conf.format, 'r') as dumpfile:
    for obj in dumpfile.getobjs():
        if conf.uploadDatafiles and obj.BeanName == "Datafile":
            fname = os.path.join(conf.dataDir, obj.name)
            client.putData(fname, obj)
        else:
            try:
                obj.create()
            except icat.ICATObjectExistsError:
                check_duplicate(obj)
