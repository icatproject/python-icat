"""Test module icat.config
"""

import os
import os.path
import getpass
import pytest
import icat.config
import icat.exception


# ============================= helper =============================

# The icat.config.Config constructor already creates and initializes
# an ICAT client.  Prevent this, as we don't want to connect to a real
# server in this test module.  Foist a fake client class on the
# icat.config module.  Note that we must monkeypatch icat.config
# rather then icat.client, as the former already imported the Client
# class at this point.

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
        self.dir = os.path.join(self.home, ".icat")
        self.path = os.path.join(self.dir, "icat.cfg")
        os.mkdir(self.dir)
        with open(self.path, "w") as f:
            f.write(content)

class TmpFiles():
    def __init__(self):
        self.files = []
    def cleanup(self):
        for p in self.files:
            os.unlink(p)
    def addfile(self, path, content):
        path = os.path.abspath(path)
        try:
            os.makedirs(os.path.dirname(path))
        except OSError:
            pass
        with open(path, "wt") as f:
            f.write(content)
        self.files.append(path)

@pytest.fixture(scope="module")
def tmpconfigfile(tmpdirsec):
    return ConfigFile(tmpdirsec, configfilestr)

@pytest.fixture(scope="function")
def tmpfiles():
    files = TmpFiles()
    yield files
    files.cleanup()

# ============================= tests ==============================

def test_config_missing_mandatory(fakeClient):
    """Not providing any config at all.

    This throws an error as url is mandatory.
    """
    config = icat.config.Config(needlogin=False, ids=False, args=[])
    with pytest.raises(icat.exception.ConfigError) as err:
        _, conf = config.getconfig()
    assert "Config option 'url' not given" in str(err.value)


def test_config_minimal(fakeClient):
    """Minimal example.

    No login credentials, only relevant config option is the url which
    is provided as command line argument.
    """

    args = ["-w", ex_icat]
    config = icat.config.Config(needlogin=False, ids=False, args=args)
    _, conf = config.getconfig()

    assert ExpectedConf(configSection=None, url=ex_icat) <= conf


def test_config_minimal_file(fakeClient, tmpconfigfile, monkeypatch):
    """Minimal example.

    Almost the same as test_config_minimal(), but read the url from
    a config file this time.
    """

    # Let the config file be found in the default location, but
    # manipulate the search path such that only the cwd exists.
    cfgdirs = [ os.path.join(tmpconfigfile.dir, "wobble"), "" ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(tmpconfigfile.dir)

    args = ["-s", "example_root"]
    config = icat.config.Config(needlogin=False, ids=False, args=args)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=["icat.cfg"],
                      configSection="example_root", 
                      url=ex_icat)
    assert ex <= conf


def test_config_minimal_defaultfile(fakeClient, tmpconfigfile, monkeypatch):
    """Minimal example.

    Almost the same as test_config_minimal_file(), but let the
    configuration file be found in the default search path rather then
    pointing to the full path.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", tmpconfigfile.home)
    cfgdirs = [ os.path.expanduser("~/.config/icat"), 
                os.path.expanduser("~/.icat"), 
                "", ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(tmpconfigfile.home)

    args = ["-s", "example_root"]
    config = icat.config.Config(needlogin=False, ids=False, args=args)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path], 
                      configSection="example_root", 
                      url=ex_icat)
    assert ex <= conf


def test_config_no_defaultvars(tmpconfigfile, monkeypatch):
    """Config object with no default variables.

    If `defaultvars=False` is passed to the constructor of Config, no
    default configuration variables will be defined other then
    `configFile` and `configSection`.  The configuration mechanism is
    still intact.  In particular, custom configuration variables may
    be defined and reading the configuration file still works.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", tmpconfigfile.home)
    cfgdirs = [ os.path.expanduser("~/.config/icat"), 
                os.path.expanduser("~/.icat"), 
                "", ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(tmpconfigfile.home)

    args = ["-s", "example_root"]
    config = icat.config.Config(defaultvars=False, args=args)
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


def test_config_simple_login(fakeClient, tmpconfigfile):
    """Simple login example.

    Standard usage, read everything from a config file.
    """

    args = ["-c", tmpconfigfile.path, "-s", "example_root"]
    _, conf = icat.config.Config(args=args).getconfig()

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


def test_config_override(fakeClient, tmpconfigfile):
    """
    Read some stuff from a config file, override some other options
    with command line arguments.
    """

    args = ["-c", tmpconfigfile.path, "-s", "example_root", 
            "-a", "db", "-u", "rbeck", "-p", "geheim"]
    _, conf = icat.config.Config(args=args).getconfig()

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


def test_config_askpass(fakeClient, tmpconfigfile, monkeypatch):
    """
    Same as test_config_override(), but do not pass the password in
    the command line arguments.  In this case, getconfig() should
    prompt for the password.
    """

    def mockgetpass(prompt='Password: '):
        return "mockpass"
    monkeypatch.setattr(getpass, "getpass", mockgetpass)

    args = ["-c", tmpconfigfile.path, "-s", "example_root", 
            "-a", "db", "-u", "rbeck"]
    _, conf = icat.config.Config(args=args).getconfig()

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


def test_config_nopass_askpass(fakeClient, tmpconfigfile, monkeypatch):
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

    args = ["-c", tmpconfigfile.path, "-s", "example_nbour", "-P"]
    _, conf = icat.config.Config(args=args).getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_nbour",
                      url=ex_icat,
                      auth="ldap",
                      username="nbour",
                      password="mockpass",
                      promptPass=True,
                      credentials={'username': 'nbour', 'password': 'mockpass'})
    assert ex <= conf


