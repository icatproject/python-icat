"""Test module icat.config
"""

import argparse
import getpass
from pathlib import Path
import sys
import pytest
import icat.config
import icat.exception


# ============================= helper =============================

class Namespace():
    def __init__(self, **kwargs):
        for (k, v) in kwargs.items():
            setattr(self, k, v)

class ExpectedConf(Namespace):
    def __le__(self, other):
        for attr in self.__dict__.keys():
            try:
                if not getattr(other, attr) == getattr(self, attr):
                    return False
            except AttributeError:
                return False
        else:
            return True

# The icat.config.Config constructor already creates and initializes
# an ICAT client.  Prevent this, as we don't want to connect to a real
# server in this test module.  Foist a fake client class on the
# icat.config module.  Note that we must monkeypatch icat.config
# rather than icat.client, as the former already imported the Client
# class at this point.

class FakeClient():
    AuthInfo = None
    def __init__(self, url, **kwargs):
        self.url = url
        self.kwargs = kwargs
    def getAuthenticatorInfo(self):
        if self.AuthInfo:
            return self.AuthInfo
        else:
            raise icat.exception.VersionMethodError("getAuthenticatorInfo")
    def __eq__(self, other):
        if isinstance(other, FakeClient):
            return self.url == other.url and self.kwargs == other.kwargs
        else:
            return NotImplemented

@pytest.fixture(scope="function")
def fakeClient(monkeypatch):
    monkeypatch.setattr(icat.config, "Client", FakeClient)

# Evil black magic: monkey patch ArgumentParser to raise an error if
# either parse_args() or parse_known_args() is called.  This is needed
# to verify that disabling the argparser is effective in
# test_config_args_disable().

class ArgumentParserErrorMixin:
    def parse_args(self, *args, **kwargs):
        assert False, "parse_args() should not get called"
    def parse_known_args(self, *args, **kwargs):
        assert False, "parse_known_args() should not get called"

@pytest.fixture(scope="function")
def patchArgParse(monkeypatch):
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args",
                        ArgumentParserErrorMixin.parse_args)
    monkeypatch.setattr(argparse.ArgumentParser, "parse_known_args",
                        ArgumentParserErrorMixin.parse_known_args)

# Deliberately not using the 'tmpdir' fixture provided by pytest,
# because it seem to use a predictable directory name in /tmp wich is
# insecure.

ex_icat = "https://icat.example.com/ICATService/ICAT?wsdl"
ex_ids = "https://icat.example.com/ids"

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

[example_pubreader]
url = https://icat.example.com/ICATService/ICAT?wsdl
auth = simple
username = pubreader
password = pwpubreader
idsurl = https://icat.example.com/ids

[example_jdoe]
url = https://icat.example.com/ICATService/ICAT?wsdl
auth = ldap
username = jdoe
password = pass
greeting = Hello %(username)s!
num = 42
invnum = forty-two
flag1 = true
flag2 = off

[example_nbour]
url = https://icat.example.com/ICATService/ICAT?wsdl
auth = ldap
username = nbour

[example_anon]
url = https://icat.example.com/ICATService/ICAT?wsdl
auth = anon

[example_quirks]
url = https://icat.example.com/ICATService/ICAT?wsdl
auth = quirks

