#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `kinjector` package."""

import json
import pytest
from pcbnew import LoadBoard
from kinjector import kinjector

@pytest.mark.parametrize("brd_file, json_file, inject, eject",
        [
            ("test.kicad_pcb", "test.json", kinjector.NetClassDefs.inject, kinjector.NetClassDefs.eject),
            ("test.kicad_pcb", "test.json", kinjector.NetClassAssigns.inject, kinjector.NetClassAssigns.eject),
        ]
    )
def test_inject_eject(brd_file, json_file, inject, eject):

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
