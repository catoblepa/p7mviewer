#!/bin/bash
# Compila tutte le traduzioni PO in MO per Flatpak
for po in */LC_MESSAGES/io.github.catoblepa.p7mviewer.po; do
  msgfmt -o "${po/.po/.mo}" "$po"
done
