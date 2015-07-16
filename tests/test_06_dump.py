"""Test icatdump and icatrestore.
"""

import os.path
import filecmp
import pytest
import icat
import icat.config
from conftest import gettestdata, callscript, filter_xml_dump, filter_yaml_dump

backends = {
    'XML': {
        'refdump': gettestdata("icatdump.xml"),
        'fileext': '.xml',
        'filter': filter_xml_dump,
    },
    'YAML': {
        'refdump': gettestdata("icatdump.yaml"),
        'fileext': '.yaml',
        'filter': filter_yaml_dump,
    },
}
users = [ "acord", "ahau", "jbotu", "jdoe", "nbour", "rbeck" ]
refsummary = { "root": gettestdata("summary") }
for u in users:
    refsummary[u] = gettestdata("summary.%s" % u)


def test_restore_xml(icatconfigfile):
    """Restore the ICAT content from a XML dumpfile.
    """
    callscript("wipeicat.py", ["-c", icatconfigfile, "-s", "root"])
    refdump = backends["XML"]['refdump']
    args = ["-c", icatconfigfile, "-s", "root", "-f", "XML", "-i", refdump]
    callscript("icatrestore.py", args)

@pytest.mark.parametrize(("backend"), sorted(backends.keys()))
def test_check_content_xml(icatconfigfile, tmpdirsec, backend):
    """Dump the content and check that we get the reference dump file back.
    """
    refdump = backends[backend]['refdump']
    fileext = backends[backend]['fileext']
    ffilter = backends[backend]['filter']
    dump = os.path.join(tmpdirsec.dir, "dump" + fileext)
    fdump = os.path.join(tmpdirsec.dir, "dump-filter" + fileext)
    reffdump = os.path.join(tmpdirsec.dir, "dump-filter-ref" + fileext)
    ffilter(refdump, reffdump)
    args = ["-c", icatconfigfile, "-s", "root", "-f", backend, "-o", dump]
    callscript("icatdump.py", args)
    ffilter(dump, fdump)
    assert filecmp.cmp(reffdump, fdump), "content of ICAT was not as expected"

def test_check_summary_root_xml(icatconfigfile, tmpdirsec):
    """Check the number of objects for each class at the ICAT server.
    """
    summary = os.path.join(tmpdirsec.dir, "summary")
    ref = refsummary["root"]
    args = ["-c", icatconfigfile, "-s", "root"]
    with open(summary, "wt") as out:
        callscript("icatsummary.py", args, stdout=out)
    assert filecmp.cmp(ref, summary), "ICAT content was not as expected"

@pytest.mark.parametrize(("user"), users)
def test_check_summary_user_xml(icatconfigfile, tmpdirsec, user):
    """Check the number of objects from a user's point of view.

    This checks which objects a given user may see and thus whether
    the (read) access rules work as expected.
    """
    summary = os.path.join(tmpdirsec.dir, "summary.%s" % user)
    ref = refsummary[user]
    args = ["-c", icatconfigfile, "-s", user]
    with open(summary, "wt") as out:
        callscript("icatsummary.py", args, stdout=out)
    assert filecmp.cmp(ref, summary), "ICAT content was not as expected"


def test_restore_yaml(icatconfigfile):
    """Restore the ICAT content from a YAML dumpfile.
    """
    callscript("wipeicat.py", ["-c", icatconfigfile, "-s", "root"])
    refdump = backends["YAML"]['refdump']
    args = ["-c", icatconfigfile, "-s", "root", "-f", "YAML", "-i", refdump]
    callscript("icatrestore.py", args)

@pytest.mark.parametrize(("backend"), sorted(backends.keys()))
def test_check_content_yaml(icatconfigfile, tmpdirsec, backend):
    """Dump the content and check that we get the reference dump file back.
    """
    refdump = backends[backend]['refdump']
    fileext = backends[backend]['fileext']
    ffilter = backends[backend]['filter']
    dump = os.path.join(tmpdirsec.dir, "dump" + fileext)
    fdump = os.path.join(tmpdirsec.dir, "dump-filter" + fileext)
    reffdump = os.path.join(tmpdirsec.dir, "dump-filter-ref" + fileext)
    ffilter(refdump, reffdump)
    args = ["-c", icatconfigfile, "-s", "root", "-f", backend, "-o", dump]
    callscript("icatdump.py", args)
    ffilter(dump, fdump)
    assert filecmp.cmp(reffdump, fdump), "content of ICAT was not as expected"

def test_check_summary_root_yaml(icatconfigfile, tmpdirsec):
    """Check the number of objects for each class at the ICAT server.
    """
    summary = os.path.join(tmpdirsec.dir, "summary")
    ref = refsummary["root"]
    args = ["-c", icatconfigfile, "-s", "root"]
    with open(summary, "wt") as out:
        callscript("icatsummary.py", args, stdout=out)
    assert filecmp.cmp(ref, summary), "ICAT content was not as expected"

@pytest.mark.parametrize(("user"), users)
def test_check_summary_user_yaml(icatconfigfile, tmpdirsec, user):
    """Check the number of objects from a user's point of view.

    This checks which objects a given user may see and thus whether
    the (read) access rules work as expected.
    """
    summary = os.path.join(tmpdirsec.dir, "summary.%s" % user)
    ref = refsummary[user]
    args = ["-c", icatconfigfile, "-s", user]
    with open(summary, "wt") as out:
        callscript("icatsummary.py", args, stdout=out)
    assert filecmp.cmp(ref, summary), "ICAT content was not as expected"