def test_config_askpass_file(fakeClient, tmpconfigfile, monkeypatch):
    """
    Set promptPass in the configuration file.  This should force
    prompting for the password.  Issue #21.
    """

    def mockgetpass(prompt='Password: '):
        return "mockpass"
    monkeypatch.setattr(getpass, "getpass", mockgetpass)

    args = ["-c", tmpconfigfile.path, "-s", "test21"]
    _, conf = icat.config.Config(args=args).getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="test21",
                      url=ex_icat,
                      auth="simple",
                      username="root",
                      password="mockpass",
                      promptPass=True,
                      credentials={'username': 'root', 'password': 'mockpass'})
    assert ex <= conf


def test_config_environment(fakeClient, tmpconfigfile, monkeypatch):
    """Set some config variables from the environment.
    """

    monkeypatch.setenv("ICAT_CFG", tmpconfigfile.path)
    monkeypatch.setenv("ICAT_AUTH", "db")
    monkeypatch.setenv("http_proxy", "http://www-cache.example.org:3128/")
    monkeypatch.setenv("https_proxy", "http://www-cache.example.org:3128/")
    monkeypatch.setenv("no_proxy", "localhost, .example.org")

    args = ["-s", "example_root", "-u", "rbeck", "-p", "geheim"]
    _, conf = icat.config.Config(args=args).getconfig()

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
def test_config_ids(fakeClient, tmpconfigfile, section, ex):
    """Simple login example.

    Ask for the idsurl configuration variable.
    """
    # We set ids="optional", the idsurl is present in section
    # example_root, but not in example_jdoe.  In the latter case, the
    # configuration variable is present, but set to None..
    args = ["-c", tmpconfigfile.path, "-s", section]
    _, conf = icat.config.Config(ids="optional", args=args).getconfig()
    assert ex <= conf


def test_config_custom_var(fakeClient, tmpconfigfile):
    """Define custom configuration variables.
    """

    # Note that ldap_filter is not defined in the configuration file,
    # but we have a default value defined here, so this is ok.
    args = ["-c", tmpconfigfile.path, "-s", "example_root"]
    config = icat.config.Config(args=args)
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


def test_config_subst_nosubst(fakeClient, tmpconfigfile):
    """Use a format string in a configuration variable.

    But disable the substitution.
    """

    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe"]
    config = icat.config.Config(args=args)
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


def test_config_subst(fakeClient, tmpconfigfile):
    """Use a format string in a configuration variable.

    Same as above, but enable the substitution this time.
    """

    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe"]
    config = icat.config.Config(args=args)
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


def test_config_subst_cmdline(fakeClient, tmpconfigfile):
    """Use a format string in a configuration variable.

    Same as above, but set the referenced variable from the command
    line.
    """

    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe", 
            "-u", "jonny", "-p", "pass"]
    config = icat.config.Config(args=args)
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


def test_config_type_int(fakeClient, tmpconfigfile):
    """Read an integer variable from the configuration file.
    """

    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe"]
    config = icat.config.Config(needlogin=False, args=args)
    config.add_variable('num', ("--num",), 
                        dict(help="Integer variable"), type=int)
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_jdoe",
                      url=ex_icat,
                      num=42)
    assert ex <= conf


