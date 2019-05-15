# MIT license
# 
# Copyright (C) 2019 by XESS Corp.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import copy
import json
from collections import namedtuple

from pcbnew import GetBoard, LoadBoard, NETCLASSPTR as NCP

# Associate each JSON net class parameter key with methods for getting/setting
# parameters in the board's net class structure.
GetSet = namedtuple('GetSet', ['get', 'set']) 
key_method_map = {
    'clearance':       GetSet(NCP.GetClearance,     NCP.SetClearance),
    'description':     GetSet(NCP.GetDescription,   NCP.SetDescription),
    'diff pair gap':   GetSet(NCP.GetDiffPairGap,   NCP.SetDiffPairGap),
    'diff pair width': GetSet(NCP.GetDiffPairWidth, NCP.SetDiffPairWidth),
    'track width':     GetSet(NCP.GetTrackWidth,    NCP.SetTrackWidth),
    'via diameter':    GetSet(NCP.GetViaDiameter,   NCP.SetViaDiameter),
    'via drill':       GetSet(NCP.GetViaDrill,      NCP.SetViaDrill),
    'uvia diameter':   GetSet(NCP.GetuViaDiameter,  NCP.SetuViaDiameter),
    'uvia drill':      GetSet(NCP.GetuViaDrill,     NCP.SetuViaDrill),
    }

def kinject(json_file, brd_file):
    """Inject net class assignments from a JSON file into a KiCad PCB file."""

    # Get the net-netclass assignments from the JSON file.
    with open(json_file, 'r') as json_fp:
        json_dict = json.load(json_fp)

    # Get all netclass definitions and net/netclass assignments.
    json_netclass_defs = json_dict.get('netclasses', {})
    json_net_netclasses = json_dict.get('net netclasses', {})

    # Create a dict with all the nets in the board indexed by net name.
    brd = LoadBoard(brd_file)
    brd_nets = brd.GetNetInfo().NetsByName()

    # Get all the netclasses in the board.
    brd_netclasses = brd.GetAllNetClasses()

    # Update existing net classes in the board with new values from JSON file
    # or create new net classes.
    for json_netclass_name, json_netclass_params in json_netclass_defs.items():

        # Create a new net class if it doesn't already exist.
        if json_netclass_name not in brd_netclasses:
            brd_netclasses[json_netclass_name] = NCP(json_netclass_name)

        # Get the parameter structure for the net class.
        brd_netclass_params = brd_netclasses[json_netclass_name]

        # Update the board's net class structure with the values from the JSON file.
        for key, value in json_netclass_params.items():
            key_method_map[key.lower()].set(brd_netclass_params,value)

    # Assign the JSON nets to the appropriate netclasses in the board.
    for json_net_name, json_net_class_name in json_net_netclasses.items():
        # Check to see if the net from the JSON file exists in the board.
        try:
            brd_net = brd_nets[json_net_name]
        except IndexError:
            continue # Should we signal an error for a missing net?

        # Remove the net from its old net class and assign it to the new class.
        old_net_class = brd_netclasses[brd_net.GetClassName()]
        old_net_class.NetNames().discard(json_net_name)
        new_net_class = brd_netclasses[json_net_class_name]
        new_net_class.NetNames().add(json_net_name)
        brd_net.SetClass(new_net_class)

    # Save the board with the updated net-netclass assignments.
    brd.Save(brd.GetFileName())

def keject(brd_file, json_file):
    """Extract net class assignments from a KiCad PCB file into a JSON file."""

    brd = LoadBoard(brd_file)

    # Extract the parameters for each net class in the board.
    netclass_dict = {}
    for netclass_name, netclass_parameters in brd.GetAllNetClasses().items():
        netclass_dict[str(netclass_name)] = {
            key: method.get(netclass_parameters)
                for (key, method) in key_method_map.items() }

    # Extract the netclass assigned to each net in the board.
    net_netclass_dict = {str(net_name):net.GetClassName() for (net_name,net)
                                in brd.GetNetInfo().NetsByName().items()}

    json_dict = {'netclasses': netclass_dict, 'net netclasses': net_netclass_dict}

    with open(json_file, 'w') as json_fp:
        json.dump(json_dict, json_fp, indent=4)
