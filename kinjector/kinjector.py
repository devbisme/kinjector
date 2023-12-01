# MIT license
#
# Copyright (C) 2019-2021 by Dave Vandenbout.
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

import collections
import sys

sys.path.append('/usr/lib/python3/dist-packages')
from pcbnew import DIFF_PAIR_DIMENSION, LSET
from pcbnew import NETCLASS as NCP
from pcbnew import PCB_PLOT_PARAMS as PPP
from pcbnew import (
    VIA_DIMENSION,
    B_Cu,
    F_Cu,
    Refresh,
    VIA_DIMENSION_Vector,
    intVector,
    wxPoint,
)


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
        if (
            k in dct
            and isinstance(dct[k], dict)
            and isinstance(merge_dct[k], collections.abc.Mapping)
        ):
            merge_dicts(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


class KinJector(object):
    """Base KinJector object."""

    # Named tuple for storing getter/setter functions.
    GetSet = collections.namedtuple("GetSet", ["get", "set"])


class Layers(KinJector):
    """Inject/eject enabled/visible layers to/from a KiCad board object."""

    dict_key = "layers"

    def inject(self, data_dict, brd):
        """Inject enabled/visible layers from data_dict into a KiCad BOARD object."""

        # Get the design rule settings from the data dict.
        data_drs = data_dict.get(self.dict_key, {})

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        try:
            brd_drs.SetBoardThickness(data_drs["board thickness"])
        except KeyError:
            pass

        try:
            brd_drs.SetCopperLayerCount(data_drs["# copper layers"])
        except KeyError:
            pass

        try:
            # Create an LSET where the bit is set for each enabled layer.
            lset = LSET()
            for l in data_drs["enabled"]:
                lset.AddLayer(l)
            # Enable the specified layers while disabling the rest.
            brd_drs.SetEnabledLayers(lset)
            brd.SetEnabledLayers(lset)
        except KeyError:
            pass

        try:
            # Create an LSET where the bit is set for each visible layer.
            lset = LSET()
            for l in data_drs["visible"]:
                lset.AddLayer(l)
            # Make the specified layers visible while hiiding the rest.
            brd_drs.SetVisibleLayers(lset)
            brd.SetVisibleLayers(lset)
        except KeyError:
            pass

        # Load the updated layer settings back into the board.
        brd.SetDesignSettings(brd_drs)
        Refresh()  # Refresh the board with the new data.

    def eject(self, brd):
        """Return enabled/visible layers as a dict from a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        return {
            self.dict_key: {
                "board thickness": brd_drs.GetBoardThickness(),
                "# copper layers": brd_drs.GetCopperLayerCount(),
                "enabled": [l for l in brd_drs.GetEnabledLayers().Seq()],
                "visible": [l for l in brd_drs.GetVisibleLayers().Seq()],
            }
        }


class DesignRules(KinJector):
    """Inject/eject board design rules to/from a KiCad BOARD object."""

    dict_key = "design rules"

    def inject(self, data_dict, brd):
        """Inject design rule settings from data_dict into a KiCad BOARD object."""

        # Get the design rule settings from the data dict.
        data_drs = data_dict.get(self.dict_key, {})

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        # Update the design rules with values from the data dict.
        # If a particular design rule parameter doesn't exist, just pass it by.

        try:
            brd_drs.m_BlindBuriedViaAllowed = data_drs["blind/buried via allowed"]
        except KeyError:
            pass

        try:
            brd_drs.m_MicroViasAllowed = data_drs["uvia allowed"]
        except KeyError:
            pass

        try:
            brd_drs.m_RequireCourtyards = data_drs["require courtyards"]
        except KeyError:
            pass

        try:
            brd_drs.m_ProhibitOverlappingCourtyards = data_drs[
                "prohibit courtyard overlap"
            ]
        except KeyError:
            pass

        try:
            brd_drs.m_TrackMinWidth = data_drs["min track width"]
        except KeyError:
            pass

        try:
            brd_drs.m_ViasMinSize = data_drs["min via diameter"]
        except KeyError:
            pass

        try:
            brd_drs.m_ViasMinDrill = data_drs["min via drill size"]
        except KeyError:
            pass
            pass

        try:
            brd_drs.m_MicroViasMinSize = data_drs["min uvia diameter"]
        except KeyError:
            pass

        try:
            brd_drs.m_MicroViasMinDrill = data_drs["min uvia drill size"]
        except KeyError:
            pass

        try:
            brd_drs.SetMinHoleSeparation(data_drs["hole to hole spacing"])
        except KeyError:
            pass

        # Load the updated design rules back into the board.
        brd.SetDesignSettings(brd_drs)
        Refresh()  # Refresh the board with the new data.

    def eject(self, brd):
        """Return a dict of design rule settings from a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        data_drs = {
            "blind/buried via allowed": brd_drs.m_BlindBuriedViaAllowed,
            "uvia allowed": brd_drs.m_MicroViasAllowed,
            "require courtyards": brd_drs.m_RequireCourtyards,
            "prohibit courtyard overlap": brd_drs.m_ProhibitOverlappingCourtyards,
            "min track width": brd_drs.m_TrackMinWidth,
            "min via diameter": brd_drs.m_ViasMinSize,
            "min via drill size": brd_drs.m_ViasMinDrill,
            "min uvia diameter": brd_drs.m_MicroViasMinSize,
            "min uvia drill size": brd_drs.m_MicroViasMinDrill,
            "hole to hole spacing": brd_drs.m_HoleToHoleMin,
        }

        return {self.dict_key: data_drs}


class NetClassDefs(KinJector):
    """Inject/eject net class definitions to/from a KiCad BOARD object."""

    dict_key = "definitions"

    # Associate each net class parameter key with methods for getting/setting
    # it in the board's net class structure.
    key_method_map = {
        "clearance": KinJector.GetSet(NCP.GetClearance, NCP.SetClearance),
        "description": KinJector.GetSet(NCP.GetDescription, NCP.SetDescription),
        "diff pair gap": KinJector.GetSet(NCP.GetDiffPairGap, NCP.SetDiffPairGap),
        "diff pair width": KinJector.GetSet(NCP.GetDiffPairWidth, NCP.SetDiffPairWidth),
        "track width": KinJector.GetSet(NCP.GetTrackWidth, NCP.SetTrackWidth),
        "via diameter": KinJector.GetSet(NCP.GetViaDiameter, NCP.SetViaDiameter),
        "via drill": KinJector.GetSet(NCP.GetViaDrill, NCP.SetViaDrill),
        "uvia diameter": KinJector.GetSet(NCP.GetuViaDiameter, NCP.SetuViaDiameter),
        "uvia drill": KinJector.GetSet(NCP.GetuViaDrill, NCP.SetuViaDrill),
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
        for data_netclass_name, data_netclass_params in data_netclass_defs.items():

            # Skip updates to the Default class. That's handled below.
            if data_netclass_name == "Default":
                continue

            # Create a new net class if it doesn't already exist.
            if data_netclass_name not in brd_netclasses:
                brd_netclasses[data_netclass_name] = NCP(data_netclass_name)

            # Point to the parameter structure for the current net class.
            brd_netclass_params = brd_netclasses[data_netclass_name]

            # Update the board's net class parameters with the values from the data dict.
            for key, value in data_netclass_params.items():
                self.key_method_map[key.lower()].set(brd_netclass_params, value)

        # Update the Default net class.
        try:
            data_dflt_params = data_netclass_defs["Default"]
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

    dict_key = "assignments"

    def inject(self, data_dict, brd):
        """Inject net class assignments from data_dict into a KiCad BOARD object."""

        # Get the netclass assignment for each net from the data dict.
        data_netclass_assigns = data_dict.get(self.dict_key, {})

        # Get all the nets in the board indexed by net names.
        brd_nets = brd.GetNetInfo().NetsByName()

        # Get all the net classes in the board.
        brd_netclasses = brd.GetNetClasses().NetClasses()
        brd_dflt = brd.GetNetClasses().GetDefault()

        # Assign the nets in data dict to the appropriate netclasses in the board.
        for data_net_name, data_net_class_name in data_netclass_assigns.items():
            # Check to see if the net from the data dict exists in the board.
            try:
                brd_net = brd_nets[data_net_name]
            except IndexError:
                continue  # Should we signal an error for a missing net?

            # Remove the net from its old net class ...
            old_net_class_name = brd_net.GetClassName()
            if old_net_class_name == "Default":
                old_net_class = brd_dflt
            else:
                old_net_class = brd_netclasses[old_net_class_name]
            # old_net_class = brd_netclasses[brd_net.GetClassName()]
            old_net_class.NetNames().discard(data_net_name)

            # And assign the net to its new class.
            if data_net_class_name == "Default":
                new_net_class = brd_dflt
            else:
                new_net_class = brd_netclasses[data_net_class_name]
            # new_net_class = brd_netclasses[data_net_class_name]
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


class NetClasses(KinJector):
    """Inject/eject net class defs and assignments to/from a KiCad BOARD object."""

    dict_key = "net classes"

    def inject(self, data_dict, brd):
        """Inject net class defs and assignments from data_dict into a KiCad BOARD object."""

        # Get the net classes from the data dict.
        data_drs = data_dict.get(self.dict_key, {})

        # Load the net class definitions into the board.
        NetClassDefs().inject(data_drs, brd)

        # Load the net/net class assignments into the board.
        NetClassAssigns().inject(data_drs, brd)

    def eject(self, brd):
        """Return a dict of net class defs and assignments from a KiCad BOARD object."""

        data_drs = {}

        # Update the data dict with the net class definitions.
        data_drs.update(NetClassDefs().eject(brd))

        # Update the data dict with the net/net class assignments.
        data_drs.update(NetClassAssigns().eject(brd))

        return {self.dict_key: data_drs}


class TrackWidths(KinJector):
    """Inject/eject track widths to/from a KiCad board object."""

    dict_key = "track width list"

    def inject(self, data_dict, brd):
        """Inject track widths from the data dict into a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        try:
            # The first track width never seems to change, so just inject the
            # list of track widths after that.
            brd_drs.m_TrackWidthList = intVector([0] + data_dict[self.dict_key])
        except KeyError:
            pass

        # Load the updated track widths back into the board.
        brd.SetDesignSettings(brd_drs)
        Refresh()  # Refresh the board with the new data.

    def eject(self, brd):
        """Return track widths as a dict from a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        # Return every track width except the first one because that's
        # set by the Default net class.
        return {self.dict_key: [w for w in brd_drs.m_TrackWidthList][1:]}


class ViaDimensions(KinJector):
    """Inject/eject via dimensions to/from a KiCad board object."""

    dict_key = "via dimensions list"

    def inject(self, data_dict, brd):
        """Inject via dimensions from data dict into a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        try:
            # The first via dimension never seems to change, so just inject the
            # list of via dimensions after that.
            brd_drs.m_ViasDimensionsList = VIA_DIMENSION_Vector(
                [VIA_DIMENSION(0, 0)]
                + [
                    VIA_DIMENSION(v["diameter"], v["drill"])
                    for v in data_dict[self.dict_key]
                ]
            )
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
            self.dict_key: [
                {"diameter": v.m_Diameter, "drill": v.m_Drill}
                for v in brd_drs.m_ViasDimensionsList[1:]
            ]
        }


class DiffPairDimensions(KinJector):
    """Inject/eject differential pair dimensions to/from a KiCad board object."""

    # THIS CODE DOESN'T WORK because there's no Python iterable for the list of
    # differential pair dimensions, just a SwigPyObject.

    dict_key = "diff pair dimensions list"

    def inject(self, data_dict, brd):
        """Inject diff pair dimensions from data_dict into a KiCad BOARD object."""

        return  # DIFF_PAIR_DIMENSION_Vector is not defined.

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        try:
            brd_drs.m_DiffPairDimensionsList = DIFF_PAIR_DIMENSION_Vector(
                [
                    DIFF_PAIR_DIMENSION(dp["width"], dp["gap"], dp["via gap"])
                    for dp in data_dict[self.dict_key]
                ]
            )
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
            self.dict_key: [
                {"width": dp.m_Width, "gap": dp.m_Gap, "via gap": dp.m_ViaGap}
                for dp in brd_drs.m_DiffPairDimensionsList
            ]
        }


class TracksViasDPs(KinJector):
    """Inject/eject tracks, vias, and differential pairs to/from a KiCad BOARD object."""

    dict_key = "tracks, vias, diff pairs"

    def inject(self, data_dict, brd):
        """Inject tracks, vias, and differential pairs from data_dict into a KiCad BOARD object."""

        # Get the track/via/DP info from the data dict.
        data_drs = data_dict.get(self.dict_key, {})

        # Load the track widths back into the board.
        TrackWidths().inject(data_drs, brd)

        # Load the via dimensions back into the board.
        ViaDimensions().inject(data_drs, brd)

        # Load the diff pair dimensions back into the board.
        DiffPairDimensions().inject(data_drs, brd)

    def eject(self, brd):
        """Return a dict of tracks, vias, and differential pairs from a KiCad BOARD object."""

        data_drs = {}

        # Update data dict with the board track widths.
        data_drs.update(TrackWidths().eject(brd))

        # Update data dict with the board via dimensions.
        data_drs.update(ViaDimensions().eject(brd))

        # Update data dict with the board differential pair dimensions.
        data_drs.update(DiffPairDimensions().eject(brd))

        return {self.dict_key: data_drs}


class SolderMaskPaste(KinJector):
    """Inject/eject solder mask/paster settings to/from a KiCad BOARD object."""

    dict_key = "solder mask/paste"

    def inject(self, data_dict, brd):
        """Inject solder mask/paste settings from data_dict into a KiCad BOARD object."""

        # Get the design rule settings from the data dict.
        data_drs = data_dict.get(self.dict_key, {})

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        # Update the design rules with values from the data dict.
        # If a particular design rule parameter doesn't exist, just pass it by.

        try:
            brd_drs.m_SolderMaskMargin = data_drs["solder mask clearance"]
        except KeyError:
            pass

        try:
            brd_drs.m_SolderMaskMinWidth = data_drs["solder mask min width"]
        except KeyError:
            pass

        try:
            brd_drs.m_SolderPasteMargin = data_drs["solder paste clearance"]
        except KeyError:
            pass

        try:
            brd_drs.m_SolderPasteMarginRatio = data_drs["solder paste clearance ratio"]
        except KeyError:
            pass

        # Load the updated solder paste/mask settings back into the board.
        brd.SetDesignSettings(brd_drs)
        Refresh()  # Refresh the board with the new data.

    def eject(self, brd):
        """Return a dict of solder mask/paste settings from a KiCad BOARD object."""

        # Get the design rules from the board.
        brd_drs = brd.GetDesignSettings()

        data_drs = {
            "solder mask clearance": brd_drs.m_SolderMaskMargin,
            "solder mask min width": brd_drs.m_SolderMaskMinWidth,
            "solder paste clearance": brd_drs.m_SolderPasteMargin,
            "solder paste clearance ratio": brd_drs.m_SolderPasteMarginRatio,
        }

        return {self.dict_key: data_drs}


class BoardSetup(KinJector):
    """Inject/eject board setup to/from a KiCad BOARD object."""

    dict_key = "board setup"

    def inject(self, data_dict, brd):
        """Inject board data from data_dict into a KiCad BOARD object."""

        # Get the design rule settings from the data dict.
        data_setup = data_dict.get(self.dict_key, {})

        # Load the enabled/visible layers into the board.
        Layers().inject(data_setup, brd)

        # Load the design rules into the board.
        DesignRules().inject(data_setup, brd)

        # Load the net class defs and assignments into the board.
        NetClasses().inject(data_setup, brd)

        # Load the track/via/differential pair dimensions back into the board.
        TracksViasDPs().inject(data_setup, brd)

        # Load the solder paste/mask dimensions back into the board.
        SolderMaskPaste().inject(data_setup, brd)

    def eject(self, brd):
        """Return a dict of board setup from a KiCad BOARD object."""

        data_setup = {}

        # Update the data dict with the enabled/visible layers.
        data_setup.update(Layers().eject(brd))

        # Update the data dict with the design rules.
        data_setup.update(DesignRules().eject(brd))

        # Update the data dict with the net class defs and assignments.
        data_setup.update(NetClasses().eject(brd))

        # Update the data dict with the track/via/differential pair dimensions.
        data_setup.update(TracksViasDPs().eject(brd))

        # Update data dict with the solder paste/mask dimensions.
        data_setup.update(SolderMaskPaste().eject(brd))

        return {self.dict_key: data_setup}


class Plot(KinJector):
    """Inject/eject plot settings to/from a KiCad BOARD object."""

    dict_key = "plot"

    # Associate each plot parameter key with methods for getting/setting
    # it in the board's plot structure.
    key_method_map = {
        "force a4 output": KinJector.GetSet(PPP.GetA4Output, PPP.SetA4Output),
        "autoscale": KinJector.GetSet(PPP.GetAutoScale, PPP.SetAutoScale),
        # Can't handle COLOR4d and I really don't care.
        "color": KinJector.GetSet(lambda x: None, lambda x, y: None),
        "plot in outline mode": KinJector.GetSet(
            PPP.GetDXFPlotPolygonMode, PPP.SetDXFPlotPolygonMode
        ),
        "drill marks": KinJector.GetSet(PPP.GetDrillMarksType, PPP.SetDrillMarksType),
        "x scale factor": KinJector.GetSet(
            PPP.GetFineScaleAdjustX, PPP.SetFineScaleAdjustX
        ),
        "y scale factor": KinJector.GetSet(
            PPP.GetFineScaleAdjustY, PPP.SetFineScaleAdjustY
        ),
        "hpgl pen size": KinJector.GetSet(
            PPP.GetHPGLPenDiameter, PPP.SetHPGLPenDiameter
        ),
        "hpgl pen num": KinJector.GetSet(PPP.GetHPGLPenNum, PPP.SetHPGLPenNum),
        "hpgl pen speed": KinJector.GetSet(PPP.GetHPGLPenSpeed, PPP.SetHPGLPenSpeed),
        "mirrored plot": KinJector.GetSet(PPP.GetMirror, PPP.SetMirror),
        "negative plot": KinJector.GetSet(PPP.GetNegative, PPP.SetNegative),
        "output directory": KinJector.GetSet(
            PPP.GetOutputDirectory, PPP.SetOutputDirectory
        ),
        "plot mode": KinJector.GetSet(PPP.GetPlotMode, PPP.SetPlotMode),
        "scale": KinJector.GetSet(PPP.GetScale, PPP.SetScale),
        "skip npth pads": KinJector.GetSet(
            PPP.GetSkipPlotNPTH_Pads, PPP.SetSkipPlotNPTH_Pads
        ),
        "text mode": KinJector.GetSet(PPP.GetTextMode, PPP.SetTextMode),
        "generate gerber job file": KinJector.GetSet(
            PPP.GetCreateGerberJobFile, PPP.SetCreateGerberJobFile
        ),
        "exclude pcb edge": KinJector.GetSet(
            PPP.GetExcludeEdgeLayer, PPP.SetExcludeEdgeLayer
        ),
        "format": KinJector.GetSet(PPP.GetFormat, PPP.SetFormat),
        "coordinate format": KinJector.GetSet(
            PPP.GetGerberPrecision, PPP.SetGerberPrecision
        ),
        "include netlist attributes": KinJector.GetSet(
            PPP.GetIncludeGerberNetlistInfo, PPP.SetIncludeGerberNetlistInfo
        ),
        "default line width": KinJector.GetSet(PPP.GetLineWidth, PPP.SetLineWidth),
        "plot border": KinJector.GetSet(PPP.GetPlotFrameRef, PPP.SetPlotFrameRef),
        "plot invisible text": KinJector.GetSet(
            PPP.GetPlotInvisibleText, PPP.SetPlotInvisibleText
        ),
        "plot pads on silk": KinJector.GetSet(
            PPP.GetPlotPadsOnSilkLayer, PPP.SetPlotPadsOnSilkLayer
        ),
        "plot footprint refs": KinJector.GetSet(
            PPP.GetPlotReference, PPP.SetPlotReference
        ),
        "plot footprint values": KinJector.GetSet(PPP.GetPlotValue, PPP.SetPlotValue),
        "do not tent vias": KinJector.GetSet(
            PPP.GetPlotViaOnMaskLayer, PPP.SetPlotViaOnMaskLayer
        ),
        "scaling": KinJector.GetSet(PPP.GetScaleSelection, PPP.SetScaleSelection),
        "subtract soldermask from silk": KinJector.GetSet(
            PPP.GetSubtractMaskFromSilk, PPP.SetSubtractMaskFromSilk
        ),
        "text mode": KinJector.GetSet(PPP.GetTextMode, PPP.SetTextMode),
        "use aux axis as origin": KinJector.GetSet(
            PPP.GetUseAuxOrigin, PPP.SetUseAuxOrigin
        ),
        "use protel filename extensions": KinJector.GetSet(
            PPP.GetUseGerberProtelExtensions, PPP.SetUseGerberProtelExtensions
        ),
        "use x2 format": KinJector.GetSet(
            PPP.GetUseGerberX2format, PPP.SetUseGerberX2format
        ),
        "track width correction": KinJector.GetSet(
            PPP.GetWidthAdjust, PPP.SetWidthAdjust
        ),
        # layers are handled as a special case.
        "layers": KinJector.GetSet(lambda x: None, lambda x, y: None),
    }

    def inject(self, data_dict, brd):
        """Inject plot settings from data_dict into a KiCad BOARD object."""

        # Get all plot settings from the data dict.
        data_plot_settings = data_dict.get(self.dict_key, {})

        # Get the plot settings from the board.
        brd_plot_settings = brd.GetPlotOptions()

        # Update existing plot settings in the board with new values from data.
        for key, value in data_plot_settings.items():
            self.key_method_map[key.lower()].set(brd_plot_settings, value)

        # Enable specified layers for plotting.
        try:
            # Create an LSET where the bit is set for each enabled plot layer.
            lset = LSET()
            for l in data_plot_settings["layers"]:
                lset.AddLayer(l)
        except KeyError:
            # No layers element found in data dict.
            pass
        else:
            # Enable the specified layers while disabling the rest.
            brd_plot_settings.SetLayerSelection(lset)

        # Load the modified plot settings into the board.
        brd.SetPlotOptions(brd_plot_settings)

    def eject(self, brd):
        """Return a dict of plot settings from a KiCad BOARD object."""

        # Extract the parameters for each plot setting in the board.
        brd_plot_settings = brd.GetPlotOptions()
        plot_settings_dict = {
            key: method.get(brd_plot_settings)
            for (key, method) in self.key_method_map.items()
        }

        # Extract the enabled plotting layers.
        plot_settings_dict["layers"] = list(brd_plot_settings.GetLayerSelection().Seq())

        return {self.dict_key: plot_settings_dict}


class ModulePosition(KinJector):
    """Inject/eject part (X,Y), rotation, front/back to/from a KiCad MODULE object."""

    dict_key = "position"

    # Index top and bottom of boards by their layer number in PCBNEW.
    top_btm = {F_Cu: "top", B_Cu: "bottom"}

    def inject(self, data_dict, module):
        """Inject part position from data_dict into a KiCad MODULE object."""

        try:
            pos_data = data_dict[self.dict_key]
        except KeyError:
            return  # No position data to inject into MODULE object.

        # Set the (X,Y) position.
        try:
            module.SetPosition(wxPoint(pos_data["x"], pos_data["y"]))
        except IndexError:
            pass  # No (X,Y) data, so skip it.

        # Set the orientation (in degrees).
        try:
            module.SetOrientationDegrees(pos_data["angle"])
        except IndexError:
            pass  # No angle data, so skip it.

        # Set whether the board is on the top or bottom side of the PCB.
        module_side = self.top_btm[module.GetLayer()]
        try:
            if module_side != pos_data["side"].lower():
                module.Flip(module.GetPosition())
        except IndexError:
            pass  # No top-side/bottom-side data, so skip it.

    def eject(self, module):
        """Return a dict with the part position from a KiCad MODULE object."""

        pos = module.GetPosition()
        return {
            self.dict_key: {
                "x": pos.x,
                "y": pos.y,
                "angle": module.GetOrientationDegrees(),
                "side": self.top_btm[module.GetLayer()],
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

    dict_key = "modules"

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
            part_ref: Module().eject(part) for (part_ref, part) in brd_parts.items()
        }

        return {self.dict_key: part_data_dict}


class Board(KinJector):
    """Inject/eject board data to/from a KiCad BOARD object."""

    dict_key = "board"

    def inject(self, data_dict, brd):
        """Inject board data from data_dict into a KiCad BOARD object."""

        # Get the design rule settings from the data dict.
        brd_data = data_dict.get(self.dict_key, {})

        # Load the design rules into the board.
        BoardSetup().inject(brd_data, brd)

        # Load the plot settings into the board.
        Plot().inject(brd_data, brd)

        # Load the module positions into the board.
        ModulesByRef().inject(brd_data, brd)

    def eject(self, brd):
        """Return a dict of board data from a KiCad BOARD object."""

        brd_data = {}
        brd_data.update(BoardSetup().eject(brd))
        brd_data.update(Plot().eject(brd))
        brd_data.update(ModulesByRef().eject(brd))
        return {self.dict_key: brd_data}
