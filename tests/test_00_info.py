"""Report version info about python-icat being tested.
"""

from __future__ import print_function
import pytest
import os.path
import icat

class Reporter(object):
    """Cumulate messages and report them later using a terminalreporter.
    """

    def __init__(self, terminalreporter):
        super(Reporter, self).__init__()
        self.terminal = terminalreporter
        self.msgs = []

    def addmsg(self, m):
        self.msgs.append(m)

    def flush(self):
        for m in self.msgs:
            self.terminal.write_line("    " + m)
        self.msgs = []

@pytest.fixture()
def terminal(pytestconfig):
    return pytestconfig.pluginmanager.getplugin('terminalreporter')

@pytest.fixture()
def diag(request, terminal):
    rep = Reporter(terminal)
    request.addfinalizer(rep.flush)
    return rep

def test_info(diag):
    assert icat.__version__
    assert icat.__revision__
    diag.addmsg("Version: python-icat %s (%s)" 
                % (icat.__version__, icat.__revision__))
    diag.addmsg("Path: %s" 
                % os.path.dirname(os.path.abspath(icat.__file__)))