[test21]
url = https://icat.example.com/ICATService/ICAT?wsdl
auth = simple
username = root
password = secret
promptPass = Yes
"""

class ConfigFile():
    def __init__(self, confdir, content):
        self.home = confdir
        self.dir = self.home / ".icat"
        self.path = self.dir / "icat.cfg"
        self.dir.mkdir()
        with self.path.open("wt") as f:
            f.write(content)

class TmpFiles():
    def __init__(self):
        self.files = []
    def cleanup(self):
        for p in self.files:
            p.unlink()
    def addfile(self, path, content):
        try:
            path.parent.mkdir(parents=True)
        except FileExistsError:
            pass
        with path.open("wt") as f:
            f.write(content)
        self.files.append(path.resolve())

@pytest.fixture(scope="module")
def tmpconfigfile(tmpdirsec):
    return ConfigFile(tmpdirsec, configfilestr)

@pytest.fixture(scope="function")
def tmpfiles():
    files = TmpFiles()
    yield files
    files.cleanup()

# ============================= tests ==============================

def test_config_missing_mandatory(monkeypatch, fakeClient):
    """Not providing any config at all.

    This throws an error as url is mandatory.
    """
    monkeypatch.setattr(sys, "argv", ["cmd"])
    config = icat.config.Config(needlogin=False, ids=False)
    with pytest.raises(icat.exception.ConfigError) as err:
        _, conf = config.getconfig()
    assert "Config option 'url' not given" in str(err.value)


def test_config_minimal(monkeypatch, fakeClient):
    """Minimal example.

    No login credentials, only relevant config option is the url which
    is provided as command line argument.
    """

    monkeypatch.setattr(sys, "argv", ("cmd -w %s" % ex_icat).split())
    config = icat.config.Config(needlogin=False, ids=False)
    _, conf = config.getconfig()

    assert ExpectedConf(configSection=None, url=ex_icat) <= conf


def test_config_minimal_file(monkeypatch, fakeClient, tmpconfigfile):
    """Minimal example.

    Almost the same as test_config_minimal(), but read the url from
    a config file this time.
    """

    # Let the config file be found in the default location, but
    # manipulate the search path such that only the cwd exists.
    cfgdirs = [ tmpconfigfile.dir / "wobble", Path(".") ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.dir))

    monkeypatch.setattr(sys, "argv", "cmd -s example_root".split())
    config = icat.config.Config(needlogin=False, ids=False)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[Path("icat.cfg")],
                      configSection="example_root", 
                      url=ex_icat)
    assert ex <= conf


def test_config_minimal_file_preset(monkeypatch, fakeClient, tmpconfigfile):
    """Minimal example.

    Almost the same as test_config_minimal_file(), but set the section
    to be read from the config file as a preset variable rather than
    faking the comandline arguments.

    The `preset` keyword argument to `Config()` was added in response
    to the feature request Issue #77.
    """

    # Let the config file be found in the default location, but
    # manipulate the search path such that only the cwd exists.
    cfgdirs = [ tmpconfigfile.dir / "wobble", Path(".") ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.dir))

    monkeypatch.setattr(sys, "argv", ["cmd"])
    preset = {"configSection": "example_root"}
    config = icat.config.Config(needlogin=False, ids=False, preset=preset)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[Path("icat.cfg")],
                      configSection="example_root",
                      url=ex_icat)
    assert ex <= conf


def test_config_file_expanduser(monkeypatch, fakeClient, tmpconfigfile):
    """Explicitely point to the config file.

    Indicate the path of the config file in the command line
    arguments.  Use tilde expansion in this path.
    """

    # Manipulate the search path such that the config file is not
    # found in the default path.
    monkeypatch.setenv("HOME", str(tmpconfigfile.home))
    cfgdirs = [ tmpconfigfile.dir / "wobble", Path(".") ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.home))

    cmdline = "cmd -c ~/.icat/icat.cfg -s example_root"
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config(needlogin=False, ids=False)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path], 
                      configSection="example_root", 
                      url=ex_icat)
    assert ex <= conf


def test_config_minimal_defaultfile(monkeypatch, fakeClient, tmpconfigfile):
    """Minimal example.

    Almost the same as test_config_minimal_file(), but let the
    configuration file be found in the default search path rather than
    pointing to the full path.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", str(tmpconfigfile.home))
    cfgdirs = [ Path("~/.config/icat").expanduser(),
                Path("~/.icat").expanduser(),
                Path("."), ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.home))

    monkeypatch.setattr(sys, "argv", "cmd -s example_root".split())
    config = icat.config.Config(needlogin=False, ids=False)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path], 
                      configSection="example_root", 
                      url=ex_icat)
    assert ex <= conf


def test_config_args_section(monkeypatch, fakeClient, tmpconfigfile):
    """Override the command line arguments in the Config() call.

    Same setting as test_config_minimal_defaultfile(), but override
    the command line arguments using the `args` keyword arguments to
    Config().
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", str(tmpconfigfile.home))
    cfgdirs = [ Path("~/.config/icat").expanduser(),
                Path("~/.icat").expanduser(),
                Path("."), ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.home))

    # Set some bogus arguments in the command line, a mixture of
    # formally valid and invalid ones, to verify that they will indeed
    # be ignored.
    cmdline = "cmd -w https://bogus.example.com/ -f foobar"
    monkeypatch.setattr(sys, "argv", cmdline.split())
    args = "-s example_root".split()
    config = icat.config.Config(needlogin=False, ids=False, args=args)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_root",
                      url=ex_icat)
    assert ex <= conf


def test_config_args_empty(monkeypatch, fakeClient, tmpconfigfile):
    """Disable command line arguments by setting empty args.

    Configuration is read from the config file, the config section is
    set with `preset`.  Setting an empty list in `args` essentially
    disables potentially interfering command line arguments.  This was
    a common setting for service scripts with python-icat <= 1.3.0.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", str(tmpconfigfile.home))
    cfgdirs = [ Path("~/.config/icat").expanduser(),
                Path("~/.icat").expanduser(),
                Path("."), ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.home))

    # Set some bogus arguments in the command line, a mixture of
    # formally valid and invalid ones, to verify that they will indeed
    # be ignored.
    cmdline = "cmd -w https://bogus.example.com/ -f foobar"
    monkeypatch.setattr(sys, "argv", cmdline.split())
    preset = dict(configSection="example_pubreader")
    config = icat.config.Config(ids=False, preset=preset, args=())
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_pubreader",
                      url=ex_icat,
                      auth="simple",
                      username="pubreader",
                      password="pwpubreader",
                      promptPass=False,
                      credentials={'username': 'pubreader',
                                   'password': 'pwpubreader'})
    assert ex <= conf


