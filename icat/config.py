"""Provide the Config class.
"""

import sys
import os
import os.path
import getpass
import argparse
import ConfigParser
from icat.exception import *

__all__ = ['boolean', 'flag', 'Configuration', 'Config']


if sys.platform.startswith("win"):
    cfgdirs = [ os.path.join(os.environ['ProgramData'], "ICAT"),
                os.path.join(os.environ['AppData'], "ICAT"),
                os.path.join(os.environ['LocalAppData'], "ICAT"), 
                "", ]
else:
    cfgdirs = [ "/etc/icat", 
                os.path.expanduser("~/.config/icat"),
                os.path.expanduser("~/.icat"), 
                "", ]
"""Search path for the configuration file"""
cfgfile = "icat.cfg"
"""Configuration file name"""
defaultsection = None
"""Default value for `configSection`"""


def boolean(value):
    """Test truth value.

    Convert the string representation of a truth value, such as ``0``,
    ``1``, ``yes``, ``no``, ``true``, or ``false`` to :class:`bool`.
    This function is suitable to be passed as type to
    :meth:`icat.config.Config.add_variable`.
    """
    if isinstance(value, basestring):
        if value.lower() in ["0", "no", "n", "false", "f", "off"]:
            return False
        elif value.lower() in ["1", "yes", "y", "true", "t", "on"]:
            return True
        else:
            raise ValueError("Invalid truth value '%s'" % value)
    elif isinstance(value, bool):
        return value
    else:
        raise TypeError("invalid type %s, expect bool or str" % type(value))

flag = object()
"""Special boolean variable type that defines two command line arguments."""

def cfgpath(p):
    """Search for a file in some default directories.

    The argument `p` should be a file path name.  If `p` is absolut,
    it will be returned unchanged.  Otherwise, `p` will be resolved
    against the directories in :data:`cfgdirs` in reversed order.  If
    a file with the resulting path is found to exist, this path will
    be returned, first match wins.  If no file exists in any of the
    directories, `p` will be returned unchanged.

    This function is suitable to be passed as `type` argument to
    :meth:`icat.config.Config.add_variable`.
    """
    if os.path.isabs(p):
        return p
    else:
        for d in reversed(cfgdirs):
            fp = os.path.join(d, p)
            if os.path.isfile(fp):
                return fp
        else:
            return p


class ConfigVariable(object):
    """Describe a configuration variable.
    """
    def __init__(self, name, envvar, optional, default, convert, subst):
        self.name = name
        self.envvar = envvar
        self.optional = optional
        self.default = default
        self.convert = convert
        self.subst = subst
    def get(self, value):
        if self.convert and value is not None:
            try:
                return self.convert(value)
            except (TypeError, ValueError):
                typename = getattr(self.convert, "__name__", str(self.convert))
                err = ConfigError("%s: invalid %s value: %r" 
                                  % (self.name, typename, value))
                raise stripCause(err)
        else:
            return value


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
        return variable.get(getattr(self.args, variable.name, None))


class ConfigSourceEnvironment(ConfigSource):
    """Get configuration from environment variables.
    """
    def get(self, variable):
        if variable.envvar:
            return variable.get(os.environ.get(variable.envvar, None))
        else:
            return None


class ConfigSourceFile(ConfigSource):
    """Get configuration from a configuration file.
    """
    def __init__(self, defaultFiles):
        super(ConfigSourceFile, self).__init__()
        self.confparser = ConfigParser.RawConfigParser()
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
        return variable.get(value)


class ConfigSourceDefault(ConfigSource):
    """Handle the case that some variable is not set from any other source.
    """
    def get(self, variable):
        value = variable.default
        if value is None and not variable.optional:
            raise ConfigError("Config option '%s' not given." % variable.name)
        return variable.get(value)


