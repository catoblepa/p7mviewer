PREFIX ?= /app

.PHONY: install install-bin install-data install-locales

install: install-bin install-data install-locales

install-bin:
	install -Dm755 p7mviewer.py $(PREFIX)/bin/p7mviewer.py
	install -Dm644 signature_parser.py $(PREFIX)/bin/signature_parser.py

install-data:
	install -Dm644 io.github.catoblepa.p7mviewer.svg $(PREFIX)/share/icons/hicolor/scalable/apps/io.github.catoblepa.p7mviewer.svg
	install -Dm644 io.github.catoblepa.p7mviewer.desktop $(PREFIX)/share/applications/io.github.catoblepa.p7mviewer.desktop
	install -Dm644 io.github.catoblepa.p7mviewer.metainfo.xml $(PREFIX)/share/metainfo/io.github.catoblepa.p7mviewer.metainfo.xml

install-locales:
	for po_file in locale/*/LC_MESSAGES/*.po; do \
		lang=$$(basename $$(dirname $$(dirname "$$po_file"))); \
		mkdir -p "$(PREFIX)/share/locale/$$lang/LC_MESSAGES"; \
		msgfmt -o "$(PREFIX)/share/locale/$$lang/LC_MESSAGES/io.github.catoblepa.p7mviewer.mo" "$$po_file"; \
	done