def test_config_args_disable(monkeypatch, fakeClient, tmpconfigfile,
                             patchArgParse):
    """Disable command line arguments by setting args to False.

    Same setting as in test_config_args_empty(), but fully disable
    parsing of command line args instead of setting an empty args
    list.  Ref. #155.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", str(tmpconfigfile.home))
    cfgdirs = [ Path("~/.config/icat").expanduser(),
                Path("~/.icat").expanduser(),
                Path("."), ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.home))

    # Set some bogus arguments in the command line, a mixture of
    # formally valid and invalid ones, to verify that they will indeed
    # be ignored.
    cmdline = "cmd -w https://bogus.example.com/ -f foobar"
    monkeypatch.setattr(sys, "argv", cmdline.split())
    preset = dict(configSection="example_pubreader")
    config = icat.config.Config(ids=False, preset=preset, args=False)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_pubreader",
                      url=ex_icat,
                      auth="simple",
                      username="pubreader",
                      password="pwpubreader",
                      promptPass=False,
                      credentials={'username': 'pubreader',
                                   'password': 'pwpubreader'})
    assert ex <= conf


def test_config_no_defaultvars(monkeypatch, tmpconfigfile):
    """Config object with no default variables.

    If `defaultvars=False` is passed to the constructor of Config, no
    default configuration variables will be defined other then
    `configFile` and `configSection`.  The configuration mechanism is
    still intact.  In particular, custom configuration variables may
    be defined and reading the configuration file still works.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", str(tmpconfigfile.home))
    cfgdirs = [ Path("~/.config/icat").expanduser(),
                Path("~/.icat").expanduser(),
                Path("."), ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.home))

    monkeypatch.setattr(sys, "argv", "cmd -s example_root".split())
    config = icat.config.Config(defaultvars=False)
    config.add_variable('url', ("-w", "--url"), 
                        dict(help="URL to the web service description"))
    config.add_variable('wobble', ("--wobble",), 
                        dict(help="Strange thing"), 
                        optional=True)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path], 
                      configSection="example_root", 
                      url=ex_icat, 
                      wobble=None)
    assert ex <= conf


def test_config_simple_login(monkeypatch, fakeClient, tmpconfigfile):
    """Simple login example.

    Standard usage, read everything from a config file.
    """

    cmdline = "cmd -c %s -s example_root" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    _, conf = icat.config.Config().getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_root",
                      url=ex_icat,
                      idsurl=ex_ids,
                      auth="simple",
                      username="root",
                      password="secret",
                      promptPass=False,
                      credentials={'username': 'root', 'password': 'secret'})
    assert ex <= conf


def test_config_override(monkeypatch, fakeClient, tmpconfigfile):
    """
    Read some stuff from a config file, override some other options
    with command line arguments.
    """

    cmdline = ("cmd -c %s -s example_root -a db -u rbeck -p geheim"
               % tmpconfigfile.path)
    monkeypatch.setattr(sys, "argv", cmdline.split())
    _, conf = icat.config.Config().getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_root",
                      url=ex_icat,
                      idsurl=ex_ids,
                      auth="db",
                      username="rbeck",
                      password="geheim",
                      promptPass=False,
                      credentials={'username': 'rbeck', 'password': 'geheim'})
    assert ex <= conf


def test_config_askpass(monkeypatch, fakeClient, tmpconfigfile):
    """
    Same as test_config_override(), but do not pass the password in
    the command line arguments.  In this case, getconfig() should
    prompt for the password.
    """

    def mockgetpass(prompt='Password: '):
        return "mockpass"
    monkeypatch.setattr(getpass, "getpass", mockgetpass)

    cmdline = "cmd -c %s -s example_root -a db -u rbeck" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    _, conf = icat.config.Config().getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_root",
                      url=ex_icat,
                      idsurl=ex_ids,
                      auth="db",
                      username="rbeck",
                      password="mockpass",
                      promptPass=False,
                      credentials={'username': 'rbeck', 'password': 'mockpass'})
    assert ex <= conf


def test_config_nopass_askpass(monkeypatch, fakeClient, tmpconfigfile):
    """
    Same as test_config_askpass(), but with no password set in the
    config file.  Very early versions of icat.config had a bug to
    raise an error if no password was set at all even if interactive
    prompt for the password was explictely requested.  (Fixed in
    67e91ed.)
    """

    def mockgetpass(prompt='Password: '):
        return "mockpass"
    monkeypatch.setattr(getpass, "getpass", mockgetpass)

    cmdline = "cmd -c %s -s example_nbour -P" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    _, conf = icat.config.Config().getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_nbour",
                      url=ex_icat,
                      auth="ldap",
                      username="nbour",
                      password="mockpass",
                      promptPass=True,
                      credentials={'username': 'nbour', 'password': 'mockpass'})
    assert ex <= conf


def test_config_askpass_file(monkeypatch, fakeClient, tmpconfigfile):
    """
    Set promptPass in the configuration file.  This should force
    prompting for the password.  Issue #21.
    """

    def mockgetpass(prompt='Password: '):
        return "mockpass"
    monkeypatch.setattr(getpass, "getpass", mockgetpass)

    cmdline = "cmd -c %s -s test21" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    _, conf = icat.config.Config().getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="test21",
                      url=ex_icat,
                      auth="simple",
                      username="root",
                      password="mockpass",
                      promptPass=True,
                      credentials={'username': 'root', 'password': 'mockpass'})
    assert ex <= conf


