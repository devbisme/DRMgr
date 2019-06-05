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


class DnDFilePickerCtrl(FBB.FileBrowseButton, wx.FileDropTarget):
    """File browser."""

    def __init__(self, *args, **kwargs):
        FBB.FileBrowseButton.__init__(self, *args, **kwargs)
        wx.FileDropTarget.__init__(self)
        self.SetDropTarget(self)
        self.SetDefaultAction(
            wx.DragCopy
        )  # Show '+' icon when hovering over this field.

    def GetPath(self, addToHistory=False):
        current_value = self.GetValue()
        return current_value

    def SetPath(self, path):
        self.SetValue(path)

    def OnChanged(self, evt):
        wx.PostEvent(
            self, wx.PyCommandEvent(wx.EVT_FILEPICKER_CHANGED.typeId, self.GetId())
        )

    def OnDropFiles(self, x, y, filenames):
        wx.PostEvent(
            self, wx.PyCommandEvent(wx.EVT_FILEPICKER_CHANGED.typeId, self.GetId())
        )


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
                    wx.Frame.__init__(self, None, title="Open/Save PCB Design Rules", pos=(150, 150))
                    panel = wx.Panel(parent=self)

                    # File browser widget for selecting the file to load/store design rules.
                    file_wildcard = "Design Rule File (*.dru)|*.dru|All Files (*.*)|*.*"
                    self.file_picker = DnDFilePickerCtrl(
                        parent=panel,
                        labelText="File:",
                        buttonText="Browse",
                        toolTip="Drag-and-drop file or browse for file or enter file name.",
                        dialogTitle="Select file to open/save PCB design rules",
                        startDirectory=get_project_directory(),
                        initialValue="",
                        fileMask=file_wildcard,
                        fileMode=wx.FD_OPEN,
                    )
                    self.Bind(
                        wx.EVT_FILEPICKER_CHANGED, self.file_handler, self.file_picker
                    )

                    self.open_btn = wx.Button(panel, label="Open")
                    self.save_btn = wx.Button(panel, label="Save")
                    self.cancel_btn = wx.Button(panel, label="Cancel")
                    self.open_btn.Bind(wx.EVT_BUTTON, self.do_open, self.open_btn)
                    self.save_btn.Bind(wx.EVT_BUTTON, self.do_save, self.save_btn)
                    self.cancel_btn.Bind(wx.EVT_BUTTON, self.cancel, self.cancel_btn)

                    btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
                    btn_sizer.AddSpacer(WIDGET_SPACING)
                    btn_sizer.Add(self.open_btn, flag=wx.ALL)
                    btn_sizer.AddSpacer(WIDGET_SPACING)
                    btn_sizer.Add(self.save_btn, flag=wx.ALL)
                    btn_sizer.AddSpacer(WIDGET_SPACING)
                    btn_sizer.Add(self.cancel_btn, flag=wx.ALL)
                    btn_sizer.AddSpacer(WIDGET_SPACING)

                    # Create a vertical sizer to hold everything in the panel.
                    sizer = wx.BoxSizer(wx.VERTICAL)
                    # sizer.Add(self.netlist_file_picker, 0, wx.ALL | wx.EXPAND, WIDGET_SPACING)
                    sizer.Add(self.file_picker, 0, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, WIDGET_SPACING)
                    sizer.Add(
                        btn_sizer,
                        0,
                        wx.ALL | wx.ALIGN_CENTER,
                        WIDGET_SPACING,
                    )

                    # Size the panel.
                    panel.SetSizer(sizer)
                    panel.Layout()
                    panel.Fit()

                    # Finally, size the frame that holds the panel.
                    self.Fit()

                except Exception as e:
                    debug_dialog("Something went wrong!", e)

            def file_handler(self, evt):
                self.file_name = self.file_picker.GetPath()
                #self.open_btn.SetFocus()

            def do_open(self, evt):
                with open(self.file_name, 'r') as fp:
                    drs = yaml.load(fp, Loader=yaml.Loader)
                    kinjector.DesignRules().inject(drs, pcbnew.GetBoard())
                self.Destroy()

            def do_save(self, evt):
                drs = kinjector.DesignRules().eject(pcbnew.GetBoard())
                try:
                    del drs['settings']['netclass assignments']
                except KeyError:
                    pass
                with open(self.file_name, "w") as fp:
                    yaml.safe_dump(drs, fp, default_flow_style=False)
                self.Destroy()

            def cancel(self, evt):
                self.Destroy()

        self.opensavedlg = OpenSaveDlg()
        self.opensavedlg.Show(True)
        return True


DRMgr().register()
