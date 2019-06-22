# -*- coding: utf-8 -*-

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

import os
import os.path
import re
import sys

import wx
import yaml

import kinjector
import pcbnew

WIDGET_SPACING = 5


def debug_dialog(msg, exception=None):
    if exception:
        msg = "\n".join((msg, str(exception)))
    dlg = wx.MessageDialog(None, msg, "", wx.OK)
    dlg.ShowModal()
    dlg.Destroy()


def get_project_directory():
    """Return the path of the PCB directory."""
    return os.path.dirname(pcbnew.GetBoard().GetFileName())


def nested_dict_exists(dict_, nested_key, separator="|"):
    """Test if nested set of keys exists in nested dictionary."""

    # Separate the nested key.
    keys = nested_key.split(separator)

    for key in keys:
        try:
            dict_ = dict_[key]  # Go to next level of nested dict.
        except KeyError:
            return False  # Nested sub dicts were not found.

    return True  # Nested subdicts were found.


def copy_nested_dict(src_dict, dst_dict, nested_key, separator="|"):
    """Copy nested dict from src dict to dst dict."""

    # Abort if the source dict doesn't contain the nested sub-dicts.
    if not nested_dict_exists(src_dict, nested_key, separator):
        return

    # Separate the nested key.
    keys = nested_key.split(separator)

    # Walk thru the source dict and create the same entries in the dest dict.
    for key in keys:
        src_dict = src_dict[key]
        try:
            dst_dict = dst_dict[key]
        except KeyError:
            dst_dict[key] = {}
            dst_dict = dst_dict[key]

    # Finally, copy the source leaf dict to the dest.
    dst_dict.update(src_dict)


