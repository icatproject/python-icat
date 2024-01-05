"""Test icatdump and icatingest.
"""

import filecmp
import re
import pytest
try:
    from pytest_dependency import depends
except ImportError:
    def depends(request, other_tests):
        pass
import icat
import icat.config
from conftest import (getConfig, icat_version, gettestdata,
                      require_dumpfile_backend,
                      get_reference_dumpfile, get_reference_summary,
                      callscript, filter_file, yaml_filter, xml_filter)


backends = {
    'XML': {
        'refdump': get_reference_dumpfile("xml"),
        'fileext': '.xml',
        'filter': xml_filter,
    },
    'YAML': {
        'refdump': get_reference_dumpfile("yaml"),
        'fileext': '.yaml',
        'filter': yaml_filter,
    },
}
users = [ "acord", "ahau", "jbotu", "jdoe", "nbour", "rbeck" ]
refsummary = get_reference_summary()

# The following cases are tuples of a backend and a file type (regular
# file, stdin/stdout, in-memory stream).  They are used for both,
# input and output.  We test all combinations, e.g. reading from a XML
# file and writing it back as YAML to stdout.
cases = [ (b, t) 
          for b in backends.keys() 
          for t in ('FILE', 'STDINOUT') ]
caseids = [ "%s-%s" % t for t in cases ]

# Read permission on DataCollection, DataCollectionDatafile,
# DataCollectionDataset, DataCollectionParameter, and Job is only
# granted to the creator of the DataCollection or the Job
# respectively.  But the createId is not preserved by an icatdump /
# icatingest cycle, so this permission is lost.  Normal users will
# thus always see zero objects of these types after a cycle.  For this
# reason, we must filter out the numbers in the reference output for
# this test.
#
# Furthermore, the test data for ICAT 4.4 do not contain Study, so we
# must also filter out those if we speak to an old server.
if icat_version < "4.7.0":
    summary_root_filter = (re.compile(r"^((?:Study(?:Investigation)?)\s*) : \d+$"),
                           r"\1 : 0")
    summary_user_filter = (re.compile(r"^((?:DataCollection(?:Datafile|Dataset|Parameter)?|Job|RelatedDatafile|Study(?:Investigation)?)\s*) : \d+$"),
                           r"\1 : 0")
else:
    summary_root_filter = None
    summary_user_filter = (re.compile(r"^((?:DataCollection(?:Datafile|Dataset|Investigation|Parameter)?|Job|RelatedDatafile)\s*) : \d+$"),
                           r"\1 : 0")

# Test queries and results for test_check_queries().  This is mostly
# to verify that object relations are kept intact after an icatdump /
# icatingest cycle.
queries = [
    pytest.param(
        "Datafile.name <-> Dataset <-> Investigation [name='10100601-ST']",
        ['e208339.dat', 'e208339.nxs', 'e208341.dat', 'e208341.nxs'],
        id="df.name"
    ),
    pytest.param(
        "SELECT p.numericValue FROM DatasetParameter p "
        "JOIN p.dataset AS ds JOIN ds.investigation AS i JOIN p.type AS t "
        "WHERE i.name = '10100601-ST' AND ds.name = 'e208339' "
        "AND t.name = 'Magnetic field'",
        [7.3],
        id="param.name"
    ),
    pytest.param(
        "SELECT ds.name FROM Dataset ds "
        "JOIN ds.dataCollectionDatasets AS dcds "
        "JOIN dcds.dataCollection AS dc JOIN dc.jobsAsOutput AS j "
        "WHERE j.id IS NOT NULL",
        ["e208947"],
        id="jobout_ds.name"
    ),
    pytest.param(
        "SELECT df.name FROM Datafile df "
        "JOIN df.dataCollectionDatafiles AS dcdf "
        "JOIN dcdf.dataCollection AS dc JOIN dc.jobsAsInput AS j "
        "WHERE j.id IS NOT NULL",
        ["e208945.nxs"],
        id="jobin_df.name"
    ),
    pytest.param(
        "SELECT COUNT(dc) FROM DataCollection dc "
        "JOIN dc.dataCollectionDatasets AS dcds JOIN dcds.dataset AS ds "
        "WHERE ds.name = 'e201215'",
        [1],
        id="dc.count"
    ),
]

