#! /usr/bin/python
#
# Dump the content of the ICAT to a YAML document to stdout.
#
# The following items are deliberately not included in the output:
#  + Log objects,
#  + the attributes id, createId, createTime, modId, and modTime.
#
# Known issues and limitations:
#  + This script is NOT suitable for a real production size ICAT.
#  + Version dependency.  This script currently works for ICAT 4.3.*
#    only.
#  + Should include some meta information in the dump, such as date,
#    URL, and version of the ICAT.
#  + The serialization of the following entity types has not yet been
#    tested: Application, DataCollection, DataCollectionDatafile,
#    DataCollectionDataset, DataCollectionParameter,
#    DatafileParameter, DatasetParameter, FacilityCycle,
#    InvestigationParameter, Job, ParameterType,
#    PermissibleStringValue, PublicStep, Publication, RelatedDatafile,
#    SampleParameter, Shift, Study, StudyInvestigation.
#

import icat
import icat.config
import datetime
import logging
import yaml

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

icat.config.defaultsection = "hzb"
config = icat.config.Config()
conf = config.getconfig()

client = icat.Client(conf.url, **conf.client_kwargs)
client.login(conf.auth, conf.credentials)


keyindex = {}
dump = {}


def entityattrdict(e):
    """Convert an entity to a dict, not considering the relations."""
    d = {}
    for attr in e.InstAttr:
        if attr == 'id':
            continue
        v = getattr(e, attr, None)
        if v is None:
            pass
        elif isinstance(v, long) or isinstance(v, int):
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
    return d

def entitydict(e):
    """Convert an entity to a dict."""
    d = entityattrdict(e)
    for attr in e.InstRel:
        o = getattr(e, attr, None)
        if o is not None:
            d[attr] = keyindex[o.id]
        else:
            d[attr] = None
    return d

def entityparamdict(e):
    """Convert an entity including its parameters to a dict."""
    d = entitydict(e)
    d['parameters'] = []
    try:
        parameters = e.parameters
    except AttributeError:   # ref. ICAT issue 130
        pass
    else:
        for i in parameters:
            p = entityattrdict(i)
            p['type'] = keyindex[i.type.id]
            d['parameters'].append(p)
    return d

def groupdict(e):
    """Convert a group including its users to a dict."""
    d = entitydict(e)
    try:
        d['users'] = [keyindex[ug.user.id] for ug in e.userGroups]
    except AttributeError:   # ref. ICAT issue 130
        d['users'] = []
    return d

def instrumentdict(e):
    """Convert an instrument including its instrument scientists to a dict."""
    d = entitydict(e)
    try:
        d['instrumentScientists'] = [keyindex[uis.user.id] 
                                     for uis in e.instrumentScientists]
    except AttributeError:   # ref. ICAT issue 130
        d['instrumentScientists'] = []
    return d

def parametertypedict(e):
    """Convert an parameter type including its permissible string
    values to a dict."""
    d = entitydict(e)
    try:
        d['permissibleStringValues'] = [entityattrdict(i) 
                                        for i in e.permissibleStringValues]
    except AttributeError:   # ref. ICAT issue 130
        d['permissibleStringValues'] = []
    return d

def investigationdict(e):
    """Convert an investigation including its instruments, shifts,
    keywords, publications, investigation users, and parameters to a
    dict."""
    d = entityparamdict(e)
    try:
        d['instruments'] = [keyindex[i.instrument.id] 
                            for i in e.investigationInstruments]
    except AttributeError:   # ref. ICAT issue 130
        d['instruments'] = []
    try:
        d['shifts'] = [entityattrdict(i) for i in e.shifts]
    except AttributeError:   # ref. ICAT issue 130
        d['shifts'] = []
    try:
        d['keywords'] = [entityattrdict(i) for i in e.keywords]
    except AttributeError:   # ref. ICAT issue 130
        d['keywords'] = []
    try:
        d['publications'] = [entityattrdict(i) for i in e.publications]
    except AttributeError:   # ref. ICAT issue 130
        d['publications'] = []

    d['investigationUsers'] = []
    try:
        investigationUsers = e.investigationUsers
    except AttributeError:   # ref. ICAT issue 130
        pass
    else:
        for i in investigationUsers:
            u = entityattrdict(i)
            u['user'] = keyindex[i.user.id]
            d['investigationUsers'].append(u)

    return d

def studydict(e):
    """Convert a study to a dict."""
    d = entitydict(e)
    try:
        d['studyInvestigations'] = [keyindex[si.investigation.id] 
                                    for si in e.studyInvestigations]
    except AttributeError:   # ref. ICAT issue 130
        d['studyInvestigations'] = []
    return d

