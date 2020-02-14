=======
History
=======


0.0.6 (2020-02-14)
------------------

* yaml.load() will accept a KiCad board file as legal YAML, so place additional checks
  to detect yaml files and prevent over-writing .kicad_pcb files with YAML. 


0.0.5 (2019-06-19)
------------------

* Rearranged hierarchy of board data to more closely reflect KiCad board setup dialog.


0.0.4 (2019-06-10)
------------------

* Added ability to inject/eject plot settings (but not drill settings).


0.0.3 (2019-06-07)
------------------

* Added ability to inject/eject layer enables and visibility.


0.0.2 (2019-05-29)
------------------

* Added ability to inject/eject part (X,Y), orientation, and PCB top/bottom-side.
* Added ability to inject/eject board design rules.
* Now works with both JSON and YAML file formats.
* Unit tests added.
* Command-line tool added.
* Documentation added.


0.0.1 (2019-05-15)
------------------

* First release on PyPI.
