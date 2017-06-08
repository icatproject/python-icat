"""Test module icat.dumpfile.

This test module has a similar structure as test_05_dump.py, but
rather then calling icatdump and icatingest as external scripts, it
uses the internal API icat.dumpfile.
"""

import sys
import io
import os.path
import filecmp
from lxml import etree
import pytest
try:
    from pytest_dependency import depends
except ImportError:
    def depends(request, other_tests):
        pass
import icat
import icat.config
from icat.query import Query
from icat.dumpfile import open_dumpfile
import icat.dumpfile_xml
import icat.dumpfile_yaml
from icat.dump_queries import *
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
assert backends.keys() == icat.dumpfile.Backends.keys()

# The following cases are tuples of a backend and a file type (regular
# file, stdin/stdout, in-memory stream).  They are used for both,
# input and output.  We test all combinations, e.g. reading from a XML
# file and writing it back as YAML to stdout.
cases = [ (b, t) 
          for b in backends.keys() 
          for t in ('FILE', 'MEMORY') ]
icases = cases + [ ('XML','ETREE') ]
icaseids = [ "%s-%s" % t for t in icases ]
ocases = cases

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

# ======== function equivalents to icatdump and icatingest ===========

def icatingest(client, f, backend):
    with open_dumpfile(client, f, backend, 'r') as dumpfile:
        for obj in dumpfile.getobjs():
            obj.create()

def icatdump(client, f, backend):
    with open_dumpfile(client, f, backend, 'w') as dumpfile:
        dumpfile.writedata(getAuthQueries(client))
        dumpfile.writedata(getStaticQueries(client))
        investsearch = Query(client, "Investigation", attribute="id", 
                             order=["facility.name", "name", "visitId"])
        for i in client.searchChunked(investsearch):
            dumpfile.writedata(getInvestigationQueries(client, i), chunksize=5)
        dumpfile.writedata(getOtherQueries(client))

# ============================ fixtures ==============================

@pytest.fixture(scope="module")
def client():
    client, conf = getConfig()
    client.login(conf.auth, conf.credentials)
    return client

@pytest.fixture(scope="module", params=icases, ids=icaseids)
def ingestcase(request, standardCmdArgs):
    param = request.param
    callscript("wipeicat.py", standardCmdArgs)
    return param

@pytest.fixture(scope="function")
def ingestcheck(ingestcase, request):
    ingestname = "test_ingest[%s-%s]" % ingestcase
    depends(request, [ingestname])
    return ingestcase

# ============================= tests ================================

@pytest.mark.dependency()
def test_ingest(ingestcase, client):
    """Restore the ICAT content from a dumpfile.
    """
    backend, filetype = ingestcase
    refdump = backends[backend]['refdump']
    if filetype == 'FILE':
        icatingest(client, refdump, backend)
    elif filetype == 'MEMORY':
        with open(refdump, "rb") as f:
            icatdata = f.read()
        if 'b' in icat.dumpfile.Backends[backend][0].mode:
            stream = io.BytesIO(icatdata)
        else:
            stream = io.StringIO(icatdata.decode('ascii'))
        icatingest(client, stream, backend)
        stream.close()
    elif filetype == 'ETREE':
        with open(refdump, "rb") as f:
            icatdata = etree.parse(f)
        icatingest(client, icatdata, backend)
    else:
        raise RuntimeError("Invalid file type %s" % filetype)

@pytest.mark.parametrize(("case"), ocases)
def test_check_content(ingestcheck, client, tmpdirsec, case):
    """Dump the content and check that we get the reference dump file back.
    """
    require_icat_version("4.6.0", "Issue icatproject/icat.server#155")
    backend, filetype = case
    if sys.version_info < (3, 0) and filetype == 'MEMORY' and backend == 'YAML':
        pytest.xfail("Issue #37")
    refdump = backends[backend]['refdump']
    fileext = backends[backend]['fileext']
    dump = os.path.join(tmpdirsec.dir, "dump" + fileext)
    fdump = os.path.join(tmpdirsec.dir, "dump-filter" + fileext)
    reffdump = os.path.join(tmpdirsec.dir, "dump-filter-ref" + fileext)
    filter_file(refdump, reffdump, *backends[backend]['filter'])
    if filetype == 'FILE':
        icatdump(client, dump, backend)
    elif filetype == 'MEMORY':
        if 'b' in icat.dumpfile.Backends[backend][0].mode:
            stream = io.BytesIO()
            icatdump(client, stream, backend)
            icatdata = stream.getvalue()
            stream.close()
        else:
            stream = io.StringIO()
            icatdump(client, stream, backend)
            icatdata = stream.getvalue().encode('ascii')
            stream.close()
        with open(dump, "wb") as f:
            f.write(icatdata)
    else:
        raise RuntimeError("Invalid file type %s" % filetype)
    filter_file(dump, fdump, *backends[backend]['filter'])
    assert filecmp.cmp(reffdump, fdump), "content of ICAT was not as expected"

@pytest.mark.parametrize(("query","result"), queries)
def test_check_queries(ingestcheck, client, query, result):
    """Check the result for some queries.
    """
    res = client.search(query)
    assert sorted(res) == result