def test_config_environment(monkeypatch, fakeClient, tmpconfigfile):
    """Set some config variables from the environment.
    """

    monkeypatch.setenv("ICAT_CFG", str(tmpconfigfile.path))
    monkeypatch.setenv("ICAT_AUTH", "db")
    monkeypatch.setenv("http_proxy", "http://www-cache.example.org:3128/")
    monkeypatch.setenv("https_proxy", "http://www-cache.example.org:3128/")
    monkeypatch.setenv("no_proxy", "localhost, .example.org")

    cmdline = "cmd -s example_root -u rbeck -p geheim"
    monkeypatch.setattr(sys, "argv", cmdline.split())
    _, conf = icat.config.Config().getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_root",
                      url=ex_icat,
                      idsurl=ex_ids,
                      http_proxy="http://www-cache.example.org:3128/",
                      https_proxy="http://www-cache.example.org:3128/",
                      no_proxy="localhost, .example.org",
                      auth="db",
                      username="rbeck",
                      password="geheim",
                      promptPass=False,
                      credentials={'username': 'rbeck', 'password': 'geheim'})
    assert ex <= conf


@pytest.mark.parametrize(("section", "ex"), [
    ("example_root",
     ExpectedConf(configSection="example_root",
                  url=ex_icat,
                  idsurl=ex_ids,
                  auth="simple",
                  username="root",
                  password="secret",
                  promptPass=False,
                  credentials={'username': 'root', 'password': 'secret'})),
    ("example_jdoe",
     ExpectedConf(configSection="example_jdoe",
                  url=ex_icat,
                  idsurl=None,
                  auth="ldap",
                  username="jdoe",
                  password="pass",
                  promptPass=False,
                  credentials={'username': 'jdoe', 'password': 'pass'})),
])
def test_config_ids(monkeypatch, fakeClient, tmpconfigfile, section, ex):
    """Simple login example.

    Ask for the idsurl configuration variable.
    """
    # We set ids="optional", the idsurl is present in section
    # example_root, but not in example_jdoe.  In the latter case, the
    # configuration variable is present, but set to None..
    cmdline = "cmd -c %s -s %s" % (tmpconfigfile.path, section)
    monkeypatch.setattr(sys, "argv", cmdline.split())
    _, conf = icat.config.Config(ids="optional").getconfig()
    assert ex <= conf


def test_config_custom_var(monkeypatch, fakeClient, tmpconfigfile):
    """Define custom configuration variables.
    """

    # Note that ldap_filter is not defined in the configuration file,
    # but we have a default value defined here, so this is ok.
    cmdline = "cmd -c %s -s example_root" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
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
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_root",
                      url=ex_icat,
                      idsurl=ex_ids,
                      auth="simple",
                      username="root",
                      password="secret",
                      promptPass=False,
                      ldap_uri="ldap://ldap.example.com",
                      ldap_base="ou=People,dc=example,dc=com",
                      ldap_filter="(uid=*)",
                      credentials={'username': 'root', 'password': 'secret'})
    assert ex <= conf


def test_config_subst_nosubst(monkeypatch, fakeClient, tmpconfigfile):
    """Use a format string in a configuration variable.

    But disable the substitution.
    """

    cmdline = "cmd -c %s -s example_jdoe" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    config.add_variable('greeting', ("--greeting",), 
                        dict(help="Greeting message"),
                        subst=False)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_jdoe",
                      url=ex_icat,
                      auth="ldap",
                      username="jdoe",
                      password="pass",
                      promptPass=False,
                      greeting="Hello %(username)s!",
                      credentials={'username': 'jdoe', 'password': 'pass'})
    assert ex <= conf


def test_config_subst(monkeypatch, fakeClient, tmpconfigfile):
    """Use a format string in a configuration variable.

    Same as above, but enable the substitution this time.
    """

    cmdline = "cmd -c %s -s example_jdoe" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    config.add_variable('greeting', ("--greeting",), 
                        dict(help="Greeting message"),
                        subst=True)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_jdoe",
                      url=ex_icat,
                      auth="ldap",
                      username="jdoe",
                      password="pass",
                      promptPass=False,
                      greeting="Hello jdoe!",
                      credentials={'username': 'jdoe', 'password': 'pass'})
    assert ex <= conf


def test_config_subst_cmdline(monkeypatch, fakeClient, tmpconfigfile):
    """Use a format string in a configuration variable.

    Same as above, but set the referenced variable from the command
    line.
    """

    cmdline = "cmd -c %s -s example_jdoe -u jonny -p pass" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    config.add_variable('greeting', ("--greeting",), 
                        dict(help="Greeting message"),
                        subst=True)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_jdoe",
                      url=ex_icat,
                      auth="ldap",
                      username="jonny",
                      password="pass",
                      promptPass=False,
                      greeting="Hello jonny!",
                      credentials={'username': 'jonny', 'password': 'pass'})
    assert ex <= conf


def test_config_type_int(monkeypatch, fakeClient, tmpconfigfile):
    """Read an integer variable from the configuration file.
    """

    cmdline = "cmd -c %s -s example_jdoe" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config(needlogin=False)
    config.add_variable('num', ("--num",), 
                        dict(help="Integer variable"), type=int)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_jdoe",
                      url=ex_icat,
                      num=42)
    assert ex <= conf