def test_config_type_int_err(fakeClient, tmpconfigfile):
    """Read an integer variable from the configuration file.

    Same as last one, but have an invalid value this time.
    """

    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe"]
    config = icat.config.Config(needlogin=False, args=args)
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
def test_config_type_boolean(fakeClient, tmpconfigfile, flags, ex):
    """Test a boolean configuration variable.
    """
    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe"] + flags
    config = icat.config.Config(needlogin=False, args=args)
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
def test_config_type_flag(fakeClient, tmpconfigfile, flags, ex):
    """Test the special configuration variable type flag.
    """
    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe"] + flags
    config = icat.config.Config(needlogin=False, args=args)
    config.add_variable('flag1', ("--flag1",), 
                        dict(help="Flag 1"), type=icat.config.flag)
    config.add_variable('flag2', ("--flag2",), 
                        dict(help="Flag 2"), type=icat.config.flag)
    _, conf = config.getconfig()
    assert ex <= conf


def test_config_positional(fakeClient, tmpconfigfile):
    """Test adding a positional argument on the command line.

    (There used to be a bug in adding positional arguments, fixed in
    7d10764.)
    """

    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe", "test.dat"]
    config = icat.config.Config(args=args)
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


def test_config_disable(fakeClient, tmpconfigfile):
    """Configuration variables may be disabled.

    Note that this feature is used internally in config and not
    intended to be used in client code.
    """

    args = ["-c", tmpconfigfile.path, "-s", "example_root"]
    config = icat.config.Config(args=args)
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


def test_config_authinfo_simple(fakeClient, monkeypatch, tmpconfigfile):
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

    args = ["-c", tmpconfigfile.path, "-s", "example_root"]
    config = icat.config.Config(args=args)
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


def test_config_authinfo_anon(fakeClient, monkeypatch, tmpconfigfile):
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

    args = ["-c", tmpconfigfile.path, "-s", "example_root", "-a", "anon"]
    config = icat.config.Config(args=args)
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


def test_config_authinfo_anon_only(fakeClient, monkeypatch, tmpconfigfile):
    """
    Talk to a server that supports getAuthenticatorInfo and has only
    the anon authenticator.
    """

    authInfo = [
        Namespace(mnemonic="anon"),
    ]
    monkeypatch.setattr(FakeClient, "AuthInfo", authInfo)

    args = ["-c", tmpconfigfile.path, "-s", "example_anon"]
    config = icat.config.Config(args=args)
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


def test_config_authinfo_strange(fakeClient, monkeypatch, tmpconfigfile):
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

    args = ["-c", tmpconfigfile.path, "-s", "example_root", 
            "-a", "quirks", "--cred_secret", "geheim"]
    config = icat.config.Config(args=args)
    assert list(config.authenticatorInfo) == authInfo
    _, conf = config.getconfig()

    ex = ExpectedConf(configFile=[tmpconfigfile.path],
                      configSection="example_root",
                      url=ex_icat,
                      auth="quirks",
                      promptPass=False,
                      cred_secret="geheim",
                      credentials={'secret': 'geheim'})
    assert ex <= conf
    assert not hasattr(conf, 'username')


def test_config_authinfo_no_authinfo(fakeClient, monkeypatch, tmpconfigfile):
    """
    Talk to an old server that does not support getAuthenticatorInfo.
    """

    args = ["-c", tmpconfigfile.path, "-s", "example_root"]
    config = icat.config.Config(args=args)
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


def test_config_authinfo_invalid_auth(fakeClient, monkeypatch, tmpconfigfile):
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

    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe"]
    config = icat.config.Config(args=args)
    with pytest.raises(icat.exception.ConfigError) as err:
        _, conf = config.getconfig()
    assert "No such authenticator 'ldap'" in str(err.value)


