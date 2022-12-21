.. _icatdump:

icatdump
========


Synopsis
~~~~~~~~

**icatdump** [*standard options*] [-o FILE] [-f FORMAT]


Description
~~~~~~~~~~~

.. program:: icatdump

This script queries the content from an ICAT server and serializes it
into a flat file.  The format of that file depends on the version of
the ICAT server and the backend that can be selected with the
:option:`--format` option.


Options
~~~~~~~

.. program:: icatdump

The configuration options may be set in the command line or in a
configuration file.  Some options may also be set in the environment.


Specific Options
................

The following options are specific to icatdump:

.. program:: icatdump

.. option:: -o FILE, --outputfile FILE

    Set the output file name.  If the value `-` is used, the output
    will be written to standard output.  This is also the default.

.. option:: -f FORMAT, --format FORMAT

    Select the backend to use and thus the output file format.  XML
    and YAML backends are available.


Standard Options
................

The following options needed to connect the ICAT service are common
for most python-icat scripts:

.. program:: icatdump

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


Known Issues and Limitations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* IDS is not supported: the script only dumps the meta data stored in
  the ICAT, not the content of the files stored in the IDS.

* The output will only contain objects that the user connecting ICAT
  has read permissions for.  The script may need to connect as the
  ICAT root user in order to get the full content.

* The following items are deliberately not included in the output:

  + Log objects (ICAT server versions older then 4.7.0),
  + The attributes :attr:`~icat.entity.Entity.id`,
    :attr:`~icat.entity.Entity.createId`,
    :attr:`~icat.entity.Entity.createTime`,
    :attr:`~icat.entity.Entity.modId`, and
    :attr:`~icat.entity.Entity.modTime` of any object.

* It is assumed that for each Dataset `ds` in the ICAT where
  `ds.sample` is not NULL, the condition `ds.investigation =
  ds.sample.investigation` holds.  If this is not satisfied, the
  script will fail with a :exc:`~icat.exception.DataConsistencyError`.

* The partition of the data into chunks is static.  It should rather
  be dynamic, e.g. chunks should be splitted if the number of objects
  in them grows too large.

* The content in the ICAT server must not be modified while this
  script is retrieving it.  Otherwise the script may fail or the
  dumpfile be inconsistent.

* The script fails if the ICAT server is older then 4.6.0 and the data
  contains any `Study`.  This is a `bug in icat.server`__.

.. __: https://github.com/icatproject/icat.server/issues/155


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


See also
~~~~~~~~

.. only:: not man

    * Section :ref:`ICAT-data-files` on the structure of the dump files.
    * Section :ref:`standard-config-vars` on the standard options.
    * The :ref:`icatingest` script.

.. only:: man

    :manpage:`icatingest(1)`