def test_config_type_int_err(monkeypatch, fakeClient, tmpconfigfile):
    """Read an integer variable from the configuration file.

    Same as last one, but have an invalid value this time.
    """

    cmdline = "cmd -c %s -s example_jdoe" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config(needlogin=False)
    config.add_variable('invnum', ("--invnum",), 
                        dict(help="Integer variable"), type=int)
    with pytest.raises(icat.exception.ConfigError) as err:
        _, conf = config.getconfig()
    assert 'invalid int value' in str(err.value)


@pytest.mark.parametrize(("flags", "ex"), [
    ([],
     ExpectedConf(configSection="example_jdoe",
                  url=ex_icat,
                  flag1=True,
                  flag2=False)),
    (["--flag2"],
     ExpectedConf(configSection="example_jdoe",
                  url=ex_icat,
                  flag1=True,
                  flag2=True)),
])
def test_config_type_boolean(monkeypatch, fakeClient, tmpconfigfile, flags, ex):
    """Test a boolean configuration variable.
    """
    cmdline = "cmd -c %s -s example_jdoe" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split() + flags)
    config = icat.config.Config(needlogin=False)
    config.add_variable('flag1', ("--flag1",), 
                        dict(help="Flag 1", action='store_const', const=True), 
                        type=icat.config.boolean)
    config.add_variable('flag2', ("--flag2",), 
                        dict(help="Flag 2", action='store_const', const=True), 
                        type=icat.config.boolean)
    _, conf = config.getconfig()
    assert ex <= conf


@pytest.mark.parametrize(("flags", "ex"), [
    ([],
     ExpectedConf(configSection="example_jdoe",
                  url=ex_icat,
                  flag1=True,
                  flag2=False)),
    (["--no-flag1", "--flag2"],
     ExpectedConf(configSection="example_jdoe",
                  url=ex_icat,
                  flag1=False,
                  flag2=True)),
])
def test_config_type_flag(monkeypatch, fakeClient, tmpconfigfile, flags, ex):
    """Test the special configuration variable type flag.
    """
    cmdline = "cmd -c %s -s example_jdoe" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split() + flags)
    config = icat.config.Config(needlogin=False)
    config.add_variable('flag1', ("--flag1",), 
                        dict(help="Flag 1"), type=icat.config.flag)
    config.add_variable('flag2', ("--flag2",), 
                        dict(help="Flag 2"), type=icat.config.flag)
    _, conf = config.getconfig()
    assert ex <= conf


def test_config_positional(monkeypatch, fakeClient, tmpconfigfile):
    """Test adding a positional argument on the command line.

    (There used to be a bug in adding positional arguments, fixed in
    7d10764.)
    """

    cmdline = "cmd -c %s -s example_jdoe test.dat" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    config.add_variable('datafile', ("datafile",), 
                        dict(metavar="input.dat", 
                             help="name of the input datafile"))
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_jdoe",
                      url=ex_icat,
                      auth="ldap",
                      username="jdoe",
                      password="pass",
                      promptPass=False,
                      credentials={'username': 'jdoe', 'password': 'pass'},
                      datafile="test.dat")
    assert ex <= conf


def test_config_disable(monkeypatch, fakeClient, tmpconfigfile):
    """Configuration variables may be disabled.

    Note that this feature is used internally in config and not
    intended to be used in client code.
    """

    cmdline = "cmd -c %s -s example_root" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    config.confvariable['promptPass'].disabled = True
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_root",
                      url=ex_icat,
                      auth="simple",
                      username="root",
                      password="secret",
                      credentials={'username': 'root', 'password': 'secret'})
    assert ex <= conf
    assert not hasattr(conf, 'promptPass')


def test_config_authinfo_simple(monkeypatch, fakeClient, tmpconfigfile):
    """Simple login example.

    Talking to a server that supports getAuthenticatorInfo.
    """

    userkey = Namespace(name='username')
    passkey = Namespace(name='password', hide=True)
    authInfo = [
        Namespace(mnemonic="simple", admin=True, 
                  keys=[userkey, passkey]),
        Namespace(mnemonic="db", 
                  keys=[userkey, passkey]),
        Namespace(mnemonic="anon"),
    ]
    monkeypatch.setattr(FakeClient, "AuthInfo", authInfo)

    cmdline = "cmd -c %s -s example_root" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    assert list(config.authenticatorInfo) == authInfo
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_root",
                      url=ex_icat,
                      auth="simple",
                      username="root",
                      password="secret",
                      promptPass=False,
                      credentials={'username': 'root', 'password': 'secret'})
    assert ex <= conf


def test_config_authinfo_anon(monkeypatch, fakeClient, tmpconfigfile):
    """Anon login example.

    Same as last test, but selecting the anon authenticator this time.
    """

    userkey = Namespace(name='username')
    passkey = Namespace(name='password', hide=True)
    authInfo = [
        Namespace(mnemonic="simple", admin=True, 
                  keys=[userkey, passkey]),
        Namespace(mnemonic="db", 
                  keys=[userkey, passkey]),
        Namespace(mnemonic="anon"),
    ]
    monkeypatch.setattr(FakeClient, "AuthInfo", authInfo)

    cmdline = "cmd -c %s -s example_root -a anon" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    assert list(config.authenticatorInfo) == authInfo
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_root",
                      url=ex_icat,
                      auth="anon",
                      promptPass=False,
                      credentials={})
    assert ex <= conf
    assert not hasattr(conf, 'username')


