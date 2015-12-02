"""Setup content on the test ICAT server.

This test goes the complete cycle of setting up content on a test
server, including wiping all previous content, initializing the
server, creating a few example investigations, and adding some data to
these investigations.  It then compares the result with a reference
dump file.
"""

import os.path
import filecmp
import yaml
import pytest
import icat
import icat.config
from icat.query import Query
from conftest import getConfig, require_icat_version
from conftest import gettestdata, callscript, filter_file, yaml_filter


# FIXME: dependency of tests.

# wipeicat uses JPQL search syntax.
require_icat_version("4.3.0")

testinput = gettestdata("example_data.yaml")
refdump = gettestdata("icatdump.yaml")
users = [ "acord", "ahau", "jbotu", "jdoe", "nbour", "rbeck" ]
refsummary = { "root": gettestdata("summary") }
for u in users:
    refsummary[u] = gettestdata("summary.%s" % u)

@pytest.fixture(scope="module")
def data():
    with open(testinput, 'r') as f:
        return yaml.load(f)


def initobj(obj, attrs):
    """Initialize an entity object from a dict of attributes."""
    for a in obj.InstAttr:
        if a != 'id' and a in attrs:
            setattr(obj, a, attrs[a])

def get_datafile(client, df):
    query = Query(client, "Datafile", conditions={
        "name":"= '%s'" % df['name'], 
        "dataset.name":"= '%s'" % df['dataset'], 
        "dataset.investigation.name":"= '%s'" % df['investigation']
    })
    return client.assertedSearch(query)[0]

def create_datafile(client, data, df):
    query = Query(client, "Dataset", conditions={
        "name":"= '%s'" % df['dataset'], 
        "investigation.name":"= '%s'" % df['investigation']
    })
    dataset = client.assertedSearch(query)[0]
    dff = data['datafile_formats'][df['format']]
    query = Query(client, "DatafileFormat", conditions={
        "name":"= '%s'" % dff['name'], 
        "version":"= '%s'" % dff['version'], 
    })
    datafile_format = client.assertedSearch(query)[0]
    datafile = client.new("datafile")
    initobj(datafile, df)
    datafile.dataset = dataset
    datafile.datafileFormat = datafile_format
    if 'parameters' in df:
        for p in df['parameters']:
            param = client.new('datafileParameter')
            initobj(param, p)
            ptdata = data['parameter_types'][p['type']]
            query = ("ParameterType [name='%s' AND units='%s']"
                     % (ptdata['name'], ptdata['units']))
            param.type = client.assertedSearch(query)[0]
            datafile.parameters.append(param)
    datafile.create()
    return datafile


def test_init(standardConfig):
    callscript("wipeicat.py", standardConfig.cmdargs)
    callscript("init-icat.py", standardConfig.cmdargs + [testinput])


@pytest.mark.parametrize("invname", [
    "08100122-EF", 
    "10100601-ST", 
    "12100409-ST"
])
def test_create_investigation(invname):
    conf = getConfig(confSection="useroffice")
    args = conf.cmdargs + [testinput, invname]
    callscript("create-investigation.py", args)

@pytest.mark.parametrize(("user", "sample"), [
    ("jbotu", "durol"), 
    ("ahau",  "nimnga"), 
    ("nbour", "nio")
])
def test_create_sampletype(user, sample):
    conf = getConfig(confSection=user)
    args = conf.cmdargs + [testinput, sample]
    callscript("create-sampletype.py", args)

@pytest.mark.parametrize(("user", "invname"), [
    ("nbour", "08100122-EF"), 
    ("ahau",  "10100601-ST"), 
    ("nbour", "12100409-ST")
])
def test_addinvdata(user, invname):
    conf = getConfig(confSection=user)
    args = conf.cmdargs + [testinput, invname]
    callscript("add-investigation-data.py", args)

