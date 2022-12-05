"""Test ingest of legacy ICAT data files.

In order to accommodate for the ICAT 5.0 schema extensions the order
and arrangement of data objects in the dump file created by icatdump
has been changed in python-icat 1.0.0 in an incompatible way.  In some
cases, older versions of icatingest will fail to read dump files
written by new versions of icatdump.

In the other direction, compatibility should be retained: current
versions of icatingest should be able to read legacy dump files
created by older versions of icatdump.  This is verified by the test
in this module.
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
from conftest import (getConfig, icat_version, require_icat_version, _skip,
                      gettestdata, callscript,
                      filter_file, yaml_filter, xml_filter)


def get_dumpfiles(ext = "yaml"):
    require_icat_version("4.4.0", "oldest available set of test data")
    if icat_version < "4.7":
        legacy_fname = "legacy-icatdump-4.4.%s" % ext
        reference_fname = "icatdump-4.4.%s" % ext
    elif icat_version < "4.10":
        legacy_fname = "legacy-icatdump-4.7.%s" % ext
        reference_fname = "icatdump-4.7.%s" % ext
    elif icat_version < "5.0":
        legacy_fname = "legacy-icatdump-4.10.%s" % ext
        reference_fname = "icatdump-4.10.%s" % ext
    else:
        _skip("legacy dumpfiles only available for ICAT server versions "
              "older than 5.0")
    return (gettestdata(legacy_fname), gettestdata(reference_fname))

backends = {
    'XML': {
        'dumpfiles': get_dumpfiles("xml"),
        'fileext': '.xml',
        'filter': xml_filter,
    },
    'YAML': {
        'dumpfiles': get_dumpfiles("yaml"),
        'fileext': '.yaml',
        'filter': yaml_filter,
    },
}

@pytest.fixture(scope="module")
def client():
    client, conf = getConfig()
    client.login(conf.auth, conf.credentials)
    return client

@pytest.fixture(scope="module", params=backends.keys())
def ingestcase(request, standardCmdArgs):
    param = request.param
    callscript("wipeicat.py", standardCmdArgs)
    return param

@pytest.fixture(scope="function")
def ingestcheck(ingestcase, request):
    ingestname = "test_ingest[%s]" % ingestcase
    depends(request, [ingestname])
    return ingestcase


@pytest.mark.dependency()
def test_ingest(ingestcase, standardCmdArgs):
    """Ingest a legacy dumpfile.
    """
    legacy_dump, _ = backends[ingestcase]['dumpfiles']
    args = standardCmdArgs + ["-f", ingestcase, "-i", str(legacy_dump)]
    callscript("icatingest.py", args)

def test_check_content(ingestcheck, standardCmdArgs, tmpdirsec):
    """Dump the content and check that we get the reference dump file back.
    """
    _, ref_dump = backends[ingestcheck]['dumpfiles']
    fileext = backends[ingestcheck]['fileext']
    dump = tmpdirsec / ("dump" + fileext)
    fdump = tmpdirsec / ("dump-filter" + fileext)
    ref_fdump = tmpdirsec / ("dump-filter-ref" + fileext)
    filter_file(ref_dump, ref_fdump, *backends[ingestcheck]['filter'])
    args = standardCmdArgs + ["-f", ingestcheck, "-o", str(dump)]
    callscript("icatdump.py", args)
    filter_file(dump, fdump, *backends[ingestcheck]['filter'])
    assert filecmp.cmp(str(ref_fdump), str(fdump)), \
        "content of ICAT was not as expected"
