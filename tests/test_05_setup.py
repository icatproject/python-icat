"""Setup content on the test ICAT server.

This test goes the complete cycle of setting up content on a test
server, including wiping all previous content, initializing the
server, creating a few example investigations, and adding some data to
these investigations.  It then compares the result with a reference
dump file.
"""

import filecmp
import re
try:
    import yaml
except ImportError:
    yaml = None
import pytest
import icat
import icat.config
from icat.query import Query
from conftest import (getConfig, icat_version, gettestdata,
                      require_dumpfile_backend,
                      get_reference_dumpfile, get_reference_summary,
                      callscript, filter_file, yaml_filter)


# Study is broken in icat.server older then 4.6.0, see
# icatproject/icat.server#155.  We do not maintain specific set of
# test data for 4.6.  Therefore we skip testing Study for ICAT older
# then 4.7.
skip_study = icat_version < "4.7.0"

have_data_publication = icat_version >= "5.0.0"

testinput = gettestdata("example_data.yaml")
users = [ "acord", "ahau", "jbotu", "jdoe", "nbour", "rbeck" ]
refdump = get_reference_dumpfile("yaml")
refsummary = get_reference_summary()
# Labels used in test dependencies.
if not skip_study:
    alldata = ["init", "sample_durol", "sample_nimnga", "sample_nio",
               "inv_081", "inv_101", "inv_121",
               "invdata_081", "invdata_101", "invdata_121",
               "job1", "rdf1", "study1", "pub1", "data_collect1"]
else:
    alldata = ["init", "sample_durol", "sample_nimnga", "sample_nio",
               "inv_081", "inv_101", "inv_121",
               "invdata_081", "invdata_101", "invdata_121",
               "job1", "rdf1", "pub1", "data_collect1"]
if have_data_publication:
    alldata.extend(["data_pub1", "data_collect2"])
summary_study_filter = (re.compile(r"^((?:Study(?:Investigation)?)\s*) : \d+$"),
                        r"\1 : 0")


@pytest.fixture(scope="module")
def data():
    if yaml is None:
        pytest.skip("Need yaml")
    with testinput.open('r') as f:
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
    datafile = client.new("Datafile")
    initobj(datafile, df)
    datafile.dataset = dataset
    datafile.datafileFormat = datafile_format
    if 'parameters' in df:
        for p in df['parameters']:
            param = client.new("DatafileParameter")
            initobj(param, p)
            ptdata = data['parameter_types'][p['type']]
            query = ("ParameterType [name='%s' AND units='%s']"
                     % (ptdata['name'], ptdata['units']))
            param.type = client.assertedSearch(query)[0]
            datafile.parameters.append(param)
    datafile.create()
    return datafile

def fix_file_size(inv_name):
    client, conf = getConfig()
    if 'fileSize' not in client.typemap['investigation'].InstAttr:
        # ICAT < 5.0: there are no fileSize and fileCount attributes
        # to fix in Investigation and Dataset.  Nothing to do.
        return
    client.login(conf.auth, conf.credentials)
    inv_query = Query(client, "Investigation", conditions={
        "name":"= '%s'" % inv_name
    }, includes="1")
    inv = client.assertedSearch(inv_query)[0]
    inv.fileCount = 0
    inv.fileSize = 0
    ds_query = Query(client, "Dataset", conditions={
        "investigation.id": "= %d" % inv.id
    }, includes="1")
    for ds in client.search(ds_query):
        fileCount_query = Query(client, "Datafile", conditions={
            "dataset.id": "= %d" % ds.id
        }, aggregate="COUNT")
        ds.fileCount = int(client.assertedSearch(fileCount_query)[0])
        if not ds.fileCount:
            ds.fileSize = 0
        else:
            fileSize_query = Query(client, "Datafile", conditions={
                "dataset.id": "= %d" % ds.id
            }, attributes="fileSize", aggregate="SUM")
            ds.fileSize = int(client.assertedSearch(fileSize_query)[0])
        ds.update()
        inv.fileCount += ds.fileCount
        inv.fileSize += ds.fileSize
    inv.update()


@pytest.mark.dependency(name="init")
def test_init(standardCmdArgs):
    if yaml is None:
        pytest.skip("Need yaml")
    callscript("wipeicat.py", standardCmdArgs)
    callscript("init-icat.py", standardCmdArgs + [str(testinput)])


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
    args = conf.cmdargs + [str(testinput), invname]
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
    args = conf.cmdargs + [str(testinput), sample]
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
    args = conf.cmdargs + [str(testinput), invname]
    callscript("add-investigation-data.py", args)
    fix_file_size(invname)

