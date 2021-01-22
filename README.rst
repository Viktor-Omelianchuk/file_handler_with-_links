=======================
Link Parser
=======================


.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
     :target: https://github.com/ambv/black
     :alt: Black code style

:License: MIT

The script allows you to parse the submitted Wikipedia page.
Find links to other Wikipedia pages that exist there, save the content
of these pages to files, as well as the dates of the last changes to the
database and memcache. For correct work script you need to run memcached process

.. contents::

Installation
-------------------
On Unix, Linux, BSD, macOS, and Cygwin::

  $ git clone https://github.com/Viktor-Omelianchuk/link_parser.git

Create and activate isolated Python environments
-------------------------------------------------
::

    $ cd link_parser
    $ virtualenv env
    $ source env/bin/activate

Install requirements
--------------------------------------
::

    $ make install

Run local development FastAPI server
--------------------------------------
List of available endpoints - http://127.0.0.1:8000/docs
::

    $ make run

Run tests
-------------------
::

    $ make test


Check code coverage quickly with the default Python
---------------------------------------------------------
::

    $ make coverage

Remove all build, test, coverage and Python artifacts
---------------------------------------------------------
::

    $ make clean

Arguments and Usage
--------------------------------------
Usage
=====

::

    usage: email_parser [-h] [-f --file] [-l --link] [-n --number-of-links]
                        [-ll --logging-level] [-d --directory]
                        [-mw ---max-workers] [-c --config]


Arguments
=========
Quick reference table
=========================
+---------+----------------------+-------------------------+-------------------------------------+
|Short    |Long                  |Default                  |Description                          |
+---------+----------------------+-------------------------+-------------------------------------+
| ``-h``  |``--help``            |                         |Show help                            |
+---------+----------------------+-------------------------+-------------------------------------+
| ``-l``  |``--link``            |                         |URL link to Wikipedia page           |
+---------+----------------------+-------------------------+-------------------------------------+
|``-ll``  |``--logging-level``   |  "INFO"                 |Level for logging module             |
+---------+----------------------+-------------------------+-------------------------------------+
|``-d``   |``--directory``       |                         |Directory where file will be save    |
+---------+----------------------+-------------------------+-------------------------------------+
|``-n``   |``--number-of-links`` |                         |Number of url links for processing   |
+---------+----------------------+-------------------------+-------------------------------------+
|``-c``   |``--config``          | ../etc/config.ini       |Config file for config parser        |
+---------+----------------------+-------------------------+-------------------------------------+
|``-mw``  |``--max-workers``     |                         |The humber of work threads           |
+---------+----------------------+-------------------------+-------------------------------------+

Examples to use
--------------------------------------
Run script
==================================================
::

    $ cd src
    For multithrading
    $ python link_parser.py -l https://en.wikipedia.org/wiki/Portal:Current_events
    For asyncio
    $ python async_link_parser.py -l https://en.wikipedia.org/wiki/Portal:Current_events


