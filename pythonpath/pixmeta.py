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
