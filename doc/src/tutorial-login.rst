Authentication and login
~~~~~~~~~~~~~~~~~~~~~~~~

Until now, we only connected the ICAT server to query its version.
This doesn't require a login to the server and hence the flag
``needlogin=False`` in the constructor call of
:class:`icat.config.Config` in our example program.  If we leave this
flag out, we get a bunch of new configuration variables.  Consider the
following example program:

.. literalinclude:: ../tutorial/login.py

Let's check the available command line options now::

  $ python login.py -h
  usage: login.py [-h] [-c CONFIGFILE] [-s SECTION] [-w URL] [--idsurl IDSURL]
                  [--no-check-certificate] [--http-proxy HTTP_PROXY]
                  [--https-proxy HTTPS_PROXY] [--no-proxy NO_PROXY] [-a AUTH]
                  [-u USERNAME] [-P] [-p PASSWORD]

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
plugin as shown in this example.

.. note::
   For this tutorial we assume that the root user in the ICAT server
   has the user name `root` and is configured in the `simple`
   authenticator and that there are two users with name `jdoe` and
   `nbour` configured in the `db` authenticator.  If this is not the
   case in your ICAT, you'll need to adapt the examples accordingly.

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

You might have noticed that the program again prompted us for a
password even though there is one set in the config file.  The
:mod:`icat.config` module is smart enough to assume that if we
overrode the user name on the command line, the password in the config
file will likely not be valid for that user.

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

We shall use some of this configuration in the following sections of
the tutorial.  Do not forget to adapt the URLs, the authenticator
names, and the passwords to what is configured in your ICAT.