class DRMgr(pcbnew.ActionPlugin):
    """Plugin class for tool to open/save PCB design rules."""

    class SaveRecallOption(object):
        def __init__(self, label_, dict_key_, chkbx_, checked_, tooltip_):
            self.label = label_  # Checkbox text.
            self.dict_key = dict_key_  # Key for a section of the design rule dict.
            self.chkbx = chkbx_  # Checkbox widget.
            self.checked = checked_  # Initial state of the checkbox.
            self.tooltip = tooltip_  # Tool-tip for the checkbox.

    save_recall_options = [
        SaveRecallOption(
            "Layers",
            "board|board setup|layers",
            None,
            True,
            "PCB layers and thickness.",
        ),
        SaveRecallOption(
            "Design Rules",
            "board|board setup|design rules",
            None,
            True,
            "Minimum track/via/uvia dimensions.",
        ),
        SaveRecallOption(
            "Tracks && Vias",
            "board|board setup|tracks, vias, diff pairs",
            None,
            True,
            "Pre-defined track widths and via sizes.",
        ),
        SaveRecallOption(
            "Solder Mask/Paste",
            "board|board setup|solder mask/paste",
            None,
            True,
            "Solder mask and paste minimum dimensions.",
        ),
        SaveRecallOption(
            "Net Class Definitions",
            "board|board setup|net classes|definitions",
            None,
            True,
            "Net class clearance/track/via/uvia dimensions.",
        ),
        SaveRecallOption(
            "Net Class Assignments",
            "board|board setup|net classes|assignments",
            None,
            False,
            "Net assignments to net classes.",
        ),
        SaveRecallOption(
            "Plot Settings", "board|plot", None, True, "Options for plot output file."
        ),
        SaveRecallOption(
            "Drill Settings",
            "board|plot|drill",
            None,
            False,
            "Options for drill output file.",
        ),
    ]

    def defaults(self):
        self.name = "DRMgr"
        self.category = "Layout"
        self.description = "Open/save PCB design rules."

    def Run(self):
        class OpenSaveDlg(wx.Frame):
            def __init__(self):
                try:
                    wx.Frame.__init__(
                        self, None, -1, "Open/Save PCB Design Rules", size=(400, 300)
                    )
                    panel = wx.Panel(parent=self)

                    panel_sizer = wx.BoxSizer(wx.VERTICAL)

                    # Create checkboxes for enabling portions of the design rules.
                    chkbx_sizer = wx.BoxSizer(wx.VERTICAL)
                    for option in DRMgr.save_recall_options:
                        option.chkbx = wx.CheckBox(panel, wx.ID_ANY, option.label)
                        option.chkbx.SetValue(option.checked)
                        option.chkbx.SetToolTip(wx.ToolTip(option.tooltip))
                        chkbx_sizer.Add(option.chkbx, 0, wx.ALL, WIDGET_SPACING)

                    panel_sizer.Add(chkbx_sizer, 0, wx.ALL, WIDGET_SPACING)

                    # Create buttons for saving/recalling design rules.
                    btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

                    # Open button for recalling a file of design rules.
                    open_btn = wx.Button(panel, label="Open")
                    open_btn.SetToolTip(
                        wx.ToolTip("Click to load new PCB design rules from a file.")
                    )
                    open_btn.Bind(wx.EVT_BUTTON, self.open_dr, open_btn)
                    btn_sizer.Add(open_btn, 0, wx.ALL, WIDGET_SPACING)

                    # Save button for saving design rules from the current board.
                    save_btn = wx.Button(panel, label="Save")
                    save_btn.SetToolTip(
                        wx.ToolTip(
                            "Click to store current PCB design rules into a file."
                        )
                    )
                    save_btn.Bind(wx.EVT_BUTTON, self.save_dr, save_btn)
                    btn_sizer.Add(save_btn, 0, wx.ALL, WIDGET_SPACING)

                    # Cancel button.
                    cancel_btn = wx.Button(panel, label="Cancel")
                    cancel_btn.Bind(wx.EVT_BUTTON, self.cancel, cancel_btn)
                    btn_sizer.Add(cancel_btn, 0, wx.ALL, WIDGET_SPACING)

                    panel_sizer.Add(
                        btn_sizer,
                        0,
                        wx.ALIGN_CENTER_HORIZONTAL | wx.ALL,
                        WIDGET_SPACING,
                    )

                    panel.SetSizer(panel_sizer)

                except Exception as e:
                    debug_dialog("Something went wrong!", e)

            def open_dr(self, evt):
                # Open a design rule file and apply it to the board.

                # Get file name.
                file_dialog = wx.FileDialog(
                    parent=self,
                    message="Open PCB Design Rules File",
                    defaultDir=get_project_directory(),
                    defaultFile="",
                    wildcard="Design rules (*.kidr)|*.kidr|All files (*.*)|*.*",
                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                )
                file_dialog.ShowModal()
                file_name = file_dialog.GetPath()

                # Open file and get design rule settings.
                with open(file_name, "r") as fp:
                    drs = yaml.load(fp, Loader=yaml.Loader)

                # Copy selected portions of design rules.
                selected_drs = {}
                for option in DRMgr.save_recall_options:
                    if option.chkbx.GetValue():
                        copy_nested_dict(drs, selected_drs, option.dict_key)

                # Apply selected design rule settings to the current board.
                kinjector.Board().inject(selected_drs, pcbnew.GetBoard())

                # Clean up.
                file_dialog.Destroy()
                self.Destroy()

            def save_dr(self, evt):
                # Save the board design rule settings to a file.

                # Get file name.
                file_dialog = wx.FileDialog(
                    parent=self,
                    message="Save PCB Design Rules File",
                    defaultDir=get_project_directory(),
                    defaultFile="",
                    wildcard="Design rules (*.kidr)|*.kidr|All files (*.*)|*.*",
                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                )
                file_dialog.ShowModal()
                file_name = file_dialog.GetPath()

                # Get board design rule settings.
                drs = kinjector.Board().eject(pcbnew.GetBoard())

                # Copy selected portions of design rules.
                selected_drs = {}
                for option in DRMgr.save_recall_options:
                    if option.chkbx.GetValue():
                        copy_nested_dict(drs, selected_drs, option.dict_key)

                # Save selected design rules into the file.
                with open(file_name, "w") as fp:
                    yaml.safe_dump(selected_drs, fp, default_flow_style=False)

                # Clean up.
                file_dialog.Destroy()
                self.Destroy()

            def cancel(self, evt):
                self.Destroy()

        self.open_save_dlg = OpenSaveDlg()
        self.open_save_dlg.Show()
        return True


DRMgr().register()
