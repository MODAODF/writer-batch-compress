"""Modal options dialog: picture list + DPI / JPEG quality / PNG compression."""

import unohelper

from com.sun.star.awt import XItemListener

import easymacro as app

DEFAULTS = {
    "dpi": 96,
    "quality": 80,
    "compression": 6,
}

DPI_PRESETS = ("96", "150", "200", "300", "600")

_NUMERIC_FIELDS = (
    ("numQuality",     "JPEG quality:",    DEFAULTS["quality"],       1,  99),
    ("numCompression", "PNG compression:", DEFAULTS["compression"],   1,   9),
)


class _Controller:
    def __init__(self, dialog):
        self.d = dialog
        self.action = None
        self.selected_positions = ()

    def on_listbox_change(self):
        sels = self.d.lstImages.obj.getSelectedItemsPos()
        self.d.cmd_selected.model.Enabled = len(sels) > 0

    def cmd_all_action(self, event):
        self.action = "all"
        self.d.close(1)

    def cmd_selected_action(self, event):
        self.action = "selected"
        self.selected_positions = tuple(self.d.lstImages.obj.getSelectedItemsPos())
        self.d.close(1)

    def cmd_cancel_action(self, event):
        self.d.close(0)


class _ListboxListener(unohelper.Base, XItemListener):
    def __init__(self, controller):
        self.controller = controller

    def itemStateChanged(self, event):
        self.controller.on_listbox_change()

    def disposing(self, event):
        pass


def ask_options(picture_labels, selected_index=-1, total_kb=0.0):
    """Show the options dialog.

    Returns (dpi, quality, compression, action, list_pos) where action is
    'all' / 'selected' (list_pos is the chosen picture's index inside
    picture_labels), or None if the user cancelled.
    """
    has_doc_selection = 0 <= selected_index < len(picture_labels)
    dlg = app.dialog.create({
        "Title": "PixCompress",
        "Width": 320,
        "Height": 180,
    })
    dlg.events = _Controller

    dlg.add_control({
        "Type": "listbox", "Name": "lstImages",
        "MultiSelection": True,
        "X": 5, "Y": 5, "Width": 180, "Height": 140,
    })
    lst = dlg.lstImages.obj
    for i, label in enumerate(picture_labels):
        lst.addItem(label, i)
    if has_doc_selection:
        lst.selectItemPos(selected_index, True)
    lst.addItemListener(_ListboxListener(dlg.events))

    dlg.add_control({
        "Type": "Label", "Name": "lblTotal",
        "Label": f"Total: {total_kb:,.2f} KB ({len(picture_labels)} pictures)",
        "X": 5, "Y": 148, "Width": 180, "Height": 12,
    })

    y = 10
    dlg.add_control({
        "Type": "Label", "Name": "lblDPI", "Label": "DPI:",
        "X": 190, "Y": y + 2, "Width": 50, "Height": 14,
    })
    dlg.add_control({
        "Type": "combobox", "Name": "numDPI",
        "Text": str(DEFAULTS["dpi"]), "Dropdown": True,
        "X": 245, "Y": y, "Width": 65, "Height": 14,
    })
    combo = dlg.numDPI.obj
    for pos, val in enumerate(DPI_PRESETS):
        combo.addItem(val, pos)
    y += 20

    for name, label, default, vmin, vmax in _NUMERIC_FIELDS:
        dlg.add_control({
            "Type": "Label", "Name": f"lbl_{name}", "Label": label,
            "X": 190, "Y": y + 2, "Width": 50, "Height": 14,
        })
        dlg.add_control({
            "Type": "numeric", "Name": name,
            "Value": default, "ValueMin": vmin, "ValueMax": vmax,
            "DecimalAccuracy": 0, "Spin": True,
            "X": 245, "Y": y, "Width": 65, "Height": 14,
        })
        y += 20

    by = 80
    dlg.add_control({
        "Type": "button", "Name": "cmd_all",
        "Label": "Compress all",
        "X": 190, "Y": by, "Width": 120, "Height": 18,
    })
    dlg.add_control({
        "Type": "button", "Name": "cmd_selected",
        "Label": "Compress selected",
        "X": 190, "Y": by + 22, "Width": 120, "Height": 18,
    })
    dlg.add_control({
        "Type": "button", "Name": "cmd_cancel",
        "Label": "Cancel", "PushButtonType": 2,
        "X": 190, "Y": by + 44, "Width": 120, "Height": 18,
    })
    dlg.cmd_selected.model.Enabled = has_doc_selection
    dlg.cmd_all.model.DefaultButton = not has_doc_selection
    dlg.cmd_selected.model.DefaultButton = has_doc_selection

    if dlg.open() == 0:
        return None
    ctrl = dlg.events
    if ctrl.action is None:
        return None
    try:
        dpi = int(dlg.numDPI.value)
    except ValueError:
        dpi = DEFAULTS["dpi"]
    dpi = max(72, min(600, dpi))
    return (dpi, dlg.numQuality.int, dlg.numCompression.int,
            ctrl.action, ctrl.selected_positions)