@pytest.mark.parametrize(("user", "jobname"), [
    pytest.param("nbour", "job1",
                 marks=pytest.mark.dependency(
                     name="job1", depends=["invdata_101", "invdata_121"])),
])
def test_addjob(user, jobname):
    _, conf = getConfig(confSection=user)
    args = conf.cmdargs + [str(testinput), jobname]
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
    rdf = client.new("RelatedDatafile")
    initobj(rdf, rdfdata)
    rdf.sourceDatafile = get_datafile(client, rdfdata['source'])
    rdf.destDatafile = create_datafile(client, data, rdfdata['dest'])
    rdf.create()
    fix_file_size(rdfdata['dest']['investigation'])

@pytest.mark.parametrize(("user", "studyname"), [
    pytest.param("useroffice", "study1",
                 marks=pytest.mark.dependency(
                     name="study1", depends=["inv_101", "inv_121"])),
])
@pytest.mark.skipif(skip_study, reason="Issue icatproject/icat.server#155")
def test_add_study(data, user, studyname):
    client, conf = getConfig(confSection=user)
    client.login(conf.auth, conf.credentials)
    studydata = data['studies'][studyname]
    study = client.new("Study")
    initobj(study, studydata)
    query = "User [name='%s']" % data['users'][studydata['user']]['name']
    study.user = client.assertedSearch(query)[0]
    for invname in studydata['investigations']:
        query = "Investigation [name='%s']" % invname
        si = client.new("StudyInvestigation")
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
    publication = client.new("Publication")
    initobj(publication, pubdata)
    query = "Investigation [name='%s']" % pubdata['investigation']
    publication.investigation = client.assertedSearch(query)[0]
    publication.create()

@pytest.mark.parametrize("pubname", [
    pytest.param("data_pub1",
                 marks=pytest.mark.dependency(name="data_pub1",
                                              depends=["inv_121"])),
])
@pytest.mark.skipif(not have_data_publication,
                    reason=("need ICAT server version 5.0.0 or newer: "
                            "need DataPublication"))
def test_add_data_publication(data, pubname):
    pubdata = data['data_publications'][pubname]
    client, conf = getConfig(confSection="ingest")
    client.login(conf.auth, conf.credentials)
    content = client.new("DataCollection")
    ds = pubdata['dataset']
    query = Query(client, "Investigation", conditions={
        "name":"= '%s'" % ds['investigation']
    })
    investigation = client.assertedSearch(query)[0]
    query = Query(client, "DatasetType", conditions={
        "name":"= '%s'" % data['dataset_types'][ds['type']]['name']
    })
    dataset_type = client.assertedSearch(query)[0]
    dataset = client.new("Dataset")
    initobj(dataset, ds)
    dataset.investigation = investigation
    dataset.type = dataset_type
    for df in ds['datafiles']:
        dff = data['datafile_formats'][df['format']]
        query = Query(client, "DatafileFormat", conditions={
            "name":"= '%s'" % dff['name'],
            "version":"= '%s'" % dff['version'],
        })
        datafile_format = client.assertedSearch(query)[0]
        datafile = client.new("Datafile")
        initobj(datafile, df)
        datafile.datafileFormat = datafile_format
        dataset.datafiles.append(datafile)
    dataset.complete = False
    dataset.create()
    if ds['complete']:
        del dataset.datafiles
        dataset.complete = True
        dataset.update()
    dcs = client.new("DataCollectionDataset", dataset=dataset)
    content.dataCollectionDatasets.append(dcs)
    content.create()
    content.truncateRelations()
    fix_file_size(ds['investigation'])
    client, conf = getConfig(confSection="useroffice")
    client.login(conf.auth, conf.credentials)
    data_publication = client.new("DataPublication")
    initobj(data_publication, pubdata)
    query = Query(client, "Facility", conditions={
        "name": "= '%s'" % data['facilities'][pubdata['facility']]['name']
    })
    data_publication.facility = client.assertedSearch(query)[0]
    data_publication.content = content
    if pubdata['type']:
        t = data['data_publication_types'][pubdata['type']]
        query = Query(client, "DataPublicationType", conditions={
            "name": "= '%s'" % t['name']
        })
        data_publication.type = client.assertedSearch(query)[0]
    for d in pubdata['dates']:
        data_publication.dates.append(client.new("DataPublicationDate", **d))
    for ri in pubdata['relatedItems']:
        data_publication.relatedItems.append(client.new("RelatedItem", **ri))
    for u in pubdata['users']:
        pub_user = client.new("DataPublicationUser")
        initobj(pub_user, u)
        query = Query(client, "User", conditions={
            "name": "= '%s'" % data['users'][u['user']]['name']
        })
        pub_user.user = client.assertedSearch(query)[0]
        for a in u['affiliations']:
            pub_user.affiliations.append(client.new("Affiliation", **a))
        data_publication.users.append(pub_user)
    for fr in pubdata['fundingReferences']:
        funding_ref = client.new("FundingReference")
        initobj(funding_ref, data['fundings'][fr])
        try:
            funding_ref.create()
        except icat.ICATObjectExistsError:
            funding_ref = client.searchMatching(funding_ref)
        dp_fund = client.new("DataPublicationFunding", funding=funding_ref)
        data_publication.fundingReferences.append(dp_fund)
    data_publication.create()

