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
      board setup:
        design rules:
          blind/buried via allowed: true
          hole to hole spacing: 678976266
          min track width: 320000
          min uvia diameter: 470000
          min uvia drill size: 120000
          min via diameter: 120000
          min via drill size: 110000
          prohibit courtyard overlap: false
          require courtyards: false
          uvia allowed: true
        layers:
          '# copper layers': 4
          board thickness: 3200000
          enabled:
          - 0
          - 1
          - 2
          - 31
          - 32
          - 33
          - 34
          - 35
          - 36
          - 37
          - 38
          - 39
          - 49
          visible:
          - 0
          - 31
          - 32
          - 33
          - 34
          - 35
          - 36
          - 37
          - 38
          - 39
          - 49
        net classes:
          net class assignments:
            ? ''
            : Default
            Net-(D1-Pad1): new_new_class
            Net-(D1-Pad2): Default
            Net-(R1-Pad2): Default
            Net-(R2-Pad1): new_new_class
          net class definitions:
            Default:
              clearance: 600000
              description: ''
              diff pair gap: 450000
              diff pair width: 400000
              track width: 350000
              uvia diameter: 800000
              uvia drill: 300000
              via diameter: 900000
              via drill: 800000
            new_new_class:
              clearance: 220000
              description: ''
              diff pair gap: 255000
              diff pair width: 150000
              track width: 225000
              uvia diameter: 330000
              uvia drill: 110000
              via diameter: 880000
              via drill: 455000
        solder mask/paste:
          solder mask clearance: 34000
          solder mask min width: 570000
          solder paste clearance: 1
          solder paste clearance ratio: -0.2
        tracks, vias, diff pairs:
          diff pair dimensions list: []
          track width list:
          - 1990000
          - 456000
          via dimensions list:
          - diameter: 480000
            drill: 841000
      modules:
        D1:
          position:
            angle: -120.0
            side: bottom
            x: 172517000
            y: 90297000
        R1:
          position:
            angle: -30.0
            side: top
            x: 161528000
            y: 102248000
        R2:
          position:
            angle: 120.0
            side: top
            x: 166187222
            y: 99187111
        R3:
          position:
            angle: 30.0
            side: bottom
            x: 277187000
            y: 203137000
      plot:
        autoscale: true
        color: null
        coordinate format: 4
        default line width: 150000
        do not tent vias: true
        drill marks: 2
        exclude pcb edge: false
        force a4 output: true
        format: 2
        generate gerber job file: true
        hpgl pen num: 2
        hpgl pen size: 16.0
        hpgl pen speed: 30
        include netlist attributes: true
        layers:
        - 0
        - 1
        - 2
        - 31
        - 34
        - 35
        - 36
        - 37
        - 38
        - 39
        - 44
        mirrored plot: true
        negative plot: true
        output directory: ''
        plot border: true
        plot footprint refs: false
        plot footprint values: false
        plot in outline mode: false
        plot invisible text: true
        plot mode: 1
        plot pads on silk: true
        scale: 2.0
        scaling: 3
        skip npth pads: true
        subtract soldermask from silk: true
        text mode: 2
        track width correction: 1
        use aux axis as origin: true
        use protel filename extensions: true
        use x2 format: true
        x scale factor: 2.0
        y scale factor: 1.2

You don't need to specify every field in order to inject data into a board:
only the fields you want to change are needed.
For example, this YAML file will change the minimum track width to 
0.3 mm (300000 nm) and leave the rest of the board unchanged:

.. code-block:: yaml

    board:
      board setup:
        design rules:
          min track width: 320000


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
