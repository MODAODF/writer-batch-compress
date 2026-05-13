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
    # Forbid the user from closing the progress window mid-loop. If the
    # window goes away while pixcompress.resample is still iterating,
    # the next advance() lands on a disposed peer and the whole run
    # falls over.
    dlg_model.Closeable = False

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
    _pump(toolkit)

    return _Handle(dialog, dialog.getControl("bar"), toolkit)


def _pump(toolkit):
    try:
        toolkit.processEventsToIdle()
    except AttributeError:
        pass


class _Handle:
    def __init__(self, dialog, bar, toolkit):
        self._dialog = dialog
        self._bar = bar
        self._toolkit = toolkit
        self._closed = False

    def advance(self, value):
        if self._closed:
            return
        try:
            self._bar.setValue(value)
            _pump(self._toolkit)
        except Exception:
            self._closed = True

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self._dialog.setVisible(False)
            self._dialog.dispose()
        except Exception:
            pass
