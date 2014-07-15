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
    def __init__(self, argparser, args=None):
        super(ConfigSourceCmdArgs, self).__init__()
        self.args = argparser.parse_args(args)

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
    """Provide a name space to store the configuration.

    `Config.getconfig` returns a ``Configuration`` object having the
    configuration values stored in the respective attributes.
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
    """Set configuration variables.

    Allow configuration variables to be set via command line
    arguments, environment variables, configuration files, and default
    values, in this order.  The first value found will be taken.
    Command line arguments and configuration files are read using the
    standard Python library modules ``argparse`` and ``ConfigParser``
    respectively, see the documentation of these modules for details
    on how to setup custom arguments or for the format of the
    configuration files.

    The following set of configuration variables that an ICAT client
    typically needs is predefined:

      ``configFile``
        Name of the configuration file to read.

        =========================  ==================================
        command line               ``-c``, ``--configfile``
        environment                ``ICAT_CFG``
        default                    ``~/.icat/icat.cfg``, ``icat.cfg``
        mandatory                  no
        =========================  ==================================

      ``configSection``
        Name of the section in the configuration file to apply.  If
        not set, no values will be read from the configuration file.

        =========================  ==================================
        command line               ``-s``, ``--configsection``
        environment                ``ICAT_CFG_SECTION``
        default                    ``None``
        mandatory                  no
        =========================  ==================================

      ``url``
        URL to the web service description of the ICAT server.

        =========================  ==================================
        command line               ``-w``, ``--url``
        environment                ``ICAT_SERVICE``
        mandatory                  yes
        =========================  ==================================

      ``http_proxy``
        Proxy to use for http requests.

        =========================  ==================================
        command line               ``--http-proxy``
        environment                ``http_proxy``
        default                    ``None``
        mandatory                  no
        =========================  ==================================

      ``https_proxy``
        Proxy to use for https requests.

        =========================  ==================================
        command line               ``--https-proxy``
        environment                ``https_proxy``
        default                    ``None``
        mandatory                  no
        =========================  ==================================

      ``auth``
        Name of the authentication plugin to use for login.

        =========================  ==================================
        command line               ``-a``, ``--auth``
        environment                ``ICAT_AUTH``
        mandatory                  yes
        =========================  ==================================

      ``username``
        The ICAT user name.

        =========================  ==================================
        command line               ``-u``, ``--user``
        environment                ``ICAT_USER``
        mandatory                  yes
        =========================  ==================================

      ``password``
        The user's password.  Will prompt for the password if not set.

        =========================  ==================================
        command line               ``-p``, ``--pass``
        default                    ``None``
        mandatory                  no
        =========================  ==================================

      ``promptPass``
        Prompt for the password.

        =========================  ==================================
        command line               ``-P``, ``--prompt-pass``
        default                    ``False``
        mandatory                  no
        =========================  ==================================

      ``idsurl``
        URL to the ICAT Data Service.

        =========================  ==================================
        command line               ``--idsurl``
        environment                ``ICAT_DATA_SERVICE``
        default                    ``None``
        mandatory                  depends on constructor arguments
        =========================  ==================================

    Mandatory means that an error will be raised if no value is found
    for the configuration variable in question.

    Two further derived variables are set in ``getconfig``:

      ``client_kwargs``
        contains the proxy settings and should be passed as the
        keyword arguments to the constructor `Client.__init__` of the
        client.

      ``credentials``
        contains username and password suitable to be passed to
        `Client.login`.
    """

    ReservedVariables = ['client_kwargs', 'credentials']
    """Reserved names of configuration variables."""

    def __init__(self, needlogin=True, ids=False):
        """Initialize the object.

        Setup the predefined configuration variables.  If
        ``needlogin`` is set to ``False``, the configuration variables
        ``auth``, ``username``, ``password``, ``promptPass``, and
        ``credentials`` will be left out.  The configuration variable
        ``idsurl`` will not be set up at all, or be set up as a
        mandatory or as an optional variable, if ``ids`` is set to
        ``False``, to "mandatory", or to "optional" respectively.
        """
        super(Config, self).__init__()
        self.defaultFiles = [os.path.join(basedir, filename), filename]
        self.needlogin = needlogin
        self.ids = ids
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
        if self.ids:
            if self.ids == "mandatory":
                idsopt = False
            elif self.ids == "optional":
                idsopt = True
            else:
                raise ValueError("invalid value '%s' for argument ids." 
                                 % self.ids) 
            self.add_variable('idsurl', ("--idsurl",), 
                              dict(help="URL to the ICAT Data Service"),
                              envvar='ICAT_DATA_SERVICE', optional=idsopt)
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
        """Defines a new configuration variable.

        Call ``ArgumentParser.add_argument`` to add a new command line
        argument if ``arg_opts`` is set.

        :param name: the name of the variable.  This will be used as
            the name of the attribute of the `Configuration` returned
            by `getconfig` and as the name of the option to be looked
            for in the configuration file.  The name must be unique
            and not in `ReservedVariables`.  If ``arg_opts``
            corresponds to a positional argument, the name must be
            equal to this argument name.
        :type name: ``str``
        :param arg_opts: command line flags associated with this
            variable.  This will be passed as ``name or flags`` to
            ``ArgumentParser.add_argument``.
        :type arg_opts: ``tuple`` of ``str``
        :param arg_kws: keyword arguments to be passed to
            ``ArgumentParser.add_argument``.
        :type arg_kws: ``dict``
        :param envvar: name of the environment variable or ``None``.
            If set, the value for the variable may be set from the
            respective environment variable.
        :type envvar: ``str``
        :param optional: flag wether the configuration variable is
            optional.  If set to ``False`` and ``default`` is ``None``
            the variable is mandatory.
        :type optional: ``bool``
        :param default: default value.
        :raise ValueError: if the name is not valid.
        :see: the documentation of the ``argparse`` standard library
            module for details on ``arg_opts`` and ``arg_kws``.
        """
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

    def getconfig(self, args=None):
        """Get the configuration.

        Parse the command line arguments, evaluate environment
        variables, read the configuration file, and apply default
        values (in this order) to get the value for each defined
        configuration variable.  The first defined value found will be
        taken.

        :param args: list of command line arguments or ``None``.
            If not set, the command lien arguments will be taken from
            ``sys.argv``.
        :type args: ``list`` of ``str``
        :return: an object having the configuration values set as
            attributes.
        :rtype: ``Configuration``
        :raise ConfigError: if ``configFile`` is defined but the file
            by this name can not be read, if ``configSection`` is
            defined but no section by this name could be found in the
            configuration file, or if a mandatory variable is not
            defined.
        """
        self.args = ConfigSourceCmdArgs(self.argparser, args)
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
        if self.ids:
            config.client_kwargs['idsurl'] = config.idsurl

        return config
