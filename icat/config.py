"""Provide the Config class.
"""

import argparse
import getpass
import os
import ConfigParser

basedir = os.path.expanduser("~/.icat")
filename = "icat.cfg"
defaultsection = None

class ConfigError(Exception):
    """Error getting configuration options from files or command line."""
    pass


class ConfigField(object):
    """Describe a configuration variable.
    """
    def __init__(self, name, envvar, optional, default):
        self.name = name
        self.envvar = envvar
        self.optional = optional
        self.default = default


class ConfigSource(object):
    """A configuration source.

    This is the base class for all configuration sources, such as
    command line arguments, configuration files, and environment
    variables.
    """
    def get(self, field):
        raise NotImplementedError


class ConfigSourceCmdArgs(ConfigSource):
    """Get configuration from command line arguments.
    """
    def __init__(self, argumentparser):
        super(ConfigSourceCmdArgs, self).__init__()
        self.argparser = argumentparser

    def get(self, field):
        return getattr(self.argparser, field.name, None)


class ConfigSourceEnvironment(ConfigSource):
    """Get configuration from environment variables.
    """
    def get(self, field):
        if field.envvar:
            return os.environ.get(field.envvar, None)
        else:
            return None


class ConfigSourceFile(ConfigSource):
    """Get configuration from a configuration file.
    """
    def __init__(self, configparser, defaultFiles):
        super(ConfigSourceFile, self).__init__()
        self.confparser = configparser
        self.defaultFiles = defaultFiles
        self.section = None

    def read(self, filename):
        if filename:
            readfile = self.confparser.read(filename)
            if not readfile:
                raise ConfigError("Could not read config file '%s'." % filename)
        elif filename is None:
            readfile = self.confparser.read(self.defaultFiles)
        else:
            readfile = filename
        return readfile

    def setsection(self, section):
        if section and not self.confparser.has_section(section):
            raise ConfigError("Could not read config section '%s'." % section)
        self.section = section
        return section

    def get(self, field):
        value = None
        if self.section:
            try:
                value = self.confparser.get(self.section, field.name)
            except ConfigParser.NoOptionError:
                pass
        return value


class ConfigSourceDefault(ConfigSource):
    """Handle the case that some field is not set from any source.
    """
    def get(self, field):
        value = field.default
        if value is None and not field.optional:
            raise ConfigError("Config option '%s' not given." % field.name)
        return value


class Config(object):
    """Parse command line arguments and read a configuration file.

    Setup an argument parser for the common set of configuration
    arguments that a ICAT client typically needs: the url of the ICAT
    service, the name of the authentication plugin, the username, and
    password.  Read a configuration file and get the configuration
    variables not found in the command line.
    """

    def __init__(self, needlogin=True):
        super(Config, self).__init__()
        self.defaultFiles = [os.path.join(basedir, filename), filename]
        self.needlogin = needlogin
        self.conffields = []

        self.argparser = argparse.ArgumentParser()
        self.add_field('configFile', ("-c", "--configfile"), 
                       dict(help="config file"),
                       envvar='ICAT_CFG', optional=True)
        self.add_field('configSection', ("-s", "--configsection"), 
                       dict(help="section in the config file", 
                            metavar='SECTION'), 
                       envvar='ICAT_CFG_SECTION', optional=True, 
                       default=defaultsection)
        self.add_field('url', ("-w", "--url"), 
                       dict(help="URL to the web service description"),
                       envvar='ICAT_SERVICE')
        self.add_field('http_proxy', ("--http-proxy",), 
                       dict(help="proxy to use for http requests"),
                       envvar='http_proxy', optional=True)
        self.add_field('https_proxy', ("--https-proxy",), 
                       dict(help="proxy to use for https requests"),
                       envvar='https_proxy', optional=True)
        if self.needlogin:
            self.add_field('auth', ("-a", "--auth"), 
                           dict(help="authentication plugin"),
                           envvar='ICAT_AUTH')
            self.add_field('username', ("-u", "--user"), dict(help="username"),
                           envvar='ICAT_USER')
            self.add_field('password', ("-p", "--pass"), dict(help="password"), 
                           optional=True)
            self.add_field('promptPass', ("-P", "--prompt-pass"), 
                           dict(help="prompt for the password", 
                                action='store_true'), 
                           optional=True)
        self.args = None

    def add_field(self, name, arg_opts=(), arg_kws=dict(), 
                   envvar=None, optional=False, default=None):
        if hasattr(self, name):
            raise ValueError("Config field name '%s' is reserved." % name)
        if arg_opts:
            prefix = self.argparser.prefix_chars
            if len(arg_opts) == 1 and arg_opts[0][0] not in prefix:
                # positional argument
                if arg_opts[0] != name:
                    raise ValueError("Config field name '%s' must be equal to "
                                     "argument name for positional argument." % 
                                     name)
            else:
                # optional argument
                arg_kws['dest'] = name
            self.argparser.add_argument(*arg_opts, **arg_kws)
        self.conffields.append(ConfigField(name, envvar, optional, default))

    def parse_args(self):
        self.args = self.argparser.parse_args()
        return self.args

    def getconfig(self):

        if self.args is None:
            self.parse_args()
        args = ConfigSourceCmdArgs(self.args)
        environ = ConfigSourceEnvironment()
        config = ConfigSourceFile(ConfigParser.ConfigParser(), 
                                  self.defaultFiles)
        defaults = ConfigSourceDefault()

        # this code relies on the fact, that the first two fields in
        # self.conffields are 'configFile' and 'configSection' in that
        # order.

        for field in self.conffields:

            for source in [ args, environ, config, defaults ]:
                value = source.get(field)
                if value is not None: 
                    break

            setattr(self, field.name, value)

            if field.name == 'configFile':
                self.configFile = config.read(self.configFile)

            elif field.name == 'configSection':
                config.setsection(self.configSection)

        if self.needlogin:
            # special rule: if the username was given in the command
            # line and password not, this always implies promptPass.
            if ((args.argparser.username and not args.argparser.password) 
                or not self.password):
                self.promptPass = True
            if self.promptPass:
                self.password = getpass.getpass()
            self.credentials = { 'username':self.username, 
                                 'password':self.password }

        self.client_kwargs = {}
        if self.http_proxy or self.https_proxy:
            proxy={}
            if self.http_proxy:
                proxy['http'] = self.http_proxy
            if self.https_proxy:
                proxy['https'] = self.https_proxy
            self.client_kwargs['proxy'] = proxy

    def __str__(self):
        typename = type(self).__name__
        arg_strings = []
        for field in self.conffields:
            arg_strings.append('%s=%r' % (field.name, getattr(self, field.name)))
        if self.needlogin:
            arg_strings.append('%s=%r' % ('credentials', self.credentials))
        arg_strings.append('%s=%r' % ('client_kwargs', self.client_kwargs))
        return '%s(%s)' % (typename, ', '.join(arg_strings))
