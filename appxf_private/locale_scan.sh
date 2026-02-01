#!/bin/bash

# locale_scan.sh: Scan code to fill POT, update all POs from POT, compile all POs and show statistics

set -e

echo "Scanning code for translatable strings..."
# Extract POT from all Python files in src/ with context support
# _:1c,2 means: first arg is context, second is message
xgettext --language=Python --keyword=_ --keyword=_:1c,2 \
    --from-code=UTF-8 --output=src/appxf/locale/appxf-gui.pot \
    --package-name=appxf-gui \
    $(find src -name "*.py")
echo ".. done."

echo -e "\nUpdating PO files from POT..."
# Update all PO files
for po_file in src/appxf/locale/*/LC_MESSAGES/appxf-gui.po; do
    if [ -f "$po_file" ]; then
        echo "Updating $po_file"
        msgmerge --update --backup=none "$po_file" locale/appxf-gui.pot
    fi
done

# Compile PO files and run statistics:
echo -e ""
./locale_update.sh