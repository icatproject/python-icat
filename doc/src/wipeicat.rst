.. _wipeicat:

wipeicat
========


Synopsis
~~~~~~~~

| **wipeicat** [*options*]


Description
~~~~~~~~~~~

.. program:: wipeicat

Delete all content from an ICAT server.

In order to avoid leaving orphan content in the IDS server behind, the
script first tries to delete all Datafiles having the
:attr:`~icat.entities.Datafile.location` attribute set from the IDS
server.  If deleting the Datafiles succeeded, the remaing content is
deleted from ICAT in palatable chunks.


Options
~~~~~~~

.. program:: wipeicat

The configuration options may be set in the command line or in a
configuration file.  Some options may also be set in the environment.

These options are needed to connect the ICAT service and are common
for most python-icat scripts.

.. program:: wipeicat

.. option:: -h, --help

    Display a help message and exit.

.. option:: -c CONFIGFILE, --configfile CONFIGFILE

    Name of a configuration file.

.. option:: -s SECTION, --configsection SECTION

    Name of a section in the configuration file.  If set, the values
    in this configuration section will be applied to define other
    options.

.. option:: -w URL, --url URL

    URL of the ICAT server.  This should point to the web service
    descriptions.  If the URL has no path component, a default path
    will be added.

.. option:: --no-check-certificate

    Do not verify the ICAT server's TLS certificate.  This is only
    relevant if the URL set with :option:`--url` uses HTTPS.  It is
    mostly only useful for connecting a test server that does not have
    a trusted certificate.

.. option:: --http-proxy HTTP_PROXY

    Proxy to use for http requests.

.. option:: --https-proxy HTTPS_PROXY

    Proxy to use for https requests.

.. option:: --no-proxy NO_PROXY

    Comma separated list of exclusions for proxy use.

.. option:: -a AUTH, --auth AUTH

    Name of the authentication plugin to use for login to the ICAT
    server.

.. option:: -u USERNAME, --user USERNAME

    The ICAT user name.

.. option:: -p PASSWORD, --pass PASSWORD

    The user's password.  Will prompt for the password if not set.

.. option:: -P, --prompt-pass

    Prompt for the password.  This is mostly useful to override a
    password set in the configuration file.


Known Issues with old IDS Versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The recommended version of the IDS server is 1.6.0 or newer.  The
script does not take any particular measure to work around issues in
servers older than that.  In particular, the script mail fail or leave
rubbish behind in the following situations:

* The IDS server is older then 1.6.0 and there is any Dataset with
  many Datafiles, see `IDS Issue #42`_.

* The IDS server is older then 1.3.0 and restoring of any Dataset
  takes a significant amount of time, see `IDS Issue #14`_.

The script does however take care not trying to delete any Datafile
having a NULL :attr:`~icat.entities.Datafile.location` attribute in
order to work around `IDS Issue #63`_ in IDS server older then 1.9.0.

.. _IDS Issue #14: https://github.com/icatproject/ids.server/issues/14
.. _IDS Issue #42: https://github.com/icatproject/ids.server/issues/42
.. _IDS Issue #63: https://github.com/icatproject/ids.server/issues/63


Environment Variables
~~~~~~~~~~~~~~~~~~~~~

.. describe:: ICAT_CFG

    Name of a configuration file, see :option:`--configfile`.

.. describe:: ICAT_CFG_SECTION

    Name of a section in the configuration file, see
    :option:`--configsection`.

.. describe:: ICAT_SERVICE

    URL of the ICAT server, see :option:`--url`.

.. describe:: http_proxy

    Proxy to use for http requests, see :option:`--http-proxy`.

.. describe:: https_proxy

    Proxy to use for https requests, see :option:`--https-proxy`.

.. describe:: no_proxy

    Exclusions for proxy use, see :option:`--no-proxy`.

.. describe:: ICAT_AUTH

    Name of the authentication plugin, see :option:`--auth`.

.. describe:: ICAT_USER

    ICAT user name, see :option:`--user`.