def test_config_authinfo_anon_only(monkeypatch, fakeClient, tmpconfigfile):
    """
    Talk to a server that supports getAuthenticatorInfo and has only
    the anon authenticator.
    """

    authInfo = [
        Namespace(mnemonic="anon"),
    ]
    monkeypatch.setattr(FakeClient, "AuthInfo", authInfo)

    cmdline = "cmd -c %s -s example_anon" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    assert list(config.authenticatorInfo) == authInfo
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_anon",
                      url=ex_icat,
                      auth="anon",
                      credentials={})
    assert ex <= conf
    assert not hasattr(conf, 'promptPass')
    assert not hasattr(conf, 'username')


def test_config_authinfo_strange(monkeypatch, fakeClient, tmpconfigfile):
    """
    Talk to a server that requests strange credential keys.  Note the
    prefix "cred_" in the name of configuration variable and the
    command line option.
    """

    secretkey = Namespace(name='secret', hide=True)
    authInfo = [
        Namespace(mnemonic="quirks", 
                  keys=[secretkey]),
    ]
    monkeypatch.setattr(FakeClient, "AuthInfo", authInfo)

    cmdline = ("cmd -c %s -s example_quirks --cred_secret geheim"
               % tmpconfigfile.path)
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    assert list(config.authenticatorInfo) == authInfo
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_quirks",
                      url=ex_icat,
                      auth="quirks",
                      promptPass=False,
                      cred_secret="geheim",
                      credentials={'secret': 'geheim'})
    assert ex <= conf
    assert not hasattr(conf, 'username')


def test_config_authinfo_strange_preset(monkeypatch, fakeClient, tmpconfigfile):
    """Talk to a server that requests strange credential keys.

    Almost the same as test_config_authinfo_strange(), but set the
    configuration as preset variables rather than faking the
    comandline arguments.

    The `preset` keyword argument to `Config()` was added in response
    to the feature request Issue #77.  One major use case for
    requesting that feature was related to custom authenticators.
    """

    secretkey = Namespace(name='secret', hide=True)
    authInfo = [
        Namespace(mnemonic="quirks",
                  keys=[secretkey]),
    ]
    monkeypatch.setattr(FakeClient, "AuthInfo", authInfo)

    preset = {"configFile": str(tmpconfigfile.path),
              "configSection": "example_quirks",
              "cred_secret": "geheim",}
    monkeypatch.setattr(sys, "argv", ["cmd"])
    config = icat.config.Config(preset=preset)
    assert list(config.authenticatorInfo) == authInfo
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_quirks",
                      url=ex_icat,
                      auth="quirks",
                      promptPass=False,
                      cred_secret="geheim",
                      credentials={'secret': 'geheim'})
    assert ex <= conf
    assert not hasattr(conf, 'username')


def test_config_authinfo_no_authinfo(monkeypatch, fakeClient, tmpconfigfile):
    """
    Talk to an old server that does not support getAuthenticatorInfo.
    """

    cmdline = "cmd -c %s -s example_root" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    client, conf = config.getconfig()

    with pytest.raises(icat.exception.VersionMethodError) as err:
        authInfo = client.getAuthenticatorInfo()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_root",
                      url=ex_icat,
                      auth="simple",
                      username="root",
                      password="secret",
                      promptPass=False,
                      credentials={'username': 'root', 'password': 'secret'})
    assert ex <= conf


def test_config_authinfo_invalid_auth(monkeypatch, fakeClient, tmpconfigfile):
    """
    Try to use an invalid authenticator.

    Issue #41: AttributeError is raised during internal error handling.
    """

    userkey = Namespace(name='username')
    passkey = Namespace(name='password', hide=True)
    authInfo = [
        Namespace(mnemonic="simple", admin=True, 
                  keys=[userkey, passkey]),
        Namespace(mnemonic="db", 
                  keys=[userkey, passkey]),
        Namespace(mnemonic="anon"),
    ]
    monkeypatch.setattr(FakeClient, "AuthInfo", authInfo)

    cmdline = "cmd -c %s -s example_jdoe" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    with pytest.raises(icat.exception.ConfigError) as err:
        _, conf = config.getconfig()
    assert "No such authenticator 'ldap'" in str(err.value)


