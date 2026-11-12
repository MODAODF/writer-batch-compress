"""Pure-Python helpers for reading picture metadata out of an odt zip.

Replaces the brittle BASIC parser that walked content.xml char-by-char.
zipfile + ElementTree handle long offsets and namespaces correctly.
"""

import posixpath
from urllib.parse import unquote
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


def picture_frames(odt_path):
    """Map unique draw:frame names to embedded image sizes, or None.

    Frame names identify Writer/Draw objects independently of enumeration order.
    Repeated references retain their size. Ambiguous names, external links,
    missing resources and frames with multiple image representations are unknown.
    Headers/footers can live in styles.xml rather than content.xml.
    """
    frames = {}
    with zipfile.ZipFile(odt_path) as zf:
        sizes = {info.filename: info.file_size for info in zf.infolist()
                 if not info.is_dir()}
        for xml_name in ("content.xml", "styles.xml"):
            if xml_name not in sizes:
                continue
            with zf.open(xml_name) as stream:
                tree = ET.parse(stream)
            for frame in tree.iter(f"{DRAW_NS}frame"):
                images = frame.findall(f"{DRAW_NS}image")
                if not images:
                    continue
                name = frame.get(f"{DRAW_NS}name")
                if not name:
                    continue
                size = None
                if len(images) == 1:
                    href = unquote(images[0].get(f"{XLINK_NS}href", ""))
                    path = posixpath.normpath(href)
                    if path.startswith("Pictures/"):
                        size = sizes.get(path)
                frames[name] = None if name in frames else size
    return frames
