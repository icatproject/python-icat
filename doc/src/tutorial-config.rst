Configuration
~~~~~~~~~~~~~

The example from the last section had the URL of the ICAT service hard
coded in the program.  This is certainly not the best way to do it.
You could make it a command line argument, but then you would need to
indicate it each time you run the program, which is also not very
convenient.  The module :mod:`icat.config` has been created to solve
this.  It manages several configuration variables that most ICAT
client programs need.

Lets modify the example program as follows::

  #! /usr/bin/python
  
  from __future__ import print_function
  import icat
  import icat.config
  
  conf = icat.config.Config(needlogin=False).getconfig()
  
  client = icat.Client(conf.url, **conf.client_kwargs)
  print("Connect to %s\nICAT version %s" % (conf.url, client.apiversion))

If we run this without any command line arguments, we get an error::

  $ python hello3.py 
  Traceback (most recent call last):
    ...
  icat.exception.ConfigError: Config option 'url' not given.

Apparently, there is a configuration option named `url` and we didn't
specify it.  Let's have a look on the command line options, that this
program now accepts::

  $ python hello3.py -h
  usage: hello3.py [-h] [-c CONFIGFILE] [-s SECTION] [-w URL]
                   [--no-check-certificate] [--http-proxy HTTP_PROXY]
                   [--https-proxy HTTPS_PROXY] [--no-proxy NO_PROXY]
  
  optional arguments:
    -h, --help            show this help message and exit
    -c CONFIGFILE, --configfile CONFIGFILE
                          config file
    -s SECTION, --configsection SECTION
                          section in the config file
    -w URL, --url URL     URL to the web service description
    --no-check-certificate
                          don't verify the server certificate
    --http-proxy HTTP_PROXY
                          proxy to use for http requests
    --https-proxy HTTPS_PROXY
                          proxy to use for https requests
    --no-proxy NO_PROXY   list of exclusions for proxy use

So there is a command line option ``-w URL``.  Let's try::

  $ python hello3.py -w 'https://icat.example.com:8181/ICATService/ICAT?wsdl' --no-check-certificate
  Connect to https://icat.example.com:8181/ICATService/ICAT?wsdl
  ICAT version 4.7

(Again, the ``--no-check-certificate`` flag is only needed if your
ICAT server does not have a trusted SSL certificate and if you are
using Python 2.7.9 or newer.)  This does the job.  But as mentioned
above, it's not very convenient having to indicate the URL each time
you run the program.  But in the command line arguments, there is also
a mention of a configuration file.  Create a text file named
``icat.cfg`` in the current working directory with the following
content::

  [myicat]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  # uncomment, if your server does not have a trusted certificate
  #checkCert = No

Now you can do the following::

  $ python hello3.py -s myicat
  Connect to https://icat.example.com:8181/ICATService/ICAT?wsdl
  ICAT version 4.7

The command line option ``-s SECTION`` selects a section in the
configuration file to read options from.

python-icat is not only a client for ICAT, but also for IDS.  Since
both may be on a different server, we need to tell python-icat also
about the URL to IDS.  Modify the example program to read as::

  #! /usr/bin/python
  
  from __future__ import print_function
  import icat
  import icat.config
  
  conf = icat.config.Config(needlogin=False, ids="optional").getconfig()
  
  client = icat.Client(conf.url, **conf.client_kwargs)
  print("Connect to %s\nICAT version %s" % (conf.url, client.apiversion))
  if conf.idsurl:
      print("Connect to %s\nIDS version %s" 
            % (conf.idsurl, client.ids.apiversion))
  else:
      print("No IDS configured")

If you run this in the same way as above, you'll get::

  $ python hello4.py -s myicat
  Connect to https://icat.example.com:8181/ICATService/ICAT?wsdl
  ICAT version 4.7
  No IDS configured

