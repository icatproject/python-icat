"""Test module icat.dumpfile.

This test module has a similar structure as test_05_dump.py, but
rather than calling icatdump and icatingest as external scripts, it
uses the internal API icat.dumpfile.
"""

import filecmp
import io
try:
    from lxml import etree
except ImportError:
    etree = None
import pytest
try:
    from pytest_dependency import depends
except ImportError:
    def depends(request, other_tests):
        pass
import icat
import icat.config
from icat.dump_queries import *
from icat.dumpfile import open_dumpfile
from icat.query import Query
from conftest import (getConfig, require_dumpfile_backend,
                      get_reference_dumpfile, callscript,
                      filter_file, yaml_filter, xml_filter)


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

# ======== function equivalents to icatdump and icatingest ===========

def icatingest(client, f, backend):
    with open_dumpfile(client, f, backend, 'r') as dumpfile:
        for obj in dumpfile.getobjs():
            obj.create()

def icatdump(client, f, backend):
    with open_dumpfile(client, f, backend, 'w') as dumpfile:
        dumpfile.writedata(getAuthQueries(client))
        dumpfile.writedata(getStaticQueries(client))
        dumpfile.writedata(getFundingQueries(client))
        investsearch = Query(client, "Investigation", attributes="id",
                             order=["facility.name", "name", "visitId"])
        for i in client.searchChunked(investsearch):
            dumpfile.writedata(getInvestigationQueries(client, i), chunksize=5)
        dumpfile.writedata(getDataCollectionQueries(client))
        if 'dataPublication' in client.typemap:
            pubsearch = Query(client, "DataPublication", attributes="id",
                              order=["facility.name", "pid"])
            for i in client.searchChunked(pubsearch):
                dumpfile.writedata(getDataPublicationQueries(client, i))
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
    require_dumpfile_backend(backend)
    refdump = backends[backend]['refdump']
    if filetype == 'FILE':
        icatingest(client, refdump, backend)
    elif filetype == 'MEMORY':
        with refdump.open("rb") as f:
            icatdata = f.read()
        if 'b' in icat.dumpfile.Backends[backend][0].mode:
            stream = io.BytesIO(icatdata)
        else:
            stream = io.StringIO(icatdata.decode('ascii'))
        icatingest(client, stream, backend)
        stream.close()
    elif filetype == 'ETREE':
        if etree is None:
            pytest.skip("Need lxml")
        with refdump.open("rb") as f:
            icatdata = etree.parse(f)
        icatingest(client, icatdata, backend)
    else:
        raise RuntimeError("Invalid file type %s" % filetype)

@pytest.mark.parametrize(("case"), ocases)
def test_check_content(ingestcheck, client, tmpdirsec, case):
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
        with dump.open("wb") as f:
            f.write(icatdata)
    else:
        raise RuntimeError("Invalid file type %s" % filetype)
    filter_file(dump, fdump, *backends[backend]['filter'])
    assert filecmp.cmp(str(reffdump), str(fdump)), \
        "content of ICAT was not as expected"

@pytest.mark.parametrize(("query","result"), queries)
def test_check_queries(ingestcheck, client, query, result):
    """Check the result for some queries.
    """
    res = client.search(query)
    assert sorted(res) == result
