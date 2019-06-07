﻿# MIT license
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
"""
A module for injecting values from a dict into a KiCad PCB board file,
and for ejecting values from a board file into a dict.
"""

import copy
import json
import collections

from pcbnew import (NETCLASSPTR as NCP, F_Cu, B_Cu, wxPoint, intVector, LSET,
                    Refresh, VIA_DIMENSION, VIA_DIMENSION_Vector,
                    DIFF_PAIR_DIMENSION)


def merge_dicts(dct, merge_dct):
    """ 
    Dict merge that recurses through both dicts and updates keys.

    Args:
        dct: The dict that will be updated.
        merge_dct: The dict whose values will be inserted into dct.

    Returns:
        Nothing.
    """

    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            merge_dicts(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


class KinJector(object):
    """Base KinJector object."""

    # Named tuple for storing getter/setter functions.
    GetSet = collections.namedtuple('GetSet', ['get', 'set'])


class NetClassDefs(KinJector):
    """Inject/eject net class definitions to/from a KiCad BOARD object."""

    dict_key = 'netclasses'

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
        data_netclass_defs = data_dict.get(self.dict_key, {})

        # Get all the net classes in the board except the Default class.
        # Using brd.GetAllNetClasss() injects a duplicate of the Default into
        # the set of net classes.
        brd_netclasses = brd.GetNetClasses().NetClasses()

        # Update existing net classes in the board with new values from data
        # or create new net classes.
        for data_netclass_name, data_netclass_params in data_netclass_defs.items(
        ):

            # Skip updates to the Default class. That's handled below.
            if data_netclass_name == 'Default':
                continue

            # Create a new net class if it doesn't already exist.
            if data_netclass_name not in brd_netclasses:
                brd_netclasses[data_netclass_name] = NCP(data_netclass_name)

            # Point to the parameter structure for the current net class.
            brd_netclass_params = brd_netclasses[data_netclass_name]

            # Update the board's net class parameters with the values from the data dict.
            for key, value in data_netclass_params.items():
                self.key_method_map[key.lower()].set(brd_netclass_params,
                                                     value)

        # Update the Default net class.
        try:
            data_dflt_params = data_netclass_defs['Default']
        except KeyError:
            # No Default class was found in the data dict, so don't update Default.
            pass
        else:
            # Update the Default net class from the data dict.
            brd_dflt_params = brd.GetNetClasses().GetDefault()
            for key, value in data_dflt_params.items():
                self.key_method_map[key.lower()].set(brd_dflt_params, value)

    def eject(self, brd):
        """Return a dict of net class definitions from a KiCad BOARD object."""

        # Extract the parameters for each net class in the board.
        netclass_dict = {}
        for netclass_name, netclass_params in brd.GetAllNetClasses().items():
            netclass_dict[str(netclass_name)] = {
                key: method.get(netclass_params)
                for (key, method) in self.key_method_map.items()
            }

        return {self.dict_key: netclass_dict}


class NetClassAssigns(KinJector):
    """Inject/eject net class assignments to/from a KiCad BOARD object."""

    dict_key = 'netclass assignments'

    def inject(self, data_dict, brd):
        """Inject net class assignments from data_dict into a KiCad BOARD object."""

        # Get the netclass assignment for each net from the data dict.
        data_netclass_assigns = data_dict.get(self.dict_key, {})

        # Get all the nets in the board indexed by net names.
        brd_nets = brd.GetNetInfo().NetsByName()

        # Get all the net classes in the board.
        brd_netclasses = brd.GetNetClasses().NetClasses()
        brd_dflt = brd.GetNetClasses().GetDefault()

        # Assign the JSON nets to the appropriate netclasses in the board.
        for data_net_name, data_net_class_name in data_netclass_assigns.items(
        ):
            # Check to see if the net from the data dict exists in the board.
            try:
                brd_net = brd_nets[data_net_name]
            except IndexError:
                continue  # Should we signal an error for a missing net?

            # Remove the net from its old net class ...
            old_net_class_name = brd_net.GetClassName()
            if old_net_class_name == 'Default':
                old_net_class = brd_dflt
            else:
                old_net_class = brd_netclasses[old_net_class_name]
            #old_net_class = brd_netclasses[brd_net.GetClassName()]
            old_net_class.NetNames().discard(data_net_name)

            # And assign the net to its new class.
            if data_net_class_name == 'Default':
                new_net_class = brd_dflt
            else:
                new_net_class = brd_netclasses[data_net_class_name]
            #new_net_class = brd_netclasses[data_net_class_name]
            new_net_class.NetNames().add(data_net_name)
            brd_net.SetClass(new_net_class)

    def eject(self, brd):
        """Return a dict of net class assignments from a KiCad BOARD object."""

        # Extract the netclass assigned to each net in the board.
        netclass_assignment_dict = {
            str(net_name): net.GetClassName()
            for (net_name, net) in brd.GetNetInfo().NetsByName().items()
        }

        return {self.dict_key: netclass_assignment_dict}


class ModulePosition(KinJector):
    """Inject/eject part (X,Y), rotation, front/back to/from a KiCad MODULE object."""

    dict_key = 'position'

    # Index top and bottom of boards by their layer number in PCBNEW.
    top_btm = {F_Cu: 'top', B_Cu: 'bottom'}

    def inject(self, data_dict, module):
        """Inject part position from data_dict into a KiCad MODULE object."""

        try:
            pos_data = data_dict[self.dict_key]
        except KeyError:
            return  # No position data to inject into MODULE object.

        # Set the (X,Y) position.
        try:
            module.SetPosition(wxPoint(pos_data['x'], pos_data['y']))
        except IndexError:
            pass  # No (X,Y) data, so skip it.

        # Set the orientation (in degrees).
        try:
            module.SetOrientationDegrees(pos_data['angle'])
        except IndexError:
            pass  # No angle data, so skip it.

        # Set whether the board is on the top or bottom side of the PCB.
        module_side = self.top_btm[module.GetLayer()]
        try:
            if module_side != pos_data['side'].lower():
                module.Flip(module.GetPosition())
        except IndexError:
            pass  # No top-side/bottom-side data, so skip it.

    def eject(self, module):
        """Return a dict with the part position from a KiCad MODULE object."""

        pos = module.GetPosition()
        return {
            self.dict_key: {
                'x': pos.x,
                'y': pos.y,
                'angle': module.GetOrientationDegrees(),
                'side': self.top_btm[module.GetLayer()],
            }
        }


class Module(KinJector):
    """Inject/eject part data to/from a KiCad MODULE object."""

    def inject(self, data_dict, module):
        """Inject part data from data_dict into a KiCad MODULE object."""

        ModulePosition().inject(data_dict, module)

    def eject(self, module):
        """Return a dict of part data from a KiCad MODULE object."""

        data_dict = {}
        data_dict.update(ModulePosition().eject(module))
        return data_dict


class ModulesByRef(KinJector):
    """Inject/eject data to/from parts in a KiCad BOARD object by part reference."""

    dict_key = 'modules'

    @staticmethod
    def get_id(module):
        return str(module.GetReference())

    def inject(self, data_dict, brd):
        """Inject data from data_dict into parts of a KiCad BOARD object."""

        # Get the module data from the data dict.
        data_modules = data_dict.get(self.dict_key, {})

        # Get all the parts in the board indexed by references.
        brd_modules = {self.get_id(m): m for m in brd.GetModules()}

        # Assign the data in the data_dict to the parts on the board.
        for data_module_ref, data_module_data in data_modules.items():

            # Check to see if the part from the data dict exists on the board.
            try:
                brd_module = brd_modules[data_module_ref]
            except KeyError:
                continue  # Should we signal an error for a missing part?

            # Inject the data into the part.
            Module().inject(data_module_data, brd_module)

    def eject(self, brd):
        """Return part data from parts as a dict in a KiCad BOARD object."""

        # Get all the parts in the board indexed by references.
        brd_parts = {self.get_id(m): m for m in brd.GetModules()}

        # Get data from each part and store it in dict using part ref as key.
        part_data_dict = {
            part_ref: Module().eject(part)
            for (part_ref, part) in brd_parts.items()
        }

        return {self.dict_key: part_data_dict}


class TrackWidths(KinJector):
    """Inject/eject track widths to/from a KiCad board object."""

    dict_key = 'track width list'

    def inject(self, data_dict, brd):
        """Inject track widths from JSON into a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        try:
            # The first track width never seems to change, so just inject the
            # list of track widths after that.
            brd_drs.m_TrackWidthList = intVector([
                0,
            ] + data_dict[self.dict_key])
        except KeyError:
            pass

        # Load the updated track widths back into the board.
        brd.SetDesignSettings(brd_drs)
        Refresh()  # Refresh the board with the new data.

    def eject(self, brd):
        """Return JSON track widths from a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        # Return every track width except the first one because that's
        # set by the Default net class.
        return {self.dict_key: [w for w in brd_drs.m_TrackWidthList][1:]}


class ViaDimensions(KinJector):
    """Inject/eject via dimensions to/from a KiCad board object."""

    dict_key = 'via dimensions list'

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
                    for v in data_dict[self.dict_key]
                ])
        except KeyError:
            pass

        # Load the updated via dimensions back into the board.
        brd.SetDesignSettings(brd_drs)
        Refresh()  # Refresh the board with the new data.

    def eject(self, brd):
        """Return via dimensions as a dict from a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        # Return every via dimension except the first one because that's
        # set by the Default net class.
        return {
            self.dict_key: [{
                'diameter': v.m_Diameter,
                'drill': v.m_Drill
            } for v in brd_drs.m_ViasDimensionsList[1:]]
        }


class DiffPairDimensions(KinJector):
    """Inject/eject differential pair dimensions to/from a KiCad board object."""

    # THIS CODE DOESN'T WORK because there's no Python iterable for the list of
    # differential pair dimensions, just a SwigPyObject.

    dict_key = 'diff pair dimensions list'

    def inject(self, data_dict, brd):
        """Inject diff pair dimensions from data_dict into a KiCad BOARD object."""

        return  # DIFF_PAIR_DIMENSION_Vector is not defined.

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        try:
            brd_drs.m_DiffPairDimensionsList = DIFF_PAIR_DIMENSION_Vector([
                DIFF_PAIR_DIMENSION(dp['width'], dp['gap'], dp['via gap'])
                for dp in data_dict[self.dict_key]
            ])
        except KeyError:
            pass

        # Load the updated diff pair dimensions back into the board.
        brd.SetDesignSettings(brd_drs)
        Refresh()  # Refresh the board with the new data.

    def eject(self, brd):
        """Return diff pair dimensions as a dict from a KiCad BOARD object."""

        # Can't iterate over a SwigPyObject. DIFF_PAIR_DIMENSION_Vector is not defined.
        return {self.dict_key: []}

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        return {
            self.dict_key: [{
                'width': dp.m_Width,
                'gap': dp.m_Gap,
                'via gap': dp.m_ViaGap
            } for dp in brd_drs.m_DiffPairDimensionsList]
        }


class Layers(KinJector):
    """Inject/eject enabled/visible layers to/from a KiCad board object."""

    dict_key = 'layers'

    def inject(self, data_dict, brd):
        """Inject enabled/visible layers from data_dict into a KiCad BOARD object."""

        # Get the design rule settings from the data dict.
        data_drs = data_dict.get(self.dict_key, {})

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        try:
            # Create an LSET where the bit is set for each enabled layer.
            lset = LSET()
            for l in data_drs['enabled']:
                lset.AddLayer(l)
            # Enable the specified layers while disabling the rest.
            brd_drs.SetEnabledLayers(lset)
            brd.SetEnabledLayers(lset)
        except KeyError:
            pass

        try:
            # Create an LSET where the bit is set for each visible layer.
            lset = LSET()
            for l in data_drs['visible']:
                lset.AddLayer(l)
            # Make the specified layers visible while hiiding the rest.
            brd_drs.SetVisibleLayers(lset)
            brd.SetVisibleLayers(lset)
        except KeyError:
            pass

        # Load the updated diff pair dimensions back into the board.
        brd.SetDesignSettings(brd_drs)
        Refresh()  # Refresh the board with the new data.

    def eject(self, brd):
        """Return enabled/visible layers as a dict from a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        return {
            self.dict_key: {
                'enabled': [l for l in brd_drs.GetEnabledLayers().Seq()],
                'visible': [l for l in brd_drs.GetVisibleLayers().Seq()],
            }
        }


