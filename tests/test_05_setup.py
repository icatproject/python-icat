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


require_icat_version("4.3.0", "need JPQL query syntax")

testinput = gettestdata("example_data.yaml")
refdump = gettestdata("icatdump.yaml")
users = [ "acord", "ahau", "jbotu", "jdoe", "nbour", "rbeck" ]
refsummary = { "root": gettestdata("summary") }
for u in users:
    refsummary[u] = gettestdata("summary.%s" % u)
# Labels used in test dependencies.
alldata = ["init", "sample_durol", "sample_nimnga", "sample_nio", "inv_081",
           "inv_101", "inv_121", "invdata_081", "invdata_101", "invdata_121",
           "job1", "rdf1", "study1", "pub1"]

@pytest.fixture(scope="module")
def data():
    with open(testinput, 'r') as f:
        return yaml.safe_load(f)


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


@pytest.mark.dependency(name="init")
def test_init(standardCmdArgs):
    callscript("wipeicat.py", standardCmdArgs)
    callscript("init-icat.py", standardCmdArgs + [testinput])


@pytest.mark.parametrize("invname", [
    pytest.param("08100122-EF",
                 marks=pytest.mark.dependency(name="inv_081",
                                              depends=["init"])),
    pytest.param("10100601-ST",
                 marks=pytest.mark.dependency(name="inv_101",
                                              depends=["init"])),
    pytest.param("12100409-ST",
                 marks=pytest.mark.dependency(name="inv_121",
                                              depends=["init"])),
])
def test_create_investigation(invname):
    _, conf = getConfig(confSection="useroffice")
    args = conf.cmdargs + [testinput, invname]
    callscript("create-investigation.py", args)

@pytest.mark.parametrize(("user", "sample"), [
    pytest.param("jbotu", "durol",
                 marks=pytest.mark.dependency(name="sample_durol",
                                              depends=["init"])),
    pytest.param("ahau",  "nimnga",
                 marks=pytest.mark.dependency(name="sample_nimnga",
                                              depends=["init"])),
    pytest.param("nbour", "nio",
                 marks=pytest.mark.dependency(name="sample_nio",
                                              depends=["init"])),
])
def test_create_sampletype(user, sample):
    _, conf = getConfig(confSection=user)
    args = conf.cmdargs + [testinput, sample]
    callscript("create-sampletype.py", args)

@pytest.mark.parametrize(("user", "invname"), [
    pytest.param("nbour", "08100122-EF",
                 marks=pytest.mark.dependency(
                     name="invdata_081", depends=["inv_081", "sample_durol"])),
    pytest.param("ahau",  "10100601-ST",
                 marks=pytest.mark.dependency(
                     name="invdata_101", depends=["inv_101", "sample_nimnga"])),
    pytest.param("nbour", "12100409-ST",
                 marks=pytest.mark.dependency(
                     name="invdata_121", depends=["inv_121", "sample_nio"])),
])
def test_addinvdata(user, invname):
    _, conf = getConfig(confSection=user)
    args = conf.cmdargs + [testinput, invname]
    callscript("add-investigation-data.py", args)

@pytest.mark.parametrize(("user", "jobname"), [
    pytest.param("nbour", "job1",
                 marks=pytest.mark.dependency(
                     name="job1", depends=["invdata_101", "invdata_121"])),
])
def test_addjob(user, jobname):
    _, conf = getConfig(confSection=user)
    args = conf.cmdargs + [testinput, jobname]
    callscript("add-job.py", args)

@pytest.mark.parametrize(("user", "rdfname"), [
    pytest.param("nbour", "rdf1",
                 marks=pytest.mark.dependency(
                     name="rdf1", depends=["invdata_101", "invdata_121"])),
])
def test_add_relateddatafile(data, user, rdfname):
    client, conf = getConfig(confSection=user)
    client.login(conf.auth, conf.credentials)
    rdfdata = data['related_datafiles'][rdfname]
    rdf = client.new("relatedDatafile")
    initobj(rdf, rdfdata)
    rdf.sourceDatafile = get_datafile(client, rdfdata['source'])
    rdf.destDatafile = create_datafile(client, data, rdfdata['dest'])
    rdf.create()

@pytest.mark.parametrize(("user", "studyname"), [
    pytest.param("useroffice", "study1",
                 marks=pytest.mark.dependency(
                     name="study1", depends=["inv_101", "inv_121"])),
])
def test_add_study(data, user, studyname):
    client, conf = getConfig(confSection=user)
    client.login(conf.auth, conf.credentials)
    studydata = data['studies'][studyname]
    study = client.new("study")
    initobj(study, studydata)
    query = "User [name='%s']" % data['users'][studydata['user']]['name']
    study.user = client.assertedSearch(query)[0]
    for invname in studydata['investigations']:
        query = "Investigation [name='%s']" % invname
        si = client.new("studyInvestigation")
        si.investigation = client.assertedSearch(query)[0]
        study.studyInvestigations.append(si)
    study.create()

@pytest.mark.parametrize(("user", "pubname"), [
    pytest.param("useroffice", "pub1",
                 marks=pytest.mark.dependency(name="pub1",
                                              depends=["inv_101"])),
])
def test_add_publication(data, user, pubname):
    client, conf = getConfig(confSection=user)
    client.login(conf.auth, conf.credentials)
    pubdata = data['publications'][pubname]
    publication = client.new("publication")
    initobj(publication, pubdata)
    query = "Investigation [name='%s']" % pubdata['investigation']
    publication.investigation = client.assertedSearch(query)[0]
    publication.create()


@pytest.mark.dependency(depends=alldata)
def test_check_content(standardCmdArgs, tmpdirsec):
    """Dump the resulting content and compare with a reference dump.
    """
    require_icat_version("4.6.0", "Issue icatproject/icat.server#155")
    dump = os.path.join(tmpdirsec, "dump.yaml")
    fdump = os.path.join(tmpdirsec, "dump-filter.yaml")
    reffdump = os.path.join(tmpdirsec, "dump-filter-ref.yaml")
    filter_file(refdump, reffdump, *yaml_filter)
    args = standardCmdArgs + ["-f", "YAML", "-o", dump]
    callscript("icatdump.py", args)
    filter_file(dump, fdump, *yaml_filter)
    assert filecmp.cmp(reffdump, fdump), "content of ICAT was not as expected"

@pytest.mark.dependency(depends=alldata)
def test_check_summary_root(standardCmdArgs, tmpdirsec):
    """Check the number of objects for each class at the ICAT server.
    """
    summary = os.path.join(tmpdirsec, "summary")
    ref = refsummary["root"]
    with open(summary, "wt") as out:
        callscript("icatsummary.py", standardCmdArgs, stdout=out)
    assert filecmp.cmp(ref, summary), "ICAT content was not as expected"

@pytest.mark.dependency(depends=alldata)
@pytest.mark.parametrize(("user"), users)
def test_check_summary_user(tmpdirsec, user):
    """Check the number of objects from a user's point of view.

    This checks which objects a given user may see and thus whether
    the (read) access rules work as expected.
    """
    summary = os.path.join(tmpdirsec, "summary.%s" % user)
    ref = refsummary[user]
    _, conf = getConfig(confSection=user)
    with open(summary, "wt") as out:
        callscript("icatsummary.py", conf.cmdargs, stdout=out)
    assert filecmp.cmp(ref, summary), "ICAT content was not as expected"
