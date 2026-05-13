"""gettext bootstrap. Loads writer-batch-compress.mo from the bundled
locales/ directory and exposes `_` for translations.
Pattern adapted from extensions/odf-ai-service.
"""

import gettext

import easymacro as app

APPNAME = "writer-batch-compress"
ID_EXTENSION = "org.ossii.WriterBatchCompress"

PATH_EXT = app.paths.extension(ID_EXTENSION)
PATH_LOCALES = app.paths.join(PATH_EXT, "locales")

t = gettext.translation(APPNAME, PATH_LOCALES, fallback=True)
_ = t.gettext