def datacollectiondict(e):
    """Convert a data collection to a dict."""
    d = entitydict(e)
    try:
        d['dataCollectionDatasets'] = [entityattrdict(i) 
                                       for i in e.dataCollectionDatasets]
    except AttributeError:   # ref. ICAT issue 130
        d['dataCollectionDatasets'] = []
    try:
        d['dataCollectionDatafiles'] = [entityattrdict(i) 
                                        for i in e.dataCollectionDatafiles]
    except AttributeError:   # ref. ICAT issue 130
        d['dataCollectionDatafiles'] = []
    return d

# Entities without a constraint will use their id to form the unique
# key as a last resort.  But we want the keys to have a well defined
# order, independent from the id.  Enforce this by artificially adding
# some suitable attribute values to the constraint.
client.typemap['job'].Constraint = ('application', 'id')
client.typemap['rule'].Constraint = ('grouping', 'what', 'id')
client.typemap['study'].Constraint = ('name', 'id')

entitytypes = [('User', entitydict, "User", False), 
               ('Group', groupdict, "Grouping INCLUDE UserGroup, User", False),
               ('Rule', entitydict, "Rule INCLUDE Grouping", True),
               ('PublicStep', entitydict, "PublicStep", False),
               ('Facility', entitydict, "Facility", False),
               ('Instrument', instrumentdict, 
                "Instrument INCLUDE Facility, InstrumentScientist, User", 
                False),
               ('ParameterType', parametertypedict, 
                "ParameterType INCLUDE Facility, PermissibleStringValue", 
                False),
               ('InvestigationType', entitydict, 
                "InvestigationType INCLUDE Facility", False),
               ('SampleType', entitydict, "SampleType INCLUDE Facility", 
                False),
               ('DatasetType', entitydict, "DatasetType INCLUDE Facility", 
                False),
               ('DatafileFormat', entitydict, 
                "DatafileFormat INCLUDE Facility", False),
               ('FacilityCycle', entitydict, "FacilityCycle INCLUDE Facility", 
                False),
               ('Application', entitydict, "Application INCLUDE Facility", 
                False),
               ('Investigation', investigationdict, 
                "SELECT i FROM Investigation i "
                "INCLUDE i.facility, i.type, "
                "i.investigationInstruments AS ii, ii.instrument, "
                "i.shifts, i.keywords, i.publications, "
                "i.investigationUsers AS iu, iu.user, "
                "i.parameters AS ip, ip.type", 
                False),
               ('Study', studydict, 
                "SELECT i FROM Study i INCLUDE i.user, "
                "i.studyInvestigations AS si, si.investigation", 
                True),
               ('Sample', entityparamdict, 
                "SELECT i FROM Sample i "
                "INCLUDE i.investigation, i.investigation.facility, i.type, "
                "i.parameters AS ip, ip.type", 
                False),
               ('Dataset', entityparamdict, 
                "SELECT i FROM Dataset i "
                "INCLUDE i.investigation, i.investigation.facility, "
                "i.type, i.sample, i.parameters AS ip, ip.type", 
                False),
               ('Datafile', entityparamdict, 
                "SELECT i FROM Datafile i "
                "INCLUDE i.dataset, i.dataset.investigation, "
                "i.dataset.investigation.facility, i.datafileFormat, "
                "i.parameters AS ip, ip.type", 
                False),
               ('RelatedDatafile', entitydict, 
                "SELECT i FROM RelatedDatafile i "
                "INCLUDE i.sourceDatafile, i.destDatafile", 
                False),
               ('DataCollection', datacollectiondict, 
                "SELECT i FROM DataCollection i "
                "INCLUDE i.dataCollectionDatasets AS ds, ds.dataset, "
                "i.dataCollectionDatafiles AS df, df.datafile, "
                "i.parameters AS ip, ip.type", 
                False),
               ('Job', entitydict, 
                "SELECT i FROM Job i INCLUDE i.application, "
                "i.inputDataCollection, i.outputDataCollection", 
                True)]

for (name, convert, searchexp, reindex) in entitytypes:
    d = {}
    for e in client.search(searchexp):
        k = e.getUniqueKey(False)
        keyindex[e.id] = k
        d[k] = convert(e)
    if reindex:
        ds = {}
        keys = d.keys()
        keys.sort()
        i = 0
        for k in keys:
            i += 1
            n = "%s_%08d" % (name, i)
            ds[n] = d[k]
        d = ds
    dump[name] = d

print yaml.dump(dump, default_flow_style=False)
