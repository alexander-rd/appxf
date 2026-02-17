#!/bin/bash
# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: 0BSD

# locale_update.sh: Compile all POs and show statistics

echo "Compiling PO files to MO"
for po_file in src/appxf/locale/*/LC_MESSAGES/appxf-gui.po; do
    if [ -f "$po_file" ]; then
        mo_file="${po_file%.po}.mo"
        echo "Compiling $po_file -> $mo_file"
        msgfmt "$po_file" -o "$mo_file"
    fi
done

echo -e "\nStatistics"

# Show available contexts from POT file
PYTHONPATH=src python -m appxf.locale.po_stats --contexts "src/appxf/locale/appxf-gui.pot"

# Analyze each PO file
for po_file in src/appxf/locale/*/LC_MESSAGES/appxf-gui.po; do
    if [ -f "$po_file" ]; then
        echo -e "\n$po_file:"
        echo -e "  Overall: $(msgfmt --statistics "$po_file" 2>&1)"
        PYTHONPATH=src python -m appxf.locale.po_stats --incomplete "$po_file"
    fi
done

if [ -f ./messages.mo ]; then
    rm ./messages.mo
fi