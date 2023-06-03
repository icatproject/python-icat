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
from conftest import (getConfig, icat_version, require_icat_version,
                      require_dumpfile_backend, gettestdata, callscript,
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
        # In the case of ICAT 5.0, it makes no sense to test a
        # "legacy" dump file corresponding to the icatdump-5.0.*
        # example files, because the legacy icatdump would not be able
        # to deal with the new schema entity classes.  We use the 4.10
        # legacy dump files instead.  But then, we need a reference
        # file corresponding to the same content defined on the ICAT
        # 5.0 schema, e.g. having the fileCount and fileSize attibutes
        # in datasets and investigations.
        legacy_fname = "legacy-icatdump-4.10.%s" % ext
        reference_fname = "ref-icatdump-5.0.%s" % ext
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
    require_dumpfile_backend(ingestcase)
    legacy_dump, _ = backends[ingestcase]['dumpfiles']
    args = standardCmdArgs + ["-f", ingestcase, "-i", str(legacy_dump)]
    callscript("icatingest.py", args)

def test_check_content(ingestcheck, standardCmdArgs, tmpdirsec):
    """Dump the content and check that we get the reference dump file back.
    """
    require_dumpfile_backend(ingestcheck)
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
