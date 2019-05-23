#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `kinjector` package."""

import json
import pytest
from pcbnew import LoadBoard
from kinjector import kinjector

@pytest.mark.parametrize("brd_in_file, json_in_file, brd_out_file, json_out_file, obj",
        [
            ("test.kicad_pcb",     "ncd_test_in.json",
             "test_out.kicad_pcb", "ncd_test_out.json", kinjector.NetClassDefs()),
            ("test.kicad_pcb",     "nca_test_in.json",
             "test_out.kicad_pcb", "nca_test_out.json", kinjector.NetClassAssigns()),
            ("test.kicad_pcb",     "pp_test_in.json",
             "test_out.kicad_pcb", "pp_test_out.json",  kinjector.PartPositions()),
            ("test.kicad_pcb",     "dr_test_in.json",
             "test_out.kicad_pcb", "dr_test_out.json",  kinjector.DesignRules()),
        ]
    )
def test_inject_eject(brd_in_file, json_in_file, brd_out_file, json_out_file, obj):

    # Inject JSON file into board and store updated board in a new file.
    brd = LoadBoard(brd_in_file)
    with open(json_in_file, 'r') as json_fp:
        json_dict = json.load(json_fp)
    obj.inject(json_dict, brd)
    brd.Save(brd_out_file)

    # Extract info from the updated board and store it in a new JSON file.
    brd = LoadBoard(brd_out_file)
    json_dict = obj.eject(brd)
    with open(json_out_file, 'w') as json_fp:
        json.dump(json_dict, json_fp, indent=4)
