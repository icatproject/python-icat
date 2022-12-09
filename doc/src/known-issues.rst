Known issues, bugs and limitations
==================================

+ There are issues with ICAT server 4.8.0 and older when using
  suds-community, see `Issue #72`_ for details.  Use suds-jurko when
  you need to talk to those older ICAT servers.  See also the Section
  on :ref:`Suds` in the install instructions.

+ If supported by the ICAT server (icat.server 4.9.0 and newer), the
  icat.config module queries the server for information on available
  authenticators and the credential keys they require for login.  The
  configuration variables for these keys are then adapted accordingly.
  Therefore, the set of configuration variables depends on the ICAT
  server and the available authentication plugins.  But the help
  message displayed by the `--help` command line option is static.  As
  a result, this help message is not always accurate.  When connecting
  to a specific ICAT service, it may happen that different
  configuration variables and thus command line arguments are
  effective then those shown by the generic help message.

+ The return value of the `formal string representation operator`__ of
  :class:`icat.query.Query` can not be used to recreate another query
  object with the same value as required by Python standards, see
  `Issue #94`_ for details.

+ The entries in the no_proxy configuration variable are matched
  against the host part of the URL by simple string comparison.  The
  host is excluded from proxy use if its name ends with any item in
  no_proxy.  It is not checked whether the matching part starts with a
  domain component.  E.g. setting no_proxy=ion.example.org will not
  only exclude icat.ion.example.org, but also lion.example.org,
  although the latter is not in the ion.example.org domain.  IP
  addresses are not supported in no_proxy.  This is a limitation in
  the implementation of the underlying Python library.


.. __: https://docs.python.org/3/reference/datamodel.html#object.__repr__
.. _Issue #72: https://github.com/icatproject/python-icat/issues/72
.. _Issue #94: https://github.com/icatproject/python-icat/issues/94