def test_config_cfgpath_default(monkeypatch, fakeClient, tmpconfigfile,
                                tmpfiles):
    """Test a cfgpath configuration variable.

    This searches a file in the default configuration directories.
    Feature added in Issue #30.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", str(tmpconfigfile.home))
    cfgdirs = [ Path("~/.config/icat").expanduser(),
                Path("~/.icat").expanduser(),
                Path("."), ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.home))
    cpath = Path("~/.config/icat/control.dat").expanduser()
    tmpfiles.addfile(cpath, "control\n")

    cmdline = "cmd -c %s -s example_jdoe" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    config.add_variable('controlfile', ("--control",), 
                    dict(metavar="control.dat", help="control file"), 
                    default="control.dat", type=icat.config.cfgpath)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_jdoe",
                      url=ex_icat,
                      auth="ldap",
                      username="jdoe",
                      password="pass",
                      promptPass=False,
                      credentials={'username': 'jdoe', 'password': 'pass'},
                      controlfile=cpath)
    assert ex <= conf
    assert conf.controlfile.is_file()


def test_config_cfgpath_cwd(monkeypatch, fakeClient, tmpconfigfile, tmpfiles):
    """Test a cfgpath configuration variable.

    Same as test_config_cfgpath_default() but a file in the current
    working directory takes precedence of the one in the configuration
    directory.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", str(tmpconfigfile.home))
    cfgdirs = [ Path("~/.config/icat").expanduser(),
                Path("~/.icat").expanduser(),
                Path("."), ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.home))
    cpath = Path("~/.config/icat/control.dat").expanduser()
    tmpfiles.addfile(cpath, "control config dir\n")
    hpath = tmpconfigfile.home / "control.dat"
    tmpfiles.addfile(hpath, "control home\n")

    cmdline = "cmd -c %s -s example_jdoe" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    config.add_variable('controlfile', ("--control",), 
                    dict(metavar="control.dat", help="control file"), 
                    default="control.dat", type=icat.config.cfgpath)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_jdoe",
                      url=ex_icat,
                      auth="ldap",
                      username="jdoe",
                      password="pass",
                      promptPass=False,
                      credentials={'username': 'jdoe', 'password': 'pass'},
                      controlfile=hpath)
    assert ex <= conf
    assert conf.controlfile.is_file()


@pytest.mark.parametrize('abspath', [True, False])
def test_config_cfgpath_cmdline(monkeypatch, fakeClient, tmpconfigfile,
                                tmpfiles, abspath):
    """Test a cfgpath configuration variable.

    Same as test_config_cfgpath_cwd() but override the path on the
    command line.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", str(tmpconfigfile.home))
    cfgdirs = [ Path("~/.config/icat").expanduser(),
                Path("~/.icat").expanduser(),
                Path("."), ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.home))
    cpath = Path("~/.config/icat/control.dat").expanduser()
    tmpfiles.addfile(cpath, "control config dir\n")
    hpath = tmpconfigfile.home / "control.dat"
    tmpfiles.addfile(hpath, "control home\n")
    if abspath:
        apath = Path("~/custom/cl.dat").expanduser()
        cfarg = str(apath)
    else:
        apath = Path("~/.config/icat/cl.dat").expanduser()
        cfarg = "cl.dat"
    tmpfiles.addfile(apath, "control cmdline\n")

    cmdline = ("cmd -c %s -s example_jdoe --control %s"
               % (tmpconfigfile.path, cfarg))
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    config.add_variable('controlfile', ("--control",), 
                    dict(metavar="control.dat", help="control file"), 
                    default="control.dat", type=icat.config.cfgpath)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_jdoe",
                      url=ex_icat,
                      auth="ldap",
                      username="jdoe",
                      password="pass",
                      promptPass=False,
                      credentials={'username': 'jdoe', 'password': 'pass'},
                      controlfile=apath)
    assert ex <= conf
    assert conf.controlfile.is_file()


def test_config_client_kwargs(monkeypatch, fakeClient, tmpconfigfile):
    """Test client_kwargs attribute of config.

    Issue #38: There should be a way to access the kwargs used to
    create the client in config.  The resolution was to add this
    attribute to the config object.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", str(tmpconfigfile.home))
    cfgdirs = [ Path("~/.config/icat").expanduser(),
                Path("~/.icat").expanduser(),
                Path("."), ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.home))

    # Add proxy settings just to have non-trivial content in client_kwargs.
    monkeypatch.setenv("http_proxy", "http://www-cache.example.org:3128/")
    monkeypatch.setenv("https_proxy", "http://www-cache.example.org:3128/")
    monkeypatch.setenv("no_proxy", "localhost, .example.org")

    cmdline = "cmd -c %s -s example_root" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    client, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_root",
                      url=ex_icat,
                      idsurl=ex_ids,
                      http_proxy="http://www-cache.example.org:3128/",
                      https_proxy="http://www-cache.example.org:3128/",
                      no_proxy="localhost, .example.org",
                      auth="simple",
                      username="root",
                      password="secret",
                      promptPass=False,
                      credentials={'username': 'root', 'password': 'secret'})
    assert ex <= conf
    # create a second, independent client object and check that it
    # has been created using the same arguments.
    client2 = FakeClient(conf.url, **config.client_kwargs)
    assert client2 == client


