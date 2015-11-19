"""Test icatdump and icatingest.
"""

import os.path
import filecmp
import pytest
import icat
import icat.config
from conftest import getConfig, require_icat_version
from conftest import gettestdata, callscript
from conftest import filter_file, yaml_filter, xml_filter

# test content has InvestigationGroup objects.
require_icat_version("4.4.0")

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


def test_ingest_xml(standardConfig):
    """Restore the ICAT content from a XML dumpfile.
    """
    callscript("wipeicat.py", standardConfig.cmdargs)
    refdump = backends["XML"]['refdump']
    args = standardConfig.cmdargs + ["-f", "XML", "-i", refdump]
    callscript("icatingest.py", args)

@pytest.mark.parametrize(("backend"), sorted(backends.keys()))
def test_check_content_xml(standardConfig, tmpdirsec, backend):
    """Dump the content and check that we get the reference dump file back.
    """
    refdump = backends[backend]['refdump']
    fileext = backends[backend]['fileext']
    dump = os.path.join(tmpdirsec.dir, "dump" + fileext)
    fdump = os.path.join(tmpdirsec.dir, "dump-filter" + fileext)
    reffdump = os.path.join(tmpdirsec.dir, "dump-filter-ref" + fileext)
    filter_file(refdump, reffdump, *backends[backend]['filter'])
    args = standardConfig.cmdargs + ["-f", backend, "-o", dump]
    callscript("icatdump.py", args)
    filter_file(dump, fdump, *backends[backend]['filter'])
    assert filecmp.cmp(reffdump, fdump), "content of ICAT was not as expected"

def test_check_summary_root_xml(standardConfig, tmpdirsec):
    """Check the number of objects for each class at the ICAT server.
    """
    summary = os.path.join(tmpdirsec.dir, "summary")
    ref = refsummary["root"]
    with open(summary, "wt") as out:
        callscript("icatsummary.py", standardConfig.cmdargs, stdout=out)
    assert filecmp.cmp(ref, summary), "ICAT content was not as expected"

@pytest.mark.parametrize(("user"), users)
def test_check_summary_user_xml(tmpdirsec, user):
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


def test_ingest_yaml(standardConfig):
    """Restore the ICAT content from a YAML dumpfile.
    """
    callscript("wipeicat.py", standardConfig.cmdargs)
    refdump = backends["YAML"]['refdump']
    args = standardConfig.cmdargs + ["-f", "YAML", "-i", refdump]
    callscript("icatingest.py", args)

@pytest.mark.parametrize(("backend"), sorted(backends.keys()))
def test_check_content_yaml(standardConfig, tmpdirsec, backend):
    """Dump the content and check that we get the reference dump file back.
    """
    refdump = backends[backend]['refdump']
    fileext = backends[backend]['fileext']
    dump = os.path.join(tmpdirsec.dir, "dump" + fileext)
    fdump = os.path.join(tmpdirsec.dir, "dump-filter" + fileext)
    reffdump = os.path.join(tmpdirsec.dir, "dump-filter-ref" + fileext)
    filter_file(refdump, reffdump, *backends[backend]['filter'])
    args = standardConfig.cmdargs + ["-f", backend, "-o", dump]
    callscript("icatdump.py", args)
    filter_file(dump, fdump, *backends[backend]['filter'])
    assert filecmp.cmp(reffdump, fdump), "content of ICAT was not as expected"

def test_check_summary_root_yaml(standardConfig, tmpdirsec):
    """Check the number of objects for each class at the ICAT server.
    """
    summary = os.path.join(tmpdirsec.dir, "summary")
    ref = refsummary["root"]
    with open(summary, "wt") as out:
        callscript("icatsummary.py", standardConfig.cmdargs, stdout=out)
    assert filecmp.cmp(ref, summary), "ICAT content was not as expected"

@pytest.mark.parametrize(("user"), users)
def test_check_summary_user_yaml(tmpdirsec, user):
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
