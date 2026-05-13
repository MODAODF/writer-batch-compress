import easymacro as app

import pixmeta
import pixresample

_GRAPHIC_SERVICES = (
    "com.sun.star.text.TextGraphicObject",
    "com.sun.star.drawing.GraphicObjectShape",
)


def _is_picture(shape):
    return any(shape.supportsService(s) for s in _GRAPHIC_SERVICES)


def run():
    doc = app.active
    if doc is None or doc.type != "writer":
        app.msgbox("Open a Writer document first.")
        return
    if not doc.path:
        app.msgbox("Save the document before compressing its pictures.")
        return

    # Stage 3: hardcoded params; dialog comes in stage 4.
    dpi, quality, compression = 96, 80, 6

    before = sum(pixmeta.picture_sizes(doc.path).values())

    compressed = skipped = 0
    for shape in doc.draw_page:
        if _is_picture(shape.obj):
            if pixresample.resample(shape.obj, dpi, quality, compression):
                compressed += 1
            else:
                skipped += 1

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
