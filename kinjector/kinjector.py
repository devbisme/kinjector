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

from pcbnew import (NETCLASSPTR as NCP, F_Cu, B_Cu, wxPoint, intVector,
                    VIA_DIMENSION, VIA_DIMENSION_Vector, DIFF_PAIR_DIMENSION,
                    DIFF_PAIR_DIMENSION_swigregister)


class KinJector(object):

    # Named tuple for storing getter/setter functions.
    GetSet = namedtuple('GetSet', ['get', 'set'])


class NetClassDefs(KinJector):
    """Inject/eject net class definitions to/from a KiCad BOARD object."""

    # Associate each net class parameter key with methods for getting/setting
    # it in the board's net class structure.
    key_method_map = {
        'clearance':
        KinJector.GetSet(NCP.GetClearance, NCP.SetClearance),
        'description':
        KinJector.GetSet(NCP.GetDescription, NCP.SetDescription),
        'diff pair gap':
        KinJector.GetSet(NCP.GetDiffPairGap, NCP.SetDiffPairGap),
        'diff pair width':
        KinJector.GetSet(NCP.GetDiffPairWidth, NCP.SetDiffPairWidth),
        'track width':
        KinJector.GetSet(NCP.GetTrackWidth, NCP.SetTrackWidth),
        'via diameter':
        KinJector.GetSet(NCP.GetViaDiameter, NCP.SetViaDiameter),
        'via drill':
        KinJector.GetSet(NCP.GetViaDrill, NCP.SetViaDrill),
        'uvia diameter':
        KinJector.GetSet(NCP.GetuViaDiameter, NCP.SetuViaDiameter),
        'uvia drill':
        KinJector.GetSet(NCP.GetuViaDrill, NCP.SetuViaDrill),
    }

    def inject(self, data_dict, brd):
        """Inject net class definitions from data dict into a KiCad BOARD object."""

        # Get all net class definitions from the data dict.
        data_netclass_defs = data_dict.get('netclasses', {})

        # Get all the net classes in the board.
        brd_netclasses = brd.GetAllNetClasses()

        # Update existing net classes in the board with new values from data
        # or create new net classes.
        for data_netclass_name, data_netclass_params in data_netclass_defs.items(
        ):

            # Create a new net class if it doesn't already exist.
            if data_netclass_name not in brd_netclasses:
                brd_netclasses[data_netclass_name] = NCP(data_netclass_name)

            # Point to the parameter structure for the current net class.
            brd_netclass_params = brd_netclasses[data_netclass_name]

            # Update the board's net class parameters with the values from the data dict.
            for key, value in data_netclass_params.items():
                self.key_method_map[key.lower()].set(brd_netclass_params,
                                                     value)

    def eject(self, brd):
        """Return net class definitions as a dict from a KiCad BOARD object."""

        # Extract the parameters for each net class in the board.
        netclass_dict = {}
        for netclass_name, netclass_parameters in brd.GetAllNetClasses().items(
        ):
            netclass_dict[str(netclass_name)] = {
                key: method.get(netclass_parameters)
                for (key, method) in self.key_method_map.items()
            }

        return {'netclasses': netclass_dict}


class NetClassAssigns(KinJector):
    """Inject/eject net class assignments to/from a KiCad BOARD object."""

    def inject(self, data_dict, brd):
        """Inject net class assignments from data_dict into a KiCad BOARD object."""

        # Get the netclass assignment for each net from the data dict.
        data_netclass_assignments = data_dict.get('netclass assignments', {})

        # Get all the nets in the board indexed by net names.
        brd_nets = brd.GetNetInfo().NetsByName()

        # Get all the net classes in the board.
        brd_netclasses = brd.GetAllNetClasses()

        # Assign the JSON nets to the appropriate netclasses in the board.
        for data_net_name, data_net_class_name in data_netclass_assignments.items(
        ):
            # Check to see if the net from the data dict exists in the board.
            try:
                brd_net = brd_nets[data_net_name]
            except IndexError:
                continue  # Should we signal an error for a missing net?

            # Remove the net from its old net class and assign it to the new class.
            old_net_class = brd_netclasses[brd_net.GetClassName()]
            old_net_class.NetNames().discard(data_net_name)
            new_net_class = brd_netclasses[data_net_class_name]
            new_net_class.NetNames().add(data_net_name)
            brd_net.SetClass(new_net_class)

    def eject(self, brd):
        """Return net class assignments as a dict from a KiCad BOARD object."""

        # Extract the netclass assigned to each net in the board.
        netclass_assignment_dict = {
            str(net_name): net.GetClassName()
            for (net_name, net) in brd.GetNetInfo().NetsByName().items()
        }

        return {'netclass assignments': netclass_assignment_dict}


