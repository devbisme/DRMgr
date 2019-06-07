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
import traceback

import yaml

import kinjector
import pcbnew
import wx
import wx.aui
import wx.lib.filebrowsebutton as FBB

WIDGET_SPACING = 5


def debug_dialog(msg, exception=None):
    if exception:
        msg = "\n".join((msg, str(exception)))
        # msg = "\n".join((msg, str(exception), traceback.format.exc()))
    dlg = wx.MessageDialog(None, msg, "", wx.OK)
    dlg.ShowModal()
    dlg.Destroy()


def get_project_directory():
    """Return the path of the PCB directory."""
    return os.path.dirname(pcbnew.GetBoard().GetFileName())


class DRMgr(pcbnew.ActionPlugin):
    """Plugin class for tool to open/save PCB design rules."""

    def defaults(self):
        self.name = "DRMgr"
        self.category = "Layout"
        self.description = "Open/save PCB design rules."

    def Run(self):
        class OpenSaveDlg(wx.Frame):
            def __init__(self):
                try:
                    wx.Frame.__init__(
                        self, None, title="Open/Save PCB Design Rules", pos=(200, 200)
                    )
                    panel = wx.Panel(parent=self)

                    self.open_btn = wx.Button(panel, label="Open")
                    self.open_btn.SetToolTip(
                        wx.ToolTip('Click to load new PCB design rules from a file.'))
                    self.save_btn = wx.Button(panel, label="Save")
                    self.save_btn.SetToolTip(
                        wx.ToolTip('Click to store current PCB design rules into a file.'))
                    self.cancel_btn = wx.Button(panel, label="Cancel")
                    self.open_btn.Bind(wx.EVT_BUTTON, self.open_dr, self.open_btn)
                    self.save_btn.Bind(wx.EVT_BUTTON, self.save_dr, self.save_btn)
                    self.cancel_btn.Bind(wx.EVT_BUTTON, self.cancel, self.cancel_btn)

                    btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
                    btn_sizer.AddSpacer(WIDGET_SPACING)
                    btn_sizer.Add(self.open_btn, flag=wx.ALL | wx.ALIGN_CENTER)
                    btn_sizer.AddSpacer(WIDGET_SPACING)
                    btn_sizer.Add(self.save_btn, flag=wx.ALL | wx.ALIGN_CENTER)
                    btn_sizer.AddSpacer(WIDGET_SPACING)
                    btn_sizer.Add(self.cancel_btn, flag=wx.ALL | wx.ALIGN_CENTER)
                    btn_sizer.AddSpacer(WIDGET_SPACING)

                    # Size the panel.
                    panel.SetSizer(btn_sizer)
                    panel.Layout()
                    panel.Fit()

                    # Finally, size the frame that holds the panel.
                    self.Fit()

                except Exception as e:
                    debug_dialog("Something went wrong!", e)

            def open_dr(self, evt):
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
                with open(file_name, "r") as fp:
                    drs = yaml.load(fp, Loader=yaml.Loader)
                    kinjector.DesignRules().inject(drs, pcbnew.GetBoard())
                file_dialog.Destroy()
                self.Destroy()

            def save_dr(self, evt):
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
                drs = kinjector.DesignRules().eject(pcbnew.GetBoard())
                # try:
                    # del drs["settings"]["netclass assignments"]
                # except KeyError:
                    # pass
                with open(file_name, "w") as fp:
                    yaml.safe_dump(drs, fp, default_flow_style=False)
                file_dialog.Destroy()
                self.Destroy()

            def cancel(self, evt):
                self.Destroy()

        self.opensavedlg = OpenSaveDlg()
        self.opensavedlg.Show(True)
        return True


DRMgr().register()
