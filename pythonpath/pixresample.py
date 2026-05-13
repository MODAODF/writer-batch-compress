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

from easymacro import dict_to_property

_CTX = uno.getComponentContext()
_SM = _CTX.getServiceManager()

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

    filter_dict = {"PixelWidth": pixel_w, "PixelHeight": pixel_h}
    if target_mime == "image/jpeg":
        filter_dict["Quality"] = quality
    else:
        filter_dict["Compression"] = compression
    # PyUNO needs an explicit [] type for nested PropertyValue sequences,
    # otherwise LibreOffice silently ignores FilterData entries and the
    # bitmap is exported at its native resolution.
    filter_data = dict_to_property(filter_dict, uno_any=True)

    fd, tmp_path = tempfile.mkstemp(prefix="pixcompress_", suffix=".tmp")
    os.close(fd)
    tmp_url = uno.systemPathToFileUrl(tmp_path)

    provider = _SM.createInstanceWithContext(
        "com.sun.star.graphic.GraphicProvider", _CTX)
    new_graphic = None
    try:
        provider.storeGraphic(graphic, dict_to_property({
            "URL": tmp_url,
            "MimeType": target_mime,
            "FilterData": filter_data,
        }))
        new_graphic = provider.queryGraphic(dict_to_property({"URL": tmp_url}))
        if new_graphic is not None:
            img.Graphic = new_graphic
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return new_graphic is not None
