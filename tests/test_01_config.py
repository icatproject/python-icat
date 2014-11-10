"""Test module icat.config
"""

import pytest
import os.path
import shutil
import tempfile
import getpass
import icat.config


# ============================= helper =============================

# Deliberately not using the 'tmpdir' fixture provided by pytest,
# because it seem to use a predictable directory name in /tmp wich is
# insecure.

class TmpConfigFile(object):
    """Provide a temporary configuration file.
    """
    def __init__(self, content):
        self.dir = tempfile.mkdtemp(prefix="python-icat-test-config-")
        self.path = os.path.join(self.dir, "icat.cfg")
        with open(self.path, "w") as f:
            f.write(content)
    def __del__(self):
        self.cleanup()
    def cleanup(self):
        if self.dir:
            shutil.rmtree(self.dir)
        self.dir = None
        self.path = None

# Content of the configuration file used in the tests
configfilestr = """
[example_root]
url = https://icat.example.com/ICATService/ICAT?wsdl
auth = simple
username = root
password = secret
idsurl = https://icat.example.com/ids
ldap_uri = ldap://ldap.example.com
ldap_base = ou=People,dc=example,dc=com

[example_jdoe]
url = https://icat.example.com/ICATService/ICAT?wsdl
auth = ldap
username = jdoe
password = pass
"""

@pytest.fixture(scope="module")
def tmpconfigfile(request):
    tmpconf = TmpConfigFile(configfilestr)
    request.addfinalizer(tmpconf.cleanup)
    return tmpconf

# ============================= tests ==============================

def test_config_minimal():
    """Minimal example.

    No login credentials, only relevant config option is the url which
    is provided as command line argument.
    """

    args = ["-w", "https://icat.example.com/ICATService/ICAT?wsdl"]
    conf = icat.config.Config(needlogin=False).getconfig(args)

    attrs = [ a for a in sorted(conf.__dict__.keys()) if a[0] != '_' ]
    assert attrs == [ 'client_kwargs', 'configFile', 'configSection', 
                      'http_proxy', 'https_proxy', 'no_proxy', 'url' ]

    # Deliberately not checking client_kwargs, configFile, http_proxy,
    # and https_proxy.  configFile contains the default location of
    # the config file which is not relevant here.  *_proxy may be set
    # from environment variables.  client_kwargs should be opaque for
    # the user of the module anyway.  It may contain the proxy
    # settings, if any are set, and may also contain other stuff in
    # future versions.
    assert conf.configSection is None
    assert conf.url == "https://icat.example.com/ICATService/ICAT?wsdl"


def test_config_minimal_file(tmpconfigfile, monkeypatch):
    """Minimal example.

    Almost the same as test_config_minimal(), but read the url from
    a config file this time.
    """

    # Let the config file be found in the default location, which is
    # [basedir+"/icat.cfg", "icat.cfg"], where basedir is "~/.icat".
    # Make sure that basedir does not exist and that our config file
    # is in the cwd.
    monkeypatch.setattr(icat.config, "basedir", 
                        os.path.join(tmpconfigfile.dir, ".icat"))
    monkeypatch.chdir(tmpconfigfile.dir)

    args = ["-s", "example_root"]
    conf = icat.config.Config(needlogin=False).getconfig(args)

    attrs = [ a for a in sorted(conf.__dict__.keys()) if a[0] != '_' ]
    assert attrs == [ 'client_kwargs', 'configFile', 'configSection', 
                      'http_proxy', 'https_proxy', 'no_proxy', 'url' ]

    assert conf.configFile == ["icat.cfg"]
    assert conf.configSection == "example_root"
    assert conf.url == "https://icat.example.com/ICATService/ICAT?wsdl"


def test_config_simple_login(tmpconfigfile):
    """Simple login example.

    Standard usage, read everything from a config file.
    """

    args = ["-c", tmpconfigfile.path, "-s", "example_root"]
    conf = icat.config.Config().getconfig(args)

    attrs = [ a for a in sorted(conf.__dict__.keys()) if a[0] != '_' ]
    assert attrs == [ 'auth', 'client_kwargs', 'configFile', 'configSection', 
                      'credentials', 'http_proxy', 'https_proxy', 'no_proxy', 
                      'password', 'promptPass', 'url', 'username' ]

    assert conf.configFile == [tmpconfigfile.path]
    assert conf.configSection == "example_root"
    assert conf.url == "https://icat.example.com/ICATService/ICAT?wsdl"
    assert conf.auth == "simple"
    assert conf.username == "root"
    assert conf.password == "secret"
    assert conf.promptPass == False
    assert conf.credentials == {'username': 'root', 'password': 'secret'}


