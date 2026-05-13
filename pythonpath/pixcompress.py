import traceback

import easymacro as app

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
        app.msgbox("PixCompress error:\n\n" + traceback.format_exc())


def _run():
    doc = app.active
    if doc is None or doc.type != "writer":
        app.msgbox("Open a Writer document first.")
        return
    if not doc.path:
        app.msgbox("Save the document before compressing its pictures.")
        return

    pictures = _analyze(doc)
    if not pictures:
        app.msgbox("No pictures found in this document.")
        return

    sel_idx = _selected_picture_index(doc, pictures)
    total_kb = sum(p.size_bytes for p in pictures) / 1000
    opts = pixdialog.ask_options([p.label for p in pictures], sel_idx, total_kb)
    if opts is None:
        return
    dpi, quality, compression, action = opts

    targets = pictures if action == "all" else [pictures[sel_idx]]
    before = sum(p.size_bytes for p in pictures)

    progress = pixprogress.create("Compressing pictures...", len(targets))
    compressed = skipped = 0
    try:
        for i, pic in enumerate(targets):
            if pixresample.resample(pic.shape, dpi, quality, compression):
                compressed += 1
            else:
                skipped += 1
            progress.advance(i + 1)
    finally:
        progress.close()

    new_url = _compressed_url(doc.obj.URL)
    doc.obj.storeToURL(new_url, ())

    after = sum(pixmeta.picture_sizes(_url_to_path(new_url)).values())
    app.msgbox(
        f"Compressed {compressed}, skipped {skipped} (vector/unsupported).\n"
        f"Pictures: {before/1000:,.2f} KB > {after/1000:,.2f} KB\n"
        f"Saved to: {new_url}"
    )


def _analyze(doc):
    progress = pixprogress.create("Analyzing pictures...", 2)
    try:
        sizes = pixmeta.picture_sizes(doc.path)
        order = pixmeta.picture_order(doc.path)
        progress.advance(1)

        pictures = []
        pic_idx = 0
        for shape in doc.draw_page:
            if not _is_picture(shape.obj):
                continue
            zip_name = order[pic_idx] if pic_idx < len(order) else ""
            size_bytes = sizes.get(zip_name, 0)
            graphic = shape.obj.Graphic
            ext = graphic.MimeType.split("/")[-1] if graphic else "?"
            label = f"{shape.obj.Name}  ({ext})  {size_bytes/1000:,.2f} KB"
            pictures.append(_Picture(shape.obj, shape.obj.Name, label, size_bytes))
            pic_idx += 1
        progress.advance(2)
    finally:
        progress.close()
    return pictures


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
