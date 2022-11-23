#! /usr/bin/python
#
# A simple command line tool to manage ParameterTypes.  See
# https://repo.icatproject.org/site/icat/server/4.10.0/schema.html#ParameterType
# for a definition of ParameterType in the ICAT schema.
#
# This example also shows the use of sub-commands in with the
# icat.config module.

import logging
import re
import icat
import icat.config
from icat.query import Query

logging.basicConfig(level=logging.INFO)

applicableTypes = ["Investigation", "DataCollection",
                   "Sample", "Dataset", "Datafile"]
valueTypes = ["NUMERIC", "STRING", "DATE_AND_TIME"]

def getUnits(s):
    if '(' in s:
        m = re.fullmatch(r'\s*([^()]+)\(([^()]+)\)\s*', s)
        if not m:
            raise ValueError("Invalid unit string '%s'" % s)
        return (m.group(1).strip(), m.group(2).strip())
    else:
        return (s.strip(), None)

def getMinMax(s):
    minmax_re = re.compile(r'''
        \s*
        ([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)
        \s*/\s*
        ([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)
        \s*
    ''', re.X)
    m = minmax_re.fullmatch(s)
    if not m:
        raise ValueError("Invalid min/max value string '%s'" % s)
    return (m.group(1), m.group(2))

config = icat.config.Config(ids=False)
subcmd = config.add_subcommands()

def add_paramtype(client, conf):
    pt = client.new("ParameterType")
    pt.facility = client.assertedSearch("Facility")[0]
    pt.name = conf.name
    units, units_fullname = getUnits(conf.units)
    pt.units = units
    if units_fullname:
        pt.unitsFullName = units_fullname
    if conf.description:
        pt.description = conf.description
    pt.valueType = conf.valueType
    if conf.applicable == "Investigation":
        pt.applicableToInvestigation = True
    elif conf.applicable == "DataCollection":
        pt.applicableToDataCollection = True
    elif conf.applicable == "Sample":
        pt.applicableToSample = True
    elif conf.applicable == "Dataset":
        pt.applicableToDataset = True
    elif conf.applicable == "Datafile":
        pt.applicableToDatafile = True
    if conf.minmax:
        if conf.valueType != "NUMERIC":
            raise ValueError("min/max value does not make sense "
                             "for %s value type" % conf.valueType)
        pt.minimumNumericValue, pt.maximumNumericValue = getMinMax(conf.minmax)
    if conf.permstrings:
        if conf.valueType != "STRING":
            raise ValueError("permissible strings do not make sense "
                             "for %s value type" % conf.valueType)
        for s in conf.permstrings.split(','):
            psv = client.new("PermissibleStringValue", value=s)
            pt.permissibleStringValues.append(psv)
    pt.create()
    return pt

add_config = subcmd.add_subconfig("add",
                                  dict(help="add a new ParameterType"),
                                  func=add_paramtype)
add_config.add_variable('name', ("--name",),
                        dict(help="name"))
add_config.add_variable('units', ("--units",),
                        dict(help="units (unit full name)"))
add_config.add_variable('description', ("--description",),
                        dict(help="description"), optional=True)
add_config.add_variable('valueType', ("--valueType",),
                        dict(help="value type", choices=valueTypes))
add_config.add_variable('applicable', ("--applicable",),
                        dict(help="entity this ParameterTypes is applicable to",
                             choices=applicableTypes), default="Dataset")
add_config.add_variable('minmax', ("--minmax",),
                        dict(help="min/max value"), optional=True)
add_config.add_variable('permstrings', ("--permissible-strings",),
                        dict(help="comma separated list of permissible "
                             "strings"),
                        optional=True)

def ls_paramtypes(client, conf):
    query = Query(client, "ParameterType", includes=["permissibleStringValues"])
    if conf.name:
        query.addConditions({"name": "LIKE '%s%%'" % conf.name})
    if conf.applicable == "Investigation":
        query.addConditions({"applicableToInvestigation": "= 'True'"})
    elif conf.applicable == "DataCollection":
        query.addConditions({"applicableToDataCollection": "= 'True'"})
    elif conf.applicable == "Sample":
        query.addConditions({"applicableToSample": "= 'True'"})
    elif conf.applicable == "Dataset":
        query.addConditions({"applicableToDataset": "= 'True'"})
    elif conf.applicable == "Datafile":
        query.addConditions({"applicableToDatafile": "= 'True'"})
    for pt in client.search(query):
        if pt.unitsFullName:
            units = "%s (%s)" % (pt.units, pt.unitsFullName)
        else:
            units = pt.units
        applicable = []
        if pt.applicableToInvestigation:
            applicable.append("Investigation")
        if pt.applicableToDataCollection:
            applicable.append("DataCollection")
        if pt.applicableToSample:
            applicable.append("Sample")
        if pt.applicableToDataset:
            applicable.append("Dataset")
        if pt.applicableToDatafile:
            applicable.append("Datafile")
        print("----------------------------------------")
        print("name: %s" % pt.name)
        if pt.pid:
            print("pid: %s" % pt.pid)
        print("units: %s" % units)
        if pt.description:
            print("description: %s" % pt.description)
        print("valueType: %s" % pt.valueType)
        if pt.valueType == "STRING" and pt.permissibleStringValues:
            values = [psv.value for psv in pt.permissibleStringValues]
            print("permissibleStringValues: %s" % ", ".join(values))
        if pt.valueType == "NUMERIC" and (pt.minimumNumericValue is not None or
                                          pt.maximumNumericValue is not None):
            print("min - max: %s - %s" % (pt.minimumNumericValue,
                                          pt.maximumNumericValue))
        if pt.verified is not None:
            print("verified: %s" % pt.verified)
        if pt.enforced is not None:
            print("enforced: %s" % pt.enforced)
        print("applicable to: %s" % ", ".join(applicable))
        print("----------------------------------------")
        print()

ls_config = subcmd.add_subconfig("ls",
                                 dict(help="list existing ParameterTypes"),
                                 func=ls_paramtypes)
ls_config.add_variable('name', ("-n", "--name",),
                       dict(help="search by name (prefix)"), optional=True)
ls_config.add_variable('applicable', ("--applicable",),
                       dict(help="limit search to ParameterTypes applicable to "
                            "some entity", choices=applicableTypes),
                       optional=True)

client, conf = config.getconfig()
client.login(conf.auth, conf.credentials)
conf.subcmd.func(client, conf)