def test_config_override(tmpconfigfile):
    """
    Read some stuff from a config file, override some other options
    with command line arguments.
    """

    args = ["-c", tmpconfigfile.path, "-s", "example_root", 
            "-a", "db", "-u", "rbeck", "-p", "geheim"]
    conf = icat.config.Config().getconfig(args)

    attrs = [ a for a in sorted(conf.__dict__.keys()) if a[0] != '_' ]
    assert attrs == [ 'auth', 'client_kwargs', 'configFile', 'configSection', 
                      'credentials', 'http_proxy', 'https_proxy', 'no_proxy', 
                      'password', 'promptPass', 'url', 'username' ]

    assert conf.configFile == [tmpconfigfile.path]
    assert conf.configSection == "example_root"
    assert conf.url == "https://icat.example.com/ICATService/ICAT?wsdl"
    assert conf.auth == "db"
    assert conf.username == "rbeck"
    assert conf.password == "geheim"
    assert conf.promptPass == False
    assert conf.credentials == {'username': 'rbeck', 'password': 'geheim'}


def test_config_askpass(tmpconfigfile, monkeypatch):
    """
    Same as test_config_override(), but do not pass the password in
    the command line arguments.  In this case, getconfig() should
    prompt for the password.
    """

    def mockgetpass():
        return "mockpass"
    monkeypatch.setattr(getpass, "getpass", mockgetpass)

    args = ["-c", tmpconfigfile.path, "-s", "example_root", 
            "-a", "db", "-u", "rbeck"]
    conf = icat.config.Config().getconfig(args)

    attrs = [ a for a in sorted(conf.__dict__.keys()) if a[0] != '_' ]
    assert attrs == [ 'auth', 'client_kwargs', 'configFile', 'configSection', 
                      'credentials', 'http_proxy', 'https_proxy', 'no_proxy', 
                      'password', 'promptPass', 'url', 'username' ]

    assert conf.configFile == [tmpconfigfile.path]
    assert conf.configSection == "example_root"
    assert conf.url == "https://icat.example.com/ICATService/ICAT?wsdl"
    assert conf.auth == "db"
    assert conf.username == "rbeck"
    assert conf.password == "mockpass"
    assert conf.promptPass == True
    assert conf.credentials == {'username': 'rbeck', 'password': 'mockpass'}


def test_config_environment(tmpconfigfile, monkeypatch):
    """
    Set some config variables from the environment.
    """

    monkeypatch.setenv("ICAT_CFG", tmpconfigfile.path)
    monkeypatch.setenv("ICAT_AUTH", "db")
    monkeypatch.setenv("http_proxy", "http://www-cache.example.org:3128/")
    monkeypatch.setenv("https_proxy", "http://www-cache.example.org:3128/")
    monkeypatch.setenv("no_proxy", "localhost, .example.org")

    args = ["-s", "example_root", "-u", "rbeck", "-p", "geheim"]
    conf = icat.config.Config().getconfig(args)

    attrs = [ a for a in sorted(conf.__dict__.keys()) if a[0] != '_' ]
    assert attrs == [ 'auth', 'client_kwargs', 'configFile', 'configSection', 
                      'credentials', 'http_proxy', 'https_proxy', 'no_proxy', 
                      'password', 'promptPass', 'url', 'username' ]

    assert conf.configFile == [tmpconfigfile.path]
    assert conf.configSection == "example_root"
    assert conf.url == "https://icat.example.com/ICATService/ICAT?wsdl"
    assert conf.http_proxy == "http://www-cache.example.org:3128/"
    assert conf.https_proxy == "http://www-cache.example.org:3128/"
    assert conf.no_proxy == "localhost, .example.org"
    assert conf.auth == "db"
    assert conf.username == "rbeck"
    assert conf.password == "geheim"
    assert conf.promptPass == False
    assert conf.credentials == {'username': 'rbeck', 'password': 'geheim'}
    assert conf.client_kwargs['proxy'] == {
        'http': 'http://www-cache.example.org:3128/', 
        'https': 'http://www-cache.example.org:3128/', 
    }


