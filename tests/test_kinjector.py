#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `kinjector` package."""

import json
import pytest
from pcbnew import LoadBoard
from kinjector import kinjector

@pytest.mark.parametrize("brd_file, json_file, eject, inject",
        [
            ("test.kicad_pcb", "test.json", kinjector.NetClassDefs.eject, kinjector.NetClassDefs.inject),
            ("test.kicad_pcb", "test.json", kinjector.NetClassAssigns.eject, kinjector.NetClassAssigns.inject),
            ("test.kicad_pcb", "test.json", kinjector.PartPositions.eject, kinjector.PartPositions.inject),
        ]
    )
def test_eject_inject(brd_file, json_file, eject, inject):

    # Extract info from the board and store it in JSON file.
    brd = LoadBoard(brd_file)
    json_dict = eject(brd)
    with open(json_file, 'w') as json_fp:
        json.dump(json_dict, json_fp, indent=4)

    # Inject JSON file info back into board.
    brd = LoadBoard(brd_file)
    with open(json_file, 'r') as json_fp:
        json_dict = json.load(json_fp)
    inject(json_dict, brd)
    brd.Save(brd.GetFileName())

@pytest.mark.parametrize("brd_file, json_file, inject, eject",
        [
            ("test_pos.kicad_pcb", "test_pos.json", kinjector.PartPositions.inject, kinjector.PartPositions.eject),
        ]
    )
def test_inject_eject(json_file, brd_file, inject, eject):

    # Inject JSON file into board.
    brd = LoadBoard(brd_file)
    with open(json_file, 'r') as json_fp:
        json_dict = json.load(json_fp)
    inject(json_dict, brd)
    brd.Save(brd.GetFileName())

    # Extract info from the board and store it in JSON file.
    brd = LoadBoard(brd_file)
    json_dict = eject(brd)
    with open(json_file, 'w') as json_fp:
        json.dump(json_dict, json_fp, indent=4)

    