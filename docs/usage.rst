=====
Usage
=====

Command Line
------------

KinJector comes with a command-line script called (appropriately enough) ``kinjector``.
It can be used in two ways:

1. To inject data stored in a JSON or YAML file into a KiCad board file

.. code-block:: console

    $ kinjector -from data.json -to test.kicad_pcb

2. To extract data from a KiCad board file and store it in a JSON or YAML file

.. code-block:: console

    $ kinjector -from test.kicad_pcb -to data.yaml

The data file can contain information on:

* Design rule settings (allowable track widths, via sizes, etc.);
* Enabled board layers and layer visibility;
* Net class definitions;
* Assignments of nets to net classes;
* Plot settings (format, output layers, etc.);
* Part information such as (X,Y) position, angle of orientation, and location on
  the top or bottom side of the PCB.

The easiest way to comprehend the structure of the data is to extract an example
from an existing board and look at the resulting JSON/YAML file as follows:

.. code-block:: yaml

    board:
      modules:
        D1:
          position:
            angle: 304.0
            side: top
            x: 161417004
            y: 99187004
        R1:
          position:
            angle: 122.0
            side: top
            x: 161417002
            y: 102137002
        R2:
          position:
            angle: 147.0
            side: bottom
            x: 166187003
            y: 99187003
        R3:
          position:
            angle: 329.0
            side: bottom
            x: 166187001
            y: 102137001
      settings:
        '# copper layers': 4
        blind/buried via allowed: true
        board thickness: 1600001
        diff pair dimensions list: []
        hole to hole spacing: 0
        netclass assignments:
          ? ''
          : Default
          Net-(D1-Pad1): new_new_class
          Net-(D1-Pad2): Default
          Net-(R1-Pad2): Default
          Net-(R2-Pad1): new_new_class
        netclasses:
          Default:
            clearance: 200001
            description: ''
            diff pair gap: 250001
            diff pair width: 200001
            track width: 250001
            uvia diameter: 300001
            uvia drill: 100001
            via diameter: 800001
            via drill: 400001
          new_new_class:
            clearance: 400001
            description: ''
            diff pair gap: 500001
            diff pair width: 400001
            track width: 500001
            uvia diameter: 600001
            uvia drill: 200001
            via diameter: 1600001
            via drill: 800001
        prohibit courtyard overlap: false
        require courtyards: false
        solder mask margin: 51001
        solder mask min width: 500001
        solder paste margin: 1
        solder paste margin ratio: 0.1
        track min width: 200001
        track width list:
        - 250000
        - 250001
        - 1000001
        - 650001
        uvia allowed: true
        uvia min diameter: 200001
        uvia min drill size: 100001
        via dimensions list:
        - diameter: 800000
          drill: 400000
        - diameter: 800001
          drill: 400001
        via min diameter: 200001
        via min drill size: 300001

You don't need to specify every field in order to inject data into a board:
only the fields you want to change are needed.
For example, this YAML file will change the minimum track width to 
0.3 mm (300000 nm) and leave the rest of the board unchanged:

.. code-block:: yaml

    board:
      settings:
        track min width: 300000


As a Package
------------

To use the KinJector package in a Python project:

.. code-block:: python

    import kinjector

This will give you access to the ``Board`` class that has two methods:

* ``inject(self, data_dict, brd)``: This will inject the data in a dictionary
  into a KiCad ``BOARD`` object.

* ``eject(self, brd)``: This will return a dictionary containing all the data
  that is currently supported from a ``BOARD`` object.

As an example, the code shown below will extract all the data from a KiCad
PCB file and then inject it all back into the same board:

.. code-block:: python

    import json
    import pcbnew
    import kinjector

    # Extract info from a KiCad board and store it in a data file.
    brd = pcbnew.LoadBoard('test.kicad_pcb')
    data_dict = kinjector.Board().eject(brd)
    with open('test.json', 'w') as data_fp:
        json.dump(data_dict, data_fp, indent=4)

    # Inject data from file back into board.
    brd = pcbnew.LoadBoard('test.kicad_pcb')
    with open('test.json', 'r') as data_fp:
        data_dict = json.load(data_fp)
    kinjector.Board().inject(data_dict, brd)
    brd.Save('test_output.kicad_pcb')

You can also inject data into a board using Python dicts.
Just replicate the hierarchical structure and field labels shown above.
