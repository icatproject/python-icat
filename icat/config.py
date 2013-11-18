"""Provide the Config class.
"""

import os
import getpass
import argparse
import ConfigParser
from icat.exception import *

__all__ = ['Configuration', 'Config']


basedir = os.path.expanduser("~/.icat")
filename = "icat.cfg"
defaultsection = None


class ConfigVariable(object):
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
    def get(self, variable):
        raise NotImplementedError


class ConfigSourceCmdArgs(ConfigSource):
    """Get configuration from command line arguments.
    """
    def __init__(self, argparser):
        super(ConfigSourceCmdArgs, self).__init__()
        self.args = argparser.parse_args()

    def get(self, variable):
        return getattr(self.args, variable.name, None)


class ConfigSourceEnvironment(ConfigSource):
    """Get configuration from environment variables.
    """
    def get(self, variable):
        if variable.envvar:
            return os.environ.get(variable.envvar, None)
        else:
            return None


class ConfigSourceFile(ConfigSource):
    """Get configuration from a configuration file.
    """
    def __init__(self, defaultFiles):
        super(ConfigSourceFile, self).__init__()
        self.confparser = ConfigParser.ConfigParser()
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

    def get(self, variable):
        value = None
        if self.section:
            try:
                value = self.confparser.get(self.section, variable.name)
            except ConfigParser.NoOptionError:
                pass
        return value


class ConfigSourceDefault(ConfigSource):
    """Handle the case that some variable is not set from any source.
    """
    def get(self, variable):
        value = variable.default
        if value is None and not variable.optional:
            raise ConfigError("Config option '%s' not given." % variable.name)
        return value


class Configuration(object):
    """Define a name space to store the configuration.
    """
    def __init__(self, config):
        super(Configuration, self).__init__()
        self._config = config

    def __str__(self):
        typename = type(self).__name__
        arg_strings = []
        vars = [var.name for var in self._config.confvariables] \
            + self._config.ReservedVariables
        for f in vars:
            if hasattr(self, f):
                arg_strings.append('%s=%r' % (f, getattr(self, f)))
        return '%s(%s)' % (typename, ', '.join(arg_strings))


class Config(object):
    """Parse command line arguments and read a configuration file.

    Setup an argument parser for the common set of configuration
    arguments that a ICAT client typically needs: the url of the ICAT
    service, the name of the authentication plugin, the username, and
    password.  Read a configuration file and get the configuration
    variables not found in the command line.
    """

    ReservedVariables = ['credentials', 'client_kwargs']
    """Reserved names of configuration variables."""

    def __init__(self, needlogin=True):
        super(Config, self).__init__()
        self.defaultFiles = [os.path.join(basedir, filename), filename]
        self.needlogin = needlogin
        self.confvariables = []
        self.confvariable = {}

        self.argparser = argparse.ArgumentParser()
        self.add_variable('configFile', ("-c", "--configfile"), 
                          dict(help="config file"),
                          envvar='ICAT_CFG', optional=True)
        self.add_variable('configSection', ("-s", "--configsection"), 
                          dict(help="section in the config file", 
                               metavar='SECTION'), 
                          envvar='ICAT_CFG_SECTION', optional=True, 
                          default=defaultsection)
        self.add_variable('url', ("-w", "--url"), 
                          dict(help="URL to the web service description"),
                          envvar='ICAT_SERVICE')
        self.add_variable('http_proxy', ("--http-proxy",), 
                          dict(help="proxy to use for http requests"),
                          envvar='http_proxy', optional=True)
        self.add_variable('https_proxy', ("--https-proxy",), 
                          dict(help="proxy to use for https requests"),
                          envvar='https_proxy', optional=True)
        if self.needlogin:
            self.add_variable('auth', ("-a", "--auth"), 
                              dict(help="authentication plugin"),
                              envvar='ICAT_AUTH')
            self.add_variable('username', ("-u", "--user"), 
                              dict(help="username"),
                              envvar='ICAT_USER')
            self.add_variable('password', ("-p", "--pass"), 
                              dict(help="password"), 
                              optional=True)
            self.add_variable('promptPass', ("-P", "--prompt-pass"), 
                              dict(help="prompt for the password", 
                                   action='store_true'), 
                              optional=True)

    def add_variable(self, name, arg_opts=(), arg_kws=dict(), 
                   envvar=None, optional=False, default=None):
        if name in self.ReservedVariables or name[0] == '_':
            raise ValueError("Config variable name '%s' is reserved." % name)
        if name in self.confvariable:
            raise ValueError("Config variable '%s' is already defined." % name)
        if arg_opts:
            prefix = self.argparser.prefix_chars
            if len(arg_opts) == 1 and arg_opts[0][0] not in prefix:
                # positional argument
                if arg_opts[0] != name:
                    raise ValueError("Config variable name '%s' must be equal "
                                     "to argument name for positional "
                                     "argument." % name)
            else:
                # optional argument
                arg_kws['dest'] = name
            self.argparser.add_argument(*arg_opts, **arg_kws)
        var = ConfigVariable(name, envvar, optional, default)
        self.confvariable[name] = var
        self.confvariables.append(var)

    def getconfig(self):

        self.args = ConfigSourceCmdArgs(self.argparser)
        self.environ = ConfigSourceEnvironment()
        self.file = ConfigSourceFile(self.defaultFiles)
        self.defaults = ConfigSourceDefault()
        self.sources = [ self.args, self.environ, self.file, self.defaults ]

        # this code relies on the fact, that the first two variables in
        # self.confvariables are 'configFile' and 'configSection' in that
        # order.

        config = Configuration(self)
        for var in self.confvariables:

            for source in self.sources:
                value = source.get(var)
                if value is not None: 
                    break

            setattr(config, var.name, value)

            if var.name == 'configFile':
                config.configFile = self.file.read(config.configFile)
            elif var.name == 'configSection':
                self.file.setsection(config.configSection)

        if self.needlogin:
            # special rule: if the username was given in the command
            # line and password not, this always implies promptPass.
            if ((self.args.args.username and not self.args.args.password) 
                or not config.password):
                config.promptPass = True
            if config.promptPass:
                config.password = getpass.getpass()
            config.credentials = { 'username':config.username, 
                                   'password':config.password }

        config.client_kwargs = {}
        if config.http_proxy or config.https_proxy:
            proxy={}
            if config.http_proxy:
                proxy['http'] = config.http_proxy
            if config.https_proxy:
                proxy['https'] = config.https_proxy
            config.client_kwargs['proxy'] = proxy

        return config