class PartsByRef(KinJector):
    """Inject/eject data to/from parts in a KiCad BOARD object by part reference."""

    def __init__(self):
        super(PartsByRef, self).__init__()
        part_class = None
        data_key = None

    @staticmethod
    def get_id(module):
        return str(module.GetReference())

    def inject(self, data_dict, brd):
        """Inject data from data_dict into parts of a KiCad BOARD object."""

        # Get all the parts in the board indexed by references.
        brd_parts = {self.get_id(m): m for m in brd.GetModules()}

        # Assign the data in the data_dict to the parts on the board.
        for data_part_ref, data_part_data in data_dict[self.data_key].items():

            # Check to see if the part from the data dict exists on the board.
            try:
                brd_part = brd_parts[data_part_ref]
            except IndexError:
                continue  # Should we signal an error for a missing part?

            self.part_class.inject(data_part_data, brd_part)

    def eject(self, brd):
        """Return part data from parts as a dict in a KiCad BOARD object."""

        # Get all the parts in the board indexed by references.
        brd_parts = {self.get_id(m): m for m in brd.GetModules()}

        # Extract the data from each part on the board.
        part_data_dict = {
            part_ref: self.part_class.eject(part)
            for (part_ref, part) in brd_parts.items()
        }

        return {self.data_key: part_data_dict}


class PartPosition(KinJector):
    """Inject/eject part (X,Y), rotation, front/back to/from a KiCad MODULE object."""

    # Index top and bottom of boards by their layer number in PCBNEW.
    top_btm = {F_Cu: 'top', B_Cu: 'bottom'}

    def inject(self, data_dict, module):
        """Inject part position from data_dict into a KiCad MODULE object."""

        # Set the (X,Y) position.
        try:
            module.SetPosition(wxPoint(data_dict['x'], data_dict['y']))
        except IndexError:
            pass  # No (X,Y) data, so skip it.

        # Set the orientation (in degrees).
        try:
            module.SetOrientationDegrees(data_dict['angle'])
        except IndexError:
            pass  # No angle data, so skip it.

        # Set whether the board is on the top or bottom side of the PCB.
        module_side = self.top_btm[module.GetLayer()]
        try:
            if module_side != data_dict['side'].lower():
                module.Flip(module.GetPosition())
        except IndexError:
            pass  # No top-side/bottom-side data, so skip it.

    def eject(self, module):
        """Return part position as a dict from a KiCad MODULE object."""

        pos = module.GetPosition()
        return {
            'x': pos.x,
            'y': pos.y,
            'angle': module.GetOrientationDegrees(),
            'side': self.top_btm[module.GetLayer()],
        }


class PartPositions(PartsByRef):
    """Inject/eject part (X,Y), rotation, front/back to/from a KiCad BOARD object."""

    PartsByRef.part_class = PartPosition()
    PartsByRef.data_key = 'part positions'


class TrackWidths(KinJector):
    """Inject/eject track widths to/from a KiCad board object."""

    def inject(self, data_dict, brd):
        """Inject track widths from JSON into a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        try:
            # The first track width never seems to change, so just inject the
            # list of track widths after that.
            brd_drs.m_TrackWidthList = intVector([
                0,
            ] + data_dict['track width list'])
        except KeyError:
            pass

        # Load the updated track widths back into the board.
        brd.SetDesignSettings(brd_drs)

    def eject(self, brd):
        """Return JSON track widths from a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        return {'track width list': [w for w in brd_drs.m_TrackWidthList]}


class ViaDimensions(KinJector):
    """Inject/eject via dimensions to/from a KiCad board object."""

    def inject(self, data_dict, brd):
        """Inject via dimensions from data dict into a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        try:
            # The first via dimension never seems to change, so just inject the
            # list of via dimensions after that.
            brd_drs.m_ViasDimensionsList = VIA_DIMENSION_Vector(
                [VIA_DIMENSION(0, 0)] + [
                    VIA_DIMENSION(v['diameter'], v['drill'])
                    for v in data_dict['via dimensions list']
                ])
        except KeyError:
            pass

        # Load the updated via dimensions back into the board.
        brd.SetDesignSettings(brd_drs)

    def eject(self, brd):
        """Return via dimensions as a dict from a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        return {
            'via dimensions list': [{
                'diameter': v.m_Diameter,
                'drill': v.m_Drill
            } for v in brd_drs.m_ViasDimensionsList]
        }


class DiffPairDimensions(KinJector):
    """Inject/eject differential pair dimensions to/from a KiCad board object."""

    # THIS CODE DOESN'T WORK because there's no Python iterable for the list of
    # differential pair dimensions, just a SwigPyObject.

    def inject(self, data_dict, brd):
        """Inject diff pair dimensions from data_dict into a KiCad BOARD object."""

        return  # DIFF_PAIR_DIMENSION_Vector is not defined.

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        try:
            brd_drs.m_DiffPairDimensionsList = DIFF_PAIR_DIMENSION_Vector([
                DIFF_PAIR_DIMENSION(dp['width'], dp['gap'], dp['via gap'])
                for dp in data_dict['diff pair dimensions list']
            ])
        except KeyError:
            pass

        # Load the updated diff pair dimensions back into the board.
        brd.SetDesignSettings(brd_drs)

    def eject(self, brd):
        """Return diff pair dimensions as a dict from a KiCad BOARD object."""

        # Can't iterate over a SwigPyObject. DIFF_PAIR_DIMENSION_Vector is not defined.
        return {'diff pair dimensions list': []}

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        return {
            'diff pair dimensions list': [{
                'width': dp.m_Width,
                'gap': dp.m_Gap,
                'via gap': dp.m_ViaGap
            } for dp in brd_drs.m_DiffPairDimensionsList]
        }


