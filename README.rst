=========
KinJector
=========


.. image:: https://img.shields.io/pypi/v/kinjector.svg
        :target: https://pypi.python.org/pypi/kinjector


Inject/eject JSON/YAML data to/from KiCad Board files.


* Free software: MIT license
* Documentation: https://xesscorp.github.io/kinjector.docs/_site/index.html .


Features
--------

* Parameters in one or more JSON or YAML files can be injected into a 
  KiCad PCB file.
* Parameters from a KiCad PCB file can be extracted and stored in a
  JSON or YAML file.
* The currently-supported set of parameters can control the design rules, net classes,
  assignment of netclasses to particular nets, and (X,Y)/orientation/top-bottom-side
  position of part footprints.
* Subsets of parameters can be used to restrict the scope of effects upon the PCB.
* A script is provided to allow injection/ejection of JSON/YAML data to/from
  a KiCad PCB file. In addition, the ``kinjector`` module can be used within
  other Python scripts to manipulate KiCad PCB files.