def test_config_ids(tmpconfigfile):
    """Simple login example.

    Ask for the idsurl configuration variable.
    """

    # We set ids="optional", the idsurl is present in section example_root.
    args = ["-c", tmpconfigfile.path, "-s", "example_root"]
    conf = icat.config.Config(ids="optional").getconfig(args)

    attrs = [ a for a in sorted(conf.__dict__.keys()) if a[0] != '_' ]
    assert attrs == [ 'auth', 'client_kwargs', 'configFile', 'configSection', 
                      'credentials', 'http_proxy', 'https_proxy', 'idsurl', 
                      'no_proxy', 'password', 'promptPass', 'url', 'username' ]

    assert conf.configFile == [tmpconfigfile.path]
    assert conf.configSection == "example_root"
    assert conf.url == "https://icat.example.com/ICATService/ICAT?wsdl"
    assert conf.idsurl == "https://icat.example.com/ids"
    assert conf.auth == "simple"
    assert conf.username == "root"
    assert conf.password == "secret"
    assert conf.promptPass == False
    assert conf.credentials == {'username': 'root', 'password': 'secret'}

    # In section example_jdoe, idsurl is not set, so the configuration
    # variable is present, but set to None.
    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe"]
    conf = icat.config.Config(ids="optional").getconfig(args)

    attrs = [ a for a in sorted(conf.__dict__.keys()) if a[0] != '_' ]
    assert attrs == [ 'auth', 'client_kwargs', 'configFile', 'configSection', 
                      'credentials', 'http_proxy', 'https_proxy', 'idsurl', 
                      'no_proxy', 'password', 'promptPass', 'url', 'username' ]

    assert conf.configFile == [tmpconfigfile.path]
    assert conf.configSection == "example_jdoe"
    assert conf.url == "https://icat.example.com/ICATService/ICAT?wsdl"
    assert conf.idsurl == None
    assert conf.auth == "ldap"
    assert conf.username == "jdoe"
    assert conf.password == "pass"
    assert conf.promptPass == False
    assert conf.credentials == {'username': 'jdoe', 'password': 'pass'}


def test_config_custom_var(tmpconfigfile):
    """
    Define custom configuration variables.
    """

    # Note that ldap_filter is not defined in the configuration file,
    # but we have a default value defined here, so this is ok.
    args = ["-c", tmpconfigfile.path, "-s", "example_root"]
    config = icat.config.Config()
    config.add_variable('ldap_uri', ("-l", "--ldap-uri"), 
                        dict(help="URL of the LDAP server"),
                        envvar='LDAP_URI')
    config.add_variable('ldap_base', ("-b", "--ldap-base"), 
                        dict(help="base DN for searching the LDAP server"),
                        envvar='LDAP_BASE')
    config.add_variable('ldap_filter', ("-f", "--ldap-filter"), 
                        dict(help="search filter to select the user entries"),
                        default='(uid=*)')
    conf = config.getconfig(args)

    attrs = [ a for a in sorted(conf.__dict__.keys()) if a[0] != '_' ]
    assert attrs == [ 'auth', 'client_kwargs', 'configFile', 'configSection', 
                      'credentials', 'http_proxy', 'https_proxy', 
                      'ldap_base', 'ldap_filter', 'ldap_uri', 'no_proxy', 
                      'password', 'promptPass', 'url', 'username' ]

    assert conf.configFile == [tmpconfigfile.path]
    assert conf.configSection == "example_root"
    assert conf.url == "https://icat.example.com/ICATService/ICAT?wsdl"
    assert conf.auth == "simple"
    assert conf.username == "root"
    assert conf.password == "secret"
    assert conf.promptPass == False
    assert conf.ldap_uri == "ldap://ldap.example.com"
    assert conf.ldap_base == "ou=People,dc=example,dc=com"
    assert conf.ldap_filter == "(uid=*)"
    assert conf.credentials == {'username': 'root', 'password': 'secret'}
