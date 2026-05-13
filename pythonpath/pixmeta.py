"""Pure-Python helpers for reading picture metadata out of an odt zip.

Replaces the brittle BASIC parser that walked content.xml char-by-char.
zipfile + ElementTree handle long offsets and namespaces correctly.
"""

import zipfile
from xml.etree import ElementTree as ET

DRAW_NS = "{urn:oasis:names:tc:opendocument:xmlns:drawing:1.0}"
XLINK_NS = "{http://www.w3.org/1999/xlink}"


def picture_sizes(odt_path):
    """Return {filename: size_bytes} for every entry under Pictures/."""
    sizes = {}
    with zipfile.ZipFile(odt_path, "r") as zf:
        for info in zf.infolist():
            if info.filename.startswith("Pictures/") and not info.filename.endswith("/"):
                sizes[info.filename[len("Pictures/"):]] = info.file_size
    return sizes


def picture_meta(odt_path):
    """Return [{filename, ext, size, width, height}, ...] for every Pictures/*.

    width/height are decoded from the file header when the format is one we
    can parse cheaply (PNG, GIF). For other formats we leave them at 0 and
    callers fall back to matching by (size, ext).
    """
    out = []
    with zipfile.ZipFile(odt_path, "r") as zf:
        for info in zf.infolist():
            if not info.filename.startswith("Pictures/") or info.filename.endswith("/"):
                continue
            name = info.filename[len("Pictures/"):]
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            with zf.open(info) as f:
                head = f.read(32)
            w, h = _decode_dims(head)
            out.append({"filename": name, "ext": ext,
                        "size": info.file_size, "width": w, "height": h})
    return out


def _decode_dims(head):
    if head[:8] == b"\x89PNG\r\n\x1a\n" and len(head) >= 24:
        return (int.from_bytes(head[16:20], "big"),
                int.from_bytes(head[20:24], "big"))
    if head[:6] in (b"GIF87a", b"GIF89a") and len(head) >= 10:
        return (int.from_bytes(head[6:8], "little"),
                int.from_bytes(head[8:10], "little"))
    return (0, 0)


def picture_order(odt_path):
    """Filenames of <draw:image> hrefs in document order.

    Matches the order in which LibreOffice's DrawPage enumerates picture
    shapes, so callers can index into this list with the picture's
    position in DrawPage.
    """
    with zipfile.ZipFile(odt_path, "r") as zf:
        tree = ET.parse(zf.open("content.xml"))
    order = []
    for elem in tree.iter(f"{DRAW_NS}image"):
        href = elem.get(f"{XLINK_NS}href", "")
        if href.startswith("Pictures/"):
            order.append(href[len("Pictures/"):])
    return order