@pytest.fixture(scope="module")
def client():
    client, conf = getConfig()
    client.login(conf.auth, conf.credentials)
    return client

@pytest.fixture(scope="module", params=cases, ids=caseids)
def ingestcase(request, standardCmdArgs):
    param = request.param
    callscript("wipeicat.py", standardCmdArgs)
    return param

@pytest.fixture(scope="function")
def ingestcheck(ingestcase, request):
    ingestname = "test_ingest[%s-%s]" % ingestcase
    depends(request, [ingestname])
    return ingestcase


@pytest.mark.dependency()
def test_ingest(ingestcase, standardCmdArgs):
    """Restore the ICAT content from a dumpfile.
    """
    backend, filetype = ingestcase
    require_dumpfile_backend(backend)
    refdump = backends[backend]['refdump']
    if filetype == 'FILE':
        args = standardCmdArgs + ["-f", backend, "-i", str(refdump)]
        callscript("icatingest.py", args)
    elif filetype == 'STDINOUT':
        args = standardCmdArgs + ["-f", backend]
        with refdump.open("rt") as infile:
            callscript("icatingest.py", args, stdin=infile)
    else:
        raise RuntimeError("Invalid file type %s" % filetype)

@pytest.mark.parametrize(("case"), cases)
def test_check_content(ingestcheck, standardCmdArgs, tmpdirsec, case):
    """Dump the content and check that we get the reference dump file back.
    """
    backend, filetype = case
    require_dumpfile_backend(backend)
    refdump = backends[backend]['refdump']
    fileext = backends[backend]['fileext']
    dump = tmpdirsec / ("dump" + fileext)
    fdump = tmpdirsec / ("dump-filter" + fileext)
    reffdump = tmpdirsec / ("dump-filter-ref" + fileext)
    filter_file(refdump, reffdump, *backends[backend]['filter'])
    if filetype == 'FILE':
        args = standardCmdArgs + ["-f", backend, "-o", str(dump)]
        callscript("icatdump.py", args)
    elif filetype == 'STDINOUT':
        args = standardCmdArgs + ["-f", backend]
        with dump.open("wt") as outfile:
            callscript("icatdump.py", args, stdout=outfile)
    else:
        raise RuntimeError("Invalid file type %s" % filetype)
    filter_file(dump, fdump, *backends[backend]['filter'])
    assert filecmp.cmp(str(reffdump), str(fdump)), \
        "content of ICAT was not as expected"

def test_check_summary_root(ingestcheck, standardCmdArgs, tmpdirsec):
    """Check the number of objects for each class at the ICAT server.
    """
    summary = tmpdirsec / "summary"
    ref = refsummary["root"]
    if summary_root_filter:
        reff = tmpdirsec / "summary-filter-ref"
        filter_file(ref, reff, *summary_root_filter)
        ref = reff
    with summary.open("wt") as out:
        callscript("icatsummary.py", standardCmdArgs, stdout=out)
    assert filecmp.cmp(str(ref), str(summary)), \
        "ICAT content was not as expected"

@pytest.mark.parametrize(("user"), users)
def test_check_summary_user(ingestcheck, tmpdirsec, user):
    """Check the number of objects from a user's point of view.

    This checks which objects a given user may see and thus whether
    the (read) access rules work as expected.
    """
    summary = tmpdirsec / ("summary.%s" % user)
    ref = refsummary[user]
    reff = tmpdirsec / ("summary-filter-ref.%s" % user)
    filter_file(ref, reff, *summary_user_filter)
    _, conf = getConfig(confSection=user)
    with summary.open("wt") as out:
        callscript("icatsummary.py", conf.cmdargs, stdout=out)
    assert filecmp.cmp(str(reff), str(summary)), \
        "ICAT content was not as expected"

@pytest.mark.parametrize(("query","result"), queries)
def test_check_queries(ingestcheck, client, query, result):
    """Check the result for some queries.
    """
    res = client.search(query)
    assert sorted(res) == result