class DesignRules(KinJector):
    """Inject/eject board design rules to/from a KiCad BOARD object."""

    dict_key = 'settings'

    def inject(self, data_dict, brd):
        """Inject design rule settings from data_dict into a KiCad BOARD object."""

        # Get the design rule settings from the data dict.
        data_drs = data_dict.get(self.dict_key, {})

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        # Update the design rules with values from the data dict.
        # If a particular design rule parameter doesn't exist, just pass it by.

        try:
            brd_drs.SetBoardThickness(data_drs['board thickness'])
        except KeyError:
            pass

        try:
            brd_drs.SetCopperLayerCount(data_drs['# copper layers'])
        except KeyError:
            pass

        try:
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
        Refresh()  # Refresh the board with the new data.

        # The following items are part of the design rules but they have their
        # own classes for injecting their data into a board.

        # Load the track widths back into the board.
        TrackWidths().inject(data_drs, brd)

        # Load the via dimensions back into the board.
        ViaDimensions().inject(data_drs, brd)

        # Load the diff pair dimensions back into the board.
        DiffPairDimensions().inject(data_drs, brd)

        # Load the net class definitions into the board.
        NetClassDefs().inject(data_drs, brd)

        # Load the net/net class assignments into the board.
        NetClassAssigns().inject(data_drs, brd)

        # Load the enabled/visible layers into the board.
        Layers().inject(data_drs, brd)

    def eject(self, brd):
        """Return a dict of design rule settings from a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        data_drs = {
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

        # The following items are part of the design rules but they have their
        # own classes for ejecting their data from a board.

        # Update data dict with the board track widths.
        data_drs.update(TrackWidths().eject(brd))

        # Update data dict with the board via dimensions.
        data_drs.update(ViaDimensions().eject(brd))

        # Update data dict with the board differential pair dimensions.
        data_drs.update(DiffPairDimensions().eject(brd))

        # Update the data dict with the net class definitions.
        data_drs.update(NetClassDefs().eject(brd))

        # Update the data dict with the net/net class assignments.
        data_drs.update(NetClassAssigns().eject(brd))

        # Update the data dict with the enabled/visible layers.
        data_drs.update(Layers().eject(brd))

        return {self.dict_key: data_drs}


class Board(KinJector):
    """Inject/eject board data to/from a KiCad BOARD object."""

    dict_key = 'board'

    def inject(self, data_dict, brd):
        """Inject board data from data_dict into a KiCad BOARD object."""

        # Get the design rule settings from the data dict.
        brd_data = data_dict.get(self.dict_key, {})

        # Load the design rules into the board.
        DesignRules().inject(brd_data, brd)

        # Load the module positions into the board.
        ModulesByRef().inject(brd_data, brd)

    def eject(self, brd):
        """Return a dict of board data from a KiCad BOARD object."""

        brd_data = {}
        brd_data.update(DesignRules().eject(brd))
        brd_data.update(ModulesByRef().eject(brd))
        return {self.dict_key: brd_data}
