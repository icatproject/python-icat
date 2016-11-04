Hello World!
~~~~~~~~~~~~

The minimal task to start any program environment is to print a simple
message.  The minimal interaction with an ICAT server is to connect to
it and get its version.  We'll combine both in a simple program::

  #! /usr/bin/python

  from __future__ import print_function
  import icat.client
  
  url = "https://icat.example.com:8181/ICATService/ICAT?wsdl"
  client = icat.client.Client(url)
  print("Connect to %s\nICAT version %s" % (url, client.apiversion))

If you run this script, you should get something like the following as
output::

  $ python hello.py
  Connect to https://icat.example.com:8181/ICATService/ICAT?wsdl
  ICAT version 4.7

The constructor of :class:`icat.client.Client` takes the URL of the
ICAT service as argument.  It contacts the ICAT server, queries the
version and stores the result to the attribute :attr:`apiversion` of
the client object.  Obviously, you'll need to change the variable
`url` in this example to point to your ICAT server.

If your ICAT server does not have a trusted SSL certificate you may
get (depending on your Python version) an error instead::

  $ python hello.py
  Traceback (most recent call last):
    ...
  urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:548)>

In this case, you may either install a trusted certificate in your
server now or modify your hello program and add a flag
``checkCert=False`` to the constructor call like this::

  #! /usr/bin/python

  from __future__ import print_function
  import icat.client
  
  url = "https://icat.example.com:8181/ICATService/ICAT?wsdl"
  client = icat.client.Client(url, checkCert=False)
  print("Connect to %s\nICAT version %s" % (url, client.apiversion))

The future statement at the beginning of the example is only needed to
compile `print` as a built-in function rather then a statement.  We'll
use it throughout the tutorial to ensure that the examples will work
with Python 2 as well as with Python 3.

The class :class:`icat.client.Client` plays the central role in
python-icat programs.  Most of your code will deal with objects of
this class.  For this reason, the class is imported by default in the
:mod:`icat` package.  The above example could also be written as::

  #! /usr/bin/python

  from __future__ import print_function
  import icat
  
  url = "https://icat.example.com:8181/ICATService/ICAT?wsdl"
  client = icat.Client(url)
  print("Connect to %s\nICAT version %s" % (url, client.apiversion))