@pytest.mark.parametrize(("user", "jobname"), [
    ("nbour", "job1"),
])
def test_addjob(user, jobname):
    conf = getConfig(confSection=user)
    args = conf.cmdargs + [testinput, jobname]
    callscript("add-job.py", args)

@pytest.mark.parametrize(("user", "rdfname"), [
    ("nbour", "rdf1"),
])
def test_add_relateddatafile(data, user, rdfname):
    conf = getConfig(confSection=user)
    client = icat.Client(conf.url, **conf.client_kwargs)
    client.login(conf.auth, conf.credentials)
    rdfdata = data['related_datafiles'][rdfname]
    rdf = client.new("relatedDatafile")
    initobj(rdf, rdfdata)
    rdf.sourceDatafile = get_datafile(client, rdfdata['source'])
    rdf.destDatafile = create_datafile(client, data, rdfdata['dest'])
    rdf.create()

@pytest.mark.parametrize(("user", "studyname"), [
    ("useroffice", "study1"),
])
def test_add_study(data, user, studyname):
    pytest.skip("Study disabled, see Issue icatproject/icat.server#155")
    conf = getConfig(confSection=user)
    client = icat.Client(conf.url, **conf.client_kwargs)
    client.login(conf.auth, conf.credentials)
    studydata = data['studies'][studyname]
    study = client.new("study")
    initobj(study, studydata)
    query = "User [name='%s']" % studydata['user']
    study.user = client.assertedSearch(query)[0]
    for invname in studydata['investigations']:
        query = "Investigation [name='%s']" % invname
        si = client.new("studyInvestigation")
        si.investigation = client.assertedSearch(query)[0]
        study.studyInvestigations.append(si)
    study.create()

@pytest.mark.parametrize(("user", "pubname"), [
    ("useroffice", "pub1"),
])
def test_add_publication(data, user, pubname):
    conf = getConfig(confSection=user)
    client = icat.Client(conf.url, **conf.client_kwargs)
    client.login(conf.auth, conf.credentials)
    pubdata = data['publications'][pubname]
    publication = client.new("publication")
    initobj(publication, pubdata)
    query = "Investigation [name='%s']" % pubdata['investigation']
    publication.investigation = client.assertedSearch(query)[0]
    publication.create()


def test_check_content(standardConfig, tmpdirsec):
    """Dump the resulting content and compare with a reference dump.
    """
    dump = os.path.join(tmpdirsec.dir, "dump.yaml")
    fdump = os.path.join(tmpdirsec.dir, "dump-filter.yaml")
    reffdump = os.path.join(tmpdirsec.dir, "dump-filter-ref.yaml")
    filter_file(refdump, reffdump, *yaml_filter)
    args = standardConfig.cmdargs + ["-f", "YAML", "-o", dump]
    callscript("icatdump.py", args)
    filter_file(dump, fdump, *yaml_filter)
    assert filecmp.cmp(reffdump, fdump), "content of ICAT was not as expected"

def test_check_summary_root(standardConfig, tmpdirsec):
    """Check the number of objects for each class at the ICAT server.
    """
    summary = os.path.join(tmpdirsec.dir, "summary")
    ref = refsummary["root"]
    with open(summary, "wt") as out:
        callscript("icatsummary.py", standardConfig.cmdargs, stdout=out)
    assert filecmp.cmp(ref, summary), "ICAT content was not as expected"

@pytest.mark.parametrize(("user"), users)
def test_check_summary_user(tmpdirsec, user):
    """Check the number of objects from a user's point of view.

    This checks which objects a given user may see and thus whether
    the (read) access rules work as expected.
    """
    summary = os.path.join(tmpdirsec.dir, "summary.%s" % user)
    ref = refsummary[user]
    conf = getConfig(confSection=user)
    with open(summary, "wt") as out:
        callscript("icatsummary.py", conf.cmdargs, stdout=out)
    assert filecmp.cmp(ref, summary), "ICAT content was not as expected"
