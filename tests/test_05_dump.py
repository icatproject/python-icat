"""Test icatdump and icatingest.
"""

import os.path
import re
import filecmp
import pytest
try:
    from pytest_dependency import depends
except ImportError:
    def depends(request, other_tests):
        pass
import icat
import icat.config
from conftest import getConfig, require_icat_version
from conftest import gettestdata, callscript
from conftest import filter_file, yaml_filter, xml_filter


require_icat_version("4.4.0", "need InvestigationGroup")

backends = {
    'XML': {
        'refdump': gettestdata("icatdump.xml"),
        'fileext': '.xml',
        'filter': xml_filter,
    },
    'YAML': {
        'refdump': gettestdata("icatdump.yaml"),
        'fileext': '.yaml',
        'filter': yaml_filter,
    },
}
users = [ "acord", "ahau", "jbotu", "jdoe", "nbour", "rbeck" ]
refsummary = { "root": gettestdata("summary") }
for u in users:
    refsummary[u] = gettestdata("summary.%s" % u)

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
summary_filter = (re.compile(r"^((?:DataCollection(?:Datafile|Dataset|Parameter)?|Job|RelatedDatafile)\s*) : \d+$"),
                  r"\1 : 0")

# Test queries and results for test_check_queries().  This is mostly
# to verify that object relations are kept intact after an icatdump /
# icatingest cycle.
queries = [
    ("Datafile.name <-> Dataset <-> Investigation [name='12100409-ST']",
     ['e208341.nxs', 'e208945-2.nxs', 'e208945.dat', 'e208945.nxs',
      'e208947.nxs']),
    ("SELECT p.numericValue FROM DatasetParameter p "
     "JOIN p.dataset AS ds JOIN ds.investigation AS i JOIN p.type AS t "
     "WHERE i.name = '10100601-ST' AND ds.name = 'e208339' "
     "AND t.name = 'Magnetic field'",
     [7.3]),
    ("SELECT ds.name FROM Dataset ds "
     "JOIN ds.dataCollectionDatasets AS dcds "
     "JOIN dcds.dataCollection AS dc JOIN dc.jobsAsOutput AS j "
     "WHERE j.id IS NOT NULL",
     ["e208947"]),
    ("SELECT df.name FROM Datafile df "
     "JOIN df.dataCollectionDatafiles AS dcdf "
     "JOIN dcdf.dataCollection AS dc JOIN dc.jobsAsInput AS j "
     "WHERE j.id IS NOT NULL",
     ["e208945.nxs"]),
]

@pytest.fixture(scope="module")
def client():
    conf = getConfig()
    client = icat.Client(conf.url, **conf.client_kwargs)
    client.login(conf.auth, conf.credentials)
    return client

@pytest.fixture(scope="module", params=cases, ids=caseids)
def ingestcase(request, standardConfig):
    param = request.param
    callscript("wipeicat.py", standardConfig.cmdargs)
    return param

@pytest.fixture(scope="function")
def ingestcheck(ingestcase, request):
    ingestname = "test_ingest[%s-%s]" % ingestcase
    depends(request, [ingestname])
    return ingestcase


@pytest.mark.dependency()
def test_ingest(ingestcase, standardConfig):
    """Restore the ICAT content from a dumpfile.
    """
    backend, filetype = ingestcase
    refdump = backends[backend]['refdump']
    if filetype == 'FILE':
        args = standardConfig.cmdargs + ["-f", backend, "-i", refdump]
        callscript("icatingest.py", args)
    elif filetype == 'STDINOUT':
        args = standardConfig.cmdargs + ["-f", backend]
        with open(refdump, "rt") as infile:
            callscript("icatingest.py", args, stdin=infile)
    else:
        raise RuntimeError("Invalid file type %s" % filetype)

@pytest.mark.parametrize(("case"), cases)
def test_check_content(ingestcheck, standardConfig, tmpdirsec, case):
    """Dump the content and check that we get the reference dump file back.
    """
    require_icat_version("4.6.0", "Issue icatproject/icat.server#155")
    backend, filetype = case
    refdump = backends[backend]['refdump']
    fileext = backends[backend]['fileext']
    dump = os.path.join(tmpdirsec.dir, "dump" + fileext)
    fdump = os.path.join(tmpdirsec.dir, "dump-filter" + fileext)
    reffdump = os.path.join(tmpdirsec.dir, "dump-filter-ref" + fileext)
    filter_file(refdump, reffdump, *backends[backend]['filter'])
    if filetype == 'FILE':
        args = standardConfig.cmdargs + ["-f", backend, "-o", dump]
        callscript("icatdump.py", args)
    elif filetype == 'STDINOUT':
        args = standardConfig.cmdargs + ["-f", backend]
        with open(dump, "wt") as outfile:
            callscript("icatdump.py", args, stdout=outfile)
    else:
        raise RuntimeError("Invalid file type %s" % filetype)
    filter_file(dump, fdump, *backends[backend]['filter'])
    assert filecmp.cmp(reffdump, fdump), "content of ICAT was not as expected"

def test_check_summary_root(ingestcheck, standardConfig, tmpdirsec):
    """Check the number of objects for each class at the ICAT server.
    """
    summary = os.path.join(tmpdirsec.dir, "summary")
    ref = refsummary["root"]
    with open(summary, "wt") as out:
        callscript("icatsummary.py", standardConfig.cmdargs, stdout=out)
    assert filecmp.cmp(ref, summary), "ICAT content was not as expected"

@pytest.mark.parametrize(("user"), users)
def test_check_summary_user(ingestcheck, tmpdirsec, user):
    """Check the number of objects from a user's point of view.

    This checks which objects a given user may see and thus whether
    the (read) access rules work as expected.
    """
    summary = os.path.join(tmpdirsec.dir, "summary.%s" % user)
    ref = refsummary[user]
    reff = os.path.join(tmpdirsec.dir, "summary-filter-ref.%s" % user)
    filter_file(ref, reff, *summary_filter)
    conf = getConfig(confSection=user)
    with open(summary, "wt") as out:
        callscript("icatsummary.py", conf.cmdargs, stdout=out)
    assert filecmp.cmp(reff, summary), "ICAT content was not as expected"

@pytest.mark.parametrize(("query","result"), queries)
def test_check_queries(ingestcheck, client, query, result):
    """Check the result for some queries.
    """
    res = client.search(query)
    assert sorted(res) == result