@pytest.mark.parametrize(("user", "objects"), [
    pytest.param(
        "jbotu",
        [
            'Dataset_investigation-(name-08100122=2DEF)_name-e201215',
            'Dataset_investigation-(name-08100122=2DEF)_name-e201216',
            'Datafile_dataset-(investigation-(name-10100601=2DST)'
            '_name-e208339)_name-e208339=2Enxs',
        ],
        marks=pytest.mark.dependency(name="data_collect1",
                                     depends=["invdata_081", "invdata_101"])
    ),
    pytest.param(
        "rbeck",
        [
            'Investigation_name-12100409=2DST',
            'Datafile_dataset-(investigation-(name-12100409=2DST)'
            '_name-e208945)_name-e208945=2Enxs',
            'Dataset_investigation-(name-08100122=2DEF)_name-e201216',
        ],
        marks=pytest.mark.dependency(name="data_collect2",
                                      depends=["invdata_081", "invdata_121"])
    ),
])
def test_add_datacollections(data, user, objects):
    """Create some arbitrary DataCollections
    """
    client, conf = getConfig(confSection=user)
    client.login(conf.auth, conf.credentials)
    collection = client.new("DataCollection")
    for key in objects:
        obj = client.searchUniqueKey(key)
        if obj.BeanName == 'Investigation':
            if 'dataCollectionInvestigation' not in client.typemap:
                pytest.skip("need DataCollectionInvestigation")
            dcinv = client.new("DataCollectionInvestigation", investigation=obj)
            collection.dataCollectionInvestigations.append(dcinv)
        elif obj.BeanName == 'Dataset':
            dcds = client.new("DataCollectionDataset", dataset=obj)
            collection.dataCollectionDatasets.append(dcds)
        elif obj.BeanName == 'Datafile':
            dcdf = client.new("DataCollectionDatafile", datafile=obj)
            collection.dataCollectionDatafiles.append(dcdf)
        else:
            raise AssertionError("invalid object type %s" % obj.BeanName)
    collection.create()

@pytest.mark.dependency(depends=alldata)
def test_check_content(standardCmdArgs, tmpdirsec):
    """Dump the resulting content and compare with a reference dump.
    """
    require_dumpfile_backend("YAML")
    dump = tmpdirsec / "dump.yaml"
    fdump = tmpdirsec / "dump-filter.yaml"
    reffdump = tmpdirsec / "dump-filter-ref.yaml"
    filter_file(refdump, reffdump, *yaml_filter)
    args = standardCmdArgs + ["-f", "YAML", "-o", str(dump)]
    callscript("icatdump.py", args)
    filter_file(dump, fdump, *yaml_filter)
    assert filecmp.cmp(str(reffdump), str(fdump)), \
        "content of ICAT was not as expected"

@pytest.mark.dependency(depends=alldata)
def test_check_summary_root(standardCmdArgs, tmpdirsec):
    """Check the number of objects for each class at the ICAT server.
    """
    summary = tmpdirsec / "summary"
    ref = refsummary["root"]
    if skip_study:
        reff = tmpdirsec / "summary-filter-ref"
        filter_file(ref, reff, *summary_study_filter)
        ref = reff
    with summary.open("wt") as out:
        callscript("icatsummary.py", standardCmdArgs, stdout=out)
    assert filecmp.cmp(str(ref), str(summary)), \
        "ICAT content was not as expected"

@pytest.mark.dependency(depends=alldata)
@pytest.mark.parametrize(("user"), users)
def test_check_summary_user(tmpdirsec, user):
    """Check the number of objects from a user's point of view.

    This checks which objects a given user may see and thus whether
    the (read) access rules work as expected.
    """
    summary = tmpdirsec / ("summary.%s" % user)
    ref = refsummary[user]
    if skip_study:
        reff = tmpdirsec / ("summary-filter-ref.%s" % user)
        filter_file(ref, reff, *summary_study_filter)
        ref = reff
    _, conf = getConfig(confSection=user)
    with summary.open("wt") as out:
        callscript("icatsummary.py", conf.cmdargs, stdout=out)
    assert filecmp.cmp(str(ref), str(summary)), \
        "ICAT content was not as expected"
