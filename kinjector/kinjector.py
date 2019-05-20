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

from pcbnew import NETCLASSPTR as NCP, F_Cu, B_Cu, wxPoint


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

    def inject(self, json_dict, brd):
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
                self.key_method_map[key.lower()].set(brd_netclass_params,value)

    def eject(self, brd):
        """Return JSON net class definitions from a KiCad BOARD object."""

        # Extract the parameters for each net class in the board.
        netclass_dict = {}
        for netclass_name, netclass_parameters in brd.GetAllNetClasses().items():
            netclass_dict[str(netclass_name)] = {
                key: method.get(netclass_parameters)
                    for (key, method) in self.key_method_map.items() }

        return {'netclasses': netclass_dict}


class NetClassAssigns(KinJector):
    """Inject/eject net class assignments to/from a KiCad BOARD object."""

    def inject(self, json_dict, brd):
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

    def eject(self, brd):
        """Return JSON net class assignments from a KiCad BOARD object."""

        # Extract the netclass assigned to each net in the board.
        netclass_assignment_dict = {str(net_name):net.GetClassName() for (net_name,net)
                                    in brd.GetNetInfo().NetsByName().items()}

        return {'netclass assignments': netclass_assignment_dict}


class PartsByRef(KinJector):
    """Inject/eject data to/from parts in a KiCad BOARD object by part reference."""

    def __init__(self):
        super(PartsByRef,self).__init__()
        part_class = None
        json_key = None

    @staticmethod
    def get_id(module):
        return module.GetReference()

    def inject(self, json_dict, brd):
        """Inject data from JSON into parts of a KiCad BOARD object."""

        # Get all the parts in the board indexed by references.
        brd_parts = {self.get_id(m):m for m in brd.GetModules()}

        # Assign the data in the JSON to the parts on the board.
        for json_part_ref, json_part_data in json_dict[self.json_key].items():

            # Check to see if the part from the JSON file exists on the board.
            try:
                brd_part = brd_parts[json_part_ref]
            except IndexError:
                continue # Should we signal an error for a missing part?

            self.part_class.inject(json_part_data, brd_part)

    def eject(self, brd):
        """Return JSON part data from parts in a KiCad BOARD object."""

        # Get all the parts in the board indexed by references.
        brd_parts = {self.get_id(m):m for m in brd.GetModules()}

        # Extract the data from each part on the board.
        part_data_dict = {part_ref:self.part_class.eject(part) for (part_ref, part)
                                    in brd_parts.items()}

        return {self.json_key: part_data_dict}


class PartPosition(KinJector):
    """Inject/eject part (X,Y), rotation, front/back to/from a KiCad MODULE object."""

    # Index top and bottom of boards by their layer number in PCBNEW.
    top_btm = {F_Cu: 'top', B_Cu: 'bottom'}

    def inject(self, json_dict, module):
        """Inject part position from JSON into a KiCad MODULE object."""

        # Set the (X,Y) position.
        try:
            module.SetPosition(wxPoint(json_dict['x'], json_dict['y']))
        except IndexError:
            pass # No (X,Y) data, so skip it.

        # Set the orientation (in degrees).
        try:
            module.SetOrientationDegrees(json_dict['angle'])
        except IndexError:
            pass # No angle data, so skip it.
        
        # Set whether the board is on the top or bottom side of the PCB.
        module_side = self.top_btm[module.GetLayer()]
        try:
            if module_side != json_dict['side'].lower():
                module.Flip(module.GetPosition())
        except IndexError:
            pass # No top-side/bottom-side data, so skip it.

    def eject(self, module):
        """Return JSON part position from a KiCad MODULE object."""

        pos = module.GetPosition()
        return { 
            'x': pos.x, 'y': pos.y,
            'angle': module.GetOrientationDegrees(),
            'side': self.top_btm[module.GetLayer()],
        }


class PartPositions(PartsByRef):
    """Inject/eject part (X,Y), rotation, front/back to/from a KiCad BOARD object."""

    PartsByRef.part_class = PartPosition()
    PartsByRef.json_key = 'part positions'

class DesignRules(KinJector):
    """Inject/eject board design rules to/from a KiCad BOARD object."""

    def inject(self, json_dict, brd):
        """Inject design rule settings from JSON into a KiCad BOARD object."""

        # Get the design rule settings from the JSON.
        json_drs = json_dict.get('design rules', {})

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings();

        try:
            brd_drs.SetBoardThickness(json_drs['board thickness'])
        except KeyError:
            pass

        try:
            brd_drs.SetCopperLayerCount(json_drs['# copper layers'])
        except KeyError:
            pass

        try:
            brd_drs.m_HoleToHoleMin = json_drs['hole to hole spacing']
        except KeyError:
            pass

        try:
            brd_drs.m_ProhibitOverlappingCourtyards = json_drs['prohibit courtyard overlap']
        except KeyError:
            pass

        try:
            brd_drs.m_RequireCourtyards = json_drs['require courtyards']
        except KeyError:
            pass

        try:
            brd_drs.m_MicroViasAllowed = json_drs['uvia allowed']
        except KeyError:
            pass

        try:
            brd_drs.m_MicroViasMinDrill = json_drs['uvia min drill size']
        except KeyError:
            pass

        try:
            brd_drs.m_MicroViasMinSize = json_drs['uvia min diameter']
        except KeyError:
            pass

        try:
            brd_drs.m_ViasMinDrill = json_drs['via min drill size']
        except KeyError:
            pass

        try:
            brd_drs.m_ViasMinSize = json_drs['via min diameter']
        except KeyError:
            pass

        try:
            brd_drs.m_TrackMinWidth = json_drs['track min width']
        except KeyError:
            pass

        # Load the updated design rules back into the board.
        brd.SetDesignSettings(brd_drs)

    def eject(self, brd):
        """Return JSON design rule settings from a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings();

        return {
            'design rules': {
                'board thickness': brd_drs.GetBoardThickness(),
                '# copper layers': brd_drs.GetCopperLayerCount(),
                'hole to hole spacing': brd_drs.m_HoleToHoleMin,
                'prohibit courtyard overlap': brd_drs.m_ProhibitOverlappingCourtyards,
                'require courtyards': brd_drs.m_RequireCourtyards,
                'uvia allowed': brd_drs.m_MicroViasAllowed,
                'uvia min drill size': brd_drs.m_MicroViasMinDrill,
                'uvia min diameter': brd_drs.m_MicroViasMinSize,
                'via min drill size': brd_drs.m_ViasMinDrill,
                'via min diameter': brd_drs.m_ViasMinSize,
                'track min width': brd_drs.m_TrackMinWidth,
            }
        }
