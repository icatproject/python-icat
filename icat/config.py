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

    This is a helper class, designed for the internal use in Config.
    The user of this module might not need it.
    """
    def __init__(self, name, optional):
        self.name = name
        self.optional = optional


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
        self.defaultSection = defaultsection
        self.needlogin = needlogin
        self.conffields = []

        self.argparser = argparse.ArgumentParser()
        self.add_field('configFile', ("-c", "--configfile"), 
                       dict(help="config file"),
                       optional=True)
        self.add_field('configSection', ("-s", "--configsection"), 
                       dict(help="section in the config file", 
                            metavar='SECTION',
                            default=defaultsection), 
                       optional=True)
        self.add_field('url', ("-w", "--url"), 
                       dict(help="URL to the web service description"))
        if self.needlogin:
            self.add_field('auth', ("-a", "--auth"), 
                           dict(help="authentication plugin"))
            self.add_field('username', ("-u", "--user"), dict(help="username"))
            self.add_field('password', ("-p", "--pass"), dict(help="password"), 
                           optional=True)
            self.add_field('promptPass', ("-P", "--prompt-pass"), 
                           dict(help="prompt for the password", 
                                action='store_true'), 
                           optional=True)
        self.args = None

    def add_field(self, name, arg_opts=(), arg_kws=dict(), optional=False):
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
        self.conffields.append(ConfigField(name, optional))

    def parse_args(self):
        self.args = self.argparser.parse_args()
        return self.args

    def getconfig(self):

        if self.args is None:
            self.parse_args()
        args = self.args
        config = ConfigParser.ConfigParser()
        section = None

        # this code relies on the fact, that the first two fields in
        # self.conffields are 'configFile' and 'configSection' in that
        # order.

        for field in self.conffields:

            value = getattr(args, field.name, None)

            if value is None and section:
                try:
                    value = config.get(section, field.name)
                except ConfigParser.NoOptionError:
                    value = None

            if value is None and not field.optional:
                raise ConfigError("Config option '%s' not given." % field.name)

            setattr(self, field.name, value)

            if field.name == 'configFile':

                if self.configFile:
                    if not config.read(self.configFile):
                        raise ConfigError("Could not read config file '%s'." % 
                                          self.configFile)
                elif self.configFile is None:
                    self.configFile = config.read(self.defaultFiles)

            elif field.name == 'configSection':

                section = self.configSection
                if section and not config.has_section(section):
                    raise ConfigError("Could not read config section '%s'." % 
                                      section)

        if self.needlogin:
            # special rule: if the username was given in the command
            # line and password not, this always implies promptPass.
            if (args.username and not args.password) or not self.password:
                self.promptPass = True
            if self.promptPass:
                self.password = getpass.getpass()
            self.credentials = { 'username':self.username, 
                                 'password':self.password }

    def __str__(self):
        typename = type(self).__name__
        arg_strings = []
        for field in self.conffields:
            arg_strings.append('%s=%r' % (field.name, getattr(self, field.name)))
        if self.needlogin:
            arg_strings.append('%s=%r' % ('credentials', self.credentials))
        return '%s(%s)' % (typename, ', '.join(arg_strings))
