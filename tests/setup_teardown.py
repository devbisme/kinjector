import json

import yaml


def setup():
    """Convert JSON input files into equivalent YAML input files."""

    for filename_stub in ["ncd", "nca", "dr", "brd"]:
        with open(filename_stub + "_test_in.json", "r") as json_fp:
            data_dict = json.load(json_fp)
            with open(filename_stub + "_test_in.yaml", "w") as yaml_fp:
                yaml.safe_dump(data_dict, yaml_fp, default_flow_style=False)