class Configuration(object):
    """Provide a name space to store the configuration.

    :meth:`icat.config.Config.getconfig` returns a Configuration
    object having the configuration values stored in the respective
    attributes.
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

    def as_dict(self):
        """Return the configuration as a dict."""
        vars = [var.name for var in self._config.confvariables] \
            + self._config.ReservedVariables
        return { f:getattr(self, f) for f in vars if hasattr(self, f) }


class Config(object):
    """Set configuration variables.

    Allow configuration variables to be set via command line
    arguments, environment variables, configuration files, and default
    values, in this order.  The first value found will be taken.
    Command line arguments and configuration files are read using the
    standard Python library modules :mod:`argparse` and
    :mod:`ConfigParser` respectively, see the documentation of these
    modules for details on how to setup custom arguments or for the
    format of the configuration files.
    """

    ReservedVariables = ['configDir', 'client_kwargs', 'credentials']
    """Reserved names of configuration variables."""

    def __init__(self, needlogin=True, ids=False):
        """Initialize the object.

        Setup the predefined configuration variables.  If `needlogin`
        is set to :const:`False`, the configuration variables `auth`,
        `username`, `password`, `promptPass`, and `credentials` will
        be left out.  The configuration variable `idsurl` will not be
        set up at all, or be set up as a mandatory, or as an optional
        variable, if `ids` is set to :const:`False`, to "mandatory",
        or to "optional" respectively.
        """
        super(Config, self).__init__()
        self.defaultFiles = [os.path.join(d, cfgfile) for d in cfgdirs]
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
        self.add_variable('checkCert', ("--check-certificate",), 
                          dict(help="don't verify the server certificate"), 
                          type=flag, default=True)
        self.add_variable('http_proxy', ("--http-proxy",), 
                          dict(help="proxy to use for http requests"),
                          envvar='http_proxy', optional=True)
        self.add_variable('https_proxy', ("--https-proxy",), 
                          dict(help="proxy to use for https requests"),
                          envvar='https_proxy', optional=True)
        self.add_variable('no_proxy', ("--no-proxy",), 
                          dict(help="list of exclusions for proxy use"),
                          envvar='no_proxy', optional=True)
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
                                   action='store_const', const=True), 
                              type=boolean, default=False)

    def add_variable(self, name, arg_opts=(), arg_kws=dict(), 
                     envvar=None, optional=False, default=None, type=None, 
                     subst=False):

        """Defines a new configuration variable.

        Call :meth:`argparse.ArgumentParser.add_argument` to add a new
        command line argument if `arg_opts` is set.

        :param name: the name of the variable.  This will be used as
            the name of the attribute of
            :class:`icat.config.Configuration` returned by
            :meth:`icat.config.Config.getconfig` and as the name of
            the option to be looked for in the configuration file.
            The name must be unique and not in
            :attr:`icat.config.Config.ReservedVariables`.  If
            `arg_opts` corresponds to a positional argument, the name
            must be equal to this argument name.
        :type name: :class:`str`
        :param arg_opts: command line flags associated with this
            variable.  This will be passed as `name or flags` to
            :meth:`argparse.ArgumentParser.add_argument`.
        :type arg_opts: :class:`tuple` of :class:`str`
        :param arg_kws: keyword arguments to be passed to
            :meth:`argparse.ArgumentParser.add_argument`.
        :type arg_kws: :class:`dict`
        :param envvar: name of the environment variable or
            :const:`None`.  If set, the value for the variable may be
            set from the respective environment variable.
        :type envvar: :class:`str`
        :param optional: flag wether the configuration variable is
            optional.  If set to :const:`False` and `default` is
            :const:`None` the variable is mandatory.
        :type optional: :class:`bool`
        :param default: default value.
        :param type: type to which the value should be converted.
            This must be a callable that accepts one string argument
            and returns the desired value.  The builtins :func:`int`
            and :func:`float` are fine.  If set to :const:`None`, the
            string value is taken as is.  If applicable, the default
            value will also be passed through this conversion.  The
            special value of :data:`icat.config.flag` may also be used
            to indicate a variant of :func:`icat.config.boolean`.
        :type type: callable
        :param subst: flag wether substitution of other configuration
            variables using the ``%`` interpolation operator shall be
            performed.  If set to :const:`True`, the value may contain
            conversion specifications such as ``%(othervar)s``.  This
            will then be substituted by the value of `othervar`.  The
            referenced variable must have been defined earlier.
        :type subst: :class:`bool`
        :raise ValueError: if the name is not valid.
        :see: the documentation of the :mod:`argparse` standard
            library module for details on `arg_opts` and `arg_kws`.
        """
        if name in self.ReservedVariables or name[0] == '_':
            raise ValueError("Config variable name '%s' is reserved." % name)
        if name in self.confvariable:
            raise ValueError("Config variable '%s' is already defined." % name)
        if type == flag:
            # flag is a variant of boolean that defines two command
            # line arguments, a positive and a negative one.
            if '-' not in self.argparser.prefix_chars:
                raise ValueError("flag type requires '-' to be in the "
                                 "argparser's prefix_chars.")
            if len(arg_opts) != 1 or not arg_opts[0].startswith('--'):
                raise ValueError("invalid argument options for flag type.")
            arg = arg_opts[0][2:]
            arg_kws['dest'] = name
            arg_kws['action'] = 'store_const'
            if default:
                arg_kws['const'] = False
                self.argparser.add_argument("--no-"+arg, **arg_kws)
                arg_kws['const'] = True
                arg_kws['help'] = argparse.SUPPRESS
                self.argparser.add_argument("--"+arg, **arg_kws)
            else:
                arg_kws['const'] = True
                self.argparser.add_argument("--"+arg, **arg_kws)
                arg_kws['const'] = False
                arg_kws['help'] = argparse.SUPPRESS
                self.argparser.add_argument("--no-"+arg, **arg_kws)
            type = boolean
        elif arg_opts:
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
        var = ConfigVariable(name, envvar, optional, default, type, subst)
        self.confvariable[name] = var
        self.confvariables.append(var)

    def getconfig(self, args=None):
        """Get the configuration.

        Parse the command line arguments, evaluate environment
        variables, read the configuration file, and apply default
        values (in this order) to get the value for each defined
        configuration variable.  The first defined value found will be
        taken.

        :param args: list of command line arguments or :const:`None`.
            If not set, the command line arguments will be taken from
            :data:`sys.argv`.
        :type args: :class:`list` of :class:`str`
        :return: an object having the configuration values set as
            attributes.
        :rtype: :class:`icat.config.Configuration`
        :raise ConfigError: if `configFile` is defined but the file by
            this name can not be read, if `configSection` is defined
            but no section by this name could be found in the
            configuration file, if an invalid value is given to a
            variable, or if a mandatory variable is not defined.
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
            if value is not None and var.subst:
                value = value % config.as_dict()

            setattr(config, var.name, value)

            if var.name == 'configFile':
                config.configFile = self.file.read(config.configFile)
                if config.configFile:
                    f = config.configFile[-1]
                    config.configDir = os.path.dirname(os.path.abspath(f))
                else:
                    config.configDir = None
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
        if self.ids:
            config.client_kwargs['idsurl'] = config.idsurl
        config.client_kwargs['checkCert'] = config.checkCert
        if config.http_proxy or config.https_proxy:
            proxy={}
            if config.http_proxy:
                proxy['http'] = config.http_proxy
                os.environ['http_proxy'] = config.http_proxy
            if config.https_proxy:
                proxy['https'] = config.https_proxy
                os.environ['https_proxy'] = config.https_proxy
            config.client_kwargs['proxy'] = proxy
        if config.no_proxy:
                os.environ['no_proxy'] = config.no_proxy

        return config
