
Why Diesel?
===========

You should write your next network application using diesel_.

Thanks to Python_ the syntax is clean and the development pace is rapid. Thanks
to non-blocking I/O it's fast and scalable. Thanks to greenlets_ there's
unwind(to(callbacks(no))). Thanks to nose_ it's trivial to test. Thanks to
Werkzeug_ you don't need to write a new web framework using it.

It provides a clean API for writing network clients and servers. TCP and UDP
supported. It bundles battle-tested clients for HTTP, DNS, Redis, Riak and
MongoDB. It makes writing network applications fun.

Read the documentation, browse the API and join the community in #diesel on
freenode.

Prerequisites
=============

You'll need the `python3-dev` package as well as `libffi-dev`, or your
platform's equivalents (required by `cryptography` package).

Installation
============

Diesel is an active project. Your best bet to stay up with the latest at this
point is to clone from github.::

    $ git clone https://github.com/byrgazov/diesel

Once you have a clone, `cd` to the `diesel` directory and install it.::

    $ virtualenv --python=python3 --no-setuptools .venv
    $ .venv/bin/pip install -U pip setuptools
    $ .venv/bin/pip install -U zc.buildout
    $ .venv/bin/buildout
    $ bin/dnosetests
    $ bin/dconsole dummy   # [terminal 1]
    $ bin/dconsole <pid>   # [terminal 2]
    $ bin/python examples/santa.py
    $ bin/python examples/udp_echo.py server   # [terminal 1]
    $ bin/python examples/udp_echo.py client   # [terminal 2]
    $ bin/python examples/http.py
    # ...
    # profit


.. _Python: http://www.python.org/
.. _greenlets: http://readthedocs.org/docs/greenlet/en/latest/
.. _nose: http://readthedocs.org/docs/nose/en/latest/
.. _Werkzeug: https://palletsprojects.com/p/werkzeug/
