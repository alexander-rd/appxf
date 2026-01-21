#!/bin/bash

# locale_scan.sh: Scan code to fill POT, update all POs from POT, compile all POs and show statistics

echo "Compiling PO files to MO"
for po_file in locale/*/LC_MESSAGES/appxf-gui.po; do
    if [ -f "$po_file" ]; then
        mo_file="${po_file%.po}.mo"
        echo "Compiling $po_file -> $mo_file"
        msgfmt "$po_file" -o "$mo_file"
    fi
done

echo -e "\nStatistics"
for po_file in locale/*/LC_MESSAGES/appxf-gui.po; do
    if [ -f "$po_file" ]; then
        mo_file="${po_file%.po}.mo"
        echo -e -n "$po_file:\n  "
        msgfmt --statistics "$po_file" 2>&1
    fi
done

rm ./messages.mo