But if you indicate the URL to IDS with the command line option
``--idsurl``, or even better in the configuration file as follows::

  [myicat]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  idsurl = https://icat.example.com:8181/ids
  # uncomment, if your server does not have a trusted certificate
  #checkCert = No

You'll get something like::

  $ python hello4.py -s myicat
  Connect to https://icat.example.com:8181/ICATService/ICAT?wsdl
  ICAT version 4.7
  Connect to https://icat.example.com:8181/ids
  IDS version 1.6

Until now, we only connected the ICAT server to query its version.
This doesn't require a login to the server and hence the flag
``needlogin=False`` in the constructor call of
:class:`icat.config.Config` in our example program.  If we leave this
flag out, we get a bunch of new configuration variables.  Consider the
following example program::

  #! /usr/bin/python
  
  from __future__ import print_function
  import icat
  import icat.config
  
  conf = icat.config.Config(ids="optional").getconfig()
  
  client = icat.Client(conf.url, **conf.client_kwargs)
  client.login(conf.auth, conf.credentials)
  
  print("Login to %s was successful." % (conf.url))
  print("User: %s" % (client.getUserName()))

Let's check the available command line options now::

  $ python login.py -h
  usage: login.py [-h] [-c CONFIGFILE] [-s SECTION] [-w URL] [--idsurl IDSURL]
                  [--no-check-certificate] [--http-proxy HTTP_PROXY]
                  [--https-proxy HTTPS_PROXY] [--no-proxy NO_PROXY] [-a AUTH]
                  [-u USERNAME] [-p PASSWORD] [-P]
  
  optional arguments:
    -h, --help            show this help message and exit
    -c CONFIGFILE, --configfile CONFIGFILE
                          config file
    -s SECTION, --configsection SECTION
                          section in the config file
    -w URL, --url URL     URL to the web service description
    --idsurl IDSURL       URL to the ICAT Data Service
    --no-check-certificate
                          don't verify the server certificate
    --http-proxy HTTP_PROXY
                          proxy to use for http requests
    --https-proxy HTTPS_PROXY
                          proxy to use for https requests
    --no-proxy NO_PROXY   list of exclusions for proxy use
    -a AUTH, --auth AUTH  authentication plugin
    -u USERNAME, --user USERNAME
                          username
    -p PASSWORD, --pass PASSWORD
                          password
    -P, --prompt-pass     prompt for the password

Now call this program indicating the name of the authentication plugin
and a user name::

  $ python login.py -s myicat -a db -u jdoe
  Password: 
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: db/jdoe

Note that the program prompted us for a password, since we didn't
provide one.  Of course you need to specify an authentication plugin,
user name, and password that is actually configured in your ICAT.
Furthermore, the user name printed by the program may be different
from the one indicated in the command line.  This depends on the
configuration of the authentication plugin in your ICAT.  It is common
praxis to prefix the user name with the name of the authentication
plugin as in this example.

All configuration variables aside from `configFile` and
`configSection` can be set in the configuration file.  Edit your
``icat.cfg`` file to read::

  [myicat_jdoe]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  auth = db
  username = jdoe
  password = secret
  idsurl = https://icat.example.com:8181/ids
  # uncomment, if your server does not have a trusted certificate
  #checkCert = No

You should protect this file from unauthorized read access if you
store passwords in it.  Now you can do::

  $ python login.py -s myicat_jdoe
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: db/jdoe

Command line options override the settings in the configuration file.
This way, you can still log in as another user not configured in the
file::

  $ python login.py -s myicat_jdoe -u nbour
  Password: 
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: db/nbour

