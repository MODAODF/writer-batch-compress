import easymacro as app


def run():
    """Entry point invoked from main.MainJob.trigger.

    Stage 1 of the Python rewrite — just confirms wiring works end to
    end. Real compression logic lands in later stages.
    """
    doc = app.active
    if doc is None or doc.type != "writer":
        app.msgbox("Open a Writer document first.")
        return
    app.msgbox(f"PixCompress (Python) reached. Document: {doc.title}")