@pytest.mark.parametrize('subcmd', ["create", "ls", "info"])
def test_config_subcmd(monkeypatch, fakeClient, tmpconfigfile, subcmd):
    """Test sub-commands.

    Issue #59: Add support for sub-commands in config.
    """

    def create_cmd(conf):
        ex = ExpectedConf(configFile=[tmpconfigfile.path],
                          configSection="example_jdoe",
                          url=ex_icat,
                          auth="ldap",
                          username="jdoe",
                          password="pass",
                          promptPass=False,
                          credentials={'username': 'jdoe', 'password': 'pass'},
                          name="energy",
                          units="J",
                          description=None)
        assert ex <= conf

    def ls_cmd(conf):
        ex = ExpectedConf(configFile=[tmpconfigfile.path],
                          configSection="example_jdoe",
                          url=ex_icat,
                          auth="ldap",
                          username="jdoe",
                          password="pass",
                          promptPass=False,
                          credentials={'username': 'jdoe', 'password': 'pass'},
                          format="long")
        assert ex <= conf

    def info_cmd(conf):
        ex = ExpectedConf(configFile=[tmpconfigfile.path],
                          configSection="example_jdoe",
                          url=ex_icat,
                          auth="ldap",
                          username="jdoe",
                          password="pass",
                          promptPass=False,
                          credentials={'username': 'jdoe', 'password': 'pass'},
                          name="brightness")
        assert ex <= conf

    sub_args = {
        "create": ["create", "--name", "energy", "--units", "J"],
        "ls": ["ls", "--format", "long"],
        "info": ["info", "--name", "brightness", ],
    }
    cmdline = "cmd -c %s -s example_jdoe" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split() + sub_args[subcmd])
    config = icat.config.Config()
    subcmds = config.add_subcommands()

    create_config = subcmds.add_subconfig('create', dict(help="create a foo"),
                                          func=create_cmd)
    create_config.add_variable('name', ("--name",),
                               dict(help="name"))
    create_config.add_variable('units', ("--units",),
                               dict(help="units (unit full name)"))
    create_config.add_variable('description', ("--description",),
                               dict(help="description"), optional=True)

    ls_config = subcmds.add_subconfig('ls', dict(help="list foos"),
                                      func=ls_cmd)
    ls_config.add_variable('format', ("--format",),
                           dict(help="format", choices=["long", "short"]))

    info_config = subcmds.add_subconfig('info', dict(help="show info"),
                                        func=info_cmd)
    info_config.add_variable('name', ("--name",),
                             dict(help="name"))

    _, conf = config.getconfig()
    conf.subcmd.func(conf)
    assert conf.subcmd.name == subcmd


def test_config_subcmd_err_var_nonunique(monkeypatch, fakeClient,
                                         tmpconfigfile):
    """Test sub-commands.

    Issue #59: Add support for sub-commands in config.

    The variable names must be unique, e.g. variables defined in the
    sub-configuration must not collide with already defined variables
    in the main configuration.  (Note that it's ok if two sub-
    configurations define the same variables, see for instance "name"
    which is defined in both "create" and "info" in the last test.)
    """
    cmdline = ("cmd -c %s -s example_jdoe sub --url http://example.org/"
               % tmpconfigfile.path)
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    subcmds = config.add_subcommands()
    subconfig = subcmds.add_subconfig('sub')
    with pytest.raises(ValueError) as err:
        subconfig.add_variable('url', ("--url",), dict(help="url"))
    assert "variable 'url' is already defined" in str(err.value)


def test_config_subcmd_err_subcmd_nonunique(monkeypatch, fakeClient,
                                            tmpconfigfile):
    """Test sub-commands.

    Issue #59: Add support for sub-commands in config.

    Similar situation as last test: sub-command names may not collide
    with already defined variables as well.
    """
    cmdline = "cmd -c %s -s example_jdoe url" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    with pytest.raises(ValueError) as err:
        subcmds = config.add_subcommands('url')
    assert "variable 'url' is already defined" in str(err.value)


def test_config_subcmd_err_add_more_vars(monkeypatch, fakeClient,
                                         tmpconfigfile):
    """Test sub-commands.

    Issue #59: Add support for sub-commands in config.

    No more variables may be added to a config after a subcommand has
    been added.
    """
    cmdline = "cmd -c %s -s example_jdoe sub --name foo" % tmpconfigfile.path
    monkeypatch.setattr(sys, "argv", cmdline.split())
    config = icat.config.Config()
    subcmds = config.add_subcommands()
    subconfig = subcmds.add_subconfig('sub')
    with pytest.raises(RuntimeError) as err:
        config.add_variable('name', ("--name",), dict(help="name"))
    assert "config already has subcommands" in str(err.value)


def test_deprecated_config_defaultsection(monkeypatch, fakeClient,
                                          tmpconfigfile):
    """The module variable icat.config.defaultsection is deprecated since
    1.0.0.

    Setting it should raise a DeprecationWarning.
    """

    # Use the same setting as test_config_minimal_file(), but don't
    # set the configSection via a command line argument, but by
    # setting defaultsection.  Note that setting the variable cannot
    # easily be detected, the DeprecationWarning is raised during
    # icat.config.Config() later on.
    cfgdirs = [ tmpconfigfile.dir / "wobble", Path(".") ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(str(tmpconfigfile.dir))

    monkeypatch.setattr(icat.config, "defaultsection", "example_root")
    monkeypatch.setattr(sys, "argv", ["cmd"])
    with pytest.deprecated_call():
        config = icat.config.Config(needlogin=False, ids=False, args=())
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[Path("icat.cfg")],
                      configSection="example_root",
                      url=ex_icat)
    assert ex <= conf
