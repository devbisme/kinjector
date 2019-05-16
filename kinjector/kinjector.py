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

from pcbnew import NETCLASSPTR as NCP


class KinJector(object):

    # Named tuple for storing getter/setter functions.
    GetSet = namedtuple('GetSet', ['get', 'set'])


class NetClassDefs(KinJector):
    """Inject/eject net class definitions to/from a KiCad BOARD object."""

    # Associate each JSON net class parameter key with methods for getting/setting
    # it in the board's net class structure.
    key_method_map = {
        'clearance':       KinJector.GetSet(NCP.GetClearance,     NCP.SetClearance),
        'description':     KinJector.GetSet(NCP.GetDescription,   NCP.SetDescription),
        'diff pair gap':   KinJector.GetSet(NCP.GetDiffPairGap,   NCP.SetDiffPairGap),
        'diff pair width': KinJector.GetSet(NCP.GetDiffPairWidth, NCP.SetDiffPairWidth),
        'track width':     KinJector.GetSet(NCP.GetTrackWidth,    NCP.SetTrackWidth),
        'via diameter':    KinJector.GetSet(NCP.GetViaDiameter,   NCP.SetViaDiameter),
        'via drill':       KinJector.GetSet(NCP.GetViaDrill,      NCP.SetViaDrill),
        'uvia diameter':   KinJector.GetSet(NCP.GetuViaDiameter,  NCP.SetuViaDiameter),
        'uvia drill':      KinJector.GetSet(NCP.GetuViaDrill,     NCP.SetuViaDrill),
        }

    @staticmethod
    def inject(json_dict, brd):
        """Inject net class definitions from JSON into a KiCad BOARD object."""

        # Get all net class definitions from the JSON.
        json_netclass_defs = json_dict.get('netclasses', {})

        # Get all the net classes in the board.
        brd_netclasses = brd.GetAllNetClasses()

        # Update existing net classes in the board with new values from JSON
        # or create new net classes.
        for json_netclass_name, json_netclass_params in json_netclass_defs.items():

            # Create a new net class if it doesn't already exist.
            if json_netclass_name not in brd_netclasses:
                brd_netclasses[json_netclass_name] = NCP(json_netclass_name)

            # Point to the parameter structure for the current net class.
            brd_netclass_params = brd_netclasses[json_netclass_name]

            # Update the board's net class parameters with the values from the JSON.
            for key, value in json_netclass_params.items():
                NetClassDefs.key_method_map[key.lower()].set(brd_netclass_params,value)

    @staticmethod
    def eject(brd):
        """Return JSON net class definitions from a KiCad BOARD object."""

        # Extract the parameters for each net class in the board.
        netclass_dict = {}
        for netclass_name, netclass_parameters in brd.GetAllNetClasses().items():
            netclass_dict[str(netclass_name)] = {
                key: method.get(netclass_parameters)
                    for (key, method) in NetClassDefs.key_method_map.items() }

        return {'netclasses': netclass_dict}


class NetClassAssigns(object):
    """Inject/eject net class assignments to/from a KiCad BOARD object."""

    @staticmethod
    def inject(json_dict, brd):
        """Inject net class assignments from JSON into a KiCad BOARD object."""

        # Get the netclass assignment for each net from the JSON.
        json_netclass_assignments = json_dict.get('netclass assignments', {})

        # Get all the nets in the board indexed by net names.
        brd_nets = brd.GetNetInfo().NetsByName()

        # Get all the net classes in the board.
        brd_netclasses = brd.GetAllNetClasses()

        # Assign the JSON nets to the appropriate netclasses in the board.
        for json_net_name, json_net_class_name in json_netclass_assignments.items():
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

    @staticmethod
    def eject(brd):
        """Return JSON net class assignments from a KiCad BOARD object."""

        # Extract the netclass assigned to each net in the board.
        netclass_assignment_dict = {str(net_name):net.GetClassName() for (net_name,net)
                                    in brd.GetNetInfo().NetsByName().items()}

        return {'netclass assignments': netclass_assignment_dict}
