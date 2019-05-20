#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `kinjector` package."""

import json
import pytest
from pcbnew import LoadBoard
from kinjector import kinjector

@pytest.mark.parametrize("brd_file, json_file, obj",
        [
            ("test.kicad_pcb", "test.json", kinjector.NetClassDefs()),
            ("test.kicad_pcb", "test.json", kinjector.NetClassAssigns()),
            ("test.kicad_pcb", "test.json", kinjector.PartPositions()),
            ("test.kicad_pcb", "test.json", kinjector.DesignRules()),
        ]
    )
def test_eject_inject(brd_file, json_file, obj):

    # Extract info from the board and store it in JSON file.
    brd = LoadBoard(brd_file)
    json_dict = obj.eject(brd)
    with open(json_file, 'w') as json_fp:
        json.dump(json_dict, json_fp, indent=4)

    # Inject JSON file info back into board.
    brd = LoadBoard(brd_file)
    with open(json_file, 'r') as json_fp:
        json_dict = json.load(json_fp)
    obj.inject(json_dict, brd)
    brd.Save(brd.GetFileName())

@pytest.mark.parametrize("brd_file, json_in_file, json_out_file, obj",
        [
            ("test_pos.kicad_pcb", "test_pos_in.json", "test_pos_out.json", kinjector.PartPositions()),
            ("test_dr.kicad_pcb", "test_dr_in.json", "test_dr_out.json", kinjector.DesignRules()),
        ]
    )
def test_inject_eject(brd_file, json_in_file, json_out_file, obj):

    # Inject JSON file into board.
    brd = LoadBoard(brd_file)
    with open(json_in_file, 'r') as json_fp:
        json_dict = json.load(json_fp)
    obj.inject(json_dict, brd)
    brd.Save(brd.GetFileName())

    # Extract info from the board and store it in JSON file.
    brd = LoadBoard(brd_file)
    json_dict = obj.eject(brd)
    with open(json_out_file, 'w') as json_fp:
        json.dump(json_dict, json_fp, indent=4)

    