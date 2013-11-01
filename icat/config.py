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
        argparser = argparse.ArgumentParser()
        argparser.add_argument("-c", "--configfile", 
                               help="config file")
        argparser.add_argument("-s", "--configsection", 
                               help="section in the config file", 
                               metavar='SECTION',
                               dest='config', default=defaultsection)
        argparser.add_argument("-w", "--url", 
                               help="URL to the web service description")
        if needlogin:
            argparser.add_argument("-a", "--auth", help="authentication plugin")
            argparser.add_argument("-u", "--user", help="username", 
                                   dest='username')
            argparser.add_argument("-p", "--pass", help="password", 
                                   dest='password')
            argparser.add_argument("-P", "--prompt-pass", 
                                   help="prompt for the password", 
                                   action='store_true')
            self.conffields = ('url', 'auth', 'username', 'password', 
                               'credentials')
        else:
            self.conffields = ('url',)
        self.argparser = argparser
        self.args = None

    def parse_args(self):
        self.args = self.argparser.parse_args()
        return self.args

    def getconfig(self):

        if self.args is None:
            self.parse_args()
        args = self.args

        config = ConfigParser.ConfigParser()
        fname = getattr(args, 'configfile', None)
        if fname:
            if not config.read(fname):
                raise ConfigError("could not read config file '%s'." % fname)
        else:
            config.read([os.path.join(basedir, filename), filename])
        section = getattr(args, 'config', None)
        if section and not config.has_section(section):
            raise ConfigError("could not read config section '%s'." % section)

        for f in self.conffields:
            if f != 'credentials':
                try:
                    v = getattr(args, f, None) or config.get(section, f)
                except ConfigParser.NoOptionError:
                    raise ConfigError("config option '%s' not given." % f)
                setattr(self, f, v)

        if 'credentials' in self.conffields:
            if ((args.username and not args.password) or args.prompt_pass):
                self.password = getpass.getpass()
            self.credentials = { 'username':self.username, 
                                 'password':self.password }
