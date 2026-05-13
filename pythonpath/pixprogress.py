"""Tiny non-modal progress dialog.

LibreOffice's status bar is too unobtrusive (and seems to be swallowed
during long Python loops). easymacro doesn't wrap UnoControlProgressBar,
so build the dialog directly through UNO — same pattern as the BASIC
CreeBarre helper used.
"""

import uno


def create(title, total):
    ctx = uno.getComponentContext()
    smgr = ctx.ServiceManager

    dlg_model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx)
    dlg_model.PositionX = 200
    dlg_model.PositionY = 200
    dlg_model.Width = 200
    dlg_model.Height = 22
    dlg_model.Title = title

    bar_model = dlg_model.createInstance(
        "com.sun.star.awt.UnoControlProgressBarModel")
    bar_model.PositionX = 3
    bar_model.PositionY = 3
    bar_model.Width = 194
    bar_model.Height = 16
    bar_model.ProgressValueMin = 0
    bar_model.ProgressValueMax = max(1, total)
    bar_model.ProgressValue = 0
    dlg_model.insertByName("bar", bar_model)

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx)
    dialog.setModel(dlg_model)
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    dialog.createPeer(toolkit, None)
    dialog.setVisible(True)

    return _Handle(dialog, dialog.getControl("bar"))


class _Handle:
    def __init__(self, dialog, bar):
        self._dialog = dialog
        self._bar = bar

    def advance(self, value):
        self._bar.setValue(value)

    def close(self):
        self._dialog.setVisible(False)
        self._dialog.dispose()