def test_config_cfgpath_default(fakeClient, tmpconfigfile, monkeypatch, 
                                tmpfiles):
    """Test a cfgpath configuration variable.

    This searches a file in the default configuration directories.
    Feature added in Issue #30.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", tmpconfigfile.home)
    cfgdirs = [ os.path.expanduser("~/.config/icat"), 
                os.path.expanduser("~/.icat"), 
                "", ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(tmpconfigfile.home)
    cpath = os.path.expanduser("~/.config/icat/control.dat")
    tmpfiles.addfile(cpath, "control\n")

    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe"]
    config = icat.config.Config(args=args)
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
    assert os.path.isfile(conf.controlfile)


def test_config_cfgpath_cwd(fakeClient, tmpconfigfile, monkeypatch, tmpfiles):
    """Test a cfgpath configuration variable.

    Same as test_config_cfgpath_default() but a file in the current
    working directory takes precedence of the one in the configuration
    directory.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", tmpconfigfile.home)
    cfgdirs = [ os.path.expanduser("~/.config/icat"), 
                os.path.expanduser("~/.icat"), 
                "", ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(tmpconfigfile.home)
    cpath = os.path.expanduser("~/.config/icat/control.dat")
    tmpfiles.addfile(cpath, "control config dir\n")
    hpath = os.path.join(tmpconfigfile.home, "control.dat")
    tmpfiles.addfile(hpath, "control home\n")

    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe"]
    config = icat.config.Config(args=args)
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
    assert os.path.isfile(conf.controlfile)


@pytest.mark.parametrize('abspath', [True, False])
def test_config_cfgpath_cmdline(fakeClient, tmpconfigfile, monkeypatch, 
                                tmpfiles, abspath):
    """Test a cfgpath configuration variable.

    Same as test_config_cfgpath_cwd() but override the path on the
    command line.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", tmpconfigfile.home)
    cfgdirs = [ os.path.expanduser("~/.config/icat"), 
                os.path.expanduser("~/.icat"), 
                "", ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(tmpconfigfile.home)
    cpath = os.path.expanduser("~/.config/icat/control.dat")
    tmpfiles.addfile(cpath, "control config dir\n")
    hpath = os.path.join(tmpconfigfile.home, "control.dat")
    tmpfiles.addfile(hpath, "control home\n")
    if abspath:
        apath = os.path.expanduser("~/custom/cl.dat")
        cfarg = apath
    else:
        apath = os.path.expanduser("~/.config/icat/cl.dat")
        cfarg = "cl.dat"
    tmpfiles.addfile(apath, "control cmdline\n")

    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe", 
            "--control", cfarg]
    config = icat.config.Config(args=args)
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
    assert os.path.isfile(conf.controlfile)


def test_config_client_kwargs(fakeClient, tmpconfigfile, monkeypatch):
    """Test client_kwargs attribute of config.

    Issue #38: There should be a way to access the kwargs used to
    create the client in config.  The resolution was to add this
    attribute to the config object.
    """

    # Manipulate the default search path.
    monkeypatch.setenv("HOME", tmpconfigfile.home)
    cfgdirs = [ os.path.expanduser("~/.config/icat"), 
                os.path.expanduser("~/.icat"), 
                "", ]
    monkeypatch.setattr(icat.config, "cfgdirs", cfgdirs)
    monkeypatch.chdir(tmpconfigfile.home)

    # Add proxy settings just to have non-trivial content in client_kwargs.
    monkeypatch.setenv("http_proxy", "http://www-cache.example.org:3128/")
    monkeypatch.setenv("https_proxy", "http://www-cache.example.org:3128/")
    monkeypatch.setenv("no_proxy", "localhost, .example.org")

    args = ["-c", tmpconfigfile.path, "-s", "example_root"]
    config = icat.config.Config(args=args)
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
def test_config_subcmd(fakeClient, tmpconfigfile, subcmd):
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
    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe"] + sub_args[subcmd]
    config = icat.config.Config(args=args)
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


def test_config_subcmd_err_var_nonunique(fakeClient, tmpconfigfile):
    """Test sub-commands.

    Issue #59: Add support for sub-commands in config.

    The variable names must be unique, e.g. variables defined in the
    sub-configuration must not collide with already defined variables
    in the main configuration.  (Note that it's ok if two sub-
    configurations define the same variables, see for instance "name"
    which is defined in both "create" and "info" in the last test.)
    """
    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe",
            "sub", "--url", "http://example.org/"]
    config = icat.config.Config(args=args)
    subcmds = config.add_subcommands()
    subconfig = subcmds.add_subconfig('sub')
    with pytest.raises(ValueError) as err:
        subconfig.add_variable('url', ("--url",), dict(help="url"))
    assert "variable 'url' is already defined" in str(err.value)


def test_config_subcmd_err_subcmd_nonunique(fakeClient, tmpconfigfile):
    """Test sub-commands.

    Issue #59: Add support for sub-commands in config.

    Similar situation as last test: sub-command names may not collide
    with already defined variables as well.
    """
    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe", "url"]
    config = icat.config.Config(args=args)
    with pytest.raises(ValueError) as err:
        subcmds = config.add_subcommands('url')
    assert "variable 'url' is already defined" in str(err.value)


def test_config_subcmd_err_add_more_vars(fakeClient, tmpconfigfile):
    """Test sub-commands.

    Issue #59: Add support for sub-commands in config.

    No more variables may be added to a config after a subcommand has
    been added.
    """
    args = ["-c", tmpconfigfile.path, "-s", "example_jdoe",
            "sub", "--name", "foo"]
    config = icat.config.Config(args=args)
    subcmds = config.add_subcommands()
    subconfig = subcmds.add_subconfig('sub')
    with pytest.raises(RuntimeError) as err:
        config.add_variable('name', ("--name",), dict(help="name"))
    assert "config already has subcommands" in str(err.value)
