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

    opts = pixdialog.ask_options()
    if opts is None:
        return
    dpi, quality, compression = opts

    progress = pixprogress.create("Analyzing pictures...", 1)
    try:
        before = sum(pixmeta.picture_sizes(doc.path).values())
        shapes = [s for s in doc.draw_page if _is_picture(s.obj)]
        progress.advance(1)
    finally:
        progress.close()

    progress = pixprogress.create("Compressing pictures...", len(shapes))
    compressed = skipped = 0
    try:
        for i, shape in enumerate(shapes):
            if pixresample.resample(shape.obj, dpi, quality, compression):
                compressed += 1
            else:
                skipped += 1
            progress.advance(i + 1)
    finally:
        progress.close()

    new_url = _compressed_url(doc.obj.URL)
    doc.obj.storeToURL(new_url, ())

    after = sum(pixmeta.picture_sizes(uno_url_to_path(new_url)).values())
    app.msgbox(
        f"Compressed {compressed}, skipped {skipped} (vector/unsupported).\n"
        f"Pictures: {before/1000:,.2f} KB > {after/1000:,.2f} KB\n"
        f"Saved to: {new_url}"
    )


def _compressed_url(url):
    """Insert '-compressed' before the file extension of a file:// URL."""
    dot = url.rfind(".")
    slash = url.rfind("/")
    if dot > slash:
        return url[:dot] + "-compressed" + url[dot:]
    return url + "-compressed"


def uno_url_to_path(url):
    import uno
    return uno.fileUrlToSystemPath(url)
