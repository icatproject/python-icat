:mod:`icat.config` --- Manage configuration
===========================================

.. py:module:: icat.config

This module reads configuration variables from different sources, such
as command line arguments, environment variables, and configuration
files.  A set of configuration variables that any ICAT client program
typically needs is predefined.  Custom configuration variables may be
added.  The main class that client programs interact with is
:class:`icat.config.Config`.

.. data:: icat.config.cfgdirs

    Search path for the configuration file.  The value depends on the
    operating system.

.. autodata:: icat.config.cfgfile

.. autodata:: icat.config.defaultsection

.. autofunction:: icat.config.boolean

.. data:: icat.config.flag

    Variant of :func:`icat.config.boolean` that defines two command
    line arguments to switch the value on and off respectively.  May
    be passed as type to :meth:`icat.config.Config.add_variable`.

.. autofunction:: icat.config.cfgpath

.. autoclass:: icat.config.Configuration
    :members:
    :show-inheritance:

.. autoclass:: icat.config.Config
    :members:
    :show-inheritance:


Predefined configuration variables
----------------------------------

The constructor of :class:`icat.config.Config` sets up the following
set of configuration variables that an ICAT client typically needs:

  `configFile`
    Name of the configuration file to read.

  `configSection`
    Name of the section in the configuration file to apply.  If
    not set, no values will be read from the configuration file.

  `url`
    URL to the web service description of the ICAT server.

  `idsurl`
    URL to the ICAT Data Service.

  `checkCert`
    Verify the server certificate for HTTPS connections.
    Note that this requires either Python 2.7.9 or 3.2 or newer.
    With older Python version, this option has no effect.

  `http_proxy`
    Proxy to use for HTTP requests.

  `https_proxy`
    Proxy to use for HTTPS requests.

  `no_proxy`
    Comma separated list of domain extensions proxy should not be
    used for.

  `auth`
    Name of the authentication plugin to use for login.

  `username`
    The ICAT user name.

  `password`
    The user's password.  Will prompt for the password if not set.

  `promptPass`
    Prompt for the password.

A few derived variables are also set in
:meth:`icat.config.Config.getconfig`:

  `configDir`
    the directory where (the last) configFile has been found.

  `client_kwargs`
    contains the proxy settings and other configuration that should be
    passed as the keyword arguments to the constructor of
    :class:`icat.client.Client`.

  `credentials`
    contains username and password suitable to be passed to
    :meth:`icat.client.Client.login`.

.. deprecated:: 0.13
   The derived variable `configDir` is deprecated and will be removed
   in version 1.0.

The command line arguments, environment variables, and default values
for the configuration variables are as follows:

+-----------------+-----------------------------+-----------------------+----------------+-----------+
| name            | command line                | environment           | default        | mandatory |
+=================+=============================+=======================+================+===========+
| `configFile`    | ``-c``, ``--configfile``    | ``ICAT_CFG``          | depends        | no        |
+-----------------+-----------------------------+-----------------------+----------------+-----------+
| `configSection` | ``-s``, ``--configsection`` | ``ICAT_CFG_SECTION``  | :const:`None`  | no        |
+-----------------+-----------------------------+-----------------------+----------------+-----------+
| `url`           | ``-w``, ``--url``           | ``ICAT_SERVICE``      |                | yes       |
+-----------------+-----------------------------+-----------------------+----------------+-----------+
| `idsurl`        | ``--idsurl``                | ``ICAT_DATA_SERVICE`` | :const:`None`  | depends   |
+-----------------+-----------------------------+-----------------------+----------------+-----------+
| `checkCert`     | ``--check-certificate``,    |                       | :const:`True`  | no        |
|                 | ``--no-check-certificate``  |                       |                |           |
+-----------------+-----------------------------+-----------------------+----------------+-----------+
| `http_proxy`    | ``--http-proxy``            | ``http_proxy``        | :const:`None`  | no        |
+-----------------+-----------------------------+-----------------------+----------------+-----------+
| `https_proxy`   | ``--https-proxy``           | ``https_proxy``       | :const:`None`  | no        |
+-----------------+-----------------------------+-----------------------+----------------+-----------+
| `no_proxy`      | ``--no-proxy``              | ``no_proxy``          | :const:`None`  | no        |
+-----------------+-----------------------------+-----------------------+----------------+-----------+
| `auth`          | ``-a``, ``--auth``          | ``ICAT_AUTH``         |                | yes       |
+-----------------+-----------------------------+-----------------------+----------------+-----------+
| `username`      | ``-u``, ``--user``          | ``ICAT_USER``         |                | yes       |
+-----------------+-----------------------------+-----------------------+----------------+-----------+
| `password`      | ``-p``, ``--pass``          |                       | :const:`None`  | no        |
+-----------------+-----------------------------+-----------------------+----------------+-----------+
| `promptPass`    | ``-P``, ``--prompt-pass``   |                       | :const:`False` | no        |
+-----------------+-----------------------------+-----------------------+----------------+-----------+

Mandatory means that an error will be raised in
:meth:`icat.config.Config.getconfig` if no value is found for the
configuration variable in question.

The default value for `configFile` depends on the operating system.
The default value for `configSection` may be changed in
:data:`icat.config.defaultsection`.

If the argument `needlogin` to the constructor of
:class:`icat.config.Config` is set to :const:`False`, the
configuration variables `auth`, `username`, `password`, `promptPass`,
and `credentials` will be left out.  The configuration variable
`idsurl` will not be set up at all, or be set up as a mandatory, or as
an optional variable, if the `ids` argument is set to :const:`False`,
to "mandatory", or to "optional" respectively.

The method :meth:`icat.config.Config.getconfig` will prompt the user
for a password if `promptPass` is :const:`True`, if `password` is
:const:`None`, or if the `username`, but not the `password` has been
provided by command line arguments.
