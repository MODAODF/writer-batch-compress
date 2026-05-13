import easymacro as app

import pixmeta


def run():
    doc = app.active
    if doc is None or doc.type != "writer":
        app.msgbox("Open a Writer document first.")
        return
    if not doc.path:
        app.msgbox("Save the document before compressing its pictures.")
        return

    sizes = pixmeta.picture_sizes(doc.path)
    order = pixmeta.picture_order(doc.path)

    lines = [f"Total pictures in zip: {len(sizes)}",
             f"Pictures in content.xml order: {len(order)}",
             ""]
    for i, name in enumerate(order[:5]):
        size_kb = sizes.get(name, 0) / 1000
        lines.append(f"  [{i}] {name}  {size_kb:,.2f} KB")
    if len(order) > 5:
        lines.append(f"  ... and {len(order) - 5} more")

    app.msgbox("\n".join(lines))
