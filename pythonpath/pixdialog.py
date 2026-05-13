"""Modal options dialog: DPI / JPEG quality / PNG compression."""

import easymacro as app

DEFAULTS = {
    "dpi": 96,
    "quality": 80,
    "compression": 6,
}

_FIELDS = (
    ("numDPI",         "DPI:",             DEFAULTS["dpi"],          72, 600),
    ("numQuality",     "JPEG quality:",    DEFAULTS["quality"],       1,  99),
    ("numCompression", "PNG compression:", DEFAULTS["compression"],   1,   9),
)


class _Controller:
    def __init__(self, dialog):
        self.d = dialog

    def cmd_ok_action(self, event):
        self.d.close(1)

    def cmd_cancel_action(self, event):
        self.d.close(0)


def ask_options(title="PixCompress"):
    """Show the options dialog. Returns (dpi, quality, compression) or None."""
    dlg = app.dialog.create({
        "Title": title,
        "Width": 180,
        "Height": 110,
    })
    dlg.events = _Controller

    y = 10
    for name, label, default, vmin, vmax in _FIELDS:
        dlg.add_control({
            "Type": "Label",
            "Name": f"lbl_{name}",
            "Label": label,
            "X": 10, "Y": y + 2, "Width": 90, "Height": 14,
        })
        dlg.add_control({
            "Type": "numeric",
            "Name": name,
            "Value": default,
            "ValueMin": vmin,
            "ValueMax": vmax,
            "DecimalAccuracy": 0,
            "Spin": True,
            "X": 105, "Y": y, "Width": 60, "Height": 14,
        })
        y += 20

    dlg.add_control({
        "Type": "button", "Name": "cmd_ok",
        "Label": "Compress", "DefaultButton": True, "PushButtonType": 1,
        "X": 30, "Y": 85, "Width": 60, "Height": 18,
    })
    dlg.add_control({
        "Type": "button", "Name": "cmd_cancel",
        "Label": "Cancel", "PushButtonType": 2,
        "X": 100, "Y": 85, "Width": 60, "Height": 18,
    })

    if not dlg.open():
        return None
    return dlg.numDPI.int, dlg.numQuality.int, dlg.numCompression.int
