import tempfile
from pathlib import Path
import traceback

import easymacro as app

from pixi18n import _

import pixdialog
import pixmeta
import pixprogress
import pixresample

_GRAPHIC_SERVICES = (
    "com.sun.star.text.TextGraphicObject",
    "com.sun.star.drawing.GraphicObjectShape",
)


def _is_picture(shape):
    return any(shape.supportsService(s) for s in _GRAPHIC_SERVICES)


class _Picture:
    __slots__ = ("shape", "name", "label", "size_bytes")

    def __init__(self, shape, name, label, size_bytes):
        self.shape = shape
        self.name = name
        self.label = label
        self.size_bytes = size_bytes


def run():
    try:
        _run()
    except Exception:
        app.msgbox(_("PixCompress error:\n\n{tb}").format(tb=traceback.format_exc()))


def _run():
    doc = app.active
    if doc is None or doc.type != "writer":
        app.msgbox(_("Open a Writer document first."))
        return
    if not doc.path:
        app.msgbox(_("Save the document before compressing its pictures."))
        return

    pictures, before = _analyze(doc)
    if not pictures:
        app.msgbox(_("No pictures found in this document."))
        return

    sel_idx = _selected_picture_index(doc, pictures)
    total_kb = before / 1000
    opts = pixdialog.ask_options([p.label for p in pictures], sel_idx, total_kb)
    if opts is None:
        return
    dpi, quality, compression, action, list_positions = opts

    if action == "selected" and list_positions:
        targets = [pictures[p] for p in list_positions
                   if 0 <= p < len(pictures)]
    else:
        targets = pictures

    progress = pixprogress.create(_("Compressing pictures..."), len(targets))
    compressed = skipped = 0
    try:
        for i, pic in enumerate(targets):
            try:
                ok = pixresample.resample(pic.shape, dpi, quality, compression)
            except Exception:
                ok = False
            if ok:
                compressed += 1
            else:
                skipped += 1
            progress.advance(i + 1)
    finally:
        progress.close()

    new_url = _compressed_url(doc.obj.URL)
    doc.obj.storeToURL(new_url, ())

    after = sum(pixmeta.picture_sizes(_url_to_path(new_url)).values())
    app.msgbox("\n".join([
        _("Compressed {c}, skipped {s} (vector/unsupported).").format(
            c=compressed, s=skipped),
        _("Pictures: {before} KB > {after} KB").format(
            before=f"{before/1000:,.2f}", after=f"{after/1000:,.2f}"),
        _("Saved to: {url}").format(url=new_url),
    ]))


def _analyze(doc):
    progress = pixprogress.create(_("Analyzing pictures..."), 2)
    try:
        # Export the current model, including edits not saved to doc.path.
        # storeToURL preserves the document's URL and does not save the original.
        import uno
        with tempfile.TemporaryDirectory(prefix="pixcompress_analysis_") as tmp:
            snapshot = Path(tmp) / "snapshot.odt"
            doc.obj.storeToURL(
                uno.systemPathToFileUrl(str(snapshot)),
                app.dict_to_property({"FilterName": "writer8"}),
            )
            frames = pixmeta.picture_frames(snapshot)
            total = sum(pixmeta.picture_sizes(snapshot).values())
        progress.advance(1)

        pictures = []
        for shape in doc.draw_page:
            if not _is_picture(shape.obj):
                continue
            graphic = shape.obj.Graphic
            ext = (graphic.MimeType.split("/")[-1] if graphic else "").lower()
            if ext == "jpeg":
                ext = "jpg"
            size_bytes = frames.get(shape.obj.Name)
            size_label = (f"{size_bytes/1000:,.2f} KB"
                          if size_bytes is not None else "?")
            label = f"{shape.obj.Name}  ({ext})  {size_label}"
            pictures.append(_Picture(shape.obj, shape.obj.Name, label, size_bytes))
        progress.advance(2)
    finally:
        progress.close()
    return pictures, total


def _selected_picture_index(doc, pictures):
    sel = doc.obj.CurrentSelection
    if sel is None:
        return -1
    impl = getattr(sel, "ImplementationName", "")
    if impl not in ("SwXTextGraphicObject", "SwXShape"):
        return -1
    name = getattr(sel, "Name", "")
    for i, p in enumerate(pictures):
        if p.name == name:
            return i
    return -1


def _compressed_url(url):
    dot = url.rfind(".")
    slash = url.rfind("/")
    if dot > slash:
        return url[:dot] + "-compressed" + url[dot:]
    return url + "-compressed"


def _url_to_path(url):
    import uno
    return uno.fileUrlToSystemPath(url)
