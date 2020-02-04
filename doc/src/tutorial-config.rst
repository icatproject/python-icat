Configuration
~~~~~~~~~~~~~

The example from the last section had the URL of the ICAT service hard
coded in the program.  This is certainly not the best way to do it.
You could make it a command line argument, but then you would need to
indicate it each time you run the program, which is also not very
convenient.  The module :mod:`icat.config` has been created to solve
this.  It manages several configuration variables that most ICAT
client programs need.

Let's modify the example program as follows:

.. literalinclude:: ../tutorial/config.py

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
  ICAT version 4.8

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
  ICAT version 4.8

The command line option ``-s SECTION`` selects a section in the
configuration file to read options from.

python-icat is not only a client for ICAT, but also for IDS.  Since
both may be on a different server, we need to tell python-icat also
about the URL to IDS.  Modify the example program to read as:

.. literalinclude:: ../tutorial/config-with-ids.py

If you run this in the same way as above, you'll get::

  $ python config-with-ids.py -s myicat
  Connect to https://icat.example.com:8181/ICATService/ICAT?wsdl
  ICAT version 4.8
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
  ICAT version 4.8
  Connect to https://icat.example.com:8181/ids
  IDS version 1.7

