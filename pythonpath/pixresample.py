"""Bitmap resampling via com.sun.star.graphic.GraphicProvider.

We deliberately avoid com.sun.star.drawing.GraphicExportFilter: for
Writer raster shapes its setSourceDocument path pulls the original
Graphic property and ignores FilterData entirely
(svx/source/unodraw/UnoGraphicExporter.cxx). GraphicProvider routes
through ImplApplyFilterData -> BitmapEx::Scale, which honours
PixelWidth/PixelHeight and applies Lanczos by default.
"""

import os
import tempfile
import uno

_CTX = uno.getComponentContext()
_SM = _CTX.getServiceManager()

_DIAG_FIRED = [False]

# JPEG keeps JPEG; everything else converts to PNG to preserve any
# alpha channel. Vector formats are silently skipped.
_RASTER_TARGETS = {
    "image/jpeg": "image/jpeg",
    "image/png":  "image/png",
    "image/bmp":  "image/png",
    "image/gif":  "image/png",
    "image/tiff": "image/png",
    "image/x-ms-bmp": "image/png",
}


def _prop(name, value):
    p = uno.createUnoStruct("com.sun.star.beans.PropertyValue")
    p.Name = name
    p.Value = value
    return p


def resample(img, dpi, quality, compression):
    """Resample one Writer/Draw raster shape in place.

    Returns True on success, False if the image is vector / unsupported
    or if the round-trip through GraphicProvider fails.
    """
    graphic = img.Graphic
    if graphic is None:
        return False
    target_mime = _RASTER_TARGETS.get(graphic.MimeType)
    if target_mime is None:
        return False

    size = img.Size  # com.sun.star.awt.Size, units of 1/100 mm
    pixel_w = max(1, int(size.Width * dpi / 2540))
    pixel_h = max(1, int(size.Height * dpi / 2540))

    filter_data = [
        _prop("PixelWidth", pixel_w),
        _prop("PixelHeight", pixel_h),
    ]
    if target_mime == "image/jpeg":
        filter_data.append(_prop("Quality", quality))
    else:
        filter_data.append(_prop("Compression", compression))

    fd, tmp_path = tempfile.mkstemp(prefix="pixcompress_", suffix=".tmp")
    os.close(fd)
    tmp_url = uno.systemPathToFileUrl(tmp_path)

    provider = _SM.createInstanceWithContext(
        "com.sun.star.graphic.GraphicProvider", _CTX)
    tmp_after = -1
    png_w = png_h = -1
    new_graphic = None
    try:
        provider.storeGraphic(graphic, tuple([
            _prop("URL", tmp_url),
            _prop("MimeType", target_mime),
            _prop("FilterData", tuple(filter_data)),
        ]))
        try:
            tmp_after = os.path.getsize(tmp_path)
            if target_mime == "image/png" and tmp_after > 24:
                with open(tmp_path, "rb") as f:
                    head = f.read(24)
                if head[:8] == b"\x89PNG\r\n\x1a\n":
                    png_w = int.from_bytes(head[16:20], "big")
                    png_h = int.from_bytes(head[20:24], "big")
        except OSError:
            pass
        new_graphic = provider.queryGraphic(tuple([_prop("URL", tmp_url)]))
        if new_graphic is not None:
            img.Graphic = new_graphic
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    if not _DIAG_FIRED[0]:
        _DIAG_FIRED[0] = True
        import easymacro as app
        app.msgbox(
            f"DIAG resample first call:\n"
            f"  src MimeType    = {graphic.MimeType}\n"
            f"  Size 1/100mm    = {size.Width} x {size.Height}\n"
            f"  target pixels   = {pixel_w} x {pixel_h}\n"
            f"  temp file bytes = {tmp_after}\n"
            f"  actual PNG WxH  = {png_w} x {png_h}\n"
            f"  new_graphic     = {'OK' if new_graphic else 'None'}"
        )

    return new_graphic is not None
