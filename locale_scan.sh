#!/bin/bash

# locale_scan.sh: Scan code to fill POT, update all POs from POT, compile all POs and show statistics

set -e

echo "Scanning code for translatable strings..."
# Extract POT from all Python files in src/
pygettext3 -d appxf-gui -o locale/appxf-gui.pot $(find src -name "*.py")
echo ".. done."

echo -e "\nUpdating PO files from POT..."
# Update all PO files
for po_file in locale/*/LC_MESSAGES/appxf-gui.po; do
    if [ -f "$po_file" ]; then
        echo "Updating $po_file"
        msgmerge --update --backup=none "$po_file" locale/appxf-gui.pot
    fi
done

# Compile PO files and run statistics:
echo -e ""
./locale_update.sh