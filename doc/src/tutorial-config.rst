Configuration
~~~~~~~~~~~~~

The example from the last section had the URL of the ICAT service hard
coded in the program.  This is certainly not the best way to do it.
You could make it a command line argument, but then you would need to
indicate it each time you run the program, which is also not very
convenient.  The module :mod:`icat.config` has been created to solve
this.  It manages several configuration variables that most ICAT
client programs need.

Configuration options
---------------------

Lets modify the example program as follows::

  #! /usr/bin/python

  from __future__ import print_function
  import icat
  import icat.config

  config = icat.config.Config(needlogin=False, ids=False)
  client, conf = config.getconfig()
  print("Connect to %s\nICAT version %s" % (conf.url, client.apiversion))

If we run this without any command line arguments, we get an error::

  $ python config.py
  Traceback (most recent call last):
    ...
  icat.exception.ConfigError: Config option 'url' not given.

Apparently, there is a configuration option named `url` and we didn't
specify it.  Let's have a look on the command line options, that this
program now accepts::

  $ python config.py -h
  usage: config.py [-h] [-c CONFIGFILE] [-s SECTION] [-w URL]
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

  $ python config.py -w 'https://icat.example.com:8181/ICATService/ICAT?wsdl'
  Connect to https://icat.example.com:8181/ICATService/ICAT?wsdl
  ICAT version 4.7

(Again, you may need to add the ``--no-check-certificate`` flag to the
command line if your ICAT server does not have a trusted SSL
certificate.)  This does the job.  But as mentioned above, it's not
very convenient having to indicate the URL each time you run the
program.  But in the command line arguments, there is also a mention
of a configuration file.  Create a text file named ``icat.cfg`` in the
current working directory with the following content::

  [myicat]
  url = https://icat.example.com:8181/ICATService/ICAT?wsdl
  # uncomment, if your server does not have a trusted certificate
  #checkCert = No

Now you can do the following::

  $ python config.py -s myicat
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

  config = icat.config.Config(needlogin=False, ids="optional")
  client, conf = config.getconfig()
  print("Connect to %s\nICAT version %s" % (conf.url, client.apiversion))
  if conf.idsurl:
      print("Connect to %s\nIDS version %s"
            % (conf.idsurl, client.ids.apiversion))
  else:
      print("No IDS configured")

If you run this in the same way as above, you'll get::

  $ python config-with-ids.py -s myicat
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

  $ python config-with-ids.py -s myicat
  Connect to https://icat.example.com:8181/ICATService/ICAT?wsdl
  ICAT version 4.7
  Connect to https://icat.example.com:8181/ids
  IDS version 1.6

Custom configuration variables
------------------------------

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
  client, conf = config.getconfig()
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

  $ python config-custom.py -h
  usage: config-custom.py [-h] [-c CONFIGFILE] [-s SECTION] [-w URL]
                          [--idsurl IDSURL] [--no-check-certificate]
                          [--http-proxy HTTP_PROXY] [--https-proxy HTTPS_PROXY]
                          [--no-proxy NO_PROXY] [-a AUTH] [-u USERNAME] [-P]
                          [-p PASSWORD] [-o OUTFILE]

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
    -P, --prompt-pass     prompt for the password
    -p PASSWORD, --pass PASSWORD
                          password
    -o OUTFILE, --outputfile OUTFILE
                          output file name or '-' for stdout

This new option is optional, so the program can be used as before::

  $ python config-custom.py -s myicat_jdoe
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: simple/jdoe

If we add the option on the command line, it has the expected effect::

  $ python config-custom.py -s myicat_jdoe -o out.txt
  $ cat out.txt
  Login to https://icat.example.com:8181/ICATService/ICAT?wsdl was successful.
  User: simple/jdoe

