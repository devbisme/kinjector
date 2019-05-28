"""Tests for `kinjector` package."""

import json
import yaml
import pytest
from pcbnew import LoadBoard
from kinjector import kinjector
from .setup_teardown import *  # This creates YAML test files from the JSON files.


@pytest.mark.parametrize("brd_file, data_file, obj", [
    ("test", "ncd_test", kinjector.NetClassDefs()),
    ("test", "nca_test", kinjector.NetClassAssigns()),
    ("test", "dr_test", kinjector.DesignRules()),
    ("test", "brd_test", kinjector.Board()),
])
def test_inject_eject(brd_file, data_file, obj):
    """Test data injection and ejection to/from a KiCad board file."""

    # Test injection/ejection using both JSON and YAML data formats.
    for ext, load, load_kw, dump, dump_kw in [
        ['.json', json.load, {}, json.dump, {
            'indent': 4
        }],
        [
            '.yaml', yaml.load, {
                'Loader': yaml.Loader
            }, yaml.safe_dump, {
                'default_flow_style': False
            }
        ],
    ]:
        # Inject file data into board and store updated board in a new file.
        brd = LoadBoard(brd_file + '.kicad_pcb')
        with open(data_file + '_in' + ext, 'r') as data_fp:
            data_dict = load(data_fp, **load_kw)
        obj.inject(data_dict, brd)
        brd.Save(brd_file + '_out.kicad_pcb')

        # Extract info from the updated board and store it in a new data file.
        brd = LoadBoard(brd_file + '_out.kicad_pcb')
        data_dict = obj.eject(brd)
        with open(data_file + '_out' + ext, 'w') as data_fp:
            dump(data_dict, data_fp, **dump_kw)