class DesignRules(KinJector):
    """Inject/eject board design rules to/from a KiCad BOARD object."""

    def inject(self, data_dict, brd):
        """Inject design rule settings from data_dict into a KiCad BOARD object."""

        # Get the design rule settings from the data dict.
        data_drs = data_dict.get('design rules', {})

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        try:
            brd_drs.SetBoardThickness(data_drs['board thickness'])
        except KeyError:
            pass

        try:
            brd_drs.SetCopperLayerCount(data_drs['# copper layers'])
        except KeyError:
            pass

        try:
            #brd_drs.m_HoleToHoleMin = data_drs['hole to hole spacing']
            brd_drs.SetMinHoleSeparation(data_drs['hole to hole spacing'])
        except KeyError:
            pass

        try:
            brd_drs.m_ProhibitOverlappingCourtyards = data_drs[
                'prohibit courtyard overlap']
        except KeyError:
            pass

        try:
            brd_drs.m_RequireCourtyards = data_drs['require courtyards']
        except KeyError:
            pass

        try:
            brd_drs.m_BlindBuriedViaAllowed = data_drs[
                'blind/buried via allowed']
        except KeyError:
            pass

        try:
            brd_drs.m_MicroViasAllowed = data_drs['uvia allowed']
        except KeyError:
            pass

        try:
            brd_drs.m_MicroViasMinDrill = data_drs['uvia min drill size']
        except KeyError:
            pass

        try:
            brd_drs.m_MicroViasMinSize = data_drs['uvia min diameter']
        except KeyError:
            pass

        try:
            brd_drs.m_ViasMinDrill = data_drs['via min drill size']
        except KeyError:
            pass

        try:
            brd_drs.m_ViasMinSize = data_drs['via min diameter']
        except KeyError:
            pass

        try:
            brd_drs.m_TrackMinWidth = data_drs['track min width']
        except KeyError:
            pass

        try:
            brd_drs.m_SolderMaskMargin = data_drs['solder mask margin']
        except KeyError:
            pass

        try:
            brd_drs.m_SolderMaskMinWidth = data_drs['solder mask min width']
        except KeyError:
            pass

        try:
            brd_drs.m_SolderPasteMargin = data_drs['solder paste margin']
        except KeyError:
            pass

        try:
            brd_drs.m_SolderPasteMarginRatio = data_drs[
                'solder paste margin ratio']
        except KeyError:
            pass

        # Load the updated design rules back into the board.
        brd.SetDesignSettings(brd_drs)

        # The following items are part of the design rules but they have their
        # own classes for injecting their data into a board.

        # Load the track widths back into the board.
        TrackWidths().inject(data_drs, brd)

        # Load the updated via dimensions back into the board.
        ViaDimensions().inject(data_drs, brd)

        # Load the updated diff pair dimensions back into the board.
        DiffPairDimensions().inject(data_drs, brd)

    def eject(self, brd):
        """Return design rule settings as a dict from a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        data_drs = {
            'design rules': {
                'board thickness': brd_drs.GetBoardThickness(),
                '# copper layers': brd_drs.GetCopperLayerCount(),
                'hole to hole spacing': brd_drs.m_HoleToHoleMin,
                'prohibit courtyard overlap':
                brd_drs.m_ProhibitOverlappingCourtyards,
                'require courtyards': brd_drs.m_RequireCourtyards,
                'blind/buried via allowed': brd_drs.m_BlindBuriedViaAllowed,
                'uvia allowed': brd_drs.m_MicroViasAllowed,
                'uvia min drill size': brd_drs.m_MicroViasMinDrill,
                'uvia min diameter': brd_drs.m_MicroViasMinSize,
                'via min drill size': brd_drs.m_ViasMinDrill,
                'via min diameter': brd_drs.m_ViasMinSize,
                'track min width': brd_drs.m_TrackMinWidth,
                'solder mask margin': brd_drs.m_SolderMaskMargin,
                'solder mask min width': brd_drs.m_SolderMaskMinWidth,
                'solder paste margin': brd_drs.m_SolderPasteMargin,
                'solder paste margin ratio': brd_drs.m_SolderPasteMarginRatio,
            }
        }

        # The following items are part of the design rules but they have their
        # own classes for ejecting their data from a board.

        # Update data dict with the board track widths.
        data_drs['design rules'].update(TrackWidths().eject(brd))

        # Update data dict with the board via dimensions.
        data_drs['design rules'].update(ViaDimensions().eject(brd))

        # Update data dict with the board differential pair dimensions.
        data_drs['design rules'].update(DiffPairDimensions().eject(brd))

        return data_drs
