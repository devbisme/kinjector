.. highlight:: shell

============
Installation
============

KinJector needs KiCad's ``pcbnew`` Python module to run.
For this reason, you'll probably want to install it in KiCad's Python environment.
Under Windows, you can do this by opening a terminal and issuing the command:

.. code-block:: console

    $ set path=C:\Program Files\kicad\bin;%path%

Then to install KinJector, run this command in your terminal:

.. code-block:: console

    $ pip install kinjector

This is the preferred method to install KinJector, as it will always install the most recent stable release.
However, if you want the latest features *before* a stable release is made, you can get
that with this command:

.. code-block:: console

    $ pip install git+https://github.com/xesscorp/kinjector