Configuration files can have many sections.  It may come handy to be
able to quickly switch between different users to log into the ICAT.
Edit ``icat.cfg`` again to read as follows::

  [myicat_root]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  auth = simple
  username = root
  password = secret
  idsurl = https://icat.example.com:8181/ids
  # uncomment, if your server does not have a trusted certificate
  #checkCert = No
  
  [myicat_useroffice]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  auth = simple
  username = useroffice
  password = secret
  idsurl = https://icat.example.com:8181/ids
  #checkCert = No
  
  [myicat_acord]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  auth = db
  username = acord
  password = secret
  idsurl = https://icat.example.com:8181/ids
  #checkCert = No
  
  [myicat_ahau]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  auth = db
  username = ahau
  password = secret
  idsurl = https://icat.example.com:8181/ids
  #checkCert = No
  
  [myicat_jbotu]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  auth = db
  username = jbotu
  password = secret
  idsurl = https://icat.example.com:8181/ids
  #checkCert = No
  
  [myicat_jdoe]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  auth = db
  username = jdoe
  password = secret
  idsurl = https://icat.example.com:8181/ids
  #checkCert = No
  
  [myicat_nbour]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  auth = db
  username = nbour
  password = secret
  idsurl = https://icat.example.com:8181/ids
  #checkCert = No
  
  [myicat_rbeck]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  auth = db
  username = rbeck
  password = secret
  idsurl = https://icat.example.com:8181/ids
  #checkCert = No

We shall use some of this configuration in the following sections of
the tutorial.  Do not forget to adapt the URLs, the authenticator
names, and the passwords to what is configured in your ICAT.

Programs may also define their own custom configuration variables.
Lets add the option to redirect the output of our example program to a
file::

  #! /usr/bin/python
  
  from __future__ import print_function
  import sys
  import icat
  import icat.config
  
  config = icat.config.Config(ids="optional")
  config.add_variable('outfile', ("-o", "--outputfile"), 
                      dict(help="output file name or '-' for stdout"),
                      default='-')
  conf = config.getconfig()
  
  client = icat.Client(conf.url, **conf.client_kwargs)
  client.login(conf.auth, conf.credentials)
  
  if conf.outfile == '-':
      out = sys.stdout
  else:
      out = open(conf.outfile, "wt")
  
  print("Login to %s was successful." % (conf.url), file=out)
  print("User: %s" % (client.getUserName()), file=out)
  
  out.close()

This adds a new configuration variable `outfile`.  It can be specified
on the command line as ``-o OUTFILE`` or ``--outputfile OUTFILE`` and
it defaults to the string ``-`` if not specified.  We can check this
on the list of available command line options::

  $ python login2.py -h
  usage: login2.py [-h] [-c CONFIGFILE] [-s SECTION] [-w URL] [--idsurl IDSURL]
                   [--no-check-certificate] [--http-proxy HTTP_PROXY]
                   [--https-proxy HTTPS_PROXY] [--no-proxy NO_PROXY] [-a AUTH]
                   [-u USERNAME] [-p PASSWORD] [-P] [-o OUTFILE]
  
  optional arguments:
    -h, --help            show this help message and exit
    -c CONFIGFILE, --configfile CONFIGFILE
                          config file
    -s SECTION, --configsection SECTION
                          section in the config file
    -w URL, --url URL     URL to the web service description
    --idsurl IDSURL       URL to the ICAT Data Service
    --no-check-certificate
                          don't verify the server certificate
    --http-proxy HTTP_PROXY
                          proxy to use for http requests
    --https-proxy HTTPS_PROXY
                          proxy to use for https requests
    --no-proxy NO_PROXY   list of exclusions for proxy use
    -a AUTH, --auth AUTH  authentication plugin
    -u USERNAME, --user USERNAME
                          username
    -p PASSWORD, --pass PASSWORD
                          password
    -P, --prompt-pass     prompt for the password
    -o OUTFILE, --outputfile OUTFILE
                          output file name or '-' for stdout

This new option is optional, so the program can be used as before::

  $ python login2.py -s myicat_jdoe
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: db/jdoe

If we add the option on the command line, it has the expected effect::

  $ python login2.py -s myicat_jdoe -o out.txt
  $ cat out.txt
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: db/jdoe

