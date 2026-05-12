#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

PRJNAME = writer-batch-compress
VERNUM = `cat VERSION`

FILES = \
    Addons.xcu \
    META-INF/manifest.xml \
    description.xml \
    logo.png \
    pkg-desc/pkg-description.en \
    pkg-desc/pkg-description.zh-tw \
    registration/Licence_CeCILL_V2-en.txt \
    icons/ \
    PixCompress/ \
    README.md \
    VERSION

all: $(FILES)
	$(shell ./update_version.sh)
	zip -r $(PRJNAME)-$(VERNUM).oxt $(FILES) VERSION